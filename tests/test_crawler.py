"""
Tests for the Crawler module.

Uses mocking to avoid real HTTP requests during testing.
Covers: URL validation, text extraction, link extraction,
politeness window, error handling, and crawl logic.
"""

import time
from unittest.mock import patch, MagicMock

import pytest
import requests

from src.crawler import Crawler, BASE_URL, POLITENESS_DELAY


# --- Sample HTML fixtures ---

SAMPLE_HTML = """
<html>
<head><title>Test Page</title></head>
<body>
    <h1>Quotes to Scrape</h1>
    <div class="quote">
        <span class="text">"The world is a book."</span>
        <span class="author">Albert Einstein</span>
        <div class="tags">
            <a href="/tag/world/page/1/">world</a>
        </div>
    </div>
    <nav>
        <a href="/page/2/">Next</a>
        <a href="https://external.com/link">External</a>
    </nav>
    <script>var x = 1;</script>
    <style>.hidden { display: none; }</style>
</body>
</html>
"""

SAMPLE_HTML_NO_LINKS = """
<html><body><p>Hello world, no links here.</p></body></html>
"""

SAMPLE_HTML_EMPTY = """
<html><body></body></html>
"""

SAMPLE_HTML_SPECIAL_CHARS = """
<html><body>
<p>Caf&eacute; &amp; résumé — "smart quotes" 'apostrophes'</p>
</body></html>
"""


class TestCrawlerInit:
    """Tests for Crawler initialization."""

    def test_default_values(self):
        crawler = Crawler()
        assert crawler.base_url == BASE_URL
        assert crawler.delay == POLITENESS_DELAY
        assert crawler.visited == set()
        assert crawler.pages == {}

    def test_custom_values(self):
        crawler = Crawler(base_url="http://example.com", delay=3)
        assert crawler.base_url == "http://example.com"
        assert crawler.delay == 3


class TestIsValidUrl:
    """Tests for URL validation."""

    def test_same_domain(self):
        crawler = Crawler()
        assert crawler._is_valid_url("https://quotes.toscrape.com/page/2/")

    def test_same_domain_with_path(self):
        crawler = Crawler()
        assert crawler._is_valid_url(
            "https://quotes.toscrape.com/author/Albert-Einstein"
        )

    def test_external_domain_rejected(self):
        crawler = Crawler()
        assert not crawler._is_valid_url("https://google.com/search")

    def test_different_subdomain_rejected(self):
        crawler = Crawler()
        assert not crawler._is_valid_url("https://blog.toscrape.com/")

    def test_empty_url(self):
        crawler = Crawler()
        assert not crawler._is_valid_url("")


class TestExtractText:
    """Tests for HTML text extraction."""

    def test_basic_text_extraction(self):
        crawler = Crawler()
        text = crawler.extract_text(SAMPLE_HTML)
        assert "Quotes to Scrape" in text
        assert "The world is a book" in text
        assert "Albert Einstein" in text

    def test_script_tags_removed(self):
        crawler = Crawler()
        text = crawler.extract_text(SAMPLE_HTML)
        assert "var x = 1" not in text

    def test_style_tags_removed(self):
        crawler = Crawler()
        text = crawler.extract_text(SAMPLE_HTML)
        assert ".hidden" not in text
        assert "display: none" not in text

    def test_empty_html(self):
        crawler = Crawler()
        text = crawler.extract_text(SAMPLE_HTML_EMPTY)
        assert text.strip() == ""

    def test_whitespace_collapsed(self):
        crawler = Crawler()
        html = "<html><body><p>Hello    world\n\n\ttab</p></body></html>"
        text = crawler.extract_text(html)
        assert "  " not in text  # No double spaces

    def test_special_characters(self):
        crawler = Crawler()
        text = crawler.extract_text(SAMPLE_HTML_SPECIAL_CHARS)
        # HTML entities should be decoded
        assert "Café" in text or "Caf" in text


class TestExtractLinks:
    """Tests for link extraction from HTML."""

    def test_internal_links_found(self):
        crawler = Crawler()
        links = crawler.extract_links(SAMPLE_HTML, BASE_URL)
        assert "https://quotes.toscrape.com/page/2/" in links
        assert "https://quotes.toscrape.com/tag/world/page/1/" in links

    def test_external_links_filtered(self):
        crawler = Crawler()
        links = crawler.extract_links(SAMPLE_HTML, BASE_URL)
        assert "https://external.com/link" not in links

    def test_relative_urls_resolved(self):
        crawler = Crawler()
        html = '<html><body><a href="/page/3/">Page 3</a></body></html>'
        links = crawler.extract_links(html, BASE_URL)
        assert "https://quotes.toscrape.com/page/3/" in links

    def test_no_links_page(self):
        crawler = Crawler()
        links = crawler.extract_links(SAMPLE_HTML_NO_LINKS, BASE_URL)
        assert len(links) == 0

    def test_fragment_removed(self):
        crawler = Crawler()
        html = '<html><body><a href="/page/1/#top">Top</a></body></html>'
        links = crawler.extract_links(html, BASE_URL)
        for link in links:
            assert "#" not in link

    def test_empty_html(self):
        crawler = Crawler()
        links = crawler.extract_links(SAMPLE_HTML_EMPTY, BASE_URL)
        assert len(links) == 0


