const GITHUB_RAW_BASE = "https://raw.githubusercontent.com/AtharvadChaudhari05/CoverIndex-AI/main/public";
const RENDER_API_BASE = "https://coverindex-ai.onrender.com";

const ASSETS = new Map([
  ["/", { file: "index.html", contentType: "text/html; charset=utf-8" }],
  ["/index.html", { file: "index.html", contentType: "text/html; charset=utf-8" }],
  ["/styles.css", { file: "styles.css", contentType: "text/css; charset=utf-8" }],
  ["/app.js", { file: "app.js", contentType: "application/javascript; charset=utf-8" }],
]);

addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  if (url.pathname.startsWith("/api/")) {
    return proxyApi(request, url);
  }

  if (ASSETS.has(url.pathname)) {
    return fetchAsset(url.pathname);
  }

  return fetchAsset("/");
}

async function proxyApi(request, url) {
  const target = new URL(url.pathname + url.search, RENDER_API_BASE);
  const init = {
    method: request.method,
    headers: new Headers(request.headers),
    redirect: "follow",
  };

  init.headers.delete("host");
  init.headers.delete("cf-connecting-ip");
  init.headers.delete("cf-ipcountry");
  init.headers.delete("cf-ray");
  init.headers.delete("x-forwarded-for");
  init.headers.delete("x-forwarded-proto");
  init.headers.delete("x-forwarded-host");

  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.arrayBuffer();
  }

  const response = await fetch(target.toString(), init);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: makeNoStoreHeaders(response.headers),
  });
}

async function fetchAsset(pathname) {
  const asset = ASSETS.get(pathname) || ASSETS.get("/");
  const response = await fetch(`${GITHUB_RAW_BASE}/${asset.file}`, {
    headers: { "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" },
  });

  if (!response.ok) {
    return new Response("Asset unavailable", {
      status: 502,
      headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" },
    });
  }

  const headers = makeNoStoreHeaders(response.headers);
  headers.set("Content-Type", asset.contentType);
  return new Response(response.body, {
    status: 200,
    headers,
  });
}

function makeNoStoreHeaders(sourceHeaders) {
  const headers = new Headers(sourceHeaders);
  headers.set("Cache-Control", "no-store, max-age=0");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("X-Frame-Options", "DENY");
  headers.set("Referrer-Policy", "no-referrer");
  return headers;
}
