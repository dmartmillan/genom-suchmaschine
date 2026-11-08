---
name: zotero-retrieval
description: >
  Retrieve scientific papers and PDFs from Zotero collections using the Zotero
  API v3. Fetch paper metadata, full-text, and download PDF attachments from
  personal libraries or group libraries. Use when the user asks to retrieve
  papers from their Zotero library or specific collections.
---

# Zotero API v3 Paper Retrieval

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **Environment Variables**: Configure the following in your `.env` file:
    -   `ZOTERO_API_KEY`: Your Zotero API key (get from https://www.zotero.org/settings/keys)
    -   `ZOTERO_USER_ID`: Your Zotero user ID (numeric ID, visible in API key settings)
    -   `ZOTERO_EMAIL`: Your email address (for rate limiting attribution)

    If `.env` does not exist, copy from `.env.example` and fill in your credentials.

3.  **API Key Permissions**: Ensure your API key has at least **library access**
    permission to read your personal library items.

## Core Rules

-   **Authentication**: All API requests require authentication via:
    -   `Zotero-API-Key` header, OR
    -   `Authorization: Bearer <API_KEY>` header, OR
    -   `key` query parameter (less secure, only for testing)

    The scripts automatically use the `Zotero-API-Key` header.

-   **Rate Limiting**:
    -   Maximum 1 request per second (QPS = 1.0)
    -   The provided utility scripts handle rate limiting automatically
    -   Always use the scripts rather than writing your own requests

-   **Never Use `/tmp/` as the Output Directory:** Do not write or save any generated
    files to `/tmp/` or any temporary directory. Always save outputs to
    the appropriate `project_X/` directory designated for the corresponding project plan.

-   **Privacy**: Your Zotero API key provides access to your library. Keep it secure
    and never commit it to version control.

-   **Group Libraries**: To access group libraries, use the group ID instead of
    user ID (e.g., `groups/<GROUP_ID>` instead of `users/<USER_ID>`).

## Utility Scripts

### 1. List Collections

Retrieve all collections (folders) in your Zotero library.

```bash
uv run scripts/list_collections.py 2>/dev/null > zotero_collections.json
```

*Returns*: JSON array of collections with `key`, `name`, `version`, and `parentCollection`.

*Options*:
-   `--top`: Only show top-level collections (no subcollections)
-   `--limit`: Maximum number of collections to return (default: 100, max: 100)
-   `--start`: Pagination offset (default: 0)

### 2. Get Collection Items

Retrieve all papers/items within a specific collection.

```bash
uv run scripts/get_collection_items.py --collection-key ABC123DEF 2>/dev/null > collection_items.json
```

*Returns*: JSON array of items with metadata including `key`, `title`, `creators`,
`itemType`, `date`, `abstractNote`, `tags`, `collections`, and `attachments`.

*Options*:
-   `--collection-key`: The collection key (e.g., `ABC123DEF`)
-   `--collection-name`: Alternative: search by collection name (exact match)
-   `--limit`: Maximum number of items (default: 100, max: 100)
-   `--start`: Pagination offset (default: 0)
-   `--format`: Output format - `json` (default), `bibtex`, `biblatex`, `ris`, `csv`
-   `--include-attachments`: Include attachment metadata (PDFs, notes, etc.)

### 3. Search Library

Search across your entire Zotero library (all collections).

```bash
uv run scripts/search_library.py --query "transformer attention" 2>/dev/null > library_search_results.json
```

*Returns*: JSON array of matching items with full metadata.

*Options*:
-   `--query`: Search query string
-   `--collection-key`: Limit search to specific collection
-   `--item-type`: Filter by item type (e.g., `journalArticle`, `book`, `conferencePaper`)
-   `--tag`: Filter by tag name
-   `--limit`: Maximum results (default: 100, max: 100)
-   `--start`: Pagination offset
-   `--sort`: Sort field - `title`, `date`, `dateAdded`, `dateModified`, `creator`
-   `--direction`: `asc` or `desc`
-   `--include-attachments`: Include attachment metadata

### 4. Download Paper PDF

Download the PDF attachment for a specific item.

```bash
uv run scripts/download_paper_pdf.py --item-key XYZ789ABC --output "paper_title.pdf"
```

*Options*:
-   `--item-key`: The item key (e.g., `XYZ789ABC`)
-   `--item-id`: Alternative: numeric item ID
-   `--output`: Output file path for the PDF
-   `--collection-key`: If item is in a collection, specify for faster lookup
-   `--overwrite`: Overwrite existing file if it exists

> **Important**: Not all items have PDF attachments. The script will check for
> attached PDF files and download the first available one. Some items may only
> have snapshots or web archives.

### 5. Get Item Metadata

Retrieve detailed metadata for a specific item.

```bash
uv run scripts/get_item_metadata.py --item-key XYZ789ABC 2>/dev/null > item_metadata.json
```

*Returns*: Complete item metadata including all fields, creators, tags, notes,
and attachments.

*Options*:
-   `--item-key`: The item key
-   `--item-id`: Alternative: numeric item ID
-   `--format`: Output format - `json` (default), `bibtex`, `biblatex`, `ris`
-   `--include-children`: Include child items (notes, attachments)
-   `--include-relations`: Include related items

### 6. Export Collection

Export an entire collection to various citation formats.

```bash
uv run scripts/export_collection.py --collection-key ABC123DEF --format bibtex > collection.bib
```

*Options*:
-   `--collection-key`: The collection key
-   `--collection-name`: Alternative: search by collection name
-   `--format`: Export format - `bibtex`, `biblatex`, `ris`, `csv`, `csljson`, `mods`
-   `--limit`: Maximum items (default: 100, max: 100 for some formats)
-   `--style`: Citation style (for bib format) - e.g., `apa`, `chicago-note-bibliography`
-   `--locale`: Locale code (default: `en-US`)

## API Endpoints Reference

The Zotero API v3 base URL is: `https://api.zotero.org`

### Key Endpoints

-   **Collections**: `/users/<USER_ID>/collections` or `/groups/<GROUP_ID>/collections`
-   **Collection Items**: `/users/<USER_ID>/collections/<COLLECTION_KEY>/items`
-   **Items**: `/users/<USER_ID>/items` or `/users/<USER_ID>/items/<ITEM_KEY>`
-   **Search**: `/users/<USER_ID>/items` with query parameters
-   **File Downloads**: `/users/<USER_ID>/items/<ITEM_KEY>/file`

### User/Group Prefix

The API uses `<userOrGroupPrefix>` which can be:
-   `users/<USER_ID>` for personal libraries
-   `groups/<GROUP_ID>` for group libraries
-   `users/<USER_ID>/publications` for My Publications

## Query Syntax

### Search Queries

The Zotero API supports advanced search syntax:

-   **Quick Search**: `--query "transformer attention"` searches titles and creators
-   **Item Type Filter**: `--item-type journalArticle`
-   **Tag Filter**: `--tag "deep learning"`
-   **Combined**: Use multiple filters with scripts

### Sorting

Available sort fields:
-   `title` - Alphabetical by title
-   `date` - By publication date
-   `dateAdded` - By date added to library
-   `dateModified` - By last modification date
-   `creator` - By author/creator name

## Example Workflows

### Workflow 1: Retrieve All Papers from a Collection

```bash
# 1. List collections to find the key
uv run scripts/list_collections.py 2>/dev/null | jq '.[] | {key, name}'

# 2. Get all items from a specific collection
uv run scripts/get_collection_items.py --collection-key ABC123DEF --limit 100 \
  2>/dev/null > my_papers.json

# 3. Download PDFs for each paper
while read -r item; do
  item_key=$(echo "$item" | jq -r '.key')
  title=$(echo "$item" | jq -r '.title' | tr -d '/' | tr ' ' '_')
  uv run scripts/download_paper_pdf.py --item-key "$item_key" --output "${title}.pdf"
done < my_papers.json
```

### Workflow 2: Search and Download Recent Papers

```bash
# Search for papers on a topic
uv run scripts/search_library.py --query "large language models" \
  --item-type journalArticle --sort date --direction desc --limit 50 \
  2>/dev/null > llm_papers.json

# Export to BibTeX for reference management
uv run scripts/search_library.py --query "large language models" \
  --format bibtex --style apa 2>/dev/null > llm_papers.bib
```

### Workflow 3: Export Collection for Paper Review

```bash
# Export collection to multiple formats
uv run scripts/export_collection.py --collection-name "Literature Review" \
  --format bibtex --style apa 2>/dev/null > review.bib

uv run scripts/export_collection.py --collection-name "Literature Review" \
  --format ris 2>/dev/null > review.ris

# Get detailed metadata for analysis
uv run scripts/get_collection_items.py --collection-name "Literature Review" \
  --include-attachments 2>/dev/null > review_metadata.json
```

## Error Handling

### Common Errors

-   **401 Unauthorized**: Invalid or missing API key. Check your `.env` file.
-   **403 Forbidden**: API key doesn't have access to this library/collection.
-   **404 Not Found**: Collection or item key doesn't exist.
-   **429 Too Many Requests**: Rate limit exceeded. Wait and retry.
-   **500-503 Server Errors**: Temporary API issues. Scripts retry automatically.

### Troubleshooting

1.  **Verify API Key**: Check that `ZOTERO_API_KEY` is set correctly in `.env`
2.  **Check User ID**: Ensure `ZOTERO_USER_ID` matches your numeric user ID
3.  **Permissions**: Verify API key has "Library access" permission
4.  **Collection Key**: Collection keys are case-sensitive alphanumeric strings
5.  **Rate Limiting**: Add delays between batch operations

## Getting Your Zotero API Credentials

1.  **Create API Key**:
    -   Go to https://www.zotero.org/settings/keys
    -   Click "Create New Key"
    -   Give it a descriptive name
    -   Enable "Library access" permission
    -   Click "Authorize" to generate the key

2.  **Find Your User ID**:
    -   Your user ID is visible on your Zotero profile page
    -   Or check the API key settings page
    -   It's a numeric value (e.g., `12345678`)

3.  **Configure Environment**:
    ```bash
    # Copy example env file
    cp .env.example .env

    # Edit with your credentials
    ZOTERO_API_KEY=your_api_key_here
    ZOTERO_USER_ID=your_user_id_here
    ZOTERO_EMAIL=your_email@example.com
    ```

## References

-   [Zotero API v3 Documentation](https://www.zotero.org/support/dev/web_api/v3/)
-   [API Basics](https://www.zotero.org/support/dev/web_api/v3/basics)
-   [Item Types and Fields](https://www.zotero.org/support/dev/web_api/v3/types_and_fields)
-   [OAuth Authentication](https://www.zotero.org/support/dev/web_api/v3/oauth)
-   [Zotero Style Repository](https://www.zotero.org/support/dev/citation_styles)

## Agent Usage Guidelines

This skill is designed to be used by **Computational Expert** and **Experimental Innovator** agents during literature review phases.

### Priority Order for Literature Search

When conducting literature searches, agents MUST follow this priority order:

1. **Zotero Collections (HIGHEST PRIORITY)**
   - Always search Zotero FIRST before using other literature skills
   - Zotero contains curated, high-quality papers that should be prioritized
   - Use comprehensive searches across all collections

2. **Other Literature Skills (ONLY if Zotero is insufficient)**
   - arXiv, bioRxiv, pubmed_database, EuropePMC
   - Use only to fill gaps after exhaustively searching Zotero

### Typical Agent Workflow

```bash
# 1. List available collections
uv run .opencode/skills/zotero_retrieval/scripts/list_collections.py 2>/dev/null > project_X/zotero_collections.json

# 2. Search library for relevant papers
uv run .opencode/skills/zotero_retrieval/scripts/search_library.py \
  --query "search terms" \
  --item-type journalArticle \
  --sort dateAdded \
  --direction desc \
  --limit 100 \
  2>/dev/null > project_X/zotero_search_results.json

# 3. Get items from specific collections
uv run .opencode/skills/zotero_retrieval/scripts/get_collection_items.py \
  --collection-name "CollectionName" \
  --limit 100 \
  2>/dev/null > project_X/collection_items.json

# 4. Download PDFs for detailed reading
uv run .opencode/skills/zotero_retrieval/scripts/download_paper_pdf.py \
  --item-key ITEM_KEY \
  --output "project_X/paper_title.pdf"

# 5. Export to BibTeX for references
uv run .opencode/skills/zotero_retrieval/scripts/export_collection.py \
  --collection-name "CollectionName" \
  --format bibtex \
  --style apa \
  > project_X/references.bib
```

### Best Practices for Agents

- **Always save outputs to `project_X/` directory** - never use `/tmp/`
- **Search comprehensively** - use `--limit 100` to get all relevant papers
- **Sort by date** - use `--sort dateAdded --direction desc` for recent papers
- **Read before proposing** - analyze papers before suggesting methods/protocols
- **Document sources** - cite which Zotero papers informed your recommendations
- **Download PDFs** - get full texts for detailed analysis when needed

## Version History

-   **v1.0** (Current): Initial implementation with core retrieval functionality
