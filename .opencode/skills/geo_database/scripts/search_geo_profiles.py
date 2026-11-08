#!/usr/bin/env python3
"""
Search GEO Profiles for gene-specific expression patterns.

Usage:
    uv run search_geo_profiles.py TP53
    uv run search_geo_profiles.py BRCA1 --organism "Homo sapiens" --retmax 50
    uv run search_geo_profiles.py GSE12345 --url  # Get URL for specific accession
"""

import sys
from Bio import Entrez
import argparse


def search_geo_profiles(gene_name, organism="Homo sapiens", retmax=100, email="agent@projector.local"):
    """
    Search GEO Profiles for a specific gene across studies.

    Args:
        gene_name: Gene symbol to search for
        organism: Organism name (default: Homo sapiens)
        retmax: Maximum number of results
        email: Email for NCBI Entrez

    Returns:
        Dictionary with search results
    """
    Entrez.email = email

    # Build search query
    query = f"{gene_name}[Gene Name] AND {organism}[Organism]"

    try:
        handle = Entrez.esearch(
            db="geoprofiles",
            term=query,
            retmax=retmax
        )
        results = Entrez.read(handle)
        handle.close()

        return results

    except Exception as e:
        print(f"Error searching GEO Profiles: {e}", file=sys.stderr)
        return None


def fetch_profile_summaries(id_list, email="agent@projector.local"):
    """
    Fetch summaries for GEO Profiles.

    Args:
        id_list: List of profile IDs
        email: Email for NCBI Entrez

    Returns:
        List of profile summaries
    """
    Entrez.email = email

    try:
        ids = ",".join(id_list)
        handle = Entrez.esummary(db="geoprofiles", id=ids)
        summaries = Entrez.read(handle)
        handle.close()

        # GEO Profiles returns a dictionary with 'DocumentSummarySet' key
        # The summaries are in 'DocumentSummary' which is a list
        if isinstance(summaries, dict) and 'DocumentSummarySet' in summaries:
            doc_summaries = summaries['DocumentSummarySet'].get('DocumentSummary', [])
            # Convert to list if it's a single item
            if isinstance(doc_summaries, dict):
                doc_summaries = [doc_summaries]
            return doc_summaries
        elif isinstance(summaries, list):
            return summaries
        else:
            print(f"Unexpected summary format: {type(summaries)}", file=sys.stderr)
            return []

    except Exception as e:
        print(f"Error fetching profile summaries: {e}", file=sys.stderr)
        return None


def display_results(results, summaries):
    """
    Display GEO Profiles search results.

    Args:
        results: Search results
        summaries: Profile summaries
    """
    if not results or not summaries:
        print("No results to display")
        return

    print(f"\n{'='*80}")
    print(f"Found {results['Count']} expression profiles")
    print(f"{'='*80}\n")

    for i, summary in enumerate(summaries, 0):

        # Handle both dict and object formats
        if isinstance(summary, dict):
            accession = summary.get('Accession', summary.get('accession', 'N/A'))
            title = summary.get('Title', summary.get('title', 'N/A'))
            gene_title = summary.get('geneName', summary.get('geneName', 'N/A'))
            organism = summary.get('taxon', summary.get('taxon', 'N/A'))
            gds = summary.get('GDS', summary.get('GDS', 'N/A'))
        else:
            # Fallback for unexpected format
            accession = str(summary) if not hasattr(summary, 'get') else 'N/A'
            title = 'N/A'
            gene_title = 'N/A'
            organism = 'N/A'
            gds = 'N/A'

        print(f"{i+1}. {accession}")
        print(f"   Gene: {gene_title}")
        print(f"   Study: {title}")
        print(f"   GDS: {gds}")
        print(f"   Organism: {organism}")
        print(f"   URL: https://www.ncbi.nlm.nih.gov/sites/GDSbrowser?acc=GDS{gds}")
        print()

    if len(summaries) > 20:
        print(f"... and {len(summaries) - 20} more results")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Search GEO Profiles for gene-specific expression patterns"
    )
    parser.add_argument(
        "gene",
        help="Gene symbol to search for (e.g., TP53, BRCA1)"
    )
    parser.add_argument(
        "--organism",
        default="Homo sapiens",
        help="Organism name (default: Homo sapiens)"
    )
    parser.add_argument(
        "--retmax",
        type=int,
        default=100,
        help="Maximum number of results to return (default: 100)"
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
        query_upper = args.gene.upper()
        if query_upper.startswith('GSE') or query_upper.startswith('GDS'):
            accession = query_upper
            url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"
            print(url)
            return
        else:
            print("Error: --url requires a GSE or GDS accession (e.g., GSE12345 or GDS1234)", file=sys.stderr)
            return

    print(f"Searching GEO Profiles for gene: {args.gene}")
    print(f"Organism: {args.organism}")
    print(f"Retrieving up to {args.retmax} results...")

    # Search
    results = search_geo_profiles(
        args.gene,
        args.organism,
        args.retmax,
        args.email
    )

    if not results or not results['IdList']:
        print(f"No expression profiles found for {args.gene}.")
        return

    # Fetch summaries
    summaries = fetch_profile_summaries(results['IdList'], args.email)

    # Display results
    display_results(results, summaries)


if __name__ == "__main__":
    main()
