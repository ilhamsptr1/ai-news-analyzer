"""
Phase 5C-4 — Real News Source Compatibility Tests

Tests extraction pipeline improvements using mocked HTML responses
that simulate the structure of real Indonesian and international news sources.

This ensures:
- OpenGraph extraction
- JSON-LD extraction (NewsArticle schema)
- Content quality validation
- Blocked source (403/429) handling
- Wikipedia artifact cleaning regression
- Language detection regression (id/en)
- SSRF regression
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.services.article_extractor import (
    ExtractionError,
    ExtractionResult,
    FetchError,
    _extract_with_beautifulsoup,
    _extract_with_trafilatura,
)
from app.utils.text_cleaner import clean_text

client = TestClient(app)


# ===========================================================================
# HTML Fixtures — Simulating Real News Sources
# ===========================================================================

DETIK_LIKE_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta property="og:title" content="Harga Minyak Dunia Turun Tajam, Dampaknya ke Indonesia">
  <meta property="og:description" content="Harga minyak dunia mengalami penurunan tajam pada perdagangan hari ini.">
  <meta name="author" content="Ahmad Fauzi">
  <meta property="article:published_time" content="2026-08-14T07:00:00+07:00">
  <title>Harga Minyak Dunia Turun Tajam - Detik Finance</title>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Harga Minyak Dunia Turun Tajam, Dampaknya ke Indonesia",
    "datePublished": "2026-08-14T07:00:00+07:00",
    "author": {"@type": "Person", "name": "Ahmad Fauzi"},
    "articleBody": "Harga minyak mentah dunia mengalami penurunan tajam pada perdagangan Kamis. Harga minyak Brent turun sebesar 3 persen menjadi 78 dolar AS per barel. Penurunan ini dipicu oleh meningkatnya stok minyak Amerika Serikat dan kekhawatiran tentang perlambatan ekonomi global. Analis menyebut bahwa dampak langsung bagi Indonesia adalah penurunan harga BBM bersubsidi yang kemungkinan akan disesuaikan pada bulan depan. Pemerintah Indonesia sedang mempertimbangkan revisi harga BBM untuk menyesuaikan kondisi pasar minyak global."
  }
  </script>
</head>
<body>
  <nav>Menu Navigasi | Beranda | Finansial | Ekonomi</nav>
  <div id="detikdetail">
    <h1>Harga Minyak Dunia Turun Tajam, Dampaknya ke Indonesia</h1>
    <p>Harga minyak mentah dunia mengalami penurunan tajam pada perdagangan Kamis.</p>
    <p>Harga minyak Brent turun sebesar 3 persen menjadi 78 dolar AS per barel.</p>
    <p>Penurunan ini dipicu oleh meningkatnya stok minyak Amerika Serikat dan kekhawatiran tentang perlambatan ekonomi global.</p>
    <p>Analis menyebut bahwa dampak langsung bagi Indonesia adalah penurunan harga BBM bersubsidi yang kemungkinan akan disesuaikan pada bulan depan.</p>
    <p>Pemerintah Indonesia sedang mempertimbangkan revisi harga BBM untuk menyesuaikan kondisi pasar minyak global.</p>
  </div>
  <footer>Footer | Privacy Policy | Cookie</footer>
</body>
</html>"""

CNN_INDONESIA_LIKE_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta property="og:title" content="Presiden Tanda Tangani Undang-Undang Baru tentang Investasi">
  <meta name="author" content="Redaksi CNN Indonesia">
  <meta property="article:published_time" content="2026-08-14T09:30:00+07:00">
  <title>Presiden Tanda Tangani UU Investasi - CNN Indonesia</title>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Presiden Tanda Tangani Undang-Undang Baru tentang Investasi",
    "datePublished": "2026-08-14T09:30:00+07:00",
    "author": [{"@type": "Person", "name": "Budi Santoso"}]
  }
  </script>
</head>
<body>
  <nav>Beranda | Politik | Ekonomi | Sport</nav>
  <div class="article-content">
    <h1>Presiden Tanda Tangani Undang-Undang Baru tentang Investasi</h1>
    <p>Presiden Republik Indonesia secara resmi menandatangani undang-undang baru yang mengatur investasi asing di Indonesia pada Kamis kemarin.</p>
    <p>Undang-undang ini diharapkan dapat menarik lebih banyak investasi asing langsung ke tanah air dan membuka lapangan kerja baru.</p>
    <p>Menteri Investasi menyatakan bahwa regulasi baru ini akan menyederhanakan perizinan usaha dan mengurangi hambatan birokrasi.</p>
    <p>Beberapa sektor prioritas dalam UU ini mencakup teknologi, energi terbarukan, dan manufaktur berbasis ekspor.</p>
    <p>Pelaku bisnis menyambut baik kebijakan ini dan menyebutnya sebagai langkah maju dalam iklim investasi Indonesia.</p>
  </div>
  <footer>Footer CNN Indonesia</footer>
