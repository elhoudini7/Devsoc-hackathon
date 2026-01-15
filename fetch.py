import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# --- CONFIGURATION ---
START_URL = "https://wiki.metakgp.org/w/Special:AllPages/"
BASE_DOMAIN = "https://wiki.metakgp.org"
OUTPUT_FILE = "urls.txt"

# Fake being a real browser to avoid blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def get_all_urls():
    urls = []
    next_url = START_URL
    page_count = 1

    print(f"Starting crawl at: {START_URL}")

    while next_url:
        print(f"Scraping Index Page {page_count}...")

        try:
            response = requests.get(next_url, headers=HEADERS)

            # Debug: Check if we are actually getting the page
            if response.status_code != 200:
                print(
                    f"Critical Error: Server returned status {response.status_code}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')

            # METHOD 2: Broader Selection
            # Instead of looking for a specific class, look for the main content ID
            content_div = soup.find('div', id='mw-content-text')

            if content_div:
                # In 'Special:AllPages', links are usually in <li> tags or table cells
                # We grab ALL links inside the main content
                links = content_div.find_all('a')

                found_on_page = 0
                for link in links:
                    href = link.get('href')
                    text = link.text.strip()

                    # FILTERS:
                    # 1. Must have a title/text (avoid hidden links)
                    # 2. Must not be a navigational link (Next/Previous page)
                    # 3. Must not be Special/User/etc
                    if href and text and "Next page" not in text and "Previous page" not in text:
                        if not any(x in href for x in ["Special:", "User:", "File:", "Talk:", "Category:", "Template:", "action=edit"]):
                            full_url = urljoin(BASE_DOMAIN, href)
                            urls.append(full_url)
                            found_on_page += 1

                print(
                    f"  -> Found {found_on_page} potential links on this page.")
            else:
                print("  -> Warning: Could not find 'mw-content-text' div.")

            # 2. Find the "Next page" link strictly
            # It usually looks like: <a href="...">Next page (sdkljfh)</a>
            next_link = None

            # Search specifically for the text "Next page" in all links
            all_links = soup.find_all('a')
            for link in all_links:
                if "Next page" in link.text:
                    next_link = link.get('href')
                    break

            if next_link:
                next_url = urljoin(BASE_DOMAIN, next_link)
                page_count += 1
                time.sleep(0.5)
            else:
                print("Reached the last page (No 'Next page' link found).")
                next_url = None

        except Exception as e:
            print(f"Error: {e}")
            break

    # Remove duplicates
    unique_urls = list(set(urls))

    print(f"\nFinal Count: {len(unique_urls)} unique article URLs.")

    if len(unique_urls) == 0:
        print("DEBUG INFO: If this is still 0, the wiki structure might be very unique.")
        print("Try opening the START_URL in your browser to check if it loads.")
    else:
        # Save to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for url in unique_urls:
                f.write(url + "\n")
        print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    get_all_urls()
