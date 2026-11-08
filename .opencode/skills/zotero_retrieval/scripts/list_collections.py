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

"""Lists collections from Zotero library.

This script retrieves all collections (folders) from a Zotero library
and outputs them in JSON format.
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

  # Zotero API allows 1 request per second
  client = http_client.HttpClient("https://api.zotero.org", qps=1.0)

  # Store API key for use in requests
  client._api_key = api_key

  return client


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
      description="List collections from Zotero library"
  )
  parser.add_argument(
      "--top",
      action="store_true",
      help="Only show top-level collections (no subcollections)",
  )
  parser.add_argument(
      "--limit",
      type=int,
      default=100,
      help="Maximum number of collections to return (default: 100, max: 100)",
  )
  parser.add_argument(
      "--start",
      type=int,
      default=0,
      help="Pagination offset (default: 0)",
  )
  return parser.parse_args()


def main() -> None:
  """Main function to list Zotero collections."""
  args = parse_args()

  client = _get_api_client()
  user_prefix = _get_user_prefix()

  # Build endpoint with query parameters
  params = {
      "limit": min(args.limit, 100),  # Zotero max is 100
      "start": args.start,
      "format": "json",
  }

  query_string = urllib.parse.urlencode(params)
  url = f"/{user_prefix}/collections/top?{query_string}" if args.top else f"/{user_prefix}/collections?{query_string}"

  try:
    # Fetch collections with API key header and longer timeout for HPC
    headers = {
        "Zotero-API-Key": os.environ.get("ZOTERO_API_KEY"),
        "Zotero-API-Version": "3",
    }
    print(f"Fetching collections (top={args.top}, limit={args.limit})", file=sys.stderr)
    collections = client.fetch_json(url, headers=headers, timeout=300)
    print(f"Found {len(collections)} collections", file=sys.stderr)

    # Output as JSON array
    print(json.dumps(collections, indent=2))

  except http_client.HttpError as e:
    print(f"Error fetching collections: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
