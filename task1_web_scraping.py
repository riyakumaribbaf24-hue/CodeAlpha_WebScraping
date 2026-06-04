"""
CodeAlpha Internship — Task 1: Web Scraping
===========================================
Target  : https://books.toscrape.com  (a legal public sandbox for scraping practice)
Goal    : Scrape all books across all 50 pages — title, price, rating, availability,
          category — and save the result to a clean CSV ready for EDA.

Libraries: requests, BeautifulSoup4, pandas
Run     : pip install requests beautifulsoup4 pandas
          python task1_web_scraping.py
"""

import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL   = "https://books.toscrape.com"
CATALOGUE  = BASE_URL + "/catalogue/"
OUTPUT_CSV = "books_scraped.csv"
DELAY_SEC  = 0.5          # polite delay between requests
HEADERS    = {"User-Agent": "Mozilla/5.0 (educational scraping project)"}

# ── Rating word → integer map ─────────────────────────────────────────────────
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def get_soup(url: str) -> BeautifulSoup:
    """Fetch a page and return a BeautifulSoup object."""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def scrape_book_detail(book_url: str) -> dict:
    """
    Visit an individual book page and extract extra fields:
    description, UPC, number of reviews, and category.
    """
    soup = get_soup(book_url)

    # Category is the second-to-last breadcrumb link
    breadcrumbs = soup.select("ul.breadcrumb li a")
    category = breadcrumbs[-1].text.strip() if len(breadcrumbs) >= 2 else "Unknown"

    # Product information table
    table = {}
    for row in soup.select("table.table-striped tr"):
        key = row.th.text.strip()
        val = row.td.text.strip()
        table[key] = val

    description_tag = soup.select_one("article.product_page > p")
    description = description_tag.text.strip() if description_tag else ""

    return {
        "category"     : category,
        "upc"          : table.get("UPC", ""),
        "num_reviews"  : int(table.get("Number of reviews", "0")),
        "description"  : description,
    }


def scrape_listing_page(url: str) -> list[dict]:
    """Extract all book cards from a catalogue listing page."""
    soup  = get_soup(url)
    books = []

    for article in soup.select("article.product_pod"):
        # ── Basic fields from listing ──────────────────────────────────────
        title_tag    = article.select_one("h3 a")
        title        = title_tag["title"]
        relative_url = title_tag["href"].replace("../", "")
        book_url     = CATALOGUE + relative_url

        price_text   = article.select_one("p.price_color").text.strip()
        price        = float(price_text.replace("£", "").replace("Â", "").strip())

        rating_class = article.select_one("p.star-rating")["class"][1]
        rating       = RATING_MAP.get(rating_class, 0)

        availability = article.select_one("p.availability").text.strip()
        in_stock     = availability.lower() == "in stock"

        # ── Detailed fields from individual page ───────────────────────────
        time.sleep(DELAY_SEC)
        details = scrape_book_detail(book_url)

        books.append({
            "title"       : title,
            "price_gbp"   : price,
            "rating"      : rating,
            "in_stock"    : in_stock,
            "category"    : details["category"],
            "upc"         : details["upc"],
            "num_reviews" : details["num_reviews"],
            "description" : details["description"],
            "url"         : book_url,
        })

    return books


def get_next_page_url(current_url: str, soup: BeautifulSoup):
    """Return the absolute URL of the next page, or None if on the last page."""
    next_btn = soup.select_one("li.next a")
    if not next_btn:
        return None
    next_href = next_btn["href"]
    if "catalogue/" in current_url:
        base = current_url.rsplit("/", 1)[0]
        return base + "/" + next_href
    return CATALOGUE + next_href


def main():
    print("=" * 60)
    print("  CodeAlpha Task 1 — Web Scraping: Books to Scrape")
    print("=" * 60)

    all_books   = []
    current_url = BASE_URL
    page_number = 1

    while current_url:
        print(f"  Scraping page {page_number:>3} → {current_url}")
        soup  = get_soup(current_url)
        books = scrape_listing_page(current_url)
        all_books.extend(books)

        next_url    = get_next_page_url(current_url, soup)
        current_url = next_url
        page_number += 1
        time.sleep(DELAY_SEC)

    # ── Build DataFrame & save ─────────────────────────────────────────────
    df = pd.DataFrame(all_books)
    df.sort_values("category", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.to_csv(OUTPUT_CSV, index=False)

    print("\n" + "=" * 60)
    print(f"  Done! Scraped {len(df)} books across {page_number - 1} pages.")
    print(f"  Saved to: {OUTPUT_CSV}")
    print("=" * 60)
    print(df[["title", "price_gbp", "rating", "category"]].head(10).to_string(index=False))
    print(f"\n  Columns : {list(df.columns)}")
    print(f"  Shape   : {df.shape}")


if __name__ == "__main__":
    main()
