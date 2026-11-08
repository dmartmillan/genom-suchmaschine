---
name: literature-search-arxiv
description: >
  Search for scientific papers, preprints, and publications on arXiv. Extract
  metadata, abstracts, and download full-text PDFs or HTML versions of papers.
  Use when the user asks to find research papers, literature, or specific arXiv
  IDs.
---

# arXiv Search and Retrieval

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **User Notification**: If LICENSE_NOTIFICATION.txt does not already exist in
    this skill directory then (1) prominently notify the user to check the terms
    at https://info.arxiv.org/help/api/index.html and to always check the
    license of the papers retrieved by the skill for any restrictions, then (2)
    create the file recording the notification text and timestamp.

## Core Rules

-   **Terms of Use**: You MUST respect arXiv's Terms of Use.
    -   Maximum 1 request every 3 seconds.
    -   The provided utility scripts handle rate limiting automatically. Always
        use these scripts rather than writing your own curl/python requests.
-   If this skill is used, ensure this is mentioned in the output AND list the
    URLs of all papers that were used in producing the output.
-   **Never Use `/tmp/` as the Output Directory:** Do not write or save any generated 
    files to `/tmp/` or any temporary directory. Always save outputs to 
    the appropriate `project_X/` directory designated for the corresponding project plan.

## Utility Scripts

**1. Search and Extract Metadata**

Search arXiv and return a clean JSON array of matching papers.

```bash
uv run scripts/search_arxiv.py --query "au:einstein AND ti:relativity" \
  --max_results 100 2>/dev/null > arxiv_search_results.json
```

> **Important**: The tool outputs a large JSON result to stdout. Requesting 100+
> results will produce a massive JSON that might exceed your context length.
> Limit `--max_results` (e.g., 80-100) or paginate carefully using `--start`.
> Always redirect output to a file and parse it separately, otherwise terminal
> output will be truncated.

*Returned Metadata:* JSON results include `id`, `title`, `summary`, `published`,
`authors`, `pdf_url`, `primary_category`, `doi`, `journal_ref`, and `comment`.
Note: the `doi` field only contains DOI information in case the paper has an
external DOI and if only an arXiv-issued DOI exists, this is DOI is not
returned.

*Options:*

-   `--query`: Search string. See
    [references/query_syntax.md](references/query_syntax.md) for advanced
    syntax.
-   `--id_list`: Comma-separated list of arXiv IDs to fetch directly (e.g.,
    `1706.03762v5`).
-   `--start`: Pagination offset (default 0).
-   `--max_results`: Number of results to return (default 100, recommended 80-100 for comprehensive searches).
-   `--sort_by`: `relevance`, `lastUpdatedDate`, or `submittedDate`. (Use
    `--sort_by submittedDate --sort_order descending` for the most recent
    papers).
-   `--sort_order`: `ascending` or `descending`.

**Date Filtering - CRITICAL:**

When searching for papers, **ALWAYS prioritize recent research** (within the last 2-3 years). Use date filtering to ensure you're working with current state-of-the-art techniques:

```bash
# Search for recent papers (last 2 years)
uv run scripts/search_arxiv.py --query "transformer attention" \
  --max_results 100 --sort_by submittedDate --sort_order descending \
  2>/dev/null > recent_papers.json
```

For advanced date filtering, see the [query syntax documentation](references/query_syntax.md). Example: use `submittedDate:[2024-01-01 TO *]` to search only papers from 2024 onwards.

**2. Download Paper (PDF or HTML)**

Download the full text of a paper to your local workspace for reading.

```bash
uv run scripts/download_paper.py --id 1706.03762 --format pdf --output attention.pdf
```

*Options:*

-   `--id`: The arXiv ID (e.g., `1706.03762` or `1706.03762v5`).
-   `--format`: `pdf` or `html`. Note: HTML is only available for newer papers.
-   `--output`: Filepath to save the downloaded document.

> **Important**: when downloading papers, make sure you download them to a
> location where you do not overwrite other files and do not clutter existing
> directory structure.

**3. Download Paper Source (tar.gz)**

Download the LaTeX source files of a paper to your local workspace. Note that
not all papers have source available.

```bash
uv run scripts/download_paper_source.py --id 2010.11645 --output source.tar.gz
```

*Options:*

-   `--id`: The arXiv ID (e.g., `2010.11645`).
-   `--output`: Filepath to save the downloaded tar.gz file.

> **Caution**: Care should be exercised when untar'ing the downloaded file for
> security and to avoid cluttering your filesystem, as archives may contain many
> files or unexpected directory structures.
>
> **Safe Extraction Requirements**: NEVER extract directly into your working
> directory! Always extract into a dedicated new directory: `bash mkdir
> paper_source && tar -xzf source.tar.gz -C paper_source`

## Reference

-   **Advanced Query Syntax**: See
    [references/query_syntax.md](references/query_syntax.md) for prefixes (au,
    ti, abs), booleans, and date filtering.

## Workflow

1.  Search for papers using `search_arxiv.py`. Review the JSON summaries.
2.  If full text is needed, use `download_paper.py` to fetch the PDF or HTML.
3.  If downloading a PDF, verify the PDF is not empty or corrupted.
4.  Read the downloaded file using standard file reading tools.

**All files, folders, outputs, and generated artifacts associated with a given plan must be stored exclusively within that plan's corresponding `project_X/` directory.**
