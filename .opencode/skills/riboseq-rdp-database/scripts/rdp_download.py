#!/usr/bin/env python3
"""Preview or download explicitly provided public RDP data links.

No URL guessing; HTTPS-only and exact host allowlisting. Dry run by default.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import ipaddress
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

USER_AGENT = "riboseq-rdp-skill/1.0 (public academic data retrieval)"
DEFAULT_HOSTS = {"rdp.ucc.ie"}


class DownloadError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def safe_filename(name: str) -> str:
    if not name or name in (".", "..") or name.startswith("."):
        raise DownloadError("Filename must be a non-hidden simple basename")
    if "/" in name or "\\" in name or "\x00" in name or any(ord(c) < 32 for c in name):
        raise DownloadError(f"Unsafe filename: {name!r}")
    return name


def safe_url(url: str, allowed_hosts: set[str]) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() != "https" or not parts.hostname or parts.username or parts.password:
        raise DownloadError("Only credential-free HTTPS URLs are allowed")
    try:
        port = parts.port
    except ValueError as exc:
        raise DownloadError("Invalid URL port") from exc
    if port not in (None, 443):
        raise DownloadError("Only the standard HTTPS port 443 is supported")
    host = parts.hostname.lower().rstrip(".")
    if host not in allowed_hosts:
        raise DownloadError(f"Host {host!r} is not allowlisted; add --allow-host after review")
    if host == "localhost" or host.endswith(".local"):
        raise DownloadError("Local hosts are not allowed")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise DownloadError("IP-literal URLs are not allowed")
    return url.strip()


def read_manifest(path: Path) -> list[tuple[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or set(reader.fieldnames) != {"url", "filename"}:
            raise DownloadError("Manifest must have exactly two headers: url,filename")
        rows = []
        for index, row in enumerate(reader, 2):
            if None in row:
                raise DownloadError(f"Extra CSV values at line {index}")
            if not row["url"] and not row["filename"]:
                continue
            rows.append((row["url"].strip(), safe_filename(row["filename"].strip())))
    if not rows:
        raise DownloadError("Manifest has no download rows; populate it from actual portal links")
    if len({name for _, name in rows}) != len(rows):
        raise DownloadError("Manifest has duplicate destination filenames")
    return rows


def follow_allowed_redirects(url: str, allowed_hosts: set[str], *, timeout: int):
    opener = build_opener(NoRedirect())
    current = safe_url(url, allowed_hosts)
    for _ in range(6):
        request = Request(current, headers={"User-Agent": USER_AGENT})
        try:
            response = opener.open(request, timeout=timeout)
            return response, current
        except HTTPError as exc:
            if exc.code not in (301, 302, 303, 307, 308):
                raise DownloadError(f"HTTP {exc.code} for {current}") from exc
            location = exc.headers.get("Location")
            exc.close()
            if not location:
                raise DownloadError("Redirect missing Location header")
            current = safe_url(urljoin(current, location), allowed_hosts)
        except (URLError, TimeoutError, socket.timeout) as exc:
            raise DownloadError(f"Network request failed: {exc}") from exc
    raise DownloadError("Too many redirects")


def download_one(url: str, filename: str, *, dest: Path, allowed_hosts: set[str],
                 max_bytes: int, timeout: int, overwrite: bool) -> dict:
    path = dest / safe_filename(filename)
    if path.exists() and not overwrite:
        raise DownloadError(f"Destination exists: {path} (use --overwrite to replace)")
    response, final_url = follow_allowed_redirects(url, allowed_hosts, timeout=timeout)
    part = dest / (filename + ".part")
    total = 0
    hasher = hashlib.sha256()
    part_created = False
    try:
        size_header = response.headers.get("Content-Length")
        if size_header and size_header.isdecimal() and int(size_header) > max_bytes:
            raise DownloadError(f"Content-Length exceeds max size ({max_bytes} bytes)")
        # Refuse an existing partial file rather than deleting another download's work.
        with part.open("xb") as out:
            part_created = True
            while True:
                block = response.read(min(1024 * 1024, max_bytes - total + 1))
                if not block:
                    break
                total += len(block)
                if total > max_bytes:
                    raise DownloadError(f"Stream exceeded maximum size ({max_bytes} bytes)")
                out.write(block)
                hasher.update(block)
        os.replace(part, path)
    finally:
        response.close()
        if part_created:
            part.unlink(missing_ok=True)
    return {"retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "url": url, "final_url": final_url, "filename": filename,
            "bytes": total, "sha256": hasher.hexdigest()}


def parser_factory() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path, help="CSV: url,filename")
    source.add_argument("--url", help="Single HTTPS download URL copied from portal")
    p.add_argument("--filename", help="Destination basename for --url")
    p.add_argument("--output-dir", type=Path, default=Path("downloads"))
    p.add_argument("--allow-host", action="append", default=[], help="Reviewed HTTPS host; repeat as needed")
    p.add_argument("--download", action="store_true", help="Actually download (default: preview only)")
    p.add_argument("--max-mb", type=int, default=1024, help="Max MiB per file (default: 1024)")
    p.add_argument("--timeout", type=int, default=60, help="Request timeout, seconds")
    p.add_argument("--overwrite", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    p = parser_factory()
    args = p.parse_args(argv)
    if args.url and not args.filename:
        p.error("--filename is required with --url")
    if args.filename and not args.url:
        p.error("--filename is only used with --url")
    if not 1 <= args.max_mb <= 1_000_000 or not 1 <= args.timeout <= 3600:
        p.error("Invalid max size or timeout")
    try:
        hosts = DEFAULT_HOSTS | {host.lower().rstrip(".") for host in args.allow_host}
        for host in hosts:
            if not host or ":" in host or "/" in host or "@" in host or host.startswith("."):
                raise DownloadError(f"Invalid host allowlist entry: {host!r}")
        rows = read_manifest(args.manifest) if args.manifest else [(args.url, safe_filename(args.filename))]
        for url, filename in rows:
            safe_url(url, hosts)
        if len({filename for _, filename in rows}) != len(rows):
            raise DownloadError("Duplicate destination names")
        if not args.download:
            print("DRY RUN; no files downloaded. Review the HTTPS hosts, names and sizes first.")
            for url, name in rows:
                print(f"  {name} <- {url}")
            print("To download, add --download (and any needed --allow-host options).")
            return 0
        args.output_dir.mkdir(parents=True, exist_ok=True)
        log = args.output_dir / "download_log.jsonl"
        failures = 0
        for url, filename in rows:
            try:
                data = download_one(url, filename, dest=args.output_dir, allowed_hosts=hosts,
                                    max_bytes=args.max_mb * 1024 * 1024,
                                    timeout=args.timeout, overwrite=args.overwrite)
                with log.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(data) + "\n")
                print(f"Downloaded {filename}: {data['bytes']} bytes, SHA256 {data['sha256']}")
            except (DownloadError, OSError) as exc:
                failures += 1
                print(f"ERROR for {filename}: {exc}", file=sys.stderr)
        return 1 if failures else 0
    except (DownloadError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
