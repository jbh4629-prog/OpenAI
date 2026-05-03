# Naver Cafe Public Crawl Endpoints

Use these public endpoints in order.

## Search

`GET https://apis.naver.com/cafe-web/cafe-search-api/v1.0/cafes/{cafeId}/search/articles`

Useful params:

- `query`: search keyword
- `searchBy`: `0` broad match, `1` title, `3` writer, `4` comment
- `sortBy`: `RECENCY` or `LIKE`
- `page`: page number
- `perPage`: rows per page

Search result rows usually include:

- `articleId`
- `subject`
- `art`
- `menuId`
- `commentCount`
- `writerInfo`

## Share Token

`POST https://article.cafe.naver.com/gw/v1/cafes/{cafeId}/articles/{articleId}/share/link`

Send query params:

- `query`
- `art`
- `fromPopular=false`

Use the search-result `art` token when available. The response usually returns:

- `result.art`
- `result.shortUrl`

If `result.art` is empty, treat the row as unreadable from the public path.

## Article JSON

`GET https://article.cafe.naver.com/gw/v2.1/cafes/{cafeId}/articles/{articleId}?useCafeId=true&art={shareArt}`

Read from:

- `result.article.subject`
- `result.article.writer`
- `result.article.menu`
- `result.article.contentHtml`
- `result.comments.items`

Do not append `requestFrom=A` on this public path.

## Normalization

Extract and keep:

- article id
- subject
- writer nickname
- menu name
- read count
- comment count
- body text from `contentHtml`
- comments as plain text

When summarizing, separate:

- repeated 업체 names
- repeated product names
- repeated method or installation patterns
- repeated complaints or satisfaction points
