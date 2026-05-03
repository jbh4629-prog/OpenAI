---
name: crawl-naver-blog
description: Public Naver Blog collection and summarization from searchable posts. Use when crawling public Naver Blog posts, extracting body text and comments from frameset, mobile, RSS, or commentBox endpoints, or analyzing repeated 업체/제품/방법/후기 patterns.
---

# Crawl Naver Blog

## Overview

Use this skill for public Naver Blog content only. Prefer public discovery and public read paths first, then fall back to alternate public renderings when the page body is thin or frameset-based.

Do not attempt to bypass login, private, or permission-only posts. If access is blocked, classify the post as `restricted` and stop.

## Workflow

1. Discover candidate posts from Naver blog search or RSS.
2. Normalize each candidate to `blogId` and `logNo`.
3. Read the post through `https://blog.naver.com/PostView.naver?blogId=...&logNo=...`.
4. If the page is only a frameset, follow the `mainFrame` URL.
5. Try the mobile post view as a fallback: `https://m.blog.naver.com/PostView.naver?blogId=...&logNo=...&navType=tl`.
6. Extract body text from SmartEditor blocks first, then from the public post container if needed.
7. Resolve `blogNo` from `https://m.blog.naver.com/rego/BlogInfo.nhn?blogId=...`.
8. Read comments from the public commentBox JSONP endpoint.
9. If the comment endpoint says comments are disabled, mark `comment_disabled`.
10. If the page says login, private, or permission is required, mark `restricted`.

## Public Fallbacks

Use these only for public pages:

- `web fetch / reader`
- `Jina Reader / readability extraction`
- `RSS / Atom / JSON Feed`
- `public API / CMS API`
- `.json endpoint probing`
- `.json + mobile UA`
- `mobile URL + iPhone UA`
- `AMP / print / text view`
- `curl HTTP probing`
- `HAR / XHR / fetch reverse tracing`
- `Playwright / CDP`
- `Wayback / Common Crawl / WARC`
- `DNS / CT logs / GitHub search`
- `diff monitoring`

`HAR / XHR` and `Playwright / CDP` are for public page rendering and endpoint discovery only. Do not use them to bypass access control.

## Filters

When summarizing, exclude promotional or CTA-heavy posts and comments. Treat these as promotional signals:

- `협찬`
- `광고`
- `체험단`
- `제휴`
- `원고료`
- `파트너스`
- `네이버 쇼핑 커넥트`
- `소정의 마일리지`
- `문의 유도`
- `쪽지 유도`
- `댓글 유도`

Keep separate status fields for:

- `public`
- `comment_disabled`
- `restricted`
- `unparsed`

## Use The Script

Prefer [`scripts/crawl_naver_blog.js`](scripts/crawl_naver_blog.js) for repeat jobs. It searches public blog results, resolves post URLs, extracts body text, and fetches comments through the public commentBox endpoint.

Example:

```bash
node scripts/crawl_naver_blog.js --query "보관이사" --limit 10
node scripts/crawl_naver_blog.js --query "주방 수전" --limit 10
node scripts/crawl_naver_blog.js --query "세라믹 식탁" --limit 10
```

## Reference

- [`references/endpoints.md`](references/endpoints.md): public endpoints, fallback order, and normalization notes.
