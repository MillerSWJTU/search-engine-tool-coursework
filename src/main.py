"""
Search Engine CLI

Command-line interface providing build, load, print, and find commands.
"""

from src.crawler import Crawler
from src.indexer import Indexer
from src.search import SearchEngine


def main():
    """Run the interactive search engine shell."""
    indexer = Indexer()
    search_engine = SearchEngine(indexer)

    print("=" * 50)
    print("  Search Engine Tool — quotes.toscrape.com")
    print("=" * 50)
    print("Commands: build, load, print <word>, find <words>, quit")
    print()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "build":
            crawler = Crawler()
            pages = crawler.crawl()
            indexer.build_from_pages(pages)
            indexer.save()

        elif command == "load":
            indexer.load()

        elif command == "print":
            if not args:
                print("Usage: print <word>")
            else:
                search_engine.print_word(args)

        elif command == "find":
            if not args:
                print("Usage: find <word1> [word2] ...")
            else:
                search_engine.find(args)

        elif command == "quit" or command == "exit":
            print("Goodbye!")
            break

        else:
            print(f"Unknown command: '{command}'")
            print("Commands: build, load, print <word>, find <words>, quit")


if __name__ == "__main__":
    main()
