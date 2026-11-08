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

"""Searches the Zotero library for papers.

This script searches across the entire Zotero library or within a specific
collection and returns matching items with metadata.
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


def parse_args() -> argparse.Namespace:
  """Parses command-line arguments."""
  parser = argparse.ArgumentParser(
      description="Search Zotero library for papers"
  )
  parser.add_argument(
      "--query",
      type=str,
      required=True,
      help="Search query string",
  )
  parser.add_argument(
      "--collection-key",
      type=str,
      help="Limit search to specific collection",
  )
  parser.add_argument(
      "--item-type",
      type=str,
      help="Filter by item type (e.g., journalArticle, book)",
  )
  parser.add_argument(
      "--tag",
      type=str,
      help="Filter by tag name",
  )
  parser.add_argument(
      "--limit",
      type=int,
      default=100,
      help="Maximum results (default: 100, max: 100)",
  )
  parser.add_argument(
      "--start",
      type=int,
      default=0,
      help="Pagination offset",
  )
  parser.add_argument(
      "--sort",
      choices=[
          "title",
          "date",
          "dateAdded",
          "dateModified",
          "creator",
      ],
      default="dateModified",
      help="Sort field",
  )
  parser.add_argument(
      "--direction",
      choices=["asc", "desc"],
      default="desc",
      help="Sort direction",
  )
  parser.add_argument(
      "--include-attachments",
      action="store_true",
      help="Include attachment metadata",
  )
  parser.add_argument(
      "--format",
      choices=["json", "bibtex", "biblatex", "ris", "csv"],
      default="json",
      help="Output format (default: json)",
  )
  return parser.parse_args()


def main() -> None:
  """Main function to search Zotero library."""
  args = parse_args()

  client = _get_api_client()
  user_prefix = _get_user_prefix()

  # Build endpoint with query parameters
  if args.collection_key:
    base_endpoint = f"/{user_prefix}/collections/{args.collection_key}/items"
  else:
    base_endpoint = f"/{user_prefix}/items"

  params = {
      "q": args.query,
      "limit": min(args.limit, 100),
      "start": args.start,
      "sort": args.sort,
      "direction": args.direction,
      "format": args.format,
  }

  if args.item_type:
    params["itemType"] = args.item_type

  if args.tag:
    params["tag"] = args.tag

  if args.include_attachments:
    params["include"] = "data,attachments"

  query_string = urllib.parse.urlencode(params)
  endpoint = f"{base_endpoint}?{query_string}"

  try:
    # Search items with API key header and longer timeout for HPC
    headers = {
        "Zotero-API-Key": os.environ.get("ZOTERO_API_KEY"),
        "Zotero-API-Version": "3",
    }
    print(f"Searching Zotero library for: {args.query}", file=sys.stderr)
    items = client.fetch_json(endpoint, headers=headers, timeout=120)
    print(f"Found {len(items)} items", file=sys.stderr)

    # Output based on format
    if args.format == "json":
      print(json.dumps(items, indent=2))
    else:
      if isinstance(items, str):
        print(items)
      else:
        print(json.dumps(items, indent=2))

  except http_client.HttpError as e:
    print(f"Error searching library: {e}", file=sys.stderr)
    if "401" in str(e):
      print("Check that ZOTERO_API_KEY is correct in .env file", file=sys.stderr)
    elif "403" in str(e):
      print("API key may not have access to this library", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