</body>
</html>"""

REUTERS_LIKE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta property="og:title" content="Federal Reserve holds rates steady as inflation cools">
  <meta name="author" content="Reuters Staff">
  <meta property="article:published_time" content="2026-08-14T14:00:00Z">
  <title>Federal Reserve holds rates steady as inflation cools - Reuters</title>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Federal Reserve holds rates steady as inflation cools",
    "datePublished": "2026-08-14T14:00:00Z",
    "author": {"@type": "Person", "name": "Jane Smith"}
  }
  </script>
</head>
<body>
  <nav>Home | World | Business | Technology | Finance</nav>
  <article>
    <h1>Federal Reserve holds rates steady as inflation cools</h1>
    <p>The Federal Reserve kept its benchmark interest rate unchanged on Wednesday as policymakers said inflation was continuing to decline toward their 2% target.</p>
    <p>Fed Chair Jerome Powell said the central bank was in no hurry to cut rates but acknowledged progress in bringing down price pressures.</p>
    <p>The decision was widely expected by markets, which had been pricing in a hold at this meeting following stronger-than-expected economic data.</p>
    <p>Officials left the door open for rate cuts later this year if inflation continues to decline and the labor market stays resilient.</p>
    <p>The US dollar fell slightly against major currencies following the announcement, while Treasury yields dipped modestly.</p>
  </article>
  <footer>Footer Reuters | Privacy | Terms</footer>
</body>
</html>"""

ANTARA_LIKE_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta property="og:title" content="ANTARA - Pemerintah Siapkan Paket Stimulus Ekonomi">
  <meta name="author" content="Antara News">
  <meta property="article:published_time" content="2026-08-14T06:00:00+07:00">
  <title>Pemerintah Siapkan Paket Stimulus Ekonomi - ANTARA News</title>
</head>
<body>
  <nav>Home | Ekonomi | Politik | Sport</nav>
  <main>
    <h1>Pemerintah Siapkan Paket Stimulus Ekonomi</h1>
    <p>Pemerintah Indonesia menyiapkan paket stimulus ekonomi senilai Rp 50 triliun untuk mendorong pertumbuhan di semester kedua tahun ini.</p>
    <p>Paket ini mencakup subsidi untuk sektor UMKM, insentif pajak untuk industri manufaktur, dan percepatan belanja infrastruktur pemerintah.</p>
    <p>Menteri Keuangan Sri Mulyani menyatakan bahwa stimulus ini dirancang untuk menjaga momentum pertumbuhan ekonomi Indonesia di tengah ketidakpastian global.</p>
    <p>Pertumbuhan ekonomi Indonesia pada kuartal pertama mencapai 5,2 persen, di atas rata-rata pertumbuhan negara berkembang.</p>
    <p>Analis ekonomi memperkirakan stimulus ini dapat mendorong pertumbuhan menjadi 5,5 persen pada akhir tahun.</p>
  </main>
  <footer>ANTARA Footer | Hak Cipta</footer>
</body>
</html>"""

BLOCKED_403_HTML = """<!DOCTYPE html>
<html>
<head><title>Access Denied</title></head>
<body>
  <h1>403 Forbidden</h1>
  <p>Access to this resource is denied. This page is protected by Cloudflare.</p>
  <p>Please enable cookies and disable ad blockers.</p>
</body>
</html>"""

NOISE_ONLY_HTML = """<!DOCTYPE html>
<html>
<head><title>Cookie Notice</title></head>
<body>
  <p>Please enable javascript to continue.</p>
  <p>This site requires cookies to be enabled.</p>
</body>
</html>"""

JSONLD_LIST_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>Artikel dengan JSON-LD Array</title>
  <script type="application/ld+json">
  [
    {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": []},
    {
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "headline": "Teknologi AI Semakin Canggih",
      "datePublished": "2026-08-14T10:00:00+07:00",
      "author": {"@type": "Person", "name": "Dewi Kartika"},
      "articleBody": "Perkembangan teknologi kecerdasan buatan terus menunjukkan kemajuan signifikan. Para peneliti dari berbagai universitas terkemuka di dunia telah berhasil mengembangkan model AI yang mampu memahami konteks bahasa dengan lebih baik. Teknologi ini diharapkan dapat diterapkan dalam berbagai bidang termasuk kesehatan, pendidikan, dan industri manufaktur."
    }
  ]
  </script>
</head>
<body>
  <article>
    <h1>Teknologi AI Semakin Canggih</h1>
    <p>Perkembangan teknologi kecerdasan buatan terus menunjukkan kemajuan signifikan.</p>
    <p>Para peneliti dari berbagai universitas terkemuka di dunia telah berhasil mengembangkan model AI yang mampu memahami konteks bahasa dengan lebih baik.</p>
    <p>Teknologi ini diharapkan dapat diterapkan dalam berbagai bidang termasuk kesehatan, pendidikan, dan industri manufaktur.</p>
  </article>
</body>
</html>"""

