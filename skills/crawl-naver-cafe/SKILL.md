---
name: crawl-naver-cafe
description: Public Naver Cafe collection and summarization from searchable articles. Use when crawling public Naver Cafe posts, extracting article bodies and comments, converting search results into shareable article tokens, or analyzing repeated 업체/제품/방법/후기 patterns from cafe search results.
---

# Crawl Naver Cafe

## Overview

Use this skill to crawl public Naver Cafe content without opening a browser first. Prefer the public search API, then convert each search result into a shareable token, then fetch the article JSON and extract `contentHtml` plus `comments.items`.

## Workflow

1. Search the cafe with `https://apis.naver.com/cafe-web/cafe-search-api/v1.0/cafes/{cafeId}/search/articles`.
2. Read the `art` token from each search result row.
3. Mint a share token with `POST https://article.cafe.naver.com/gw/v1/cafes/{cafeId}/articles/{articleId}/share/link`.
4. Fetch the article JSON with `GET https://article.cafe.naver.com/gw/v2.1/cafes/{cafeId}/articles/{articleId}?useCafeId=true&art={shareArt}`.
5. Normalize the result into article metadata, body text, and comment text.

## Use The Script

Prefer [`scripts/crawl_naver_cafe.js`](scripts/crawl_naver_cafe.js) for repeat jobs. It standardizes the request sequence and outputs normalized JSON so you do not need to restate the endpoint flow each time.

Example:

```bash
node scripts/crawl_naver_cafe.js --cafe-id 23700418 --query "보관이사" --limit 10
```

## Guardrails

- Keep to public articles and comments only.
- Use a normal browser user agent plus `X-Cafe-Product: pc`.
- Do not treat the search-result `art` token as the final read token; mint the share token first.
- Do not add `requestFrom=A` when reading article JSON; the public read path should stay on the share-token flow.
- Treat `0004` or an empty share token as blocked, private, or otherwise unreadable content.
- Use a browser fallback only after the public endpoints fail.

## Reference

- [`references/endpoints.md`](references/endpoints.md): endpoint map, parameter meanings, and normalization notes.
