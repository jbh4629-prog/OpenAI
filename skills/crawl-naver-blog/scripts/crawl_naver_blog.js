#!/usr/bin/env node

const DEFAULT_HEADERS = {
  'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  'Accept-Language': 'ko-KR,ko;q=0.9',
};

function decodeHtml(input = '') {
  return String(input)
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|li|tr|h\d)>/gi, '\n')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x2F;/g, '/')
    .replace(/&#xa0;/gi, ' ')
    .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCharCode(parseInt(dec, 10)))
    .replace(/<[^>]+>/g, '')
    .replace(/\r/g, '')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function stripHtmlFragment(input = '') {
  return decodeHtml(
    String(input)
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<style[\s\S]*?<\/style>/gi, '')
      .replace(/<!--[\s\S]*?-->/g, ''),
  );
}

function trim(value) {
  return String(value).trim();
}

function dedupe(items, keyFn) {
  const seen = new Set();
  const out = [];
  for (const item of items) {
    const key = keyFn(item);
    if (!seen.has(key)) {
      seen.add(key);
      out.push(item);
    }
  }
  return out;
}

function parseArgs(argv) {
  const out = {
    queries: [],
    urls: [],
    page: 1,
    maxPages: 1,
    limit: 10,
    perPage: 10,
    jsonl: false,
    includeRaw: false,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--query') out.queries.push(argv[++i]);
    else if (arg === '--queries') out.queries.push(...argv[++i].split(',').map(trim).filter(Boolean));
    else if (arg === '--url') out.urls.push(argv[++i]);
    else if (arg === '--urls') out.urls.push(...argv[++i].split(',').map(trim).filter(Boolean));
    else if (arg === '--page') out.page = Number(argv[++i]);
    else if (arg === '--max-pages') out.maxPages = Number(argv[++i]);
    else if (arg === '--limit') out.limit = Number(argv[++i]);
    else if (arg === '--per-page') out.perPage = Number(argv[++i]);
    else if (arg === '--jsonl') out.jsonl = true;
    else if (arg === '--include-raw') out.includeRaw = true;
    else if (arg === '--help' || arg === '-h') {
      printHelpAndExit();
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (out.queries.length === 0 && out.urls.length === 0) {
    throw new Error('Provide at least one --query or --url');
  }

  return out;
}

function printHelpAndExit() {
  console.log(`Usage:
  node scripts/crawl_naver_blog.js --query "보관이사" --limit 10
  node scripts/crawl_naver_blog.js --queries "주방 수전,세라믹 식탁" --limit 20
  node scripts/crawl_naver_blog.js --url "https://blog.naver.com/blogId/123456789"

Options:
  --query <q>          Add one search query
  --queries <a,b>      Add multiple search queries
  --url <u>            Add one blog post URL
  --urls <a,b>         Add multiple blog post URLs
  --page <n>           Search start page, default 1
  --max-pages <n>      Search page count per query, default 1
  --per-page <n>       Search rows per page, default 10
  --limit <n>          Max posts to collect, default 10
  --jsonl              Print one JSON object per line
  --include-raw        Include raw content HTML in output
`);
  process.exit(0);
}

function cleanSearchUrl(url) {
  return String(url).replace(/&quot;.*$/, '').replace(/&amp;.*$/, '').replace(/[),.]+$/, '');
}

function normalizeBlogUrl(value) {
  if (!value) {
    return null;
  }

  const cleaned = cleanSearchUrl(String(value).trim());

  try {
    const parsed = new URL(cleaned);

    const host = parsed.hostname.replace(/^www\./, '');
    if (!host.endsWith('blog.naver.com')) {
      return null;
    }

    if (parsed.pathname === '/PostView.naver' || parsed.pathname === '/PostView.nhn') {
      const blogId = parsed.searchParams.get('blogId');
      const postId = parsed.searchParams.get('logNo');
      if (blogId && postId) {
        return {
          blogId,
          postId,
          canonicalUrl: `https://blog.naver.com/${blogId}/${postId}`,
          desktopUrl: `https://blog.naver.com/PostView.naver?blogId=${blogId}&logNo=${postId}`,
          mobileUrl: `https://m.blog.naver.com/PostView.naver?blogId=${blogId}&logNo=${postId}&navType=tl`,
        };
      }
    }

    const parts = parsed.pathname.split('/').filter(Boolean);
    if (parts.length >= 2 && /^\d+$/.test(parts[1])) {
      const blogId = parts[0];
      const postId = parts[1];
      return {
        blogId,
        postId,
        canonicalUrl: `https://blog.naver.com/${blogId}/${postId}`,
        desktopUrl: `https://blog.naver.com/PostView.naver?blogId=${blogId}&logNo=${postId}`,
        mobileUrl: `https://m.blog.naver.com/PostView.naver?blogId=${blogId}&logNo=${postId}&navType=tl`,
      };
    }
  } catch {
    const match = cleaned.match(/blog\.naver\.com\/([^/?#]+)\/(\d+)/);
    if (match) {
      const blogId = match[1];
      const postId = match[2];
      return {
        blogId,
        postId,
        canonicalUrl: `https://blog.naver.com/${blogId}/${postId}`,
        desktopUrl: `https://blog.naver.com/PostView.naver?blogId=${blogId}&logNo=${postId}`,
        mobileUrl: `https://m.blog.naver.com/PostView.naver?blogId=${blogId}&logNo=${postId}&navType=tl`,
      };
    }
  }

  return null;
}

async function fetchText(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      ...DEFAULT_HEADERS,
      ...(options.headers || {}),
    },
  });
  return {
    status: res.status,
    text: await res.text(),
    url: res.url,
  };
}

function extractJsonp(text) {
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end < 0 || end <= start) {
    throw new Error('Missing JSON payload');
  }
  return JSON.parse(text.slice(start, end + 1));
}

