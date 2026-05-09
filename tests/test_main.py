"""
Tests for the main CLI module.

Covers: all CLI commands (build, load, print, find, quit),
unknown commands, empty input, and error handling.
"""

from unittest.mock import patch, MagicMock

import pytest

from src.main import main


class TestCLI:
    """Tests for the command-line interface."""

    @patch("builtins.input", side_effect=["quit"])
    def test_quit_command(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "Goodbye" in output

    @patch("builtins.input", side_effect=["exit"])
    def test_exit_command(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "Goodbye" in output

    @patch("builtins.input", side_effect=["", "quit"])
    def test_empty_input_ignored(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "Goodbye" in output

    @patch("builtins.input", side_effect=["unknown_cmd", "quit"])
    def test_unknown_command(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "Unknown command" in output

    @patch("builtins.input", side_effect=["print", "quit"])
    def test_print_no_args(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "Usage" in output

    @patch("builtins.input", side_effect=["find", "quit"])
    def test_find_no_args(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "Usage" in output

    @patch("builtins.input", side_effect=["print hello", "quit"])
    def test_print_word_without_index(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "not found" in output

    @patch("builtins.input", side_effect=["find hello", "quit"])
    def test_find_word_without_index(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "not found" in output

    @patch("builtins.input", side_effect=EOFError)
    def test_eof_handling(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "Goodbye" in output

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_keyboard_interrupt(self, mock_input, capsys):
        main()
        output = capsys.readouterr().out
        assert "Goodbye" in output

    @patch("builtins.input", side_effect=["load", "quit"])
    def test_load_without_index_file(self, mock_input, capsys):
        """Load should fail gracefully when no index file exists."""
        main()
        output = capsys.readouterr().out
        # Should either show error or still work without crash

    @patch("builtins.input", side_effect=["BUILD", "quit"])
    @patch("src.main.Crawler")
    def test_build_command(self, mock_crawler_class, mock_input, capsys):
        """Test build command with mocked crawler."""
        mock_crawler = MagicMock()
        mock_crawler.crawl.return_value = {
            "http://example.com": "hello world"
        }
        mock_crawler_class.return_value = mock_crawler

        with patch("src.main.Indexer") as mock_indexer_class:
            mock_indexer = MagicMock()
            mock_indexer_class.return_value = mock_indexer

            main()
            mock_crawler.crawl.assert_called_once()
            mock_indexer.build_from_pages.assert_called_once()
            mock_indexer.save.assert_called_once()
