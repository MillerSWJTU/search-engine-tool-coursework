"""
Search Engine Logic

Provides print and find functionality using the inverted index.
"""

from typing import Optional

from src.indexer import Indexer


class SearchEngine:
    """Search engine that queries the inverted index."""

    def __init__(self, indexer: Indexer):
        self.indexer = indexer

    def print_word(self, word: str) -> None:
        """Print the inverted index entry for a given word."""
        word = word.lower().strip()
        if not word:
            print("Error: Please provide a word to print.")
            return

        info = self.indexer.get_word_info(word)
        if info is None:
            print(f"Word '{word}' not found in the index.")
            return

        print(f"Inverted index for '{word}':")
        print(f"  Appears in {len(info)} page(s):")
        for url, stats in info.items():
            print(f"    URL: {url}")
            print(f"      Frequency: {stats['frequency']}")
            print(f"      Positions: {stats['positions']}")

    def find(self, query: str) -> list[str]:
        """Find pages containing all words in the query.

        For multi-word queries, returns pages where ALL words appear
        (intersection / AND logic).

        Args:
            query: A string of one or more search terms.

        Returns:
            A list of URLs containing all query terms, or empty list.
        """
        words = query.lower().split()
        if not words:
            print("Error: Please provide at least one search term.")
            return []

        # Get page sets for each word
        result_sets: list[set[str]] = []
        for word in words:
            info = self.indexer.get_word_info(word)
            if info is None:
                print(f"No results: word '{word}' not found in the index.")
                return []
            result_sets.append(set(info.keys()))

        # Intersect all sets to find pages containing ALL words
        result_urls = result_sets[0]
        for s in result_sets[1:]:
            result_urls = result_urls & s

        result_list = sorted(result_urls)

        if not result_list:
            print(f"No pages contain all the words: {', '.join(words)}")
        else:
            print(f"Found {len(result_list)} page(s) containing "
                  f"'{' '.join(words)}':")
            for url in result_list:
                print(f"  {url}")

        return result_list
