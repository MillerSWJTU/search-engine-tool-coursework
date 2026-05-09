"""
Web Crawler for quotes.toscrape.com

Crawls all pages of the website, extracts text content,
and discovers links while respecting a politeness window.
"""

import time
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# Base URL of the target website
BASE_URL = "https://quotes.toscrape.com/"
# Minimum delay between successive HTTP requests (seconds)
POLITENESS_DELAY = 6


class Crawler:
    """Crawls quotes.toscrape.com and collects page content."""

    def __init__(self, base_url=BASE_URL, delay=POLITENESS_DELAY):
        self.base_url = base_url
        self.delay = delay
        # Set of URLs already visited to avoid revisiting
        self.visited = set()
        # Dict mapping URL -> page text content
        self.pages = {}
        # Timestamp of the last HTTP request
        self._last_request_time = 0

    def _is_valid_url(self, url):
        """Check if the URL belongs to the target website."""
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        return parsed.netloc == base_parsed.netloc

    def _wait_for_politeness(self):
        """Enforce the politeness delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            wait_time = self.delay - elapsed
            print(f"  Waiting {wait_time:.1f}s (politeness window)...")
            time.sleep(wait_time)

    def fetch_page(self, url):
        """Fetch a single page and return its HTML content.

        Returns None if the request fails.
        """
        self._wait_for_politeness()
        try:
            response = requests.get(url, timeout=15)
            self._last_request_time = time.time()
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"  Error fetching {url}: {e}")
            self._last_request_time = time.time()
            return None

    def extract_text(self, html):
        """Extract visible text content from HTML, excluding scripts/styles."""
        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Collapse multiple whitespace into single spaces
        text = re.sub(r"\s+", " ", text)
        return text

    def extract_links(self, html, current_url):
        """Extract all internal links from the HTML page."""
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            # Resolve relative URLs to absolute
            full_url = urljoin(current_url, href)
            # Remove fragment identifiers
            full_url = full_url.split("#")[0]
            # Only keep URLs within the target domain
            if self._is_valid_url(full_url):
                links.add(full_url)
        return links

    def crawl(self):
        """Crawl the website starting from the base URL.

        Uses breadth-first traversal to discover and visit all pages.
        Returns a dict mapping URL -> extracted text content.
        """
        # Queue of URLs to visit
        queue = [self.base_url]
        self.visited = set()
        self.pages = {}

        print(f"Starting crawl from {self.base_url}")
        while queue:
            url = queue.pop(0)
            if url in self.visited:
                continue
            self.visited.add(url)

            print(f"Crawling: {url}")
            html = self.fetch_page(url)
            if html is None:
                continue

            # Store the extracted text for this page
            text = self.extract_text(html)
            self.pages[url] = text

            # Discover new links and add to queue
            links = self.extract_links(html, url)
            for link in links:
                if link not in self.visited:
                    queue.append(link)

        print(f"Crawl complete. Visited {len(self.pages)} pages.")
        return self.pages
