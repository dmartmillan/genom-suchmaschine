#!/usr/bin/env python3
"""
Search GEO DataSets (GDS) database by keyword and display results.

IMPORTANT: This script searches the curated GEO DataSets (GDS) database only,
which contains ~4,300 experimentally-comparable datasets. For searching the full
GEO Series (GSE) database with 264,000+ studies, use:
  - advanced_geo_search.py for broader searches
  - Or search PubMed for papers mentioning GEO accessions

Usage:
    uv run search_geo_datasets.py "breast cancer"
    uv run search_geo_datasets.py "TP53 expression" --retmax 50
    uv run search_geo_datasets.py GSE12345 --url  # Get URL for specific accession
"""

import sys
from Bio import Entrez
import argparse


def search_geo_datasets(query, retmax=20, email="agent@projector.local"):
    """
    Search GEO DataSets database for studies matching the query.

    Args:
        query: Search query string
        retmax: Maximum number of results to return
        email: Email for NCBI Entrez (required)

    Returns:
        Dictionary with search results
    """
    # Configure Entrez
    Entrez.email = email

    try:
        # Search for datasets in GDS database
        handle = Entrez.esearch(
            db="gds",
            term=query,
            retmax=retmax,
            usehistory="y"
        )
        results = Entrez.read(handle)
        handle.close()

        return results

    except Exception as e:
        print(f"Error searching GEO: {e}", file=sys.stderr)
        return None


def fetch_dataset_summaries(id_list, email="agent@projector.local"):
    """
    Fetch summaries for GEO datasets.

    Args:
        id_list: List of dataset IDs
        email: Email for NCBI Entrez

    Returns:
        List of dataset summaries
    """
    Entrez.email = email

    try:
        ids = ",".join(id_list)
        handle = Entrez.esummary(db="gds", id=ids)
        summaries = Entrez.read(handle)
        handle.close()

        return summaries

    except Exception as e:
        print(f"Error fetching summaries: {e}", file=sys.stderr)
        return None


def display_results(results, summaries):
    """
    Display search results in a formatted table.

    Args:
        results: Search results from esearch
        summaries: Dataset summaries from esummary
    """
    if not results:
        print("No results to display")
        return

    print(f"\n{'='*80}")
    print(f"Found {results['Count']} datasets matching query in GEO DataSets (GDS)")
    print(f"{'='*80}\n")

    print(f"Showing detailed metadata for {len(summaries)} curated GDS datasets:\n")

    for i, summary in enumerate(summaries, 0):
        # Handle different data formats from NCBI
        if isinstance(summary, dict):
            accession = summary.get('Accession', summary.get('accession', 'N/A'))
            title = summary.get('title', summary.get('Title', 'N/A'))
            organism = summary.get('taxon', summary.get('taxon', 'N/A'))

            # Handle n_samples which might be an IntegerElement
            n_samples = summary.get('n_samples', summary.get('n_samples', 'N/A'))
            try:
                n_samples = int(n_samples)
            except (ValueError, TypeError):
                n_samples = str(n_samples)

            pubmed_ids = summary.get('PubMedIds', summary.get('PubMedIds', 'N/A'))

            if pubmed_ids is None or pubmed_ids == []:
                pubmed_id = 'N/A'
            else:
                pubmed_ids = [int(pid) for pid in pubmed_ids if pid]
                pubmed_id = ', '.join(str(pid) for pid in pubmed_ids) if pubmed_ids else 'N/A'
            data_type = summary.get('gdsType', summary.get('gdsType', 'N/A'))
        else:
            # Fallback for unexpected format
            accession = str(summary) if not hasattr(summary, 'get') else 'N/A'
            title = 'N/A'
            organism = 'N/A'
            n_samples = 'N/A'
            pubmed_id = 'N/A'
            data_type = 'N/A'

        print(f"{i}. {accession}")
        print(f"   Title: {title}")
        print(f"   Organism: {organism}")
        print(f"   Samples: {n_samples}")
        print(f"   PubMed ID: {pubmed_id}")
        print(f"   Data Type: {data_type}")
        print(f"   URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Search GEO DataSets database for gene expression studies"
    )
    parser.add_argument(
        "query",
        help="Search query (e.g., 'breast cancer', 'TP53 expression')"
    )
    parser.add_argument(
        "--retmax",
        type=int,
        default=20,
        help="Maximum number of results to return (default: 20)"
    )
    parser.add_argument(
        "--email",
        default="agent@projector.local",
        help="Email address for NCBI Entrez (default: agent@projector.local)"
    )
    parser.add_argument(
        "--url",
        action="store_true",
        help="Return only the NCBI URL for the accession (use with a single GSE/GDS accession)"
    )

    args = parser.parse_args()

    # Handle --url mode for single accession
    if args.url:
        # Check if query looks like an accession
        query_upper = args.query.upper()
        if query_upper.startswith('GSE') or query_upper.startswith('GDS'):
            accession = query_upper
            url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"
            print(url)
            return
        else:
            print("Error: --url requires a GSE or GDS accession (e.g., GSE12345 or GDS1234)", file=sys.stderr)
            return

    print(f"Searching GEO DataSets (GDS) for: '{args.query}'")
    print(f"Retrieving up to {args.retmax} results...")
    print(f"Note: GDS contains ~4,300 curated datasets (not all 264K+ GEO studies)")
    print()

    # Search
    results = search_geo_datasets(args.query, args.retmax, args.email)

    if not results or not results['IdList']:
        print("No datasets found matching your query in the GDS database.")
        print("Try using advanced_geo_search.py for broader searches.")
        return

    # Fetch summaries
    summaries = fetch_dataset_summaries(results['IdList'], args.email)

    # Display results
    display_results(results, summaries)


if __name__ == "__main__":
    main()
