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

"""Retrieves metadata for a specific Zotero item.

This script fetches detailed metadata for a single Zotero item including
all fields, creators, tags, notes, and attachments.
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
      description="Get metadata for a Zotero item"
  )
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      "--item-key",
      type=str,
      help="The item key (e.g., XYZ789ABC)",
  )
  group.add_argument(
      "--item-id",
      type=int,
      help="Numeric item ID",
  )
  parser.add_argument(
      "--format",
      choices=["json", "bibtex", "biblatex", "ris"],
      default="json",
      help="Output format (default: json)",
  )
  parser.add_argument(
      "--include-children",
      action="store_true",
      help="Include child items (notes, attachments)",
  )
  parser.add_argument(
      "--include-relations",
      action="store_true",
      help="Include related items",
  )
  return parser.parse_args()


def main() -> None:
  """Main function to get item metadata."""
  args = parse_args()

  client = _get_api_client()
  user_prefix = _get_user_prefix()

  # Get item key (convert from ID if needed)
  item_identifier = args.item_key or str(args.item_id)

  # Add query parameters
  params = {"format": args.format}

  if args.include_children:
    params["include"] = "data,children,attachments"
  elif args.include_relations:
    params["include"] = "data,relations"
  else:
    params["include"] = "data"

  query_string = urllib.parse.urlencode(params)
  endpoint = f"/{user_prefix}/items/{item_identifier}?{query_string}"

  try:
    # Fetch item with API key header and longer timeout for HPC
    headers = {
        "Zotero-API-Key": os.environ.get("ZOTERO_API_KEY"),
        "Zotero-API-Version": "3",
    }
    item = client.fetch_json(endpoint, headers=headers, timeout=120)

    # Output based on format
    if args.format == "json":
      print(json.dumps(item, indent=2))
    else:
      if isinstance(item, str):
        print(item)
      else:
        print(json.dumps(item, indent=2))

  except http_client.HttpError as e:
    print(f"Error fetching item: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
