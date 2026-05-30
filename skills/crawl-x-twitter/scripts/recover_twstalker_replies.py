#!/usr/bin/env python3
"""Recover reply chains from TwStalker pages.

This script combines:
1. The visible first TwStalker profile page.
2. The TwStalker load-more `/service/api` pagination endpoint.
3. Official `tweet-result` parent recovery from syndication.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_KEYWORDS: list[str] = []


def run_curl(args: list[str]) -> str:
    proc = subprocess.run(
        ["curl", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def clean_html_text(raw: str) -> str:
    text = html.unescape(raw)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def fetch_profile_html(account: str) -> str:
    return run_curl(["-L", "-s", f"https://twstalker.com/{account}"])


def parse_pager(html_text: str) -> dict[str, str] | None:
    match = re.search(
        r'class="add-nw-event"[^>]+data-cursor="([^"]+)"[^>]+data-query="([^"]+)"'
        r'[^>]+data-username="([^"]+)"[^>]+data-ec="([^"]+)"',
        html_text,
        flags=re.S,
    )
    if not match:
        return None
    return {
        "cursor": match.group(1),
        "query": match.group(2),
        "username": match.group(3),
        "page": match.group(4),
    }


def fetch_service_page(account: str, page: int, cursor: str, query: str) -> dict:
    encoded = urllib.parse.urlencode(
        {
            "page": str(page),
            "cursor": cursor,
            "data": query,
            "action": "profile",
        }
    )
    raw = run_curl(
        [
            "-s",
            "https://twstalker.com/service/api",
            "-H",
            "X-Requested-With: XMLHttpRequest",
            "-H",
            f"Referer: https://twstalker.com/{account}",
            "-H",
            "Origin: https://twstalker.com",
            "--data",
            encoded,
        ]
    )
    return json.loads(raw)


def fetch_tweet_result(tweet_id: str) -> dict:
    req = urllib.request.Request(
        f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en&token=token",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def extract_visible_replies(account: str, target_account: str, html_text: str) -> list[dict]:
    rows: list[dict] = []
    blocks = html_text.split('<div class="activity-posts">')
    for block in blocks:
        if f"/{target_account}" not in block and f"@{target_account}" not in block:
            continue
        id_match = re.search(rf'href="/{re.escape(account)}/status/(\d+)"', block)
        if not id_match:
            continue
        text_match = re.search(
            r'<div class="activity-descp">.*?<p>(.*?)</p>',
            block,
            flags=re.S,
        )
        rows.append(
            {
                "source": "visible_html",
                "reply_id": id_match.group(1),
                "reply_text": clean_html_text(text_match.group(1)) if text_match else "",
            }
        )
    return rows


def extract_service_replies(page_json: dict, target_account: str) -> list[dict]:
    rows: list[dict] = []
    if not isinstance(page_json, dict):
        return rows
    for tweet_id, tweet in (page_json.get("tweets") or {}).items():
        full_text = tweet.get("full_text") or ""
        if f"/{target_account}" not in full_text and f"@{target_account}" not in full_text:
            continue
        rows.append(
            {
                "source": "service_api",
                "reply_id": str(tweet_id),
                "reply_text": clean_html_text(full_text),
            }
        )
    return rows


def enrich_reply(
    account: str,
    target_account: str,
    reply_row: dict,
    keywords: list[str],
) -> dict | None:
    try:
        data = fetch_tweet_result(reply_row["reply_id"])
    except Exception:
        return None
    in_reply_to = (data.get("in_reply_to_screen_name") or "").lower()
    parent = data.get("parent") or {}
    parent_user = ((parent.get("user") or {}).get("screen_name") or "").lower()
    if in_reply_to != target_account and parent_user != target_account:
        return None

    parent_text = clean_html_text(parent.get("text") or "")
    quoted = parent.get("quoted_tweet") if isinstance(parent, dict) else None
    quoted_text = (
        clean_html_text((quoted or {}).get("text") or "")
        if isinstance(quoted, dict)
        else ""
    )
    reply_text = clean_html_text(data.get("text") or reply_row["reply_text"])
    combo = " ".join([reply_text, parent_text, quoted_text]).lower()
    hits = [keyword for keyword in keywords if keyword in combo]

    return {
        "account": account,
        "source": reply_row["source"],
        "reply_id": reply_row["reply_id"],
        "reply_text": reply_text,
        "parent_id": parent.get("id_str"),
        "parent_text": parent_text,
        "parent_quoted_text": quoted_text,
        "keyword_hits": hits,
    }


def recover_account(
    account: str,
    target_account: str,
    service_pages: int,
    keywords: list[str],
) -> list[dict]:
    html_text = fetch_profile_html(account)
    rows = extract_visible_replies(account, target_account, html_text)

    pager = parse_pager(html_text)
    if pager:
        page = int(pager["page"])
        cursor = pager["cursor"]
        query = pager["query"]
        for _ in range(service_pages):
            page_json = fetch_service_page(account, page, cursor, query)
            rows.extend(extract_service_replies(page_json, target_account))
            if not isinstance(page_json, dict):
                break
            new_cursor = page_json.get("cursor")
            if not new_cursor or not page_json.get("tweets"):
                break
            if new_cursor == cursor:
                break
            cursor = new_cursor
            page += 1
            time.sleep(0.15)

    enriched: list[dict] = []
    seen_ids: set[str] = set()
    for row in rows:
        reply_id = row["reply_id"]
        if reply_id in seen_ids:
            continue
        seen_ids.add(reply_id)
        item = enrich_reply(account, target_account, row, keywords)
        if item is not None:
            enriched.append(item)
        time.sleep(0.1)
    return enriched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("accounts", nargs="+")
    parser.add_argument(
        "--target-account",
        required=True,
        help="Account that the listed accounts replied to, without @.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Case-insensitive keyword to keep. Repeat for multiple terms.",
    )
    parser.add_argument(
        "--keywords-file",
        type=Path,
        help="Optional newline-delimited keyword file.",
    )
    parser.add_argument("--service-pages", type=int, default=2)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    target_account = args.target_account.lower().lstrip("@")
    keywords = [item.lower() for item in args.keyword]
    if args.keywords_file and args.keywords_file.exists():
        keywords.extend(
            line.strip().lower()
            for line in args.keywords_file.read_text().splitlines()
            if line.strip()
        )
    if not keywords:
        parser.error("provide at least one --keyword or --keywords-file")

    all_rows: list[dict] = []
    for account in args.accounts:
        rows = recover_account(account, target_account, args.service_pages, keywords)
        all_rows.extend(rows)
        for row in rows:
            print(json.dumps(row, ensure_ascii=False), flush=True)

    if args.json_out:
        args.json_out.write_text(
            json.dumps(all_rows, ensure_ascii=False, indent=2) + "\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
