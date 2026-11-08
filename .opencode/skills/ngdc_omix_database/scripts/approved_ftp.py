#!/usr/bin/env python3
"""Fetch an *approved* OMIX file from the official authenticated FTP server.

No credential storage. TLS is attempted by default. Plain FTP is an explicit
opt-in because it can expose the NGDC username/password over the network.
"""
from __future__ import annotations

import argparse
import ftplib
import getpass
import os
import ssl
import sys
from pathlib import Path

HOST = "omix.big.ac.cn"
PORT = 21


def main() -> int:
    p = argparse.ArgumentParser(description="Authorized OMIX FTP download (requires prior approval)")
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument("--remote-file", help="Exact approved remote file path, obtained from OMIX")
    target.add_argument("--list-dir", help="Directory granted to you; list filenames first")
    p.add_argument("--dir", type=Path, default=Path("authorized_omix"))
    p.add_argument("--user", default=os.getenv("NGDC_USERNAME"), help="NGDC account username (or NGDC_USERNAME)")
    p.add_argument("--allow-plaintext-ftp", action="store_true", help="Explicitly accept unencrypted FTP risk if TLS is unavailable")
    args = p.parse_args()
    if not args.user:
        p.error("Supply --user or NGDC_USERNAME")
    remote = args.remote_file or args.list_dir
    if not remote.startswith("/") or "\r" in remote or "\n" in remote:
        p.error("Use the exact absolute remote path shown in your approved OMIX access information")
    password = getpass.getpass("NGDC password (not saved): ")
    if not password:
        p.error("Empty password")
    ftp = None
    try:
        if args.allow_plaintext_ftp:
            print("WARNING: FTP credentials and file content are sent without encryption.", file=sys.stderr)
            ftp = ftplib.FTP(timeout=45)
        else:
            ftp = ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=45)
        ftp.connect(HOST, PORT)
        ftp.login(user=args.user, passwd=password)
        if isinstance(ftp, ftplib.FTP_TLS):
            ftp.prot_p()
        ftp.set_pasv(True)
        if args.list_dir:
            for name in ftp.nlst(args.list_dir):
                print(name)
            return 0
        outdir = args.dir.resolve()
        outdir.mkdir(parents=True, exist_ok=True, mode=0o700)
        filename = Path(remote.rstrip("/")).name
        if filename in ("", ".", "..") or "\\" in filename:
            raise ValueError("Unsafe remote filename")
        dest = outdir / filename
        if dest.exists():
            raise FileExistsError(f"Refusing to overwrite {dest}")
        partial = outdir / (filename + ".part")
        if partial.exists():
            raise FileExistsError(f"Partial download exists: {partial}; manual review required")
        # Mode 0600 on Unix; do not loosen local access to protected data.
        fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as file:
                ftp.retrbinary("RETR " + remote, file.write)
            partial.replace(dest)
        except Exception:
            # Preserve partial for diagnosis, never falsely report success.
            raise
        print(f"Saved approved data to {dest}")
        return 0
    except (OSError, ftplib.all_errors, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("If TLS is unsupported, use NGDC-recommended FileZilla; only consider plain FTP with institutional approval.", file=sys.stderr)
        return 2
    finally:
        if ftp:
            try:
                ftp.quit()
            except Exception:
                ftp.close()


if __name__ == "__main__":
    raise SystemExit(main())
