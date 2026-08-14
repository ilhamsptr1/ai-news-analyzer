"""
Article Extractor Service — fetches and extracts article content from URLs.

Pipeline:
    URL → HTTP fetch → HTML → Trafilatura (primary) → BeautifulSoup (fallback)
        → Text cleaning → ExtractionResult
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from app.utils.text_cleaner import clean_text, clean_title, count_words, estimate_reading_time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HTTP_TIMEOUT_SECONDS = 15
HTTP_MAX_REDIRECTS = 5
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Minimum content length — articles shorter than this are likely extraction failures
MIN_CONTENT_LENGTH = 200

# Noise phrases indicating extraction failure (navigation menus, cookie walls, etc.)
_NOISE_PHRASES = [
    "enable javascript",
    "please enable cookies",
    "you need to enable javascript",
    "403 forbidden",
    "access denied",
    "captcha",
    "cloudflare",
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ExtractionResult:
    """Normalized article data after extraction and cleaning."""

    title: str
    content: str
    url: str
    source: str
    author: str | None = None
    published_at: datetime | None = None
    word_count: int = 0
    reading_time: int = 0


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class FetchError(RuntimeError):
    """Raised when the HTTP request fails."""

    pass


class TimeoutError(FetchError):
    """Raised when the HTTP request times out."""

    pass


class ExtractionError(RuntimeError):
    """Raised when content cannot be extracted from the HTML."""

    pass


# ---------------------------------------------------------------------------
# HTTP Client
# ---------------------------------------------------------------------------


def _make_http_client() -> httpx.Client:
    """Build a configured httpx sync client."""
    return httpx.Client(
        timeout=httpx.Timeout(HTTP_TIMEOUT_SECONDS),
        follow_redirects=True,
        max_redirects=HTTP_MAX_REDIRECTS,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
        },
    )


def _fetch_html(url: str) -> str:
    """
    Fetch HTML content from a URL.

    Returns:
        Raw HTML string.

    Raises:
        TimeoutError: If the request times out.
        FetchError: For any other HTTP or network error.
    """
    try:
        with _make_http_client() as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException as exc:
        raise TimeoutError(f"Request timed out after {HTTP_TIMEOUT_SECONDS}s: {url}") from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 403:
            raise FetchError(
                f"Access denied (403): The source website blocked the request for {url}"
            ) from exc
        elif status == 429:
            raise FetchError(
                f"Rate limited (429): Too many requests to {url}"
            ) from exc
        elif status in (502, 503):
            raise FetchError(
                f"Source unreachable ({status}): The news server is unavailable for {url}"
            ) from exc
        raise FetchError(
            f"HTTP {status} error fetching {url}"
        ) from exc
    except httpx.RequestError as exc:
        raise FetchError(f"Network error fetching {url}: {exc}") from exc


# ---------------------------------------------------------------------------
# Source Extraction
# ---------------------------------------------------------------------------


def _extract_source(url: str) -> str:
    """Extract the domain name (without www.) from a URL."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    # Strip www. prefix
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname


# ---------------------------------------------------------------------------
# Date Parsing
# ---------------------------------------------------------------------------


def _parse_date(date_str: str | None) -> datetime | None:
    """
    Parse a date string into a timezone-aware datetime.
    Returns None if parsing fails or input is None.
    """
    if not date_str:
        return None
    try:
        return dateutil_parser.parse(date_str, fuzzy=True)
    except (ValueError, OverflowError):
        return None


# ---------------------------------------------------------------------------
# Trafilatura Extractor (Primary)
# ---------------------------------------------------------------------------


