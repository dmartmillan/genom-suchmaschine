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

"""Downloads PDF attachments from Zotero items.

This script finds and downloads PDF attachments associated with Zotero items.
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
import os
import sys

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


def _find_pdf_attachment(
    client: http_client.HttpClient,
    user_prefix: str,
    item_key: str,
    collection_key: str | None = None,
) -> tuple[str, str] | None:
  """Finds a PDF attachment for an item.

  Returns:
    Tuple of (file_key, filename) or None if no PDF found.
  """
  # Get child items (attachments)
  endpoint = f"/{user_prefix}/items/{item_key}/children"
  params = {"format": "json", "limit": 100}

  query_string = urllib.parse.urlencode(params)
  url = f"{endpoint}?{query_string}"

  try:
    headers = {
        "Zotero-API-Key": os.environ.get("ZOTERO_API_KEY"),
        "Zotero-API-Version": "3",
    }
    children = client.fetch_json(url, headers=headers, timeout=120)
  except http_client.HttpError:
    return None

  # Look for PDF attachments
  for child in children:
    data = child.get("data", {})
    item_type = data.get("itemType", "")

    if item_type == "attachment":
      attachment_type = data.get("attachmentType", "")
      filename = data.get("title", "")

      # Check if it's a PDF
      if "application/pdf" in attachment_type or filename.lower().endswith(".pdf"):
        return (data.get("key", ""), filename)

  return None


def parse_args() -> argparse.Namespace:
  """Parses command-line arguments."""
  parser = argparse.ArgumentParser(
      description="Download PDF from Zotero item"
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
      "--output",
      type=str,
      required=True,
      help="Output file path for the PDF",
  )
  parser.add_argument(
      "--collection-key",
      type=str,
      help="If item is in a collection, specify for faster lookup",
  )
  parser.add_argument(
      "--overwrite",
      action="store_true",
      help="Overwrite existing file if it exists",
  )
  return parser.parse_args()


def main() -> None:
  """Main function to download paper PDF."""
  args = parse_args()

  client = _get_api_client()
  user_prefix = _get_user_prefix()

  # Get item key (convert from ID if needed)
  item_key = args.item_key
  if args.item_id:
    endpoint = f"/{user_prefix}/items/{args.item_id}"
    try:
      item = client.fetch_json(endpoint)
      item_key = item.get("data", {}).get("key", "")
      if not item_key:
        print(f"Error: Item with ID {args.item_id} not found", file=sys.stderr)
        sys.exit(1)
    except http_client.HttpError as e:
      print(f"Error fetching item: {e}", file=sys.stderr)
      sys.exit(1)

  # Check if file exists
  if os.path.exists(args.output) and not args.overwrite:
    print(f"File already exists: {args.output}", file=sys.stderr)
    print("Use --overwrite to replace it", file=sys.stderr)
    sys.exit(1)

  # Find PDF attachment
  pdf_info = _find_pdf_attachment(client, user_prefix, item_key, args.collection_key)

  if not pdf_info:
    print(
        f"Error: No PDF attachment found for item {item_key}",
        file=sys.stderr,
    )
    sys.exit(1)

  file_key, filename = pdf_info

  # Download the PDF
  # The file download endpoint
  endpoint = f"/{user_prefix}/items/{item_key}/file"

  try:
    # Fetch the PDF as bytes with API key header and longer timeout
    headers = {
        "Zotero-API-Key": os.environ.get("ZOTERO_API_KEY"),
        "Zotero-API-Version": "3",
    }
    pdf_data = client.fetch_bytes(endpoint, headers=headers, timeout=300)
