#!/usr/bin/env python3
"""Safe wrapper for documented RDP-Tools database queries.

Preserves stdout exactly. Nothing here guesses an undocumented REST endpoint.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://rdp.ucc.ie/home"


def build_cli_args(args: argparse.Namespace) -> list[str]:
    cmd = ["RDP-Tools", "database"]
    if args.action == "fields":
        cmd.append("sample-fields")
    elif args.action == "samples":
        if not args.query or "=" not in args.query:
            raise ValueError("--query must use the documented FIELD=VALUE format")
        key, value = args.query.split("=", 1)
        if not key.strip() or not value.strip():
            raise ValueError("--query requires a nonempty FIELD and VALUE")
        # Use exactly the upstream CLI's documented syntax; no shell expansion.
        cmd.extend(["samples", "--query", args.query])
        if args.fields:
            cmd.extend(["--fields", args.fields])
        cmd.extend(["--limit", str(args.limit)])
    else:
        raise ValueError(f"Unknown action: {args.action}")
    return cmd


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    fields = sub.add_parser("fields", help="List fields exposed by the upstream tool")
    samples = sub.add_parser("samples", help="Query sample metadata")
    samples.add_argument("--query", required=True, help="One filter, e.g. TISSUE=Lung")
    samples.add_argument("--fields", help="Comma-separated returned fields, e.g. TISSUE,CELL_LINE")
    samples.add_argument("--limit", type=int, default=100, help="Maximum rows (default: 100)")
    for command in (fields, samples):
        command.add_argument("--output", type=Path, help="Save exact stdout to this file")
        command.add_argument("--force", action="store_true", help="Overwrite an existing output")
        command.add_argument("--timeout", type=int, default=120, help="CLI timeout in seconds")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if getattr(args, "limit", 100) < 1 or getattr(args, "limit", 100) > 1_000_000:
        parser.error("--limit must be between 1 and 1000000")
    if args.timeout < 1 or args.timeout > 3600:
        parser.error("--timeout must be between 1 and 3600 seconds")
    try:
        cmd = build_cli_args(args)
    except ValueError as exc:
        parser.error(str(exc))

    if args.output and args.output.exists() and not args.force:
        print(f"Refusing to overwrite existing output: {args.output} (use --force)", file=sys.stderr)
        return 2
    if shutil.which("RDP-Tools") is None:
        print("RDP-Tools was not found on PATH. Install: python -m pip install RiboSeq-DP-Tools", file=sys.stderr)
        return 127
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=args.timeout, check=False)
    except subprocess.TimeoutExpired:
        print(f"Query timed out after {args.timeout} seconds", file=sys.stderr)
        return 124
    except OSError as exc:
        print(f"Could not run RDP-Tools: {exc}", file=sys.stderr)
        return 1
    if process.stderr:
        sys.stderr.buffer.write(process.stderr)
    if process.returncode:
        print(f"RDP-Tools exited with status {process.returncode}; no valid result was saved.", file=sys.stderr)
        return process.returncode
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_name(args.output.name + ".part")
        try:
            with open(tmp, "wb") as fp:
                fp.write(process.stdout)
            os.replace(tmp, args.output)
        finally:
            tmp.unlink(missing_ok=True)
        provenance = {
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "portal": BASE_URL,
            "tool": "RDP-Tools",
            "argv": cmd[1:],
            "stdout_bytes": len(process.stdout),
            "note": "Raw upstream output; format and results not independently validated",
        }
        audit = args.output.with_name(args.output.name + ".provenance.json")
        audit.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        print(f"Saved {len(process.stdout)} bytes to {args.output}", file=sys.stderr)
        print(f"Provenance: {audit}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(process.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
