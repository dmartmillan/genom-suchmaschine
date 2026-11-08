# Zotero Retrieval Skill

Quick reference for retrieving papers from Zotero collections.

## Setup

1. Get your API key from https://www.zotero.org/settings/keys
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   ZOTERO_API_KEY=your_api_key_here
   ZOTERO_USER_ID=your_user_id_here
   ```

## Common Commands

### List all collections
```bash
uv run .opencode/skills/zotero_retrieval/scripts/list_collections.py 2>/dev/null > collections.json
```

### Get items from a collection
```bash
uv run .opencode/skills/zotero_retrieval/scripts/get_collection_items.py \
  --collection-key ABC123DEF \
  2>/dev/null > collection_items.json
```

### Search library
```bash
uv run .opencode/skills/zotero_retrieval/scripts/search_library.py \
  --query "transformer attention" \
  --item-type journalArticle \
  2>/dev/null > search_results.json
```

### Download PDF
```bash
uv run .opencode/skills/zotero_retrieval/scripts/download_paper_pdf.py \
  --item-key XYZ789ABC \
  --output "paper.pdf"
```

### Export collection to BibTeX
```bash
uv run .opencode/skills/zotero_retrieval/scripts/export_collection.py \
  --collection-name "My Collection" \
  --format bibtex \
  --style apa \
  > collection.bib
```

## See Full Documentation

For complete documentation, see [SKILL.md](SKILL.md)
