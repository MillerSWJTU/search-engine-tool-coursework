# Search Engine Tool

A search engine tool that crawls, indexes, and searches [quotes.toscrape.com](https://quotes.toscrape.com/). Built for COMP/XJCO3011 Coursework 2.

## Architecture Overview

```
User Input (CLI)
      │
      ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│  main.py │────▶│crawler.py│────▶│indexer.py│
│   (CLI)  │     │ (Scraper)│     │ (Index)  │
└──────────┘     └──────────┘     └──────────┘
      │                                 │
      ▼                                 ▼
┌──────────┐                    ┌──────────────┐
│search.py │◀───────────────────│data/index.json│
│ (Query)  │                    └──────────────┘
└──────────┘
```

### Design Decisions

- **Inverted Index**: Uses a nested dictionary structure `{word: {url: {frequency, positions}}}` for O(1) word lookup and efficient multi-word AND queries via set intersection.
- **BFS Crawling**: Breadth-first traversal ensures all pages are discovered systematically, starting from the homepage.
- **Politeness Window**: 6-second delay between requests to respect the target server.
- **Retry Mechanism**: Failed HTTP requests are retried up to 3 times for robustness.
- **URL Normalization**: Prevents duplicate visits caused by trailing slash differences.
- **JSON Storage**: Human-readable format for the index file, easy to inspect and debug.

## Installation

```bash
# Clone the repository
git clone https://github.com/MillerSWJTU/search-engine-tool-coursework.git
cd search-engine-tool-coursework

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Dependencies

- `requests` — HTTP requests for web crawling
- `beautifulsoup4` — HTML parsing and text extraction
- `pytest` — Testing framework
- `pytest-cov` — Test coverage reporting

## Usage

Start the interactive shell:

```bash
python -m src.main
```

### Commands

#### `build`
Crawl the website, build the inverted index, and save it to `data/index.json`.

```
> build
Starting crawl from https://quotes.toscrape.com/
[1/1] Crawling: https://quotes.toscrape.com/
...
Crawl complete. Visited 214 pages.
Index built: 4327 unique words from 214 pages.
Index saved to data/index.json
```

#### `load`
Load a previously built index from the file system.

```
> load
Index loaded: 4327 unique words from 214 pages.
```

#### `print <word>`
Display the inverted index entry for a specific word.

```
> print nonsense
Inverted index for 'nonsense':
  Appears in 2 page(s):
    URL: https://quotes.toscrape.com/page/3/
      Frequency: 1
      Positions: [45]
    ...
```

#### `find <words>`
Search for pages containing all specified words (AND logic).

```
> find indifference
Found 3 page(s) containing 'indifference':
  https://quotes.toscrape.com/tag/indifference/page/1/
  ...

> find good friends
Found 5 page(s) containing 'good friends':
  https://quotes.toscrape.com/page/4/
  ...
```

### Edge Cases
- Non-existent words: `> find xyz` → "No results: word 'xyz' not found in the index."
- Empty query: `> find` → "Usage: find <word1> [word2] ..."
- Case insensitive: `> find GOOD` works the same as `> find good`

## Testing

Run the full test suite with coverage:

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### Test Summary

| Test File | Tests | Coverage |
|-----------|-------|----------|
| test_crawler.py | 36 | crawler.py: 99% |
| test_indexer.py | 26 | indexer.py: 98% |
| test_search.py | 24 | search.py: 100% |
| test_main.py | 11 | main.py: 98% |
| **Total** | **97** | **99%** |

### Testing Strategy

- **Unit tests**: Each module tested independently with mocked dependencies
- **Mock HTTP requests**: All crawler tests use `unittest.mock.patch` to avoid real network calls
- **Edge cases**: Empty inputs, non-existent words, special characters, large datasets
- **Data integrity**: Verify index correctness after save/load cycles
- **Error handling**: Network failures, missing files, invalid commands

## Project Structure

```
search-engine-tool-coursework/
├── src/
│   ├── __init__.py
│   ├── crawler.py      # Web crawler with BFS traversal
│   ├── indexer.py       # Inverted index builder and persistence
│   ├── search.py        # Search engine (print/find commands)
│   └── main.py          # CLI interactive shell
├── tests/
│   ├── __init__.py
│   ├── test_crawler.py  # 36 crawler tests
│   ├── test_indexer.py  # 26 indexer tests
│   ├── test_search.py   # 24 search tests
│   └── test_main.py     # 11 CLI tests
├── data/
│   └── index.json       # Pre-built inverted index
├── requirements.txt
└── README.md
```
