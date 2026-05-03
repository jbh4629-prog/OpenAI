#!/usr/bin/env node

const DEFAULT_HEADERS = {
  'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  'X-Cafe-Product': 'pc',
};

function decodeHtml(input = '') {
  return input
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|li|tr|h\d)>/gi, '\n')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x2F;/g, '/')
    .replace(/<[^>]+>/g, '')
    .replace(/\r/g, '')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function trim(value) {
  return String(value).trim();
}

function normalizeSearchBy(value) {
  const raw = String(value).trim().toLowerCase();
  const map = {
    content: '0',
    body: '0',
    all: '0',
    title: '1',
    subject: '1',
    writer: '3',
    comment: '4',
    comments: '4',
  };
  return map[raw] || String(value);
}

function parseArgs(argv) {
  const out = {
    cafeId: null,
    queries: [],
    articleIds: [],
    searchBy: '0',
    sortBy: 'RECENCY',
    page: 1,
    perPage: 30,
    maxPages: 1,
    limit: 10,
    jsonl: false,
    includeRaw: false,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--cafe-id') out.cafeId = argv[++i];
    else if (arg === '--query') out.queries.push(argv[++i]);
    else if (arg === '--queries') out.queries.push(...argv[++i].split(',').map(trim).filter(Boolean));
    else if (arg === '--article-id') out.articleIds.push(argv[++i]);
    else if (arg === '--article-ids') out.articleIds.push(...argv[++i].split(',').map(trim).filter(Boolean));
    else if (arg === '--search-by') out.searchBy = normalizeSearchBy(argv[++i]);
    else if (arg === '--sort-by') out.sortBy = argv[++i];
    else if (arg === '--page') out.page = Number(argv[++i]);
    else if (arg === '--per-page') out.perPage = Number(argv[++i]);
    else if (arg === '--max-pages') out.maxPages = Number(argv[++i]);
    else if (arg === '--limit') out.limit = Number(argv[++i]);
    else if (arg === '--jsonl') out.jsonl = true;
    else if (arg === '--include-raw') out.includeRaw = true;
    else if (arg === '--help' || arg === '-h') {
      printHelpAndExit();
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!out.cafeId) {
    throw new Error('Missing --cafe-id');
  }

  if (out.queries.length === 0 && out.articleIds.length === 0) {
    throw new Error('Provide at least one --query or --article-id');
  }

  if (out.queries.length === 0 && out.articleIds.length > 0) {
    throw new Error('Provide at least one --query when using --article-id filters');
  }

  return out;
}

function printHelpAndExit() {
  console.log(`Usage:
  node scripts/crawl_naver_cafe.js --cafe-id 23700418 --query "보관이사" --limit 10
  node scripts/crawl_naver_cafe.js --cafe-id 23700418 --queries "주방 수전,세라믹" --limit 20

Options:
  --cafe-id <id>       Required cafe id
  --query <q>          Add one query
  --queries <a,b>      Add multiple queries
  --article-id <id>    Filter search rows to one article id
  --search-by <mode>   0, 1, 3, 4, or content/title/writer/comment
  --sort-by <mode>     RECENCY or LIKE
  --per-page <n>       Search rows per page
  --max-pages <n>      Maximum search pages per query
  --limit <n>          Maximum article rows to fetch
  --jsonl              Print one JSON object per line
  --include-raw        Include raw contentHtml in output
`);
  process.exit(0);
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      ...DEFAULT_HEADERS,
      ...(options.headers || {}),
    },
  });

  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    json = null;
  }

  return { status: res.status, json, text };
}

async function searchArticles({ cafeId, query, searchBy, sortBy, page, perPage }) {
  const params = new URLSearchParams({
    query,
    searchBy: String(searchBy),
    sortBy,
    page: String(page),
    perPage: String(perPage),
  });

  const url = `https://apis.naver.com/cafe-web/cafe-search-api/v1.0/cafes/${cafeId}/search/articles?${params}`;
  const { json, status, text } = await fetchJson(url);

  if (status !== 200 || !json?.result?.articleList) {
    throw new Error(`Search failed for "${query}" (status ${status}): ${text.slice(0, 200)}`);
  }

  return json.result.articleList.map((row) => row.item || row).filter(Boolean);
}

async function mintShareToken({ cafeId, articleId, art, query = '', fromPopular = false }) {
  const params = new URLSearchParams({
    query,
    fromPopular: String(fromPopular),
  });

  if (art) {
    params.set('art', art);
  }

  const url = `https://article.cafe.naver.com/gw/v1/cafes/${cafeId}/articles/${articleId}/share/link?${params}`;
  const { json, status, text } = await fetchJson(url, { method: 'POST' });

  if (status !== 200 || !json?.result) {
    return { shareArt: null, shortUrl: null, error: `share-link failed (status ${status}): ${text.slice(0, 200)}` };
  }

  return {
    shareArt: json.result.art || null,
    shortUrl: json.result.shortUrl || null,
    error: json.result.art ? null : 'share-link returned empty art',
  };
}

