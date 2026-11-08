# Literature Search Protocol for Agents

## CRITICAL: Priority Order for Literature Search

**ALL agents MUST follow this exact order when searching for papers:**

### ✅ STEP 1: Search Zotero Collections (HIGHEST PRIORITY)

**ALWAYS start here. Never skip this step.**

```bash
# 1. List all collections
uv run .opencode/skills/zotero_retrieval/scripts/list_collections.py 2>/dev/null > project_X/zotero_collections.json

# 2. Search entire library
uv run .opencode/skills/zotero_retrieval/scripts/search_library.py \
  --query "YOUR_SEARCH_TERMS" \
  --item-type journalArticle \
  --sort dateAdded \
  --direction desc \
  --limit 100 \
  2>/dev/null > project_X/zotero_search_results.json

# 3. Search specific collections
uv run .opencode/skills/zotero_retrieval/scripts/get_collection_items.py \
  --collection-name "CollectionName" \
  --limit 100 \
  2>/dev/null > project_X/collection_items.json

# 4. Download PDFs for detailed reading
uv run .opencode/skills/zotero_retrieval/scripts/download_paper_pdf.py \
  --item-key ITEM_KEY \
  --output "project_X/paper_title.pdf"
```

**Your Zotero collections include:**
- Models (H8KRIY49)
- Agents (TPVSR2UT)
- Reviews (PFRD8983)
- Ribosome (MDU5I8IG)
- RNA-localization (FH5AVIR3)
- Translation (JM72MJ7Q)
- Evolution (9SCCJFIC)
- Data Visualization (AJET6XGR)
- General (SDUCWETF)
- FidelityNet (6CRDQNDK)

### ✅ STEP 2: Use Other Skills

1. **arXiv** - For CS, math, physics
   ```bash
   uv run .opencode/skills/literature_search_arxiv/scripts/search_arxiv.py \
     --query "YOUR_QUERY" \
     --max_results 100 \
     --sort_by submittedDate \
     --sort_order descending \
     2>/dev/null > project_X/arxiv_results.json
   ```

2. **bioRxiv** - For biology preprints (use narrow date ranges)
   ```bash
   uv run .opencode/skills/literature_search_biorxiv/scripts/search_biorxiv.py \
     --query "YOUR_QUERY" \
     --max_results 100 \
     2>/dev/null > project_X/biorxiv_results.json
   ```

3. **pubmed_database** - For biomedical/life sciences (CRITICAL for protocols)
   ```bash
   uv run .opencode/skills/pubmed_database/scripts/pubmed_api.py \
     --query "YOUR_QUERY" \
     --max_results 100 \
     2>/dev/null > project_X/pubmed_results.json
   ```

4. **EuropePMC** - For broader biomedical literature
   ```bash
   uv run .opencode/skills/literature_search_europepmc/scripts/search_europepmc.py \
     --query "YOUR_QUERY" \
     --limit 100 \
     --sort "P_PDATE_D desc" \
     2>/dev/null > project_X/europepmc_results.json
   ```

## Key Rules

1. **Zotero FIRST** - Never use other skills before searching Zotero
2. **Recent Papers** - Always prioritize papers from last 1-2 years
3. **Comprehensive** - Use `--limit 100` or `--max_results 100`
4. **Save to project_X/** - Never use `/tmp/` or other temp directories
5. **Read Before Proposing** - Analyze papers before suggesting methods
6. **Document Sources** - Cite which papers informed your recommendations

## Example Workflow

```bash
# Search for "attention mechanisms" in Zotero
uv run .opencode/skills/zotero_retrieval/scripts/search_library.py \
  --query "attention mechanisms" \
  --item-type journalArticle \
  --sort dateAdded \
  --direction desc \
  --limit 100 \
  2>/dev/null > project_X/zotero_attention.json

# If insufficient results, then search arXiv
uv run .opencode/skills/literature_search_arxiv/scripts/search_arxiv.py \
  --query "au:* AND ti:attention" \
  --max_results 100 \
  --sort_by submittedDate \
  --sort_order descending \
  2>/dev/null > project_X/arxiv_attention.json
```

## Remember

- **Zotero = Curated, high-quality papers** (use first!)
- **Other skills = Supplemental** (use only if needed)
- **Always prioritize recent research**
- **Always save to project_X/**
