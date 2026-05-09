"""
Tests for the SearchEngine module.

Covers: single-word search, multi-word search (AND logic),
edge cases (empty queries, nonexistent words, special input),
and print functionality.
"""

import pytest

from src.indexer import Indexer
from src.search import SearchEngine


@pytest.fixture
def search_engine():
    """Create a SearchEngine with a pre-built index for testing."""
    indexer = Indexer()
    pages = {
        "http://page1.com": "the quick brown fox jumps over the lazy dog",
        "http://page2.com": "the quick red car drives fast",
        "http://page3.com": "a lazy cat sleeps all day",
        "http://page4.com": "good friends are hard to find",
    }
    indexer.build_from_pages(pages)
    return SearchEngine(indexer)


class TestFind:
    """Tests for the find command."""

    def test_single_word_found(self, search_engine):
        results = search_engine.find("quick")
        assert set(results) == {"http://page1.com", "http://page2.com"}

    def test_single_word_unique(self, search_engine):
        results = search_engine.find("fox")
        assert results == ["http://page1.com"]

    def test_multi_word_intersection(self, search_engine):
        results = search_engine.find("the quick")
        assert set(results) == {"http://page1.com", "http://page2.com"}

    def test_multi_word_narrow_results(self, search_engine):
        results = search_engine.find("quick brown")
        assert results == ["http://page1.com"]

    def test_word_not_found(self, search_engine):
        results = search_engine.find("elephant")
        assert results == []

    def test_one_word_missing_in_multi(self, search_engine):
        results = search_engine.find("quick elephant")
        assert results == []

    def test_case_insensitive(self, search_engine):
        results = search_engine.find("QUICK")
        assert set(results) == {"http://page1.com", "http://page2.com"}

    def test_mixed_case_multi_word(self, search_engine):
        results = search_engine.find("The QUICK")
        assert set(results) == {"http://page1.com", "http://page2.com"}

    def test_empty_query(self, search_engine):
        results = search_engine.find("")
        assert results == []

    def test_whitespace_only_query(self, search_engine):
        results = search_engine.find("   ")
        assert results == []

    def test_no_common_pages(self, search_engine):
        # "fox" is only on page1, "cat" is only on page3
        results = search_engine.find("fox cat")
        assert results == []

    def test_results_sorted(self, search_engine):
        results = search_engine.find("the")
        assert results == sorted(results)

    def test_all_pages_match(self, search_engine):
        # "the" is not on page3 or page4 actually, let's check
        indexer = Indexer()
        pages = {
            "http://a.com": "hello world",
            "http://b.com": "hello there",
            "http://c.com": "hello again",
        }
        indexer.build_from_pages(pages)
        se = SearchEngine(indexer)
        results = se.find("hello")
        assert len(results) == 3

    def test_find_with_word_from_assignment(self, search_engine):
        """Test the 'find good friends' example from the assignment."""
        results = search_engine.find("good friends")
        assert results == ["http://page4.com"]


class TestPrintWord:
    """Tests for the print command."""

    def test_print_existing_word(self, search_engine, capsys):
        search_engine.print_word("quick")
        output = capsys.readouterr().out
        assert "quick" in output
        assert "page1.com" in output
        assert "page2.com" in output
        assert "Frequency" in output
        assert "Positions" in output

    def test_print_nonexistent_word(self, search_engine, capsys):
        search_engine.print_word("elephant")
        output = capsys.readouterr().out
        assert "not found" in output

    def test_print_case_insensitive(self, search_engine, capsys):
        search_engine.print_word("QUICK")
        output = capsys.readouterr().out
        assert "quick" in output

    def test_print_empty_word(self, search_engine, capsys):
        search_engine.print_word("")
        output = capsys.readouterr().out
        assert "Error" in output or "provide" in output.lower()

    def test_print_whitespace_word(self, search_engine, capsys):
        search_engine.print_word("   ")
        output = capsys.readouterr().out
        assert "Error" in output or "provide" in output.lower()

    def test_print_shows_frequency(self, search_engine, capsys):
        search_engine.print_word("the")
        output = capsys.readouterr().out
        assert "Frequency: 2" in output  # "the" appears twice in page1

    def test_print_shows_positions(self, search_engine, capsys):
        search_engine.print_word("the")
        output = capsys.readouterr().out
        assert "Positions:" in output


class TestEdgeCases:
    """Edge case tests for search functionality."""

    def test_single_page_single_word(self):
        indexer = Indexer()
        indexer.add_page("http://only.com", "alone")
        se = SearchEngine(indexer)
        results = se.find("alone")
        assert results == ["http://only.com"]

    def test_empty_index(self):
        indexer = Indexer()
        se = SearchEngine(indexer)
        results = se.find("anything")
        assert results == []

    def test_large_number_of_words(self):
        indexer = Indexer()
        # Use only alphabetic words since tokenizer strips numbers
        words = ["alpha", "bravo", "charlie", "delta", "echo"] * 200
        text = " ".join(words)
        indexer.add_page("http://big.com", text)
        se = SearchEngine(indexer)
        results = se.find("charlie")
        assert results == ["http://big.com"]

    def test_same_word_many_pages(self):
        indexer = Indexer()
        for i in range(50):
            indexer.add_page(f"http://page{i}.com", "common word here")
        se = SearchEngine(indexer)
        results = se.find("common")
        assert len(results) == 50
