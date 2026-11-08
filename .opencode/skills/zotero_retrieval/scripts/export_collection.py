# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Exports a Zotero collection to various citation formats.

This script exports all items in a collection to formats like BibTeX,
BibLaTeX, RIS, CSV, or CSL-JSON.
"""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "scienceskillscommon",
#   "python-dotenv",
# ]
# [tool.uv.sources]
# scienceskillscommon = { path = "../../scienceskillscommon" }
# ///

import argparse
import json
import os
import sys
import urllib.parse

import dotenv
from science_skills.skills.scienceskillscommon import http_client


# Load environment variables from .env file
dotenv.load_dotenv(os.path.expanduser("~/.env"))
dotenv.load_dotenv(".env")


def _get_api_client() -> http_client.HttpClient:
  """Creates an HTTP client for Zotero API with rate limiting."""
  api_key = os.environ.get("ZOTERO_API_KEY")
  if not api_key:
    print(
        "Error: ZOTERO_API_KEY not found in environment. "
        "Please set it in your .env file.",
        file=sys.stderr,
    )
    sys.exit(1)

  return http_client.HttpClient("https://api.zotero.org", qps=1.0)


def _get_user_prefix() -> str:
  """Gets the user/group prefix for API requests."""
  user_id = os.environ.get("ZOTERO_USER_ID")
  if not user_id:
    print(
        "Error: ZOTERO_USER_ID not found in environment. "
        "Please set it in your .env file.",
        file=sys.stderr,
    )
    sys.exit(1)
  return f"users/{user_id}"


def _find_collection_key_by_name(
    client: http_client.HttpClient, user_prefix: str, collection_name: str
) -> str | None:
  """Finds a collection key by its name."""
  params = {"limit": 100, "format": "json"}
  collections = client.fetch_json(
      f"/{user_prefix}/collections", query_params=params
  )

  for collection in collections:
    if collection.get("data", {}).get("name") == collection_name:
      return collection.get("data", {}).get("key")

  return None


def parse_args() -> argparse.Namespace:
  """Parses command-line arguments."""
  parser = argparse.ArgumentParser(
      description="Export Zotero collection to citation format"
  )
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      "--collection-key",
      type=str,
      help="The collection key",
  )
  group.add_argument(
      "--collection-name",
      type=str,
      help="Search by collection name",
  )
  parser.add_argument(
      "--format",
      choices=[
          "bibtex",
          "biblatex",
          "ris",
          "csv",
          "csljson",
          "mods",
          "tei",
          "wikipedia",
      ],
      default="bibtex",
      help="Export format (default: bibtex)",
  )
  parser.add_argument(
      "--limit",
      type=int,
      default=100,
      help="Maximum items to export (default: 100)",
  )
  parser.add_argument(
      "--style",
      type=str,
      default="apa",
      help="Citation style (for bib formats, e.g., apa, chicago-note-bibliography)",
  )
  parser.add_argument(
      "--locale",
      type=str,
      default="en-US",
      help="Locale code (default: en-US)",
  )
  return parser.parse_args()


def main() -> None:
  """Main function to export collection."""
  args = parse_args()

  client = _get_api_client()
  user_prefix = _get_user_prefix()

  # Get collection key
  collection_key = args.collection_key
  if args.collection_name:
    collection_key = _find_collection_key_by_name(
        client, user_prefix, args.collection_name
    )
    if not collection_key:
      print(
          f"Error: Collection '{args.collection_name}' not found",
          file=sys.stderr,
      )
      sys.exit(1)

  # Build endpoint with query parameters
  params = {
      "limit": min(args.limit, 100),
      "format": args.format,
      "style": args.style,
      "locale": args.locale,
  }

  query_string = urllib.parse.urlencode(params)
  endpoint = f"/{user_prefix}/collections/{collection_key}/items?{query_string}"

  try:
    # Export items with API key header and longer timeout for HPC
    headers = {
        "Zotero-API-Key": os.environ.get("ZOTERO_API_KEY"),
        "Zotero-API-Version": "3",
    }
    result = client.fetch_json(endpoint, headers=headers, timeout=120)

    # Output the result
    if isinstance(result, str):
      print(result)
    else:
      print(json.dumps(result, indent=2))

  except http_client.HttpError as e:
    print(f"Error exporting collection: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
