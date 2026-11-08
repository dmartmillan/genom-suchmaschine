#!/usr/bin/env python3
"""
Download GEO Series data using GEOparse.

Usage:
    uv run download_geo_series.py GSE123456
    uv run download_geo_series.py GSE123456 --output ./data
    uv run download_geo_series.py GSE123456 --supplementary
"""

import sys
import os
import argparse

try:
    import GEOparse
except ImportError:
    print("Error: GEOparse is not installed.", file=sys.stderr)
    print("Install it with: uv pip install GEOparse", file=sys.stderr)
    sys.exit(1)


def download_series(geo_id, output_dir="./geo_data", download_supplementary=False):
    """
    Download and parse a GEO Series.

    Args:
        geo_id: GEO Series accession (e.g., GSE123456)
        output_dir: Directory to save downloaded files
        download_supplementary: Whether to download supplementary files

    Returns:
        GEOparse GEO Series object or None
    """
    try:
        print(f"Downloading {geo_id}...")

        # Download series
        gse = GEOparse.get_GEO(geo=geo_id, destdir=output_dir)

        print(f"✓ Successfully downloaded {geo_id}")
        print(f"  Title: {gse.metadata.get('title', ['N/A'])[0]}")
        print(f"  Organism: {gse.metadata.get('organism', ['N/A'])[0]}")
        print(f"  Samples: {len(gse.gsms)}")
        print(f"  Platforms: {list(gse.gpls.keys())}")

        # Download supplementary files if requested
        if download_supplementary:
            print(f"\nDownloading supplementary files...")
            gse.download_supplementary_files(
                directory=os.path.join(output_dir, f"{geo_id}_suppl"),
                download_sra=False
            )
            print("✓ Supplementary files downloaded")

        # Save expression matrix
        if hasattr(gse, 'pivot_samples'):
            expr_file = os.path.join(output_dir, f"{geo_id}_expression.csv")
            expr_df = gse.pivot_samples('VALUE')
            expr_df.to_csv(expr_file)
            print(f"✓ Expression matrix saved to: {expr_file}")
            print(f"  Shape: {expr_df.shape} (genes x samples)")

        # Save metadata
        metadata_file = os.path.join(output_dir, f"{geo_id}_metadata.txt")
        with open(metadata_file, 'w') as f:
            for key, value in gse.metadata.items():
                f.write(f"{key}: {value}\n")
        print(f"✓ Metadata saved to: {metadata_file}")

        return gse

    except Exception as e:
        print(f"Error downloading {geo_id}: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Download GEO Series data using GEOparse"
    )
    parser.add_argument(
        "geo_id",
        help="GEO Series accession (e.g., GSE123456)"
    )
    parser.add_argument(
        "--output", "-o",
        default="./geo_data",
        help="Output directory (default: ./geo_data)"
    )
    parser.add_argument(
        "--supplementary", "-s",
        action="store_true",
        help="Download supplementary files"
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Download series
    gse = download_series(
        args.geo_id,
        args.output,
        args.supplementary
    )

    if gse:
        print(f"\n{'='*60}")
        print("Download complete!")
        print(f"Files saved to: {os.path.abspath(args.output)}")
        print(f"{'='*60}")
    else:
        print("\nDownload failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
