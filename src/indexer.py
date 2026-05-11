"""
Inverted Index Builder

Builds an inverted index from crawled page content, storing
word frequency and position information for each page.
"""

import json
import os
import re
from typing import Optional


# Default file path for saving/loading the index
DEFAULT_INDEX_PATH: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "index.json",
)


class Indexer:
    """Builds and manages an inverted index from page content."""

    def __init__(self):
        # Inverted index structure:
        # {
        #   "word": {
        #       "url1": {"frequency": N, "positions": [0, 5, 12]},
        #       "url2": {"frequency": M, "positions": [3, 7]},
        #   }
        # }
        self.index: dict[str, dict[str, dict]] = {}
        # Total number of documents indexed
        self.doc_count: int = 0

    def tokenize(self, text: str) -> list[str]:
        """Split text into lowercase word tokens.

        Only keeps alphabetic words, strips punctuation and numbers.
        """
        words = re.findall(r"[a-zA-Z]+", text)
        return [w.lower() for w in words]

    def add_page(self, url: str, text: str) -> None:
        """Add a page's content to the inverted index.

        Args:
            url: The URL of the page.
            text: The text content of the page.
        """
        words = self.tokenize(text)
        self.doc_count += 1

        for position, word in enumerate(words):
            if word not in self.index:
                self.index[word] = {}
            if url not in self.index[word]:
                self.index[word][url] = {"frequency": 0, "positions": []}
            self.index[word][url]["frequency"] += 1
            self.index[word][url]["positions"].append(position)

    def build_from_pages(self, pages: dict[str, str]) -> None:
        """Build the inverted index from a dict of {url: text}.

        Args:
            pages: Dict mapping URL -> text content.
        """
        self.index = {}
        self.doc_count = 0
        for url, text in pages.items():
            self.add_page(url, text)
        print(f"Index built: {len(self.index)} unique words "
              f"from {self.doc_count} pages.")

    def save(self, filepath: Optional[str] = None) -> None:
        """Save the inverted index to a JSON file."""
        if filepath is None:
            filepath = DEFAULT_INDEX_PATH
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            "doc_count": self.doc_count,
            "index": self.index,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Index saved to {filepath}")

    def load(self, filepath: Optional[str] = None) -> bool:
        """Load the inverted index from a JSON file."""
        if filepath is None:
            filepath = DEFAULT_INDEX_PATH
        if not os.path.exists(filepath):
            print(f"Error: Index file not found at {filepath}")
            print("Please run 'build' first to create the index.")
            return False

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.index = data["index"]
        self.doc_count = data["doc_count"]
        print(f"Index loaded: {len(self.index)} unique words "
              f"from {self.doc_count} pages.")
        return True

    def get_word_info(self, word: str) -> Optional[dict[str, dict]]:
        """Get the inverted index entry for a specific word.

        Returns None if the word is not found.
        """
        return self.index.get(word.lower())
