#!/usr/bin/env python3
"""Retrieve public OMIX record metadata and files via the published website.

NOT an OMIX REST API client. Uses publicly visible accession pages and their
published HTTPS file hyperlinks. Does not authenticate or apply for access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ngdc.cncb.ac.cn/omix"
PUBLIC_DOWNLOAD_HOST = "download.cncb.ac.cn"
ACCESSION_RE = re.compile(r"OMIX\d{1,10}\Z", re.IGNORECASE)
FILE_ID_RE = re.compile(r"OMIX\d{1,10}-[\d-]+\Z", re.IGNORECASE)
USER_AGENT = "NGDC-OMIX-Skill/1.0 (public-record-retrieval; local script)"
TIMEOUT = (15, 90)
FIELD_LABELS = {
    "title": "title",
    "description": "description",
    "organism": "organism",
    "data type": "data_type",
    "data accessibility": "access_type",
    "bioproject": "bioproject",
    "release date": "release_date",
    "submitter": "submitter",
    "organization": "organization",
    "submission date": "submission_date",
}


class OmixError(Exception):
    pass


def accession(value: str) -> str:
    value = value.strip().upper()
    if not ACCESSION_RE.fullmatch(value):
        raise OmixError("Expected OMIX accession, for example OMIX007792")
    return value


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def url_is_official_download(url: str) -> bool:
    p = urlparse(url)
    return (
        p.scheme.lower() == "https"
        and p.hostname == PUBLIC_DOWNLOAD_HOST
        and p.port in (None, 443)
        and p.username is None
        and p.password is None
        and p.path.startswith("/OMIX/")
    )


def parse_record(html: str, record_url: str, acc: str) -> dict:
    """Parse server-rendered content. Fail explicitly if page layout changes."""
    acc = accession(acc)
    soup = BeautifulSoup(html, "html.parser")
    record = {
        "accession": acc,
        "record_url": record_url,
        "source": "Published OMIX HTML page (not an official API)",
        "files": [],
        "access_request_links": [],
    }

    # Typical OMIX summary is in table rows: <td>Title</td><td>...</td>.
    # Also accept tables with a label/value pair in a single row.
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if len(cells) < 2:
            continue
        label = norm(cells[0].get_text(" ", strip=True)).rstrip(":").lower()
        if label in FIELD_LABELS:
            record[FIELD_LABELS[label]] = norm(cells[1].get_text(" ", strip=True))

    # Fallback for pages whose label/value structure isn't a table.
    # Only search exact standalone text nodes to avoid data contamination.
    for label, key in FIELD_LABELS.items():
        if record.get(key):
            continue
        node = soup.find(string=lambda s: bool(s and norm(str(s)).rstrip(":").lower() == label))
        if node is None:
            continue
        parent = node.parent
        next_cell = parent.find_next_sibling(["td", "dd", "span", "div"])
        if next_cell:
            record[key] = norm(next_cell.get_text(" ", strip=True))

    # Locate the file table by column headers; don't confuse publication rows.
    for table in soup.find_all("table"):
        first_row = table.find("tr")
        if not first_row:
            continue
        headers = [norm(x.get_text(" ", strip=True)).lower() for x in first_row.find_all(["th", "td"], recursive=False)]
        if not ("file id" in headers and "file title" in headers and "download" in headers):
            continue
        positions = {h: i for i, h in enumerate(headers)}
        for tr in table.find_all("tr"):
            cells = tr.find_all("td", recursive=False)
            if len(cells) < len(headers):
                continue
            get = lambda k: norm(cells[positions[k]].get_text(" ", strip=True)) if k in positions else ""
            file_id = get("file id")
            if not FILE_ID_RE.fullmatch(file_id) or not file_id.upper().startswith(acc + "-"):
                continue
            row = {
                "file_id": file_id,
                "title": get("file title"),
                "samples": get("number/samples"),
                "file_type": get("file type"),
                "size": get("file size"),
                "suffix": get("file suffix"),
                "status": get("download"),
                "https_urls": [],
                "ftp_urls": [],
            }
            for link in cells[positions["download"]].find_all("a", href=True):
                href = urljoin(record_url, link["href"])
                if url_is_official_download(href) and href not in row["https_urls"]:
                    row["https_urls"].append(href)
                if urlparse(href).scheme == "ftp" and urlparse(href).hostname == PUBLIC_DOWNLOAD_HOST:
                    row["ftp_urls"].append(href)
            record["files"].append(row)
        break

    # Some controlled datasets specify a separate authorized application portal.
    for link in soup.find_all("a", href=True):
        title = norm(link.get_text(" ", strip=True))
        if re.search(r"request data access|submit your application|visit abb|apply for access", title, re.I):
            u = urljoin(record_url, link["href"])
            if urlparse(u).scheme == "https":
                record["access_request_links"].append({"text": title, "url": u})
    seen = set()
    record["access_request_links"] = [
        item for item in record["access_request_links"]
        if not (item["url"] in seen or seen.add(item["url"]))
    ]
    text = soup.get_text(" ", strip=True)
    if "not yet been registered in the Human Genetic Resource Management Platform" in text:
        record["availability_warning"] = "This record is marked unavailable pending MOST registration."
    if not record.get("title") and not record["files"]:
        raise OmixError("No accession metadata or file rows found. Page may require login, be unavailable, or its HTML may have changed.")
    return record


def fetch_record(acc: str) -> dict:
    acc = accession(acc)
    url = f"{BASE_URL}/release/{acc}"
    try:
        res = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        res.raise_for_status()
    except requests.RequestException as e:
        raise OmixError(f"Cannot fetch OMIX accession page {url}: {e}") from e
    if urlparse(res.url).hostname != "ngdc.cncb.ac.cn":
        raise OmixError("Record page redirected off NGDC; visit the portal manually instead.")
    record = parse_record(res.text, url, acc)
    return record


def size_gb(text: str) -> float | None:
    m = re.search(r"([\d.,]+)\s*(B|KB|MB|GB|TB)\b", text or "", re.I)
    if not m:
        return None
    number = float(m.group(1).replace(",", ""))
    return number * {"B": 1e-9, "KB": 1e-6, "MB": 1e-3, "GB": 1, "TB": 1e3}[m.group(2).upper()]


def filename_from_link(url: str, file_id: str) -> str:
    # URL path can be percent-encoded and untrusted; never permit path traversal.
    name = Path(unquote(urlparse(url).path)).name
    if not name or name in {".", ".."} or "\x00" in name or "/" in name or "\\" in name:
        raise OmixError(f"Unsafe file name in link for {file_id}")
    return name


def fetch_file(url: str, destination: Path, expected_sha256: str | None = None) -> str:
    if not url_is_official_download(url):
        raise OmixError("Refusing unverified or nonofficial public download URL")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    position = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": USER_AGENT}
    if position:
        headers["Range"] = f"bytes={position}-"
    # Do not auto-follow redirects to arbitrary domains.
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True, allow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308):
            raise OmixError("Download redirected; check the official website for its current link")
        r.raise_for_status()
        if "text/html" in r.headers.get("Content-Type", "").lower():
            raise OmixError("Server returned HTML rather than a file (may need browser access or be unavailable)")
        if position and r.status_code == 206:
            start = r.headers.get("Content-Range", "").split(" ")[-1].split("-")[0]
            if start != str(position):
                raise OmixError("Server returned mismatched byte range; cannot safely resume")
            mode = "ab"
        elif position and r.status_code == 200:
            # Server ignored range: restart cleanly instead of corrupting file.
            mode = "wb"
        else:
            mode = "wb"
        with r, partial.open(mode) as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    except requests.RequestException as e:
        raise OmixError(f"Transfer failed (partial data retained for resume): {e}") from e
    h = hashlib.sha256()
    with partial.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    digest = h.hexdigest()
    if expected_sha256 and expected_sha256.lower() != digest:
        raise OmixError(f"SHA-256 mismatch for {destination.name}; partial file retained")
    partial.replace(destination)
    destination.with_name(destination.name + ".sha256").write_text(
        f"{digest}  {destination.name}\n", encoding="utf-8"
    )
    return digest


def draft_request(rec: dict) -> str:
    target = ", ".join(x for x in [rec.get("submitter", ""), rec.get("organization", "")] if x)
    extra = "\n".join(f"- {x['text']}: {x['url']}" for x in rec.get("access_request_links", []))
    return f"""# Draft access request — {rec['accession']}

