# RDP portal and API reference

Checked against publicly accessible documentation on 2026-11-08. The portal's live `/home` endpoint returned HTTP 403 to this environment; direct REST endpoint paths and response schemas were **not** verified.

## What the site contains

RDP is the RiboSeq.Org Data Portal hosted by University College Cork. It indexes ribosome-profiling studies and samples with standardized metadata and processed data links. Public RiboSeq.Org resources do not require user registration.

## Browser route (official tutorial)

1. Go to <https://rdp.ucc.ie/home> and select **Samples** or **Studies**.
2. Open **Filters** to choose relevant sample/study attributes.
3. Click a sample accession for full sample details, or a study accession for study information.
4. Select rows and click **DOWNLOAD METADATA** to export metadata for those rows.
5. Click **GENERATE LINKS** for files and browser visualization; **Options** can export metadata/links for all currently filtered results.
6. The Links page offers individual download links and visualization via GWIPS-viz or Trips-Viz.

The official website also includes a **Download All Samples** tutorial describing a downloadable Bash script to orchestrate bulk downloads. Inspect such a script before running it.

## Documented RDP-Tools CLI (recommended script path)

Install: `python -m pip install RiboSeq-DP-Tools`

```bash
RDP-Tools database sample-fields
RDP-Tools database samples --query TISSUE=Lung
RDP-Tools database samples --query TISSUE=Lung --fields TISSUE,CELL_LINE
RDP-Tools database samples --query TISSUE=Lung --fields TISSUE,CELL_LINE --limit 100
```

`--limit` defaults to 100 according to published documentation. Discover available fields at runtime. The field examples above are documented and do not imply an exhaustive field list. The actual output format is version-dependent; the skill preserves stdout rather than claiming a JSON/CSV schema.

## REST API and MCP alternative

The 2025 RiboSeq.Org publication describes a REST API built with Django REST Framework; it serves JSON metadata and can expose file download links. However, this skill does not use unconfirmed REST paths. For direct integration, refer to the RDP source code and check live endpoint documentation first.

A separately published `RDP-MCP` package advertises the following tools:

- `list_available_fields`
- `count_samples`
- `query_samples` (filters include `ScientificName`, `TISSUE`, `CELL_LINE`, `INHIBITOR`, `LIBRARYTYPE`, `CONDITION`; paginated with `limit` and `offset`)
- `get_sample_details` (run accession)
- `get_file_links` (FASTA, BAM, forward/reverse BigWig and QC links)
- `search_by_organism`

The MCP package is not installed or automatically called by these scripts. Its own installation documentation should be checked for the currently supported client/server configuration.

## File format notes

RDP data may be distributed in collapsed representations to minimize storage. The publisher's RDP-Tools package includes FASTA/BAM **inflate** commands to recover read multiplicity, as well as FASTQ collapse. Inflating FASTA to FASTQ assigns artificial high-quality values; those are **not** recovered original sequencing quality scores. Review method requirements before running analyses.

## Attribution and integrity

Record run/study accessions, portal retrieval date, filters and any downstream transformations. Cite the RiboSeq.Org portal and the original study associated with each sample where applicable. Check the portal metadata and quality-control files before drawing biological conclusions.
