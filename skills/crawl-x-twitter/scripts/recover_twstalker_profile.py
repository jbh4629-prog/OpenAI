#!/usr/bin/env python3
"""Recover keyword-matching timeline posts from TwStalker profile pagination.

This script is complementary to ``recover_twstalker_replies.py``:
1. Reads the visible TwStalker profile HTML.
2. Follows the profile `/service/api` pagination endpoint page by page.
3. Filters for high-signal keyword matches.
4. Enriches unseen tweets with official `tweet-result` payloads.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
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
    text = html.unescape(raw or "")
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


def fetch_service_page(account: str, page: int, cursor: str, query: str) -> object:
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


def write_payload(path: Path | None, payload: dict) -> None:
    if path is None:
        return
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def recover_profile(
    account: str,
    service_pages: int,
    keywords: list[str],
    sleep_s: float,
    skip_ids: set[str],
    retry_max: int,
    retry_sleep_s: float,
    json_out: Path | None,
) -> dict:
    html_text = fetch_profile_html(account)
    pager = parse_pager(html_text)
    if not pager:
        payload = {"account": account, "pages": [], "rows": []}
        write_payload(json_out, payload)
        return payload

    page = int(pager["page"])
    cursor = pager["cursor"]
    query = pager["query"]
    page_log: list[dict] = []
    rows: list[dict] = []
    seen: set[str] = set()
    payload = {"account": account, "pages": page_log, "rows": rows}

    for _ in range(service_pages):
        page_json: object | None = None
        last_error = ""
        for attempt in range(retry_max + 1):
            try:
                page_json = fetch_service_page(account, page, cursor, query)
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                page_json = None
            if isinstance(page_json, dict):
                break
            if attempt < retry_max:
                time.sleep(retry_sleep_s)

        if not isinstance(page_json, dict):
            page_log.append(
                {
                    "page": page,
                    "kind": type(page_json).__name__ if page_json is not None else "error",
                    "count": -1,
                    "detail": last_error,
                }
            )
            write_payload(json_out, payload)
            break

        tweets = page_json.get("tweets") or {}
        page_log.append(
            {
                "page": page,
                "kind": "dict",
                "count": len(tweets),
            }
        )

        for tweet_id, tweet in tweets.items():
            tweet_id = str(tweet_id)
            if tweet_id in seen:
                continue
            seen.add(tweet_id)

            raw_text = clean_html_text(tweet.get("full_text") or "")
            combo = raw_text.lower()
            if not any(keyword in combo for keyword in keywords):
                continue

            row = {
                "account": account,
                "page": page,
                "id": tweet_id,
                "raw_text": raw_text,
                "reported": tweet_id in skip_ids,
            }

            if tweet_id not in skip_ids:
                try:
                    data = fetch_tweet_result(tweet_id)
                except Exception:
                    data = {}
                parent = data.get("parent") if isinstance(data, dict) else {}
                quoted = data.get("quoted_tweet") if isinstance(data, dict) else {}
                if not isinstance(parent, dict):
                    parent = {}
                if not isinstance(quoted, dict):
                    quoted = {}
                row.update(
                    {
                        "text": clean_html_text(data.get("text") or ""),
                        "created_at": data.get("created_at"),
                        "in_reply_to": data.get("in_reply_to_screen_name"),
                        "parent_id": parent.get("id_str"),
                        "parent_text": clean_html_text(parent.get("text") or ""),
                        "quoted_text": clean_html_text(quoted.get("text") or ""),
                    }
                )
            rows.append(row)
        write_payload(json_out, payload)

        new_cursor = page_json.get("cursor")
        if not new_cursor or not tweets or new_cursor == cursor:
            write_payload(json_out, payload)
            break
        cursor = new_cursor
        page += 1
        time.sleep(sleep_s)

    write_payload(json_out, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("account")
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
    parser.add_argument("--service-pages", type=int, default=24)
    parser.add_argument("--sleep-s", type=float, default=1.0)
    parser.add_argument("--retry-max", type=int, default=3)
    parser.add_argument("--retry-sleep-s", type=float, default=1.5)
    parser.add_argument("--skip-ids-file", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    skip_ids: set[str] = set()
    if args.skip_ids_file and args.skip_ids_file.exists():
        skip_ids = {
            line.strip()
            for line in args.skip_ids_file.read_text().splitlines()
            if line.strip()
        }

    keywords = [item.lower() for item in args.keyword]
    if args.keywords_file and args.keywords_file.exists():
        keywords.extend(
            line.strip().lower()
            for line in args.keywords_file.read_text().splitlines()
            if line.strip()
        )
    if not keywords:
        parser.error("provide at least one --keyword or --keywords-file")

    payload = recover_profile(
        account=args.account,
        service_pages=args.service_pages,
        keywords=keywords,
        sleep_s=args.sleep_s,
        skip_ids=skip_ids,
        retry_max=args.retry_max,
        retry_sleep_s=args.retry_sleep_s,
        json_out=args.json_out,
    )

    for page in payload["pages"]:
        print(json.dumps({"page_log": page}, ensure_ascii=False), flush=True)
    for row in payload["rows"]:
        print(json.dumps(row, ensure_ascii=False), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