async function fetchSearchResults(query, page, perPage) {
  const start = 1 + (page - 1) * perPage;
  const url = `https://search.naver.com/search.naver?where=post&query=${encodeURIComponent(query)}&start=${start}`;
  const { status, text } = await fetchText(url);
  if (status !== 200) {
    throw new Error(`Search failed for "${query}" (status ${status})`);
  }

  const urls = [...text.matchAll(/https:\/\/blog\.naver\.com\/[^"'<> \t\r\n]+/g)]
    .map((m) => normalizeBlogUrl(cleanSearchUrl(m[0])))
    .filter(Boolean);

  return dedupe(urls, (item) => item.canonicalUrl);
}

async function followMainFrame(html, baseUrl) {
  const match = html.match(/<iframe[^>]+id="mainFrame"[^>]+src="([^"]+)"/i);
  if (!match) {
    return { html, url: baseUrl };
  }

  const frameUrl = new URL(match[1], baseUrl).href;
  const { status, text } = await fetchText(frameUrl, {
    headers: {
      Referer: baseUrl,
    },
  });

  if (status !== 200) {
    return { html, url: baseUrl };
  }

  return { html: text, url: frameUrl };
}

async function fetchPostHtml(ref) {
  const candidates = [ref.desktopUrl, ref.mobileUrl, ref.canonicalUrl];
  let best = { html: '', url: candidates[0], score: -1 };

  for (const candidate of candidates) {
    const { status, text } = await fetchText(candidate, {
      headers: {
        Referer: `https://blog.naver.com/${ref.blogId}`,
      },
    });

    if (status !== 200) {
      continue;
    }

    const followed = await followMainFrame(text, candidate);
    const score = extractBodyText(followed.html).length;

    if (score > best.score) {
      best = { html: followed.html, url: followed.url, score };
    }

    if (score > 0) {
      break;
    }
  }

  return best;
}

function extractTitle(html) {
  const og = html.match(/<meta property="og:title" content="([^"]+)"/i);
  if (og) {
    return decodeHtml(og[1]);
  }

  const seTitle = html.match(/<div class="se_documentTitle"[\s\S]*?<div class="se_textarea">([\s\S]*?)<\/div>/i);
  if (seTitle) {
    return stripHtmlFragment(seTitle[1]);
  }

  const titleTag = html.match(/<title>([\s\S]*?)<\/title>/i);
  if (titleTag) {
    return stripHtmlFragment(titleTag[1]);
  }

  return '';
}

function extractBodyText(html) {
  const smartEditorBlocks = [...html.matchAll(/<!-- SE-TEXT \{ -->([\s\S]*?)<!-- \} SE-TEXT -->/g)]
    .map((m) => stripHtmlFragment(m[1]))
    .filter(Boolean);

  if (smartEditorBlocks.length > 0) {
    return smartEditorBlocks.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  }

  const seStart = html.indexOf('<div class="se-main-container">');
  const commentStart = seStart >= 0 ? html.indexOf('<div class="wrap_postcomment"', seStart) : -1;
  if (seStart >= 0 && commentStart > seStart) {
    return stripHtmlFragment(html.slice(seStart, commentStart));
  }

  const postStart = html.indexOf('<div id="post-view');
  const postEnd = postStart >= 0 ? html.indexOf('<div class="division-line-x', postStart) : -1;
  if (postStart >= 0 && postEnd > postStart) {
    return stripHtmlFragment(html.slice(postStart, postEnd));
  }

  return '';
}

function normalizeCommentText(input) {
  return stripHtmlFragment(input || '');
}

function normalizeComments(commentList = []) {
  const comments = [];
  let head = null;

  for (const comment of [...commentList].reverse()) {
    const item = {
      id: comment.commentNo,
      parentCommentNo: comment.parentCommentNo,
      isSecret: !!comment.secret,
      writer: comment.secret ? null : (comment.userName || comment.profileUserId || null),
      profileUserId: comment.profileUserId || null,
      addDate: comment.modTime || null,
      contents: normalizeCommentText(comment.contents || ''),
      childs: [],
    };

    if (comment.parentCommentNo !== item.id && head) {
      head.childs.push(item);
    } else {
      comments.push(item);
      head = item;
    }
  }

  return comments;
}

async function fetchBlogInfo(blogId) {
  const url = `https://m.blog.naver.com/rego/BlogInfo.nhn?blogId=${blogId}`;
  const { status, text } = await fetchText(url, {
    headers: {
      Referer: `https://m.blog.naver.com/PostList.nhn?blogId=${blogId}`,
    },
  });

  if (status !== 200) {
    throw new Error(`BlogInfo failed for ${blogId} (status ${status})`);
  }

  const json = extractJsonp(text);
  if (!json?.result?.blogNo) {
    throw new Error(`BlogInfo returned no blogNo for ${blogId}`);
  }

  return json.result;
}

function classifyPost({ html, bodyText, commentStatus, promoFlag }) {
  const head = html.slice(0, 16000);
  const restrictedHints = [
    /이\s*글은\s*비공개/i,
    /비공개\s*(포스트|게시물|글)/i,
    /작성자만\s*볼\s*수\s*있습니다/i,
    /열람\s*권한이\s*없습니다/i,
    /접근\s*권한이\s*없습니다/i,
    /권한이\s*없습니다/i,
    /로그인이\s*필요합니다/i,
    /이\s*게시물은\s*비공개/i,
    /이\s*포스트는\s*비공개/i,
  ];

  if (restrictedHints.some((re) => re.test(head))) {
    return 'restricted';
  }
  if (!bodyText) {
    return 'unparsed';
  }
  return 'public';
}

function detectPromo(text) {
  return /(협찬|광고|체험단|제휴|원고료|파트너스|네이버\s*쇼핑\s*커넥트|소정의\s*마일리지|문의\s*주시면|쪽지\s*주시면|댓글\s*남겨|댓글\s*주세요|이 포스팅은 쿠팡 파트너스)/i.test(
    text,
  );
}

async function fetchComments(blogNo, postId, blogId) {
  const params = new URLSearchParams({
    ticket: 'blog',
    templateId: 'default_simple',
    pool: 'cbox9',
    _callback: 'cb',
    lang: 'ko',
    country: '',
    objectId: `${blogNo}_201_${postId}`,
    categoryId: '',
    pageSize: '50',
    indexSize: '10',
    groupId: String(blogNo),
    listType: 'OBJECT',
    pageType: 'default',
    page: '1',
    initialize: 'true',
    userType: '',
    useAltSort: 'true',
    replyPageSize: '10',
    moveTo: '',
    showReply: 'true',
    _: String(blogNo),
  });

  const url = `https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?${params}`;
  const { status, text } = await fetchText(url, {
    headers: {
      Referer: `https://m.blog.naver.com/PostList.nhn?blogId=${blogId}`,
    },
  });

  if (status !== 200) {
    return {
      status: 'blocked',
      commentCount: 0,
      comments: [],
      message: `comment fetch failed (status ${status})`,
    };
  }

  const json = extractJsonp(text);
  if (json.success === false) {
    const message = json.message || 'comment request failed';
    const statusText = /댓글을 허용하지 않는 포스트/.test(message)
      ? 'comment_disabled'
      : /로그인|권한|비공개/.test(message)
        ? 'restricted'
        : 'blocked';
    return {
      status: statusText,
      commentCount: 0,
      comments: [],
      message,
    };
  }

  const rawList = json?.result?.commentList || [];
  return {
    status: 'ok',
    commentCount: rawList.length,
    comments: normalizeComments(rawList),
    message: null,
  };
}

async function collectFromUrl(inputUrl) {
  const ref = normalizeBlogUrl(inputUrl);
  if (!ref) {
    throw new Error(`Unsupported blog URL: ${inputUrl}`);
  }

  const { html, url: resolvedUrl } = await fetchPostHtml(ref);
  const title = extractTitle(html);
  let bodyText = extractBodyText(html);

  if (title && bodyText.startsWith(`${title}\n`)) {
    bodyText = bodyText.slice(title.length + 1).trim();
  }
  if (title && bodyText === title) {
    bodyText = '';
  }

  const promoFlag = detectPromo(`${title}\n${bodyText}`);

  const blogInfo = await fetchBlogInfo(ref.blogId);
  const comments = await fetchComments(blogInfo.blogNo, ref.postId, ref.blogId);

  const accessStatus = classifyPost({
    html,
    bodyText,
    commentStatus: comments.status,
    promoFlag,
  });

  const result = {
    blogId: ref.blogId,
    postId: ref.postId,
    canonicalUrl: ref.canonicalUrl,
    resolvedUrl,
    title,
    bodyText,
    commentStatus: comments.status,
    commentCount: comments.commentCount,
    comments: comments.comments,
    accessStatus,
    promoFlag,
    source: {
      desktopUrl: ref.desktopUrl,
      mobileUrl: ref.mobileUrl,
      rssUrl: `https://rss.blog.naver.com/${ref.blogId}.xml`,
    },
  };

  if (comments.message) {
    result.commentMessage = comments.message;
  }

  if (result.accessStatus === 'restricted') {
    result.bodyText = '';
    result.comments = [];
    result.commentCount = 0;
  }

  if (result.accessStatus === 'unparsed') {
    result.commentCount = comments.commentCount;
  }

  if (result.accessStatus === 'public' && !result.bodyText && comments.status === 'ok' && comments.commentCount === 0) {
    result.accessStatus = 'unparsed';
  }

  return result;
}

async function run() {
  const args = parseArgs(process.argv);
  const seeds = [];

  for (const query of args.queries) {
    for (let page = args.page; page < args.page + args.maxPages; page += 1) {
      const urls = await fetchSearchResults(query, page, args.perPage);
      for (const ref of urls) {
        seeds.push({ ...ref, query });
      }
      if (seeds.length >= args.limit) {
        break;
      }
    }
    if (seeds.length >= args.limit) {
      break;
    }
  }

  for (const url of args.urls) {
    const ref = normalizeBlogUrl(url);
    if (ref) {
      seeds.push({ ...ref, query: null });
    }
  }

  const uniqueSeeds = dedupe(seeds, (item) => item.canonicalUrl).slice(0, args.limit);
  const results = [];

  for (const seed of uniqueSeeds) {
    const item = await collectFromUrl(seed.canonicalUrl);
    if (seed.query) {
      item.query = seed.query;
    }
    if (args.includeRaw) {
      const ref = normalizeBlogUrl(seed.canonicalUrl);
      const fetched = await fetchPostHtml(ref);
      item.contentHtml = fetched.html;
    }
    results.push(item);
  }

  if (args.jsonl) {
    for (const item of results) {
      process.stdout.write(`${JSON.stringify(item)}\n`);
    }
    return;
  }

  process.stdout.write(`${JSON.stringify(results, null, 2)}\n`);
}

run().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