**Do not send without checking the record's application procedure and applicable policies.**

To: [Designated OMIX data access contact / submitter — verify in portal]
Subject: Research data access request for {rec['accession']}

Dear Data Access Committee / Data Submitter,

I would like to request controlled access to **{rec['accession']}**, titled
**{rec.get('title') or '[dataset title]'}** ({rec['record_url']}).

- Applicant and role: [Full name, position]
- Institution / department: [Institution]
- Institutional email: [Email]
- Principal investigator / supervisor: [PI name and email]
- Research project / ethics approval: [Title, protocol ID, approval status]
- Scientific purpose and methods: [Specific aims and analyses]
- Files / samples requested: [Specific file IDs and justification]
- Intended users: [Authorized team and collaborators]
- Intended usage period: [Start/end dates]
- Data storage, access control and security: [Institution-approved measures]
- Restrictions acknowledgement: [No unauthorized onward sharing, no re-identification,
  only approved research use; compliance with applicable laws and consent]
- Required agreements / supporting documents: [List as requested by custodian]

Please advise on the formal application process, documentation and access terms.
I will not attempt access until authorization is granted.

Sincerely,\n[Name]\n[Institution]\n[Contact]

## Record context
- Record: {rec['record_url']}
- Access type: {rec.get('access_type', 'not determined')}
- Listed submitter / organization: {target or 'Verify in OMIX'}
{('- Dataset-specific application links:\n' + extra) if extra else '- No dataset-specific application link was detected; follow the OMIX website instructions.'}
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="OMIX website-based public data accessor (not an API)")
    sub = p.add_subparsers(dest="command", required=True)
    show = sub.add_parser("record", help="Fetch accession metadata + public file links")
    show.add_argument("accession")
    show.add_argument("--output", type=Path, help="Write JSON to file instead of stdout")
    dl = sub.add_parser("download", help="Download explicitly selected open-access file(s)")
    dl.add_argument("accession")
    selector = dl.add_mutually_exclusive_group(required=True)
    selector.add_argument("--file-id", action="append", help="Published file ID (repeatable)")
    selector.add_argument("--all", action="store_true", help="Select every file in the accession")
    dl.add_argument("--yes", action="store_true", help="Confirm potentially large --all batch")
    dl.add_argument("--dir", type=Path, default=Path("omix_downloads"))
    dl.add_argument("--max-size-gb", type=float, default=1.0, help="Per-file safety limit; default 1 GB")
    dl.add_argument("--dry-run", action="store_true", help="Show download plan without transferring")
    dl.add_argument("--sha256", help="Optional published SHA-256 for one file")
    req = sub.add_parser("request-draft", help="Prepare a human-reviewed controlled-access request")
    req.add_argument("accession")
    req.add_argument("--output", type=Path, help="Save Markdown draft")
    args = p.parse_args(argv)
    try:
        rec = fetch_record(args.accession)
        if args.command == "record":
            result = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(result, encoding="utf-8")
                print(f"Saved {args.output}")
            else:
                print(result, end="")
        elif args.command == "request-draft":
            result = draft_request(rec)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(result, encoding="utf-8")
                print(f"Saved draft to {args.output}")
            else:
                print(result)
        else:
            if rec.get("access_type", "").lower() not in ("open-access", "open access", "open"):
                raise OmixError("Record is not confirmed open-access. Do not use the public downloader for controlled/unreleased records.")
            if not rec["files"]:
                raise OmixError("No published file rows found; use the OMIX browser interface.")
            wanted = {s.upper() for s in args.file_id} if args.file_id else None
            found = [row for row in rec["files"] if wanted is None or row["file_id"].upper() in wanted]
            if wanted:
                missing = wanted - {row["file_id"].upper() for row in found}
                if missing:
                    raise OmixError(f"Requested file ID(s) missing from page: {', '.join(sorted(missing))}")
            if args.all and not (args.yes or args.dry_run):
                raise OmixError("For full-dataset downloads pass --all --yes, or preview with --all --dry-run")
            if args.sha256 and len(found) != 1:
                raise OmixError("--sha256 requires exactly one selected file")
            for row in found:
                if not row["https_urls"]:
                    raise OmixError(f"No verified public HTTPS link for {row['file_id']}. Check the OMIX page manually.")
                gb = size_gb(row["size"])
                if not args.dry_run and gb is not None and gb > args.max_size_gb:
                    raise OmixError(f"{row['file_id']} lists {row['size']}, exceeding --max-size-gb {args.max_size_gb}")
                u = row["https_urls"][0]
                target = args.dir / accession(args.accession) / filename_from_link(u, row["file_id"])
                print(f"{row['file_id']} ({row['size']}): {u} -> {target}")
                if not args.dry_run:
                    if target.exists():
                        raise OmixError(f"Destination exists; refusing overwrite: {target}")
                    digest = fetch_file(u, target, args.sha256)
                    print(f"Saved {target}; local SHA-256: {digest}")
        return 0
    except (OmixError, OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
