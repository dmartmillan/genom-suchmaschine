# Zotero API Query Syntax Reference

## Quick Search

The Zotero API supports various search modes and filters.

### Basic Search

```
--query "transformer attention"
```

Searches titles and individual creator fields by default.

### Item Type Filters

Available item types include:
- `journalArticle` - Journal articles
- `book` - Books
- `conferencePaper` - Conference papers
- `thesis` - Theses and dissertations
- `preprint` - Preprints
- `report` - Technical reports
- `webpage` - Web pages
- `attachment` - File attachments
- `note` - Notes

Examples:
```bash
--item-type journalArticle
--item-type book
--item-type conferencePaper
```

### Tag Filters

Filter by tags:
```bash
--tag "deep learning"
--tag "transformers"
```

### Combined Filters

Multiple filters can be combined:
```bash
--query "large language models" --item-type journalArticle --tag "NLP"
```

## Sorting Options

Available sort fields:
- `title` - Alphabetical by title
- `date` - By publication date
- `dateAdded` - By date added to library
- `dateModified` - By last modification date
- `creator` - By author/creator name

Sort direction:
- `asc` - Ascending
- `desc` - Descending

Example:
```bash
--sort date --direction desc
```

## Advanced Search Syntax

### Boolean Operators

- `||` - OR operator
- `-` - NOT operator

Examples:
```
itemType=book || journalArticle  # Books OR journal articles
tag=-draft  # Items without "draft" tag
```

### Exact Phrase Search

Use quotes for exact phrases:
```
--query "attention is all you need"
```

### Field-Specific Search

Some fields can be searched specifically:
- `title:` - Search in title
- `creator:` - Search in creators
- `abstract:` - Search in abstract
- `tag:` - Search in tags

Example:
```
--query "title:transformer"
```

## Pagination

Use `--start` and `--limit` for pagination:
```bash
--limit 100 --start 0    # First 100 items
--limit 100 --start 100  # Next 100 items
```

Note: Maximum limit is 100 items per request.

## Export Formats

Available export formats:
- `bibtex` - BibTeX format
- `biblatex` - BibLaTeX format
- `ris` - RIS format
- `csv` - CSV format
- `csljson` - CSL-JSON format
- `mods` - MODS format
- `tei` - Text Encoding Initiative
- `wikipedia` - Wikipedia citation templates

## Citation Styles

For BibTeX/BibLaTeX exports, specify a citation style:
- `apa` - APA style
- `chicago-note-bibliography` - Chicago style
- `mla` - MLA style
- `ieee` - IEEE style

Style codes correspond to CSL styles available at:
https://www.zotero.org/support/dev/citation_styles

## Examples

### Search Recent Papers
```bash
uv run scripts/search_library.py \
  --query "large language models" \
  --item-type journalArticle \
  --sort dateAdded \
  --direction desc \
  --limit 50
```

### Export Collection to BibTeX
```bash
uv run scripts/export_collection.py \
  --collection-name "Literature Review" \
  --format bibtex \
  --style apa
```

### Find Papers by Author
```bash
uv run scripts/search_library.py \
  --query "author:vaswani" \
  --item-type conferencePaper \
  --sort date
```

### Get Papers with Specific Tag
```bash
uv run scripts/search_library.py \
  --query "" \
  --tag "transformers" \
  --limit 100
```
