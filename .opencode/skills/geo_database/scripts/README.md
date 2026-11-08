# GEO Database Scripts

This folder contains executable Python scripts for searching and downloading GEO (Gene Expression Omnibus) datasets.

## Prerequisites

Install required packages:

```bash
uv pip install GEOparse biopython pandas numpy
```

## Available Scripts

### 1. `search_geo_datasets.py`

Search GEO DataSets database for gene expression studies.

**Usage:**
```bash
# Basic search
uv run search_geo_datasets.py "breast cancer"

# Search with custom result limit
uv run search_geo_datasets.py "TP53 expression" --retmax 50

# Search with custom email
uv run search_geo_datasets.py "diabetes" --email "your.email@example.com"
```

**Options:**
- `query`: Search query string (required)
- `--retmax`: Maximum number of results (default: 20)
- `--email`: Email for NCBI Entrez (default: agent@projector.local)

**Example Output:**
```
Searching GEO DataSets for: 'breast cancer'
Retrieving up to 20 results...

================================================================================
Found 1247 datasets matching query
================================================================================

1. GDS5678
   Title: Breast cancer progression stages
   Organism: Homo sapiens
   Samples: 156
   PubMed ID: 12345678
   Data Type: expression profiling by array
   URL: https://www.ncbi.nlm.nih.gov/gds/GDS5678
```

---

### 2. `search_geo_profiles.py`

Search GEO Profiles for gene-specific expression patterns across studies.

**Usage:**
```bash
# Search for a gene
uv run search_geo_profiles.py TP53

# Search with organism filter
uv run search_geo_profiles.py BRCA1 --organism "Homo sapiens" --retmax 50
```

**Options:**
- `gene`: Gene symbol to search for (required)
- `--organism`: Organism name (default: Homo sapiens)
- `--retmax`: Maximum results (default: 100)
- `--email`: Email for NCBI Entrez

**Example Output:**
```
Searching GEO Profiles for gene: TP53
Organism: Homo sapiens
Retrieving up to 100 results...

================================================================================
Found 3456 expression profiles
================================================================================

1. GPL570|1939_at
   Gene: TP53 tumor protein p53
   Study: Genome-wide analysis of TP53 targets
   GSE: GSE12345
   Organism: Homo sapiens
   URL: https://www.ncbi.nlm.nih.gov/geoprofiles/123456
```

---

### 3. `download_geo_series.py`

Download GEO Series data using GEOparse.

**Usage:**
```bash
# Download a series
uv run download_geo_series.py GSE123456

# Download to custom directory
uv run download_geo_series.py GSE123456 --output ./data

# Download with supplementary files
uv run download_geo_series.py GSE123456 --supplementary
```

**Options:**
- `geo_id`: GEO Series accession (required)
- `--output`, `-o`: Output directory (default: ./geo_data)
- `--supplementary`, `-s`: Download supplementary files

**What it does:**
- Downloads series matrix file
- Extracts expression matrix and saves as CSV
- Saves metadata
- Optionally downloads supplementary files
- Creates organized folder structure

**Example Output:**
```
Downloading GSE123456...
✓ Successfully downloaded GSE123456
  Title: Study of gene expression in breast cancer
  Organism: Homo sapiens
  Samples: 120
  Platforms: ['GPL570']
✓ Expression matrix saved to: ./geo_data/GSE123456_expression.csv
  Shape: (20530, 120) (genes x samples)
✓ Metadata saved to: ./geo_data/GSE123456_metadata.txt

============================================================
Download complete!
Files saved to: /path/to/geo_data
============================================================
```

---

### 4. `advanced_geo_search.py`

Advanced GEO search with multiple filters and criteria.

**Usage:**
```bash
# Search by disease and organism
uv run advanced_geo_search.py --disease "breast cancer" --organism "Homo sapiens"

# Search by technology type
uv run advanced_geo_search.py --technology "RNA-seq" --year 2024

# Search by author and platform
uv run advanced_geo_search.py --author "Smith" --platform "GPL570"

# Save results to file
uv run advanced_geo_search.py --disease "diabetes" --output diabetes_studies.txt
```

**Options:**
- `--disease`: Disease or condition (e.g., 'breast cancer')
- `--organism`: Organism (e.g., 'Homo sapiens')
- `--author`: Author name
- `--platform`: Platform accession (e.g., 'GPL570')
- `--year`: Publication year
- `--technology`: Technology type (RNA-seq, microarray, sequencing)
- `--dataset-type`: Dataset type filter
- `--retmax`: Maximum results (default: 50)
- `--output`, `-o`: Output file to save results
- `--email`: Email for NCBI Entrez