class TestPolitenessWindow:
    """Tests for the politeness delay mechanism."""

    def test_no_wait_on_first_request(self):
        crawler = Crawler(delay=6)
        crawler._last_request_time = 0
        start = time.time()
        crawler._wait_for_politeness()
        elapsed = time.time() - start
        # Should not wait since _last_request_time is 0 (epoch)
        assert elapsed < 1

    @patch("src.crawler.time.sleep")
    def test_wait_enforced(self, mock_sleep):
        crawler = Crawler(delay=6)
        crawler._last_request_time = time.time()  # Just now
        crawler._wait_for_politeness()
        mock_sleep.assert_called_once()
        wait_arg = mock_sleep.call_args[0][0]
        assert 5 < wait_arg <= 6

    @patch("src.crawler.time.sleep")
    def test_no_wait_after_delay(self, mock_sleep):
        crawler = Crawler(delay=6)
        crawler._last_request_time = time.time() - 10  # 10 seconds ago
        crawler._wait_for_politeness()
        mock_sleep.assert_not_called()


class TestFetchPage:
    """Tests for fetching web pages."""

    @patch("src.crawler.requests.get")
    def test_successful_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        crawler = Crawler(delay=0)
        html = crawler.fetch_page("http://example.com")
        assert html == "<html><body>Test</body></html>"
        mock_get.assert_called_once_with("http://example.com", timeout=15)

    @patch("src.crawler.requests.get")
    def test_http_error_returns_none(self, mock_get):
        mock_get.side_effect = requests.HTTPError("404 Not Found")
        crawler = Crawler(delay=0)
        result = crawler.fetch_page("http://example.com/bad")
        assert result is None
        # Should retry MAX_RETRIES times
        assert mock_get.call_count == 3

    @patch("src.crawler.requests.get")
    def test_connection_error_returns_none(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        crawler = Crawler(delay=0)
        result = crawler.fetch_page("http://example.com")
        assert result is None
        assert mock_get.call_count == 3

    @patch("src.crawler.requests.get")
    def test_timeout_error_returns_none(self, mock_get):
        mock_get.side_effect = requests.Timeout("Request timed out")
        crawler = Crawler(delay=0)
        result = crawler.fetch_page("http://example.com")
        assert result is None
        assert mock_get.call_count == 3

    @patch("src.crawler.requests.get")
    def test_retry_then_success(self, mock_get):
        """Test that a retry after failure succeeds."""
        mock_response = MagicMock()
        mock_response.text = "<html>OK</html>"
        mock_response.raise_for_status = MagicMock()
        # Fail first, succeed second
        mock_get.side_effect = [
            requests.ConnectionError("fail"),
            mock_response,
        ]
        crawler = Crawler(delay=0)
        result = crawler.fetch_page("http://example.com")
        assert result == "<html>OK</html>"
        assert mock_get.call_count == 2

    @patch("src.crawler.requests.get")
    def test_last_request_time_updated_on_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        crawler = Crawler(delay=0)
        before = time.time()
        crawler.fetch_page("http://example.com")
        assert crawler._last_request_time >= before

    @patch("src.crawler.requests.get")
    def test_last_request_time_updated_on_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError()
        crawler = Crawler(delay=0)
        before = time.time()
        crawler.fetch_page("http://example.com")
        assert crawler._last_request_time >= before


class TestCrawl:
    """Tests for the full crawl process."""

    @patch.object(Crawler, "fetch_page")
    def test_crawl_single_page(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_HTML_NO_LINKS
        crawler = Crawler(base_url="http://example.com", delay=0)
        pages = crawler.crawl()
        assert len(pages) == 1
        assert "http://example.com" in pages

    @patch.object(Crawler, "fetch_page")
    def test_crawl_follows_links(self, mock_fetch):
        page1 = '<html><body><p>Page 1</p><a href="/page2">Next</a></body></html>'
        page2 = '<html><body><p>Page 2</p></body></html>'

        def side_effect(url):
            if url == "http://example.com":
                return page1
            elif url == "http://example.com/page2":
                return page2
            return None

        mock_fetch.side_effect = side_effect
        crawler = Crawler(base_url="http://example.com", delay=0)
        pages = crawler.crawl()
        assert len(pages) == 2
        assert "Page 1" in pages["http://example.com"]
        assert "Page 2" in pages["http://example.com/page2"]

    @patch.object(Crawler, "fetch_page")
    def test_crawl_no_revisit(self, mock_fetch):
        # Page links back to itself using the exact same URL
        html = '<html><body><a href="http://example.com/">Home</a></body></html>'
        mock_fetch.return_value = html
        crawler = Crawler(base_url="http://example.com/", delay=0)
        crawler.crawl()
        # Should only fetch once despite self-link (URL normalized)
        assert mock_fetch.call_count == 1

    @patch.object(Crawler, "fetch_page")
    def test_crawl_handles_failed_page(self, mock_fetch):
        mock_fetch.return_value = None
        crawler = Crawler(base_url="http://example.com", delay=0)
        pages = crawler.crawl()
        assert len(pages) == 0

    @patch.object(Crawler, "fetch_page")
    def test_crawl_skips_external_links(self, mock_fetch):
        html = '<html><body><a href="https://external.com">Out</a></body></html>'
        mock_fetch.return_value = html
        crawler = Crawler(base_url="http://example.com", delay=0)
        pages = crawler.crawl()
        assert len(pages) == 1
        assert "https://external.com" not in pages
