#!/usr/bin/env python3
"""
Advanced GEO search with multiple filters and criteria.

Usage:
    uv run advanced_geo_search.py --disease "breast cancer" --organism "Homo sapiens"
    uv run advanced_geo_search.py --author "Smith" --platform "GPL570"
    uv run advanced_geo_search.py --year 2024 --technology "RNA-seq"
    uv run advanced_geo_search.py GSE12345 --url  # Get URL for specific accession
"""

import sys
from Bio import Entrez
import argparse
import time


def build_search_query(**kwargs):
    """
    Build a complex GEO search query from multiple criteria.

    Args:
        **kwargs: Search criteria (disease, organism, author, platform, year, technology)

    Returns:
        Search query string
    """
    terms = []

    if kwargs.get('disease'):
        terms.append(f"{kwargs['disease']}[MeSH Terms]")

    if kwargs.get('organism'):
        terms.append(f"{kwargs['organism']}[Organism]")

    if kwargs.get('author'):
        terms.append(f"{kwargs['author']}[Author]")

    if kwargs.get('platform'):
        terms.append(f"{kwargs['platform']}[Accession]")

    if kwargs.get('year'):
        terms.append(f"{kwargs['year']}[Publication Date]")

    if kwargs.get('technology'):
        # Note: Technology filters work better with full GEO Series search
        # For GDS database, use disease/organism filters instead
        tech_map = {
            'RNA-seq': 'RNA-seq',
            'microarray': 'microarray',
            'sequencing': 'sequencing'
        }
        tech_query = tech_map.get(kwargs['technology'], kwargs['technology'])
        # Add as keyword search rather than DataSet Type filter for GDS
        terms.append(f"{tech_query}")

    if kwargs.get('dataset_type'):
        terms.append(f"{kwargs['dataset_type']}[DataSet Type]")

    return " AND ".join(terms)


def search_geo_advanced(query, retmax=50, email="agent@projector.local", db="gds"):
    """
    Perform advanced GEO search.

    Args:
        query: Search query string
        retmax: Maximum results
        email: Email for NCBI Entrez
        db: Database to search (currently only 'gds' is supported)

    Returns:
        Search results
    """
    Entrez.email = email

    try:
        # Only GDS database is supported for advanced search
        # For full GEO Series search, use search_geo_datasets.py or download_geo_series.py
        if db != 'gds':
            print("Warning: Only 'gds' database is supported for advanced search.", file=sys.stderr)
            print("For full GEO Series (GSE) search, consider using other scripts.", file=sys.stderr)

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


def fetch_detailed_summaries(id_list, email="agent@projector.local", db="gds"):
    """
    Fetch detailed summaries for GEO datasets.

    Args:
        id_list: List of dataset IDs
        email: Email for NCBI Entrez
        db: Database ('gds' or 'gse')
    currently only 'gds' is supported)

    Returns:
        List of summaries
    """
    Entrez.email = email

    try:
        # Only GDS database is supported
        # Fetch in batches of 100 to avoid rate limiting
        all_summaries = []

        for i in range(0, len(id_list), 100):
            batch = id_list[i:i+100]
            ids = ",".join(batch)

            handle = Entrez.esummary(db="gds", id=ids)
            summaries = Entrez.read(handle)
            handle.close()

            all_summaries.extend(summaries)

            # Be polite to NCBI servers
            time.sleep(0.35)

        return all_summaries

    except Exception as e:
        print(f"Error fetching summaries: {e}", file=sys.stderr)
        return None


def display_results(results, summaries):
    """
    Display advanced search results.

    Args:
        results: Search results
        summaries: Dataset summaries
    """
    if not results or not summaries:
        print("No results to display")
        return

    print(f"\n{'='*80}")
    print(f"Advanced GEO Search Results")
    print(f"Total matching datasets: {results['Count']}")
    print(f"Showing: {len(summaries)} datasets")
    print(f"{'='*80}\n")

    for i, summary in enumerate(summaries, 0):
        accession = summary.get('Accession', 'N/A')
        title = summary.get('title', 'N/A')
        organism = summary.get('taxon', 'N/A')

        # Handle n_samples which might be an IntegerElement
        n_samples = summary.get('n_samples', 'N/A')
        try:
            n_samples = int(n_samples)
        except (ValueError, TypeError):
            n_samples = str(n_samples)

        # Handle pubmed_id/PubMedIds which might be IntegerElement or list
        pubmed_ids = summary.get('PubMedIds', summary.get('PubMedIds', None))
        if pubmed_ids:
            try:
                if isinstance(pubmed_ids, list):
                    pubmed_ids = [int(pid) for pid in pubmed_ids if pid]
                    pubmed_id = ', '.join(str(pid) for pid in pubmed_ids) if pubmed_ids else 'N/A'
                else:
                    pubmed_id = str(int(pubmed_ids))
            except (ValueError, TypeError):
                pubmed_id = 'N/A'
        else:
            pubmed_id = 'N/A'

        data_type = summary.get('gdsType', 'N/A')

        print(f"{i}. {accession}")
        print(f"   Title: {title}")
        print(f"   Organism: {organism}")
        print(f"   Samples: {n_samples}")
        print(f"   Data Type: {data_type}")
        print(f"   PubMed ID: {pubmed_id}")
        print(f"   URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}")
        print()


