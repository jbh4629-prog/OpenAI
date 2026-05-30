#!/usr/bin/env python3
"""Fetch a Nitter RSS feed, including simple Anubis preact challenges."""

from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


USER_AGENT = "curl/8.14.1"


def request(opener: urllib.request.OpenerDirector, url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_json_script(html: str, script_id: str) -> object | None:
    match = re.search(
        rf'<script id="{re.escape(script_id)}" type="application/json">(.*?)</script>',
        html,
        flags=re.S,
    )
    if not match:
        return None
    return json.loads(match.group(1))


def pass_anubis(opener: urllib.request.OpenerDirector, base_url: str, html: str) -> str | None:
    info = extract_json_script(html, "preact_info")
    if not isinstance(info, dict):
        return None
    challenge = str(info.get("challenge") or "")
    redir = str(info.get("redir") or "")
    if not challenge or not redir:
        return None
    result = hashlib.sha256(challenge.encode()).hexdigest()
    pass_url = urllib.parse.urljoin(base_url, redir)
    sep = "&" if "?" in pass_url else "?"
    return request(opener, f"{pass_url}{sep}{urllib.parse.urlencode({'result': result})}")


def fetch(url: str, max_challenges: int) -> str:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    html = request(opener, url)
    for _ in range(max_challenges):
        if "<rss" in html or "<feed" in html:
            return html
        next_html = pass_anubis(opener, url, html)
        if not next_html:
            return html
        html = next_html
    return html


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--max-challenges", type=int, default=2)
    args = parser.parse_args()

    body = fetch(args.url, args.max_challenges)
    if args.out:
        args.out.write_text(body)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
