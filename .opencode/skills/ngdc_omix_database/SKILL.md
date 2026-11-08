---
name: ngdc-omix-data-access
description: >-
  Find, inspect, request and retrieve data from NGDC's OMIX (Open Archive for
  Miscellaneous Data). Use when the user provides an OMIX accession or wants
  public OMIX file metadata, downloadable files, a controlled-access application
  draft, or instructions for downloading previously approved data. Follow
  official record pages and authorization rules; do not invent APIs or bypass
  controlled access.
---

# NGDC OMIX data access

## Purpose and scope

Work with the **Open Archive for Miscellaneous Data (OMIX)** at NGDC/CNCB:
<https://ngdc.cncb.ac.cn/omix/>. Supported workflows:
1. Discover records using the [released-data catalog](https://ngdc.cncb.ac.cn/omix/releaseList) or the NGDC web search UI.
2. Inspect an accession such as `OMIX007792` and save public metadata and published file links.
3. Download specifically chosen **open-access** files from links actually present on the record page.
4. Prepare a **human-reviewed** controlled-access application; never automatically submit it.
5. After the user **has been approved**, retrieve an authorized file from the official FTP server using a granted remote path.

**Important:** No documented public OMIX REST/JSON API was verified while preparing this skill (2026-11-08). The scripts parse released dataset pages, not an API. OMIX pages and download links may change; if parsing fails, use the official website and report the limitation.

## Files in this skill

- `scripts/omix.py`: fetch accession details, emit JSON, download public HTTPS-linked data, draft applications.
- `scripts/approved_ftp.py`: optional post-approval FTP retrieval (TLS-first; plain FTP explicit opt-in).
- `references/omix-access.md`: official links, access policy, restrictions, troubleshooting.
- `references/access-request-template.md`: editable controlled-access request.
- `requirements.txt`: Python dependencies.
- `tests/`: self-contained parser and input-safety checks.

## Setup

Run from the skill directory:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Requirements: Python 3.10+, outbound HTTPS for public accession records and files; optional FTP/FTPS outbound access only for approved datasets.

## Workflow A — find a dataset

- If the user gives an accession `OMIX...`, use Workflow B directly.
- Otherwise open <https://ngdc.cncb.ac.cn/omix/releaseList> and search by topic, organism, experiment type, BioProject accession, paper or OMIX ID in the browser. Record a concrete OMIX accession before downloading. The portal may be interactive, and **this skill makes no claim of machine-readable search API access**.
- Respect server load: no bulk harvesting or guessing accessions.

## Workflow B — inspect and classify accession

```bash
python scripts/omix.py record OMIX007792 --output omix_007792.json
```

Read the JSON `access_type` and `files[]` before attempting downloads. File IDs are specific to the record. Report file size, file type, link availability and access limitations. An accession marked `Controlled-access`, `Unavailable`, unreleased, or awaiting MOST registration is **not** publicly downloadable.

If a parser returns no fields / rows, try the public record page in a normal browser:
`https://ngdc.cncb.ac.cn/omix/release/OMIX007792` (replace with the validated accession). Don't guess endpoints or construct file URLs from file IDs.

## Workflow C — download public files

Preview the exact published HTTPS download links first:

```bash
python scripts/omix.py download OMIX007792 \
  --file-id OMIX007792-03 --dry-run
```

Download only the explicitly selected file:

```bash
python scripts/omix.py download OMIX007792 \
  --file-id OMIX007792-03 --dir ./data
```

Defaults protect against unintentional huge transfers: **1 GB maximum per file**. Raise it deliberately for larger files (e.g., `--max-size-gb 25`). Whole-dataset download is explicit:

```bash
python scripts/omix.py download OMIX007792 --all --dry-run
python scripts/omix.py download OMIX007792 --all --yes --max-size-gb 10 --dir ./data
```

The script uses published HTTPS URLs only under `download.cncb.ac.cn/OMIX/`, refuses to overwrite finished files, uses `.part` for interrupted transfers (HTTP Range if supported), and writes a *locally computed* `.sha256` checksum. This local checksum is **not** a repository-supplied expected checksum. Use `--sha256 EXPECTED_HEX` only if you have an authoritative reference checksum for one file.

The NGDC site recommends FTP tools for large public downloads; its user guide documents copying the exact FTP link from the portal. A public FTP directory link is not a controlled-data credential.

## Workflow D — request controlled-access data

1. Open and review the accession record. Check its `Data Accessibility` status, listed submitter, warning messages and **dataset-specific application instructions** (some use separate portals).
2. Open <https://ngdc.cncb.ac.cn/omix/term_and_policy?lang=en_GB>. Controlled human genetic resource data requires submitting an application and obtaining the original submitter's authorization. Research use, data security and non-redistribution restrictions apply.
3. Produce a draft with placeholders; **do not claim approval or email anyone without the user's instruction**:

```bash
python scripts/omix.py request-draft OMIX010131 --output request_OMIX010131.md
```

4. Ask the user to verify and complete scientific purpose, file IDs, institution, PI, ethics authorization, security controls, intended duration and any required attachments. Direct them to the correct application route shown on the accession page. A record may refer to an external application service (example: Aging BioBank).
5. Submit using the official website and authenticated user session as required. **Do not automate login, circumvent CAPTCHAs, use other users' credentials, or infer private URLs.**

## Workflow E — retrieve data after written approval

The OMIX controlled-access download guide specifies `omix.big.ac.cn`, port `21`, passive FTP, NGDC account credentials, and a limited download window. Only proceed after user confirms authorization and provides the **actual approved remote file path**. Never fabricate the path.

```bash
export NGDC_USERNAME='your-ngdc-login'
python scripts/approved_ftp.py --list-dir '/granted/directory/from-portal'
python scripts/approved_ftp.py --remote-file '/granted/directory/from-portal/file.ext' --dir ./authorized
```

The script prompts for password instead of storing it or accepting it as a command-line argument. It attempts **FTP over TLS (explicit FTPS)** first. OMIX documentation also describes standard FTP, which may transmit credentials without encryption. If TLS is unsupported, prefer NGDC's recommended FileZilla workflow and confirm with your institution whether a plaintext FTP transfer is permitted. The script only permits plaintext FTP if the user knowingly adds `--allow-plaintext-ftp`.

**Security:** Controlled data must remain in an access-restricted directory under the approved research conditions. Never include data, passwords, tokens, or sensitive metadata in reports or logs. Never redistribute controlled files or attempt individual re-identification.

## Output contract

When answering a dataset request, provide:
- accession, title, organism, BioProject and a link to the source OMIX record;
- access class (open/controlled/unavailable/unknown) and if requests or approvals are needed;
- available file IDs, format, sizes, and **actual** public links where available;
- the exact command performed or recommended and verification status;
- any missing permissions, failed downloads or inability to verify availability;
- proper source and accession attribution.

Before transferring very large files, report estimated size and avoid automatic `--all` unless specifically authorized. Include OMIX accession in publications derived from the archive. For commercial use, contact NGDC about licensing.

## Reference and failure handling

Read [`references/omix-access.md`](references/omix-access.md) for canonical links, current access policy and troubleshooting. If an accession page returns HTML but no downloadable file links, do **not** synthesize a `https://download.cncb.ac.cn/...` file URL: use the page's browser controls and/or NGDC support `gsa@cncb.ac.cn`. If a record is unavailable due to MOST registration, report that barrier rather than trying to access it another way.
