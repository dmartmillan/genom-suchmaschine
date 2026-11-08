# Recipes, failure modes, and reporting

All commands below run from the skill directory.

## Find usable query fields

```bash
python scripts/rdp_query.py fields --output results/fields.txt
```

For metadata about lung samples:

```bash
python scripts/rdp_query.py samples --query 'TISSUE=Lung' --fields 'TISSUE,CELL_LINE' --limit 100 --output results/lung.txt
```

To request more samples if there are more than the current limit:

```bash
python scripts/rdp_query.py samples --query 'TISSUE=Lung' --limit 500 --output results/lung_500.txt
```

The CLI's response format is not guaranteed. Saved text is the **original CLI output**, not a parsed or validated record set. A `.provenance.json` sidecar captures the command, portal URL and retrieval time.

## Multi-dimensional filtering (e.g., human liver + CHX)

Use the website's Samples → Filters panel, or a separately installed and configured RDP MCP integration with `query_samples(ScientificName="Homo sapiens", TISSUE="liver", INHIBITOR="CHX")`. The documented CLI example only guarantees one `FIELD=VALUE` query. Do **not** assume comma-separated multi-filter syntax works without checking the upstream help.

## Get files by sample accession

Search by accession/metadata in the portal. Open the sample and click **GENERATE LINKS**. Use actual URLs produced by the site for the requested file types. Do not derive URLs from IDs.

Create a UTF-8 CSV such as:

```csv
url,filename
https://ACTUAL_HOST/ACTUAL_PATH/sample1.bam,sample1.bam
```

The line above is a **template**—replace BOTH placeholders with the actual URL and the desired name. A blank header-only CSV is included at `templates/download_manifest.csv`.

Preview the manifest:

```bash
python scripts/rdp_download.py --manifest results/approved_manifest.csv --output-dir results/files --allow-host ACTUAL_HOST
```

After approval:

```bash
python scripts/rdp_download.py --manifest results/approved_manifest.csv --output-dir results/files --allow-host ACTUAL_HOST --max-mb 4096 --download
```

Each completed file has a SHA-256 recorded in `results/files/download_log.jsonl`. Any file that exceeds `--max-mb` is aborted and its `.part` temporary file is deleted.

## Errors and limits

| Symptom | Response |
| --- | --- |
| `RDP-Tools was not found` | Install `RiboSeq-DP-Tools` into the active environment, confirm `RDP-Tools --help`. |
| HTTP 403 / 404 / 5xx | Treat as an access/network/server error, not as empty sample results. Check browser/tutorial and try later. |
| No matches | Verify case, controlled metadata vocabulary, and exact available field names; report zero only after a successful query. |
| Timeout | Reduce query size or change `--timeout` after checking service health. |
| Link host rejected | Confirm the generated link host and explicitly add `--allow-host THAT_HOST`; never broadly trust all hosts. |
| Redirect rejected | Manually verify the target host and include it in `--allow-host` if legitimate. |
| Download too large | Agree on files and storage limits first, then raise `--max-mb` explicitly. |
| File already exists | Compare checksum; use `--overwrite` only after confirmation. |
| Multiple filters needed | Use portal UI filters or a separately configured MCP client; do not make up CLI syntax. |

## Example final user report

"Queried RDP on [retrieval timestamp] using `TISSUE=Lung`, selected fields `TISSUE,CELL_LINE` and limit 100. Results were saved verbatim to `results/lung.txt`. The command [succeeded / failed with exact error]. Links and sample counts are only provided if actually observed."
