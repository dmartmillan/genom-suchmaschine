#!/usr/bin/env python3
"""
Batch download and process multiple GEO Series.

Usage:
    uv run batch_download.py gse_list.txt
    uv run batch_download.py GSE12345 GSE67890 GSE11111
    uv run batch_download.py gse_list.txt --output ./batch_data
"""

import sys
import os
import argparse

try:
    import GEOparse
    import pandas as pd
except ImportError as e:
    print("Error: Required packages are not installed.", file=sys.stderr)
    print("Install them with: uv pip install GEOparse pandas", file=sys.stderr)
    sys.exit(1)


def read_gse_list(input_file):
    """
    Read list of GSE accessions from file.

    Args:
        input_file: Path to file containing GSE IDs (one per line)

    Returns:
        List of GSE accessions
    """
    accessions = []

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                accessions.append(line)

    return accessions


def download_single_series(gse_id, output_dir, timeout=300):
    """
    Download a single GEO series with error handling.

    Args:
        gse_id: GEO Series accession
        output_dir: Output directory
        timeout: Timeout in seconds

    Returns:
        Dictionary with download results
    """
    result = {
        'gse_id': gse_id,
        'status': 'pending',
        'error': None,
        'num_samples': 0,
        'num_genes': 0,
        'title': None
    }

    try:
        print(f"\n[{gse_id}] Downloading...")

        gse = GEOparse.get_GEO(geo=gse_id, destdir=output_dir)

        result['status'] = 'success'
        result['title'] = gse.metadata.get('title', ['N/A'])[0]
        result['num_samples'] = len(gse.gsms)
        result['organism'] = gse.metadata.get('organism', ['N/A'])[0]

        # Save expression data
        if hasattr(gse, 'pivot_samples'):
            expr_df = gse.pivot_samples('VALUE')
            expr_file = os.path.join(output_dir, f"{gse_id}_expression.csv")
            expr_df.to_csv(expr_file)
            result['num_genes'] = len(expr_df)
            result['expr_file'] = expr_file

        # Save metadata
        meta_file = os.path.join(output_dir, f"{gse_id}_metadata.txt")
        with open(meta_file, 'w') as f:
            for key, value in gse.metadata.items():
                f.write(f"{key}: {value}\n")
        result['meta_file'] = meta_file

        print(f"[{gse_id}] ✓ Success: {result['num_samples']} samples, {result['num_genes']} genes")

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        print(f"[{gse_id}] ✗ Failed: {e}")

    return result


def batch_download(gse_list, output_dir, max_concurrent=3):
    """
    Batch download multiple GEO series.

    Args:
        gse_list: List of GSE accessions
        output_dir: Output directory
        max_concurrent: Maximum concurrent downloads

    Returns:
        List of download results
    """
    results = []

    print(f"{'='*80}")
    print(f"Batch Download - {len(gse_list)} datasets")
    print(f"Output directory: {output_dir}")
    print(f"{'='*80}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Download each series
    for i, gse_id in enumerate(gse_list, 1):
        print(f"\nProgress: {i}/{len(gse_list)}")

        result = download_single_series(gse_id, output_dir)
        results.append(result)

        # Add delay between downloads to be polite to NCBI
        if i < len(gse_list):
            import time
            time.sleep(2)

    return results


def save_batch_summary(results, output_dir):
    """
    Save batch download summary.

    Args:
        results: List of download results
        output_dir: Output directory
    """
    # Create summary DataFrame
    summary_data = []

    for result in results:
        summary_data.append({
            'GSE_ID': result['gse_id'],
            'Status': result['status'],
            'Title': result['title'] or 'N/A',
            'Organism': result.get('organism', 'N/A'),
            'Samples': result['num_samples'],
            'Genes': result['num_genes'],
            'Error': result['error'] or 'N/A'
        })

    summary_df = pd.DataFrame(summary_data)

    # Save to CSV
    summary_file = os.path.join(output_dir, "batch_download_summary.csv")
    summary_df.to_csv(summary_file, index=False)

    print(f"\n{'='*80}")
    print(f"Batch Download Summary")
    print(f"{'='*80}")
    print(f"Total datasets: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results if r['status'] == 'failed')}")
    print(f"\nSummary saved to: {summary_file}")
    print(f"{'='*80}")

    return summary_df


def main():
    parser = argparse.ArgumentParser(
        description="Batch download and process multiple GEO Series"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "gse_ids",
        nargs="*",
        help="GEO Series accessions (e.g., GSE12345 GSE67890)"
    )
    group.add_argument(
        "--input-file", "-i",
        help="File containing GSE accessions (one per line)"
    )

    parser.add_argument(
        "--output", "-o",
        default="./batch_geo_data",
        help="Output directory (default: ./batch_geo_data)"
    )

    args = parser.parse_args()

    # Get GSE list
    if args.input_file:
        if not os.path.exists(args.input_file):
            print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
            sys.exit(1)

        gse_list = read_gse_list(args.input_file)
        print(f"Read {len(gse_list)} accessions from {args.input_file}")
    else:
        gse_list = args.gse_ids
        print(f"Processing {len(gse_list)} accessions")

    if not gse_list:
        print("Error: No GSE accessions provided.", file=sys.stderr)
        sys.exit(1)

    # Batch download
    results = batch_download(gse_list, args.output)

    # Save summary
    summary_df = save_batch_summary(results, args.output)

    # Exit with error code if any failed
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