async function fetchArticleJson({ cafeId, articleId, shareArt }) {
  const params = new URLSearchParams({
    useCafeId: 'true',
    art: shareArt,
  });

  const url = `https://article.cafe.naver.com/gw/v2.1/cafes/${cafeId}/articles/${articleId}?${params}`;
  const { json, status, text } = await fetchJson(url);

  if (status !== 200 || !json?.result?.article) {
    const message = json?.result?.errorMessage || json?.errorMessage || text.slice(0, 200);
    return { error: `article fetch failed (status ${status}): ${message}` };
  }

  return { json };
}

function normalizeArticle(payload, { includeRaw = false } = {}) {
  const result = payload.result;
  const article = result.article;
  const comments = (result.comments?.items || []).map((item) => ({
    id: item.id,
    writer: item.writer?.nick || null,
    content: decodeHtml(item.content || ''),
    isArticleWriter: !!item.isArticleWriter,
    isDeleted: !!item.isDeleted,
    isRef: !!item.isRef,
  }));

  const out = {
    cafeId: result.cafeId,
    articleId: result.articleId,
    subject: article.subject,
    writer: article.writer?.nick || null,
    menu: article.menu?.name || null,
    boardType: article.menu?.boardType || null,
    readCount: article.readCount ?? null,
    commentCount: article.commentCount ?? comments.length,
    writeDate: article.writeDate ?? null,
    bodyText: decodeHtml(article.contentHtml || ''),
    comments,
    source: {
      articleId: article.id,
      refArticleId: article.refArticleId ?? null,
      shortUrl: result.shortUrl || null,
    },
  };

  if (includeRaw) {
    out.contentHtml = article.contentHtml || '';
  }

  return out;
}

async function collectByQuery(options, query) {
  const seen = new Map();
  const rows = [];

  for (let page = options.page; page < options.page + options.maxPages; page += 1) {
    const items = await searchArticles({
      cafeId: options.cafeId,
      query,
      searchBy: options.searchBy,
      sortBy: options.sortBy,
      page,
      perPage: options.perPage,
    });

    for (const item of items) {
      if (!seen.has(String(item.articleId))) {
        seen.set(String(item.articleId), item);
        rows.push(item);
      }
    }

    if (rows.length >= options.limit) {
      break;
    }

    if (items.length < options.perPage) {
      break;
    }
  }

  return rows.slice(0, options.limit).map((item) => ({ query, item }));
}

async function main() {
  const options = parseArgs(process.argv);
  const searchRows = [];
  const filteredArticleIds = new Set(options.articleIds.map(String));

  for (const query of options.queries) {
    const rows = await collectByQuery(options, query);
    for (const row of rows) {
      if (filteredArticleIds.size === 0 || filteredArticleIds.has(String(row.item.articleId))) {
        searchRows.push(row);
      }
    }
  }

  if (searchRows.length === 0) {
    throw new Error('No matching search rows found for the provided queries/article ids');
  }

  const output = [];
  for (const row of searchRows) {
    const item = row.item;
    const share = await mintShareToken({
      cafeId: options.cafeId,
      articleId: item.articleId,
      art: item.art,
      query: row.query,
    });

    if (!share.shareArt) {
      output.push({
        query: row.query,
        articleId: item.articleId,
        subject: item.subject,
        error: share.error || 'missing share art',
      });
      continue;
    }

    const articleResponse = await fetchArticleJson({
      cafeId: options.cafeId,
      articleId: item.articleId,
      shareArt: share.shareArt,
    });

    if (articleResponse.error) {
      output.push({
        query: row.query,
        articleId: item.articleId,
        subject: item.subject,
        error: articleResponse.error,
        shareArt: share.shareArt,
        shortUrl: share.shortUrl,
      });
      continue;
    }

    const normalized = normalizeArticle(articleResponse.json, { includeRaw: options.includeRaw });
    normalized.query = row.query;
    normalized.search = {
      articleId: item.articleId,
      subject: item.subject,
      art: item.art || null,
      menuId: item.menuId ?? null,
      commentCount: item.commentCount ?? null,
      likeItCount: item.likeItCount ?? null,
    };
    normalized.source.shareArt = share.shareArt;
    normalized.source.shortUrl = share.shortUrl;
    output.push(normalized);
  }

  if (options.jsonl) {
    for (const row of output) {
      process.stdout.write(`${JSON.stringify(row)}\n`);
    }
  } else {
    process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
  }
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`);
  process.exit(1);
});