WIKIPEDIA_ID_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <title>Kecerdasan buatan - Wikipedia bahasa Indonesia</title>
</head>
<body>
  <article>
    <h1>Kecerdasan buatan</h1>
    <p>Kecerdasan buatan (bahasa Inggris: artificial intelligence atau AI) adalah kecerdasan yang ditambahkan kepada suatu sistem yang bisa diatur dalam konteks ilmiah.[1][2]</p>
    <p>Kecerdasan buatan adalah bidang ilmu komputer yang berfokus pada pembuatan sistem yang mampu melakukan tugas-tugas yang biasanya memerlukan kecerdasan manusia.[sunting] Termasuk pembelajaran mesin, pemrosesan bahasa alami, dan visi komputer.[sunting sumber]</p>
    <p>Sejarah kecerdasan buatan dimulai dari penelitian awal pada tahun 1950-an oleh Alan Turing dan para ilmuwan lainnya.[3]</p>
  </article>
</body>
</html>"""


# ===========================================================================
# 1. OpenGraph Extraction Tests
# ===========================================================================

class TestOpenGraphExtraction:
    def test_og_title_extracted(self):
        result = _extract_with_beautifulsoup(CNN_INDONESIA_LIKE_HTML, "https://cnnindonesia.com/nasional/article")
        assert result is not None
        assert "Presiden" in result.title or "Investasi" in result.title

    def test_og_published_time_extracted(self):
        result = _extract_with_beautifulsoup(CNN_INDONESIA_LIKE_HTML, "https://cnnindonesia.com/nasional/article")
        assert result is not None
        assert result.published_at is not None
        assert result.published_at.year == 2026

    def test_og_author_from_meta(self):
        result = _extract_with_beautifulsoup(CNN_INDONESIA_LIKE_HTML, "https://cnnindonesia.com/nasional/article")
        assert result is not None
        # Author might come from meta or JSON-LD
        # Either "Redaksi CNN Indonesia" (meta) or "Budi Santoso" (JSON-LD)
        assert result.author is not None

    def test_og_title_preferred_over_html_title(self):
        """OG title should be preferred over the <title> tag which often has site name appended."""
        result = _extract_with_beautifulsoup(DETIK_LIKE_HTML, "https://detik.com/finance/article")
        assert result is not None
        # OG title is cleaner
        assert "Detik Finance" not in result.title


# ===========================================================================
# 2. JSON-LD Extraction Tests
# ===========================================================================

class TestJSONLDExtraction:
    def test_jsonld_headline_extracted(self):
        result = _extract_with_beautifulsoup(DETIK_LIKE_HTML, "https://detik.com/finance/article")
        assert result is not None
        assert "Minyak" in result.title

    def test_jsonld_date_published_extracted(self):
        result = _extract_with_beautifulsoup(DETIK_LIKE_HTML, "https://detik.com/finance/article")
        assert result is not None
        assert result.published_at is not None

    def test_jsonld_author_dict_extracted(self):
        """JSON-LD author as a dict {"@type": "Person", "name": "..."}"""
        result = _extract_with_beautifulsoup(DETIK_LIKE_HTML, "https://detik.com/finance/article")
        assert result is not None
        # Author from meta is "Ahmad Fauzi", JSON-LD also has "Ahmad Fauzi"
        assert result.author == "Ahmad Fauzi"

    def test_jsonld_author_list_extracted(self):
        """JSON-LD author as a list [{"@type": "Person", "name": "..."}]"""
        result = _extract_with_beautifulsoup(CNN_INDONESIA_LIKE_HTML, "https://cnnindonesia.com/article")
        assert result is not None
        # Meta author is "Redaksi CNN Indonesia", JSON-LD has "Budi Santoso"
        # meta is preferred (found first)
        assert result.author is not None

    def test_jsonld_array_format_parsed(self):
        """JSON-LD in list format (e.g., [{BreadcrumbList}, {NewsArticle}]) should be handled."""
        result = _extract_with_beautifulsoup(JSONLD_LIST_HTML, "https://example.com/tech")
        assert result is not None
        assert "AI" in result.title or "Teknologi" in result.title
        assert result.author == "Dewi Kartika"
        assert result.published_at is not None

    def test_jsonld_article_body_used_for_content(self):
        """When JSON-LD has articleBody, it should be used for content."""
        result = _extract_with_beautifulsoup(DETIK_LIKE_HTML, "https://detik.com/finance/article")
        assert result is not None
        assert "minyak" in result.content.lower()
        assert len(result.content) > 100


# ===========================================================================
# 3. Content Quality Validation Tests
# ===========================================================================

class TestContentQualityValidation:
    def test_noise_only_html_returns_none(self):
        """Pure noise/cookie content should be rejected."""
        result = _extract_with_beautifulsoup(NOISE_ONLY_HTML, "https://example.com/blocked")
        assert result is None

    def test_content_not_navigation(self):
        result = _extract_with_beautifulsoup(DETIK_LIKE_HTML, "https://detik.com/article")
        assert result is not None
        assert "Menu Navigasi" not in result.content
        assert "Beranda" not in result.content

    def test_content_not_footer(self):
        result = _extract_with_beautifulsoup(REUTERS_LIKE_HTML, "https://reuters.com/article")
        assert result is not None
        assert "Footer" not in result.content
        assert "Privacy" not in result.content

    def test_content_length_meaningful(self):
        result = _extract_with_beautifulsoup(ANTARA_LIKE_HTML, "https://antaranews.com/article")
        assert result is not None
        assert result.word_count >= 30
        assert result.reading_time >= 1

    def test_english_content_extracted_correctly(self):
        result = _extract_with_beautifulsoup(REUTERS_LIKE_HTML, "https://reuters.com/business/article")
        assert result is not None
        assert "Federal Reserve" in result.content
        assert len(result.content) > 100


# ===========================================================================
# 4. Blocked Source Handling Tests
# ===========================================================================

class TestBlockedSourceHandling:
    def test_blocked_page_content_rejected(self):
        """Content like Cloudflare block pages should not pass quality gate."""
        result = _extract_with_beautifulsoup(BLOCKED_403_HTML, "https://kompas.com/blocked")
        # The title is "Access Denied" but no meaningful article content
        # We expect either None (if content is too short) or low quality
        if result is not None:
            # If somehow extracted, content should be very short
            assert result.word_count < 30

    def test_fetch_403_raises_fetch_error(self):
        """HTTP 403 should raise FetchError with meaningful message."""
        import httpx
        from app.services.article_extractor import _fetch_html

        with patch("app.services.article_extractor._make_http_client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__ = lambda s: mock_client
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "403 Forbidden", request=MagicMock(), response=mock_response
            )
            mock_client.get.return_value = mock_response

            with pytest.raises(FetchError) as exc_info:
                _fetch_html("https://kompas.com/blocked-article")
            assert "403" in str(exc_info.value) or "denied" in str(exc_info.value).lower()

    def test_fetch_429_raises_fetch_error(self):
        """HTTP 429 (rate limited) should raise FetchError."""
        import httpx
        from app.services.article_extractor import _fetch_html

        with patch("app.services.article_extractor._make_http_client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__ = lambda s: mock_client
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429 Too Many Requests", request=MagicMock(), response=mock_response
            )
            mock_client.get.return_value = mock_response

            with pytest.raises(FetchError) as exc_info:
                _fetch_html("https://detik.com/rate-limited")
            assert "429" in str(exc_info.value) or "rate" in str(exc_info.value).lower()


# ===========================================================================
# 5. Indonesian News Source Specific Tests  
# ===========================================================================

class TestIndonesianNewsSources:
    def test_detik_like_extraction(self):
        result = _extract_with_beautifulsoup(DETIK_LIKE_HTML, "https://detik.com/finance/article")
        assert result is not None
        assert result.title
        assert len(result.content) > 100
        assert result.source == "detik.com"

    def test_cnn_indonesia_like_extraction(self):
        result = _extract_with_beautifulsoup(CNN_INDONESIA_LIKE_HTML, "https://cnnindonesia.com/nasional/article")
        assert result is not None
        assert result.title
        assert len(result.content) > 100

    def test_antara_like_extraction(self):
        result = _extract_with_beautifulsoup(ANTARA_LIKE_HTML, "https://antaranews.com/berita/article")
        assert result is not None
        assert result.title
        assert len(result.content) > 100

    def test_reuters_like_extraction(self):
        result = _extract_with_beautifulsoup(REUTERS_LIKE_HTML, "https://reuters.com/business/article")
        assert result is not None
        assert result.title
        assert "Federal Reserve" in result.content


# ===========================================================================
# 6. Wikipedia Cleaning Regression Tests
# ===========================================================================

class TestWikipediaCleaningRegression:
    def test_wikipedia_sunting_removed(self):
        result = _extract_with_beautifulsoup(WIKIPEDIA_ID_HTML, "https://id.wikipedia.org/wiki/Kecerdasan_buatan")
        if result is not None:
            assert "[sunting]" not in result.content
            assert "[sunting sumber]" not in result.content

    def test_wikipedia_citation_numbers_removed(self):
        cleaned = clean_text("Kecerdasan buatan adalah bidang ilmu.[1][2] Sejarahnya panjang.[3]")
        assert "[1]" not in cleaned
        assert "[2]" not in cleaned
        assert "[3]" not in cleaned

    def test_wikipedia_mixed_citations_removed(self):
        cleaned = clean_text("Artikel ini perlu disunting.[sunting] Lihat referensi.[sunting sumber]")
        assert "[sunting]" not in cleaned
        assert "[sunting sumber]" not in cleaned

    def test_clean_text_preserves_real_content(self):
        """Cleaning should not remove actual content, only artifacts."""
        original = "Ini adalah berita penting tentang ekonomi Indonesia yang harus diketahui publik."
        cleaned = clean_text(original)
        assert "berita penting" in cleaned
        assert "ekonomi Indonesia" in cleaned


# ===========================================================================
# 7. SSRF Regression Tests
# ===========================================================================

class TestSSRFRegression:
    def test_localhost_blocked(self):
        response = client.post("/api/articles/extract", json={"url": "http://localhost/api/secret"})
        assert response.status_code == 400

    def test_private_ip_class_a_blocked(self):
        response = client.post("/api/articles/extract", json={"url": "http://10.0.0.1/internal"})
        assert response.status_code == 400

    def test_private_ip_class_b_blocked(self):
        response = client.post("/api/articles/extract", json={"url": "http://172.16.0.1/internal"})
        assert response.status_code == 400

    def test_private_ip_class_c_blocked(self):
        response = client.post("/api/articles/extract", json={"url": "http://192.168.1.1/admin"})
        assert response.status_code == 400

    def test_metadata_ip_blocked(self):
        response = client.post("/api/articles/extract", json={"url": "http://169.254.169.254/meta-data"})
        assert response.status_code == 400

    def test_valid_external_url_passes_validation(self):
        """Real news URLs should not be blocked by SSRF guard."""
        from app.utils.url_validator import validate_url
        # These should pass validation (we won't actually fetch them)
        assert validate_url("https://detik.com/article") == "https://detik.com/article"
        assert validate_url("https://reuters.com/world/article") == "https://reuters.com/world/article"


# ===========================================================================
# 8. API Error Handling Tests
# ===========================================================================

class TestAPIErrorHandling:
    def test_fetch_403_returns_502(self):
        """403 from source should return 502 to client (bad gateway / source denied)."""
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.side_effect = FetchError("Access denied (403)")
            response = client.post("/api/articles/extract", json={"url": "https://kompas.com/blocked"})
        assert response.status_code == 502

    def test_fetch_429_returns_502(self):
        """429 (rate limited) from source should return 502 to client."""
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.side_effect = FetchError("Rate limited (429)")
            response = client.post("/api/articles/extract", json={"url": "https://detik.com/article"})
        assert response.status_code == 502

    def test_extraction_failure_returns_422(self):
        """Extraction failure should return 422 unprocessable."""
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.side_effect = ExtractionError("Content could not be extracted")
            response = client.post("/api/articles/extract", json={"url": "https://example.com/empty"})
        assert response.status_code == 422

    def test_no_traceback_in_error_response(self):
        """Error responses should never include Python tracebacks."""
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.side_effect = ExtractionError("Extraction failed")
            response = client.post("/api/articles/extract", json={"url": "https://example.com/bad"})
        body = response.json()
        assert "Traceback" not in str(body)
        assert "Exception" not in str(body)
        assert "traceback" not in str(body)


# ===========================================================================
# 9. Source Extraction Tests
# ===========================================================================

class TestSourceDomainExtraction:
    def test_detik_source(self):
        result = _extract_with_beautifulsoup(DETIK_LIKE_HTML, "https://finance.detik.com/artikel/1234")
        assert result is not None
        assert result.source == "finance.detik.com"

    def test_www_stripped(self):
        result = _extract_with_beautifulsoup(REUTERS_LIKE_HTML, "https://www.reuters.com/business/article")
        assert result is not None
        assert result.source == "reuters.com"
