# Naver Blog Public Crawl Endpoints

Use these public endpoints in order.

## Discovery

`GET https://search.naver.com/search.naver?where=post&query={query}`

Useful for finding public blog post URLs. The HTML often includes direct `https://blog.naver.com/{blogId}/{logNo}` links.

`GET https://rss.blog.naver.com/{blogId}.xml`

Useful for blog-level post discovery when the `blogId` is already known.

## Post Read

`GET https://blog.naver.com/{blogId}/{logNo}`

Often returns a frameset. If so, follow the `mainFrame` URL inside the page.

`GET https://blog.naver.com/PostView.naver?blogId={blogId}&logNo={logNo}`

Primary public post view.

`GET https://m.blog.naver.com/PostView.naver?blogId={blogId}&logNo={logNo}&navType=tl`

Public mobile fallback. Use when the desktop page is thin or framed.

## Public Blog API

`GET https://m.blog.naver.com/rego/BlogInfo.nhn?blogId={blogId}`

Returns JSONP with the numeric `blogNo`. This is useful for comment lookup.

`GET https://m.blog.naver.com/rego/PostListInfo.nhn?blogId={blogId}&categoryNo=0&currentPage=1&logCode=0`

Public mobile listing endpoint. Useful when you already know the `blogId`.

## Comment API

`GET https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json`

Use these query params:

- `ticket=blog`
- `templateId=default_simple`
- `pool=cbox9`
- `lang=ko`
- `objectId={blogNo}_201_{logNo}`
- `groupId={blogNo}`
- `listType=OBJECT`
- `pageType=default`
- `page=1`
- `pageSize=50`
- `replyPageSize=10`
- `initialize=true`
- `useAltSort=true`
- `showReply=true`

If the response says comments are disabled, stop and classify the post as `comment_disabled`.

## Body Extraction

Priority order:

1. SmartEditor `<!-- SE-TEXT { --> ... <!-- } SE-TEXT -->` blocks
2. `div.se-main-container`
3. The public post container around `PostView`
4. Mobile `PostView`
5. Reader / readability fallback on the public page

## Normalization

Normalize each post to:

- `blogId`
- `logNo`
- `canonicalUrl`
- `title`
- `bodyText`
- `commentStatus`
- `commentCount`
- `comments`
- `accessStatus`
- `promoFlag`

## Comment Flattening

Comments often arrive nested in a reverse-ordered list. Preserve the thread structure, but also keep the flat text of each comment for summarization.

## Guardrails

- Public pages only.
- No login bypass.
- No private or permission-only access attempts.
- If access is blocked, mark the post as `restricted` and stop.
