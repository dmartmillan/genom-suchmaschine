# riboseq-rdp skill

AI-agent skill for querying public RiboSeq.Org Data Portal metadata and safely downloading explicitly selected public files.

**Start here:** [`SKILL.md`](SKILL.md). See [`references/sources.md`](references/sources.md) for official documentation.

## Install and validate

```bash
python -m pip install RiboSeq-DP-Tools
RDP-Tools --help
python -m unittest discover -s tests -v
```

## Try it

```bash
python scripts/rdp_query.py fields --output results/fields.txt
python scripts/rdp_query.py samples --query 'TISSUE=Lung' --fields TISSUE,CELL_LINE --limit 100 --output results/lung.txt
```

For files, obtain actual download URLs from the portal using **GENERATE LINKS**, enter them in a two-column CSV (`url,filename`), then run `scripts/rdp_download.py` first in preview mode and, with approval, with `--download`.

The scripts have not been tested against the live UCC site in this environment (HTTP 403); tests only validate local safety and argument formatting. Do not treat examples as confirmed live query results.