def save_results(summaries, output_file):
    """
    Save search results to a file.

    Args:
        summaries: Dataset summaries
        output_file: Output file path
    """
    with open(output_file, 'w') as f:
        f.write("GEO Dataset Search Results\n")
        f.write("=" * 80 + "\n\n")

        for summary in summaries:
            accession = summary.get('Accession', 'N/A')
            title = summary.get('title', 'N/A')
            organism = summary.get('taxon', 'N/A')
            n_samples = summary.get('n_samples', 'N/A')
            pubmed_ids = summary.get('PubMedIds', summary.get('PubMedIds', None))
            if pubmed_ids:
                try:
                    if isinstance(pubmed_ids, list):
                        pubmed_ids = [int(pid) for pid in pubmed_ids if pid]
                        pubmed_id = ', '.join(str(pid) for pid in pubmed_ids) if pubmed_ids else 'N/A'
                    else:
                        pubmed_id = str(int(pubmed_ids))
                except (ValueError, TypeError):
                    pubmed_id = 'N/A'
            else:
                pubmed_id = 'N/A'


            f.write(f"Accession: {accession}\n")
            f.write(f"Title: {title}\n")
            f.write(f"Organism: {organism}\n")
            f.write(f"Samples: {n_samples}\n")
            f.write(f"PubMed ID: {pubmed_id}\n")
            f.write(f"URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}\n")
            f.write("-" * 40 + "\n")

    print(f"Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Advanced GEO search with multiple filters"
    )
    parser.add_argument(
        "accession",
        nargs="?",
        default=None,
        help="GEO accession (GSE/GDS) for --url mode (e.g., GSE12345)"
    )
    parser.add_argument(
        "--disease",
        help="Disease or condition (e.g., 'breast cancer')"
    )
    parser.add_argument(
        "--organism",
        help="Organism (e.g., 'Homo sapiens', 'Mus musculus')"
    )
    parser.add_argument(
        "--author",
        help="Author name"
    )
    parser.add_argument(
        "--platform",
        help="Platform accession (e.g., 'GPL570')"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Publication year"
    )
    parser.add_argument(
        "--technology",
        choices=['RNA-seq', 'microarray', 'sequencing'],
        help="Technology type (note: works better with full GEO Series via search_geo_datasets.py)"
    )
    parser.add_argument(
        "--dataset-type",
        help="Dataset type filter"
    )
    parser.add_argument(
        "--retmax",
        type=int,
        default=50,
        help="Maximum results (default: 50)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file to save results"
    )
    parser.add_argument(
        "--email",
        default="agent@projector.local",
        help="Email for NCBI Entrez"
    )
    parser.add_argument(
        "--database",
        choices=['gds'],
        default='gds',
        help="Database to search: 'gds' (curated datasets, ~4K studies)"
    )
    parser.add_argument(
        "--url",
        action="store_true",
        help="Return only the NCBI URL for the accession (use with a single GSE/GDS accession)"
    )

    args = parser.parse_args()

    # Handle --url mode for single accession
    if args.url:
        if not args.accession:
            print("Error: --url requires an accession argument (e.g., uv run advanced_geo_search.py GSE12345 --url)", file=sys.stderr)
            sys.exit(1)

        accession = args.accession.upper()
        if accession.startswith('GSE') or accession.startswith('GDS'):
            url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"
            print(url)
            return
        else:
            print("Error: --url requires a GSE or GDS accession (e.g., GSE12345 or GDS1234)", file=sys.stderr)
            sys.exit(1)

    # Build search query
    query = build_search_query(
        disease=args.disease,
        organism=args.organism,
        author=args.author,
        platform=args.platform,
        year=args.year,
        technology=args.technology,
        dataset_type=args.dataset_type
    )

    if not query:
        print("Error: At least one search criterion must be provided.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    db_name = "GEO DataSets (curated, ~4,300 datasets)"
    print(f"Searching {db_name} with query: {query}")
    print(f"Retrieving up to {args.retmax} results...")
    print(f"Note: For full GEO Series (GSE) search with 265K+ studies, use search_geo_datasets.py")
    print()

    # Search
    results = search_geo_advanced(query, args.retmax, args.email, args.database)

    if not results:
        print("Error: Search failed. Please check your query and try again.")
        return

    if not results['IdList'] or results['Count'] == '0':
        print(f"No datasets found matching your criteria.")
        print(f"Search query: {query}")
        if args.year:
            print(f"Note: You searched for year {args.year}. Try a different year or remove the year filter.")
        if args.technology:
            print(f"Note: Technology filters work better with full GEO Series search.")
            print(f"      Try: uv run search_geo_datasets.py '{args.technology}' --retmax 50")
        print(f"      Or use disease/organism filters which work better with GDS database.")
        return

    # Fetch summaries
    summaries = fetch_detailed_summaries(results['IdList'], args.email, args.database)

    # Display results
    display_results(results, summaries)

    # Save if requested
    if args.output:
        save_results(summaries, args.output)


if __name__ == "__main__":
    main()
