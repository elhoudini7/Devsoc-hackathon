import requests
from bs4 import BeautifulSoup
import json
import time
import os

# --- CONFIGURATION ---
INPUT_FILE = "urls.txt"
OUTPUT_DIR = "scraped_data"
BATCH_SIZE = 150  # Save to disk every 150 pages
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def clean_text(soup):
    """
    Extracts relevant text from the MediaWiki content area.
    Removes scripts, styles, and navigation junk.
    """
    # 1. Find the main content area
    content = soup.find('div', id='mw-content-text')
    if not content:
        return ""

    # 2. Remove unwanted elements (Javascript, CSS, Tables of Contents)
    for script in content(["script", "style", "aside", "nav", "div.toc"]):
        script.extract()

    # 3. Get text with specific separator to keep paragraph structure
    text = content.get_text(separator="\n", strip=True)

    return text


def scrape_in_batches():
    # 1. Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. Load URLs
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found. Run fetch.py first!")
        return

    total_urls = len(urls)
    print(f"Loaded {total_urls} URLs. Starting scrape...")

    batch_data = []
    batch_index = 1

    for i, url in enumerate(urls):
        try:
            print(f"[{i+1}/{total_urls}] Scraping: {url}")
            response = requests.get(url, headers=HEADERS, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract Title
                title_tag = soup.find('h1', id='firstHeading')
                title = title_tag.text.strip() if title_tag else "Unknown Title"

                # Extract Clean Text
                body_text = clean_text(soup)

                # Only save if we actually got text
                if body_text:
                    page_data = {
                        "url": url,
                        "title": title,
                        "content": body_text
                    }
                    batch_data.append(page_data)
            else:
                print(f"Failed (Status {response.status_code}): {url}")

        except Exception as e:
            print(f"Error scraping {url}: {e}")

        # --- BATCH SAVING ---
        # Save if batch is full OR if it's the very last URL
        if len(batch_data) >= BATCH_SIZE or (i + 1) == total_urls:
            filename = f"{OUTPUT_DIR}/batch_{batch_index}.json"

            with open(filename, "w", encoding="utf-8") as out_f:
                json.dump(batch_data, out_f, indent=4, ensure_ascii=False)

            print(
                f"Saved batch {batch_index} to {filename} ({len(batch_data)} pages)")

            batch_data = []  # Reset buffer
            batch_index += 1

        # Rate limiting (be polite)
        time.sleep(0.2)

    print("\nScraping Complete!")


if __name__ == "__main__":
    scrape_in_batches()