def _extract_with_trafilatura(html: str, url: str) -> ExtractionResult | None:
    """
    Attempt extraction using Trafilatura.

    Returns ExtractionResult on success, None on failure.
    """
    try:
        # Extract full metadata
        metadata = trafilatura.extract_metadata(html, default_url=url)

        # Extract main text content
        content_raw = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=False,
            favor_recall=True,
        )

        if not content_raw or len(content_raw.strip()) < MIN_CONTENT_LENGTH:
            logger.debug("Trafilatura returned insufficient content for %s", url)
            return None

        content = clean_text(content_raw)
        
        # Quality guard: reject content that looks like noise
        content_lower = content.lower()
        if any(phrase in content_lower for phrase in _NOISE_PHRASES[:4]):  # Only most critical noise
            logger.debug("Trafilatura content looks like noise for %s", url)
            return None

        # Extract title
        title_raw = None
        if metadata:
            title_raw = metadata.title
        if not title_raw:
            return None  # No title → cannot produce valid article

        title = clean_title(title_raw)
        if not title:
            return None

        # Author
        author = None
        if metadata and metadata.author:
            author = str(metadata.author).strip() or None

        # Published date
        published_at = None
        if metadata and metadata.date:
            published_at = _parse_date(metadata.date)

        word_count = count_words(content)
        reading_time = estimate_reading_time(word_count)

        return ExtractionResult(
            title=title,
            content=content,
            url=url,
            source=_extract_source(url),
            author=author,
            published_at=published_at,
            word_count=word_count,
            reading_time=reading_time,
        )

    except Exception as exc:
        logger.warning("Trafilatura extraction failed for %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# BeautifulSoup Fallback Extractor
# ---------------------------------------------------------------------------


def _extract_with_beautifulsoup(html: str, url: str) -> ExtractionResult | None:
    """
    Fallback extraction using BeautifulSoup.

    Targets <article>, <main>, then <body> in order of preference.
    Removes noise elements before extracting text.
    Returns ExtractionResult on success, None on failure.
    """
    try:
        soup = BeautifulSoup(html, "lxml")

        # ── Remove noise elements ──────────────────────────────────────────
        for tag in soup.find_all(
            ["script", "style", "nav", "footer", "header",
             "aside", "form", "iframe", "noscript", "button"]
        ):
            # Preserve JSON-LD scripts for metadata extraction
            if tag.name == "script" and tag.get("type") == "application/ld+json":
                continue
            tag.decompose()

        # Remove common ad/cookie/comment class patterns
        for tag in soup.find_all(
            True,
            class_=lambda c: c and any(
                kw in c.lower()
                for kw in ["cookie", "banner", "advertisement", "ad-", "promo",
                            "popup", "modal", "comment", "sidebar", "widget"]
            ),
        ):
            tag.decompose()

        # ── Parse JSON-LD for metadata (check early for efficiency) ─────────
        import json as _json
        jsonld_data: dict = {}
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                raw = _json.loads(script.string or "")
                # Handle both single object and @graph array
                if isinstance(raw, list):
                    for item in raw:
                        if isinstance(item, dict) and item.get("@type") in (
                            "NewsArticle", "Article", "WebPage"
                        ):
                            jsonld_data = item
                            break
                elif isinstance(raw, dict):
                    if raw.get("@type") in ("NewsArticle", "Article", "WebPage"):
                        jsonld_data = raw
            except (_json.JSONDecodeError, TypeError):
                continue

        # ── Title Extraction ──────────────────────────────────────────────
        title_raw = None

        # 1. OG / meta title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title_raw = og_title["content"]

        # 2. JSON-LD headline (often cleaner than og:title or <title>)
        if not title_raw and jsonld_data.get("headline"):
            title_raw = jsonld_data["headline"]

        # 3. <title> tag
        if not title_raw and soup.title and soup.title.string:
            title_raw = soup.title.string

        # 4. First <h1> (last resort)
        if not title_raw:
            h1 = soup.find("h1")
            if h1:
                title_raw = h1.get_text()

        if not title_raw:
            logger.debug("BeautifulSoup: no title found for %s", url)
            return None

        title = clean_title(title_raw)
        if not title:
            return None

        # ── Content Extraction ────────────────────────────────────────────
        # Try JSON-LD articleBody first (often best for news sites)
        content_raw = None
        if jsonld_data.get("articleBody") and len(str(jsonld_data["articleBody"])) > MIN_CONTENT_LENGTH:
            content_raw = str(jsonld_data["articleBody"])

        if not content_raw:
            # Helper to safely check class names
            def _has_class(class_names: str | list | None, keyword: str) -> bool:
                if not class_names:
                    return False
                if isinstance(class_names, list):
                    return any(keyword in c for c in class_names if c)
                return keyword in class_names

            # Attempt various known content containers (including Indonesian news site patterns)
            content_el = (
                soup.find("article")
                or soup.find("main")
                or soup.find(id="content")
                or soup.find(id="main-content")
                or soup.find(id="article-body")
                or soup.find(id="detikdetail")
                or soup.find(attrs={"class": lambda c: _has_class(c, "article-content")})
                or soup.find(attrs={"class": lambda c: _has_class(c, "article-body")})
                or soup.find(attrs={"class": lambda c: _has_class(c, "detail-text")})
                or soup.find(class_="content")
                or soup.find("body")
            )

            if not content_el:
                return None

            # Get all paragraphs
            paragraphs = content_el.find_all("p")
            if paragraphs:
                content_raw = "\n\n".join(p.get_text() for p in paragraphs if p.get_text().strip())
            else:
                content_raw = content_el.get_text(separator="\n")

        if not content_raw or len(content_raw.strip()) < MIN_CONTENT_LENGTH:
            return None

        content = clean_text(content_raw)

        # Quality guard: reject content that looks like noise
        content_lower = content.lower()
        if any(phrase in content_lower for phrase in _NOISE_PHRASES[:4]):
            logger.debug("BeautifulSoup content looks like noise for %s", url)
            return None

        # ── Published Date ────────────────────────────────────────────────
        published_at = None
        for meta_name in [
            ("property", "article:published_time"),
            ("name", "publish-date"),
            ("name", "date"),
            ("itemprop", "datePublished"),
        ]:
            meta = soup.find("meta", {meta_name[0]: meta_name[1]})
            if meta and meta.get("content"):
                published_at = _parse_date(meta["content"])
                if published_at:
                    break

        # JSON-LD datePublished fallback
        if not published_at and jsonld_data.get("datePublished"):
            published_at = _parse_date(jsonld_data["datePublished"])

        # ── Author ────────────────────────────────────────────────────────
        author = None
        # 1. meta author tag
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and author_meta.get("content"):
            author = author_meta["content"].strip() or None

        # 2. JSON-LD author
        if not author and jsonld_data.get("author"):
            jld_author = jsonld_data["author"]
            if isinstance(jld_author, dict):
                author = jld_author.get("name", "").strip() or None
            elif isinstance(jld_author, list) and jld_author:
                first = jld_author[0]
                if isinstance(first, dict):
                    author = first.get("name", "").strip() or None
                elif isinstance(first, str):
                    author = first.strip() or None
            elif isinstance(jld_author, str):
                author = jld_author.strip() or None

        word_count = count_words(content)
        reading_time = estimate_reading_time(word_count)

        return ExtractionResult(
            title=title,
            content=content,
            url=url,
            source=_extract_source(url),
            author=author,
            published_at=published_at,
            word_count=word_count,
            reading_time=reading_time,
        )

    except Exception as exc:
        logger.warning("BeautifulSoup extraction failed for %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_article(url: str) -> ExtractionResult:
    """
    Fetch and extract article content from a URL.

    Pipeline:
        1. HTTP fetch
        2. Trafilatura (primary extractor)
        3. BeautifulSoup (fallback extractor)

    Args:
        url: Validated, SSRF-safe article URL.

    Returns:
        ExtractionResult with normalized article data.

    Raises:
        TimeoutError: If the HTTP request times out.
        FetchError: If the HTTP request fails.
        ExtractionError: If content cannot be extracted.
    """
    logger.info("Fetching article: %s", url)
    html = _fetch_html(url)

    # Primary extractor
    result = _extract_with_trafilatura(html, url)
    if result:
        logger.info("Trafilatura extraction succeeded for %s", url)
        return result

    # Fallback extractor
    logger.info("Trafilatura failed, trying BeautifulSoup for %s", url)
    result = _extract_with_beautifulsoup(html, url)
    if result:
        logger.info("BeautifulSoup extraction succeeded for %s", url)
        return result

    raise ExtractionError(
        f"Could not extract article content from: {url}. "
        "The page may be behind a paywall, require JavaScript, "
        "or have a non-standard layout."
    )
