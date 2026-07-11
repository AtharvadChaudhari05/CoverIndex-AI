addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

const RAW_PUBLIC_BASE =
  "https://raw.githubusercontent.com/AtharvadChaudhari05/CoverIndex-AI/main/public";
const API_BASE = "https://coverindex-ai.onrender.com";

const STATIC_ASSETS = {
  "/": { upstreamPath: "/index.html", contentType: "text/html; charset=UTF-8" },
  "/index.html": { upstreamPath: "/index.html", contentType: "text/html; charset=UTF-8" },
  "/styles.css": { upstreamPath: "/styles.css", contentType: "text/css; charset=UTF-8" },
  "/app.js": { upstreamPath: "/app.js", contentType: "application/javascript; charset=UTF-8" },
};

async function handleRequest(request) {
  const url = new URL(request.url);

  if (url.pathname.startsWith("/api/")) {
    return proxyApiRequest(url, request);
  }

  const asset = STATIC_ASSETS[url.pathname];
  if (!asset) {
    return new Response("Not found", { status: 404 });
  }

  const upstreamResponse = await fetch(`${RAW_PUBLIC_BASE}${asset.upstreamPath}`, {
    cf: {
      cacheEverything: true,
      cacheTtl: 60,
    },
  });

  if (!upstreamResponse.ok) {
    return new Response(`Failed to load ${asset.upstreamPath}`, { status: 502 });
  }

  const headers = new Headers(upstreamResponse.headers);
  headers.set("content-type", asset.contentType);
  headers.set("cache-control", "public, max-age=60");

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    headers,
  });
}

async function proxyApiRequest(url, request) {
  const target = new URL(url.pathname + url.search, API_BASE);
  const headers = new Headers(request.headers);
  headers.set("host", new URL(API_BASE).host);

  return fetch(target.toString(), {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
    redirect: "follow",
  });
}
