---
name: riboseq-rdp
description: Find, filter, retrieve, and document publicly available ribosome-profiling (Ribo-seq) samples and processed data from the University College Cork RiboSeq.Org Data Portal (https://rdp.ucc.ie/home). Use for requests involving RDP, RiboSeq.Org datasets, sample metadata, tissue/organism/inhibitor filters, sample accessions, or FASTA/BAM/BigWig download links.
---

# RiboSeq.Org Data Portal — data retrieval

Use this skill to **request and retrieve public data**, not to submit a private-data access application. The RiboSeq.Org Data Portal (RDP) at <https://rdp.ucc.ie/home> indexes public ribosome-profiling samples and studies. The portal has a REST API, but this skill intentionally uses the **documented `RDP-Tools` CLI** for scripted metadata queries rather than guessing REST URL paths.

## Before using this skill

- Determine whether the user wants (a) sample/study discovery, (b) metadata, (c) file download links, or (d) the actual data files.
- Extract explicit organism, tissue, cell line, inhibitor, condition, library type, study accession, run accession, requested fields, file formats, and output location. Do **not** invent fields, accessions, download links, or sample counts.
- If the question can be answered with metadata, do not download large sequencing files.
- Do not claim an API call or download succeeded without real command output. The portal may be unreachable; errors are not "zero results".
- Public datasets normally do not require registration; never attempt to bypass access controls. Only download public files from links supplied by the portal or an authorized user.

## Setup

Python 3.10+ recommended. Install the publisher's CLI:

```bash
python -m pip install RiboSeq-DP-Tools
RDP-Tools --help
RDP-Tools database --help
```

No external Python dependencies are needed for this skill's wrapper/downloader scripts themselves. The upstream `RDP-Tools` package is required for metadata querying. If a command behaves differently in the installed version, consult `RDP-Tools --help` and the official documentation rather than assuming an undocumented flag.

## Workflow A: discover fields before filtering

```bash
python scripts/rdp_query.py fields --output results/sample_fields.txt
```

Review returned field names. Known example fields used in public documentation include `TISSUE` and `CELL_LINE`; other metadata field names, spellings, and allowed values must be checked against the server's actual response. Preserve capitalization in query keys.

## Workflow B: query sample metadata

Use **one documented `FIELD=VALUE` filter** per call. Start with a modest result limit and request only useful columns.

```bash
python scripts/rdp_query.py samples \
  --query 'TISSUE=Lung' \
  --fields 'TISSUE,CELL_LINE' \
  --limit 100 \
  --output results/lung_samples.txt
```

The wrapper passes arguments as an array without a shell and saves the upstream output **verbatim**, since its response format may vary by version. Do not assume the output is JSON or CSV. Query metadata for additional filters only if the current installation's help confirms its syntax; otherwise apply filters through the portal website (Samples page → Filters) or use a supported RDP MCP client. Do not substitute guessed query syntax.

For large queries, expand `--limit` only on user request or when needed to answer the question. Treat the upstream CLI's limit as a result cap, not proof of total sample count.

## Workflow C: obtain download links

Preferred supported options:

1. In <https://rdp.ucc.ie/home>, open **Samples** (or **Studies**), set filters, select samples, and choose **GENERATE LINKS**. The **Options** menu can generate links for all samples matching selected filters.
2. Alternatively, use an RDP MCP integration with documented `get_file_links` functionality (see `references/portal-and-api.md`).
3. Record the actual URL(s), source sample accession, and desired file type (FASTA/BAM/BigWig/QC). **Do not construct file URLs from accession numbers.**

For a large browser export, the website may provide a Bash download script; inspect it before running. Do not execute downloaded shell scripts automatically.

## Workflow D: download explicitly selected files

Put **portal-supplied** HTTPS links into a CSV with exactly `url,filename` columns (see `templates/download_manifest.csv`). Preview first:

```bash
python scripts/rdp_download.py \
  --manifest templates/download_manifest.csv \
  --output-dir results/files
```

Then, after the user has explicitly approved downloading the selected files, run:

```bash
python scripts/rdp_download.py \
  --manifest results/approved_manifest.csv \
  --output-dir results/files \
  --allow-host ACTUAL_FILE_HOST_FROM_THE_PORTAL \
  --max-mb 2048 \
  --download
```

The downloader accepts HTTPS only, requires an explicit host allowlist (in addition to `rdp.ucc.ie`), checks redirects, avoids overwriting by default, checks size limits, and writes SHA-256 plus metadata to `download_log.jsonl`. It does **not** run shell scripts or infer file URLs. Its default operation is a dry run.

## Workflow E: report results with provenance

For each result, give the applied query/filters, requested fields, limit, number of rows **actually observed** if parseable, accessions where available, download links *returned by the portal*, and the time retrieved. Distinguish not-found from API/CLI failures. Report limitations including metadata curation and unverified experimental annotations.

If the live RDP is unavailable, state that clearly and offer the browser route, official CLI reference, and code repository; do not manufacture results.

## Reference files

- [Portal/UI/API notes](references/portal-and-api.md) — verified portal operations, known filter names, and MCP option.
- [Examples & troubleshooting](references/examples.md) — safe queries, downloading and troubleshooting.
- [Sources](references/sources.md) — original documentation and publication links.

## Tools in this folder

- `scripts/rdp_query.py`: Query metadata through the documented `RDP-Tools` CLI.
- `scripts/rdp_download.py`: Preview/download user-approved public HTTPS files, with an allowlist, size limit and SHA-256 log.
- `tests/test_scripts.py`: Offline sanity tests; no real portal calls.

**Scope limitation:** The site's live `/home` page could not be fetched during creation (HTTP 403 from the web inspection environment), so this skill does **not** assert unverified REST endpoint paths or current live API response schemas. Confirm CLI behavior in the user's environment before treating saved outputs as results.
