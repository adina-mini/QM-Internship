"""
fetch_data.py
Pulls full public-domain texts of a set of philosophers/mystics from Project
Gutenberg, using the Gutendex API (a free JSON wrapper around Gutenberg's
catalog — no auth, no scraping). Strips Gutenberg's boilerplate header/footer
so only the actual book text is saved.

Source: https://gutendex.com/books/?search=<query>
    -> each result has a "formats" dict with a direct text/plain download URL

Usage:
    python fetch_data.py
"""

import os
import re
import sys
import time
import json
import requests

DATA_DIR = "data"
MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.json")

GUTENDEX_URL = "https://gutendex.com/books/"

# (author, display title, search query used to find the book on Gutenberg)
BOOKS = [
    (
        "Friedrich Nietzsche",
        "Thus Spoke Zarathustra",
        "thus spoke zarathustra nietzsche",
    ),
    ("Friedrich Nietzsche", "Beyond Good and Evil", "beyond good and evil nietzsche"),
    ("Jalal ad-Din Rumi", "The Masnavi I Ma'navi", "masnavi rumi"),
    ("Al-Ghazali", "The Alchemy of Happiness", "alchemy of happiness ghazali"),
    ("Marcus Aurelius", "Meditations", "meditations marcus aurelius"),
]

# Gutenberg wraps every book with boilerplate like:
# *** START OF THE PROJECT GUTENBERG EBOOK <title> ***
# ... actual text ...
# *** END OF THE PROJECT GUTENBERG EBOOK <title> ***
START_MARKER = re.compile(
    r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE
)
END_MARKER = re.compile(
    r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE
)


def strip_boilerplate(raw_text: str) -> str:
    """Cut Gutenberg's license header/footer, keep just the book body."""
    start_match = START_MARKER.search(raw_text)
    end_match = END_MARKER.search(raw_text)

    start_idx = start_match.end() if start_match else 0
    end_idx = end_match.start() if end_match else len(raw_text)

    if start_idx >= end_idx:
        # markers not found or out of order — better to keep the full text
        # than to silently return an empty file
        return raw_text.strip()

    return raw_text[start_idx:end_idx].strip()


def find_book(query: str, retries: int = 3) -> dict:
    """Search Gutendex and return the top match's metadata."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(GUTENDEX_URL, params={"search": query}, timeout=20)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                print(f"[warn] No Gutenberg match for '{query}'.")
                return None
            return results[0]

        except requests.exceptions.RequestException as e:
            wait = attempt * 2
            print(
                f"[retry {attempt}/{retries}] Search failed for '{query}': {e}. Waiting {wait}s."
            )
            time.sleep(wait)

    print(f"[fail] Giving up searching for '{query}'.")
    return None


def download_text(book_meta: dict, retries: int = 3) -> str:
    """Download the plain-text body of a book from its Gutendex 'formats' entry."""
    formats = book_meta.get("formats", {})
    text_url = None
    for key, url in formats.items():
        if key.startswith("text/plain"):
            text_url = url
            break

    if not text_url:
        print(f"[warn] No plain-text format available for '{book_meta.get('title')}'.")
        return None

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(text_url, timeout=30)
            resp.raise_for_status()
            resp.encoding = resp.encoding or "utf-8"
            return resp.text

        except requests.exceptions.RequestException as e:
            wait = attempt * 2
            print(f"[retry {attempt}/{retries}] Download failed: {e}. Waiting {wait}s.")
            time.sleep(wait)

    print(f"[fail] Could not download '{book_meta.get('title')}'.")
    return None


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    manifest = {}
    saved = 0

    for author, title, query in BOOKS:
        print(f"\nSearching Gutenberg for '{title}' ({author})...")
        book_meta = find_book(query)
        if not book_meta:
            continue

        raw_text = download_text(book_meta)
        if not raw_text:
            continue

        clean_text = strip_boilerplate(raw_text)
        if len(clean_text) < 1000:
            print(f"[warn] '{title}' text looks too short after stripping — skipping.")
            continue

        filename = f"{author.lower().replace(' ', '_')}__{title.lower().replace(' ', '_').replace(chr(39), '')}.txt"
        path = os.path.join(DATA_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(clean_text)

        manifest[filename] = {"author": author, "title": title}
        saved += 1
        print(f"[ok] Saved '{title}' -> {path} ({len(clean_text)} chars)")

    if saved == 0:
        sys.exit(
            "No books were saved — check your internet connection or search queries."
        )

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(
        f"\nDone. {saved}/{len(BOOKS)} books saved. Manifest written to '{MANIFEST_FILE}'."
    )


if __name__ == "__main__":
    main()