**Example Output:**
```
Searching GEO with query: breast cancer[MeSH Terms] AND Homo sapiens[Organism]
Retrieving up to 50 results...

================================================================================
Advanced GEO Search Results
Total matching datasets: 234
Showing: 50 datasets
================================================================================

1. GDS5678
   Title: Breast cancer progression stages
   Organism: Homo sapiens
   Samples: 156
   Data Type: expression profiling by array
   PubMed: 12345678
   URL: https://www.ncbi.nlm.nih.gov/gds/GDS5678
```

---

### 5. `batch_download.py`

Batch download and process multiple GEO Series.

**Usage:**
```bash
# Download multiple series from command line
uv run batch_download.py GSE12345 GSE67890 GSE11111

# Download from file (one GSE per line)
uv run batch_download.py --input-file gse_list.txt

# Custom output directory
uv run batch_download.py GSE12345 --output ./batch_data
```

**Options:**
- `gse_ids`: GEO Series accessions (space-separated)
- `--input-file`, `-i`: File containing GSE accessions (one per line)
- `--output`, `-o`: Output directory (default: ./batch_geo_data)

**What it does:**
- Downloads multiple GEO series sequentially
- Extracts expression matrices for each
- Saves metadata for each series
- Creates comprehensive summary CSV
- Handles errors gracefully

**Example Output:**
```
================================================================================
Batch Download - 3 datasets
Output directory: ./batch_geo_data
================================================================================

Progress: 1/3

[GSE12345] Downloading...
[GSE12345] ✓ Success: 120 samples, 20530 genes

Progress: 2/3

[GSE67890] Downloading...
[GSE67890] ✓ Success: 85 samples, 20530 genes

================================================================================
Batch Download Summary
================================================================================
Total datasets: 3
Successful: 3
Failed: 0

Summary saved to: ./batch_geo_data/batch_download_summary.csv
================================================================================
```

---

## Common Workflows

### Workflow 1: Find and Download a Dataset

```bash
# Step 1: Search for relevant datasets
uv run search_geo_datasets.py "breast cancer RNA-seq"

# Step 2: Download the most relevant dataset
uv run download_geo_series.py GSE123456 --output ./breast_cancer_data
```

### Workflow 2: Gene-Centric Analysis

```bash
# Step 1: Find all studies with gene expression data for a gene
uv run search_geo_profiles.py TP53 --retmax 20

# Step 2: Download key studies
uv run download_geo_series.py GSE123456
uv run download_geo_series.py GSE789012
```

### Workflow 3: Meta-Analysis Preparation

```bash
# Step 1: Create a list of relevant GSE accessions
echo "GSE12345" > gse_list.txt
echo "GSE67890" >> gse_list.txt
echo "GSE11111" >> gse_list.txt

# Step 2: Batch download all datasets
uv run batch_download.py --input-file gse_list.txt --output ./meta_analysis_data
```

### Workflow 4: Advanced Filtering

```bash
# Find recent high-throughput RNA-seq studies
uv run advanced_geo_search.py \
  --organism "Homo sapiens" \
  --technology "RNA-seq" \
  --year 2024 \
  --retmax 100 \
  --output 2024_rnaseq_studies.txt
```

---

## Tips

1. **Rate Limiting**: Scripts automatically handle NCBI rate limits (3 requests/second without API key)

2. **Email**: Always set a valid email address for NCBI compliance:
   ```bash
   uv run search_geo_datasets.py "query" --email "your.email@example.com"
   ```

3. **Caching**: GEOparse caches downloaded files, so re-running downloads is fast

4. **Large Datasets**: Some series have >1000 samples - check before downloading

5. **Platform Compatibility**: Ensure platforms are compatible before combining datasets

6. **API Key**: For faster downloads, get an NCBI API key and add it to your environment:
   ```bash
   export NCBI_API_KEY="your_api_key"
   ```

---

## Troubleshooting

### "GEOparse is not installed"
```bash
uv pip install GEOparse
```

### "No results found"
- Try broader search terms
- Check spelling of gene names
- Verify organism name format

### "Download failed"
- Check internet connection
- Verify GSE accession number
- Try again later (NCBI server issues)

### "Rate limit exceeded"
- Add `--email` parameter
- Reduce `--retmax` value
- Use API key for higher limits

---

## References

- [GEO Database](https://www.ncbi.nlm.nih.gov/geo/)
- [GEOparse Documentation](https://geoparse.readthedocs.io/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
