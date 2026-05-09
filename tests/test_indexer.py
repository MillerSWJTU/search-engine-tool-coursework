"""
Tests for the Indexer module.

Covers: tokenization, index building, word statistics,
save/load persistence, edge cases, and data integrity.
"""

import json
import os
import tempfile

import pytest

from src.indexer import Indexer


class TestTokenize:
    """Tests for text tokenization."""

    def test_basic_tokenization(self):
        indexer = Indexer()
        tokens = indexer.tokenize("Hello World")
        assert tokens == ["hello", "world"]

    def test_case_insensitive(self):
        indexer = Indexer()
        tokens = indexer.tokenize("HELLO Hello hElLo")
        assert tokens == ["hello", "hello", "hello"]

    def test_punctuation_stripped(self):
        indexer = Indexer()
        tokens = indexer.tokenize("Hello, world! How's it going?")
        assert tokens == ["hello", "world", "how", "s", "it", "going"]

    def test_numbers_stripped(self):
        indexer = Indexer()
        tokens = indexer.tokenize("Year 2024 is great")
        assert tokens == ["year", "is", "great"]

    def test_mixed_content(self):
        indexer = Indexer()
        tokens = indexer.tokenize("Email: test@example.com — price: $9.99")
        assert tokens == ["email", "test", "example", "com", "price"]

    def test_empty_string(self):
        indexer = Indexer()
        tokens = indexer.tokenize("")
        assert tokens == []

    def test_only_numbers_and_punctuation(self):
        indexer = Indexer()
        tokens = indexer.tokenize("123 !@# $%^")
        assert tokens == []

    def test_hyphenated_words(self):
        indexer = Indexer()
        tokens = indexer.tokenize("well-known self-esteem")
        assert tokens == ["well", "known", "self", "esteem"]


class TestAddPage:
    """Tests for adding pages to the index."""

    def test_single_word(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "hello")
        assert "hello" in indexer.index
        assert indexer.index["hello"]["http://example.com"]["frequency"] == 1
        assert indexer.index["hello"]["http://example.com"]["positions"] == [0]

    def test_repeated_word(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "hello hello hello")
        assert indexer.index["hello"]["http://example.com"]["frequency"] == 3
        assert indexer.index["hello"]["http://example.com"]["positions"] == [0, 1, 2]

    def test_multiple_words(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "the quick brown fox")
        assert len(indexer.index) == 4
        for word in ["the", "quick", "brown", "fox"]:
            assert word in indexer.index

    def test_multiple_pages(self):
        indexer = Indexer()
        indexer.add_page("http://page1.com", "hello world")
        indexer.add_page("http://page2.com", "hello there")
        assert len(indexer.index["hello"]) == 2
        assert "http://page1.com" in indexer.index["hello"]
        assert "http://page2.com" in indexer.index["hello"]

    def test_doc_count_incremented(self):
        indexer = Indexer()
        indexer.add_page("http://page1.com", "word")
        indexer.add_page("http://page2.com", "word")
        assert indexer.doc_count == 2

    def test_empty_page(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "")
        assert indexer.doc_count == 1
        assert len(indexer.index) == 0

    def test_position_tracking(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "the cat sat on the mat")
        info = indexer.index["the"]["http://example.com"]
        assert info["frequency"] == 2
        assert info["positions"] == [0, 4]


class TestBuildFromPages:
    """Tests for building index from a pages dict."""

    def test_build_basic(self):
        indexer = Indexer()
        pages = {
            "http://page1.com": "hello world",
            "http://page2.com": "hello there",
        }
        indexer.build_from_pages(pages)
        assert indexer.doc_count == 2
        assert "hello" in indexer.index
        assert len(indexer.index["hello"]) == 2

    def test_build_clears_previous(self):
        indexer = Indexer()
        indexer.add_page("http://old.com", "old data")
        pages = {"http://new.com": "new data"}
        indexer.build_from_pages(pages)
        assert "old" not in indexer.index
        assert "new" in indexer.index
        assert indexer.doc_count == 1

    def test_build_empty_pages(self):
        indexer = Indexer()
        indexer.build_from_pages({})
        assert indexer.doc_count == 0
        assert len(indexer.index) == 0


class TestGetWordInfo:
    """Tests for retrieving word information."""

    def test_existing_word(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "hello world")
        info = indexer.get_word_info("hello")
        assert info is not None
        assert "http://example.com" in info

    def test_nonexistent_word(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "hello world")
        info = indexer.get_word_info("xyz")
        assert info is None

    def test_case_insensitive_lookup(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "Hello")
        assert indexer.get_word_info("HELLO") is not None
        assert indexer.get_word_info("hello") is not None
        assert indexer.get_word_info("Hello") is not None


class TestSaveLoad:
    """Tests for index persistence (save and load)."""

    def test_save_and_load(self):
        indexer = Indexer()
        pages = {
            "http://page1.com": "hello world",
            "http://page2.com": "hello there",
        }
        indexer.build_from_pages(pages)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            indexer.save(filepath)

            # Load into a new indexer
            indexer2 = Indexer()
            result = indexer2.load(filepath)
            assert result is True
            assert indexer2.doc_count == 2
            assert indexer2.index == indexer.index
        finally:
            os.unlink(filepath)

    def test_load_nonexistent_file(self):
        indexer = Indexer()
        result = indexer.load("/nonexistent/path/index.json")
        assert result is False

    def test_save_creates_directory(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "test")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "subdir", "index.json")
            indexer.save(filepath)
            assert os.path.exists(filepath)

    def test_saved_file_valid_json(self):
        indexer = Indexer()
        indexer.add_page("http://example.com", "hello world")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            indexer.save(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "index" in data
            assert "doc_count" in data
            assert data["doc_count"] == 1
        finally:
            os.unlink(filepath)

    def test_data_integrity_after_load(self):
        """Verify word statistics are preserved after save/load cycle."""
        indexer = Indexer()
        indexer.add_page("http://example.com", "the cat sat on the mat")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            indexer.save(filepath)
            indexer2 = Indexer()
            indexer2.load(filepath)

            info = indexer2.get_word_info("the")
            assert info["http://example.com"]["frequency"] == 2
            assert info["http://example.com"]["positions"] == [0, 4]
        finally:
            os.unlink(filepath)
