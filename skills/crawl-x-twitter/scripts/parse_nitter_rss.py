#!/usr/bin/env python3
"""Convert a Nitter RSS export into compact JSON rows."""

from __future__ import annotations

import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def clean(raw: str | None) -> str:
    text = html.unescape(raw or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def parse_guid(item: ET.Element) -> str:
    guid = item.findtext("guid") or ""
    if guid:
        return guid.strip()
    link = item.findtext("link") or ""
    match = re.search(r"/status/(\d+)", link)
    return match.group(1) if match else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rss_xml", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    root = ET.parse(args.rss_xml).getroot()
    rows: list[dict] = []
    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title"))
        desc = clean(item.findtext("description"))
        creator = item.findtext("{http://purl.org/dc/elements/1.1/}creator") or ""
        link = item.findtext("link") or ""
        rows.append(
            {
                "id": parse_guid(item),
                "creator": creator.strip(),
                "pubDate": (item.findtext("pubDate") or "").strip(),
                "title": title,
                "description": desc,
                "link": link.strip(),
            }
        )
    args.json_out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "out": str(args.json_out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
