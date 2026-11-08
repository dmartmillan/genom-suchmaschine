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

"""Retrieves items from a Zotero collection.

This script fetches all papers/items within a specific Zotero collection
and outputs them in JSON or other citation formats.
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
      description="Get items from a Zotero collection"
  )
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      "--collection-key",
      type=str,
      help="The collection key (e.g., ABC123DEF)",
  )
  group.add_argument(
      "--collection-name",
      type=str,
      help="Search by collection name (exact match)",
  )
  parser.add_argument(
      "--limit",
      type=int,
      default=100,
      help="Maximum number of items to return (default: 100, max: 100)",
  )
  parser.add_argument(
      "--start",
      type=int,
      default=0,
      help="Pagination offset (default: 0)",
  )
  parser.add_argument(
      "--format",
      choices=["json", "bibtex", "biblatex", "ris", "csv"],
      default="json",
      help="Output format (default: json)",
  )
  parser.add_argument(
      "--include-attachments",
      action="store_true",
      help="Include attachment metadata (PDFs, notes, etc.)",
  )
  return parser.parse_args()


def main() -> None:
  """Main function to get collection items."""
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
      "start": args.start,
      "format": args.format,
  }

  if args.include_attachments:
    params["include"] = "data,attachments"

  query_string = urllib.parse.urlencode(params)
  endpoint = f"/{user_prefix}/collections/{collection_key}/items?{query_string}"

  try:
    # Fetch items with API key header and longer timeout for HPC
    headers = {
        "Zotero-API-Key": os.environ.get("ZOTERO_API_KEY"),
        "Zotero-API-Version": "3",
    }
    items = client.fetch_json(endpoint, headers=headers, timeout=120)

    # Output based on format
    if args.format == "json":
      print(json.dumps(items, indent=2))
    else:
      # For citation formats, output as text
      if isinstance(items, str):
        print(items)
      else:
        print(json.dumps(items, indent=2))

  except http_client.HttpError as e:
    print(f"Error fetching items: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
