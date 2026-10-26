from __future__ import annotations

import ipaddress
import socket
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urlparse

from .utils import tokenize

FETCH_TIMEOUT_SECONDS = 6
MAX_PAGE_BYTES = 1_500_000
MAX_CHARS_PER_PAGE = 1500
USER_AGENT = "Mozilla/5.0 (compatible; CoverIndexAI/1.0; +https://github.com/AtharvadChaudhari05/CoverIndex-AI)"

# Text inside these tags is page chrome or code, not article content
_SKIPPED_TAGS = {"script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg", "button", "iframe"}
_BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "td", "dd", "blockquote", "article", "section", "div", "br"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._current: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _SKIPPED_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIPPED_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._current.append(data)

    def _flush(self) -> None:
        text = " ".join("".join(self._current).split())
        if text:
            self.blocks.append(text)
        self._current = []

    def close(self) -> None:
        super().close()
        self._flush()


def extract_text_blocks(html: str) -> list[str]:
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    # Short blocks are menus, buttons, and captions
    return [block for block in parser.blocks if len(block) >= 60]


def is_public_http_url(url: str) -> bool:
    """Rejects non-HTTP URLs and hosts that resolve to private, loopback, or link-local addresses,
    so a search result can never make the server fetch an internal address."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror:
        return False
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%")[0])
        if not ip.is_global:
            return False
    return True


def fetch_page_text(url: str) -> list[str]:
    if not is_public_http_url(url):
        return []
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            if "html" not in response.headers.get("Content-Type", ""):
                return []
            # Redirects can lead anywhere, so check the final address too
            if not is_public_http_url(response.geturl()):
                return []
            raw = response.read(MAX_PAGE_BYTES)
            charset = response.headers.get_content_charset() or "utf-8"
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return []
    return extract_text_blocks(raw.decode(charset, errors="ignore"))


def select_relevant_text(blocks: list[str], query: str, limit: int = MAX_CHARS_PER_PAGE) -> str:
    """Keeps the blocks that share the most words with the query, in page order, up to limit characters."""
    query_tokens = set(tokenize(query))
    scored = [(len(query_tokens.intersection(tokenize(block))), index) for index, block in enumerate(blocks)]
    chosen: list[int] = []
    used = 0
    for score, index in sorted(scored, key=lambda item: (-item[0], item[1])):
        if score == 0 or used >= limit:
            break
        chosen.append(index)
        used += len(blocks[index])
    return " ".join(blocks[index] for index in sorted(chosen))[:limit]


def read_pages(results: list[dict[str, str]], query: str) -> list[str]:
    """Fetches the search result pages in parallel and returns one source text per result.
    A result whose page cannot be read falls back to its search snippet."""
    with ThreadPoolExecutor(max_workers=max(1, len(results))) as pool:
        page_blocks = list(pool.map(lambda result: fetch_page_text(result.get("href", "")), results))

    sources = []
    for result, blocks in zip(results, page_blocks):
        href = result.get("href", "")
        title = result.get("title", "")
        text = select_relevant_text(blocks, query) or result.get("body", "")
        if href and text:
            sources.append(f"Source [{href}]: {title} - {text}")
    return sources
