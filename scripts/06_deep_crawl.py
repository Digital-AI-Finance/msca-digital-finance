"""
06_deep_crawl.py
Recursively crawls the website to discover ALL internal links,
comparing against already-scraped URLs to find missing pages.
"""

import sys
import io

# Fix Windows console encoding for Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import asyncio
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin
from collections import deque

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.run(["pip", "install", "playwright"])
    subprocess.run(["playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

from bs4 import BeautifulSoup

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

BASE_URL = "https://www.digital-finance-msca.com"
BASE_DOMAIN = "digital-finance-msca.com"


def load_scraped_urls():
    """Load already scraped URLs from progress file."""
    progress_file = DATA_DIR / "scrape_progress.json"
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('scraped_urls', []))
    return set()


def load_sitemap_urls():
    """Load all URLs from the sitemap discovery."""
    urls_file = DATA_DIR / "urls.json"
    if urls_file.exists():
        with open(urls_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_urls = set()
            for category, urls in data.get('categories', {}).items():
                for url_entry in urls:
                    all_urls.add(url_entry['url'])
            return all_urls
    return set()


def normalize_url(url):
    """Normalize URL for comparison."""
    parsed = urlparse(url)
    # Remove trailing slashes, fragments, and query strings
    path = parsed.path.rstrip('/')
    if not path:
        path = '/'
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def is_internal_url(url):
    """Check if URL is internal to the target domain."""
    if not url:
        return False
    parsed = urlparse(url)
    # Handle relative URLs
    if not parsed.netloc:
        return True
    return BASE_DOMAIN in parsed.netloc


def is_valid_page_url(url):
    """Check if URL is a valid page (not an asset)."""
    if not url:
        return False

    # Skip common non-page extensions
    skip_extensions = [
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
        '.css', '.js', '.ico', '.woff', '.woff2', '.ttf', '.eot',
        '.mp4', '.mp3', '.wav', '.avi', '.mov',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.rar', '.tar', '.gz'
    ]

    parsed = urlparse(url)
    path_lower = parsed.path.lower()

    for ext in skip_extensions:
        if path_lower.endswith(ext):
            return False

    # Skip Wix system URLs
    skip_patterns = [
        '/_functions/',
        '/_api/',
        '/sitemap',
        '/robots.txt',
        '/favicon',
        '/_partials/',
    ]

    for pattern in skip_patterns:
        if pattern in parsed.path:
            return False

    return True


async def extract_links(page, base_url):
    """Extract all internal links from the current page."""
    links = set()

    try:
        # Get all anchor elements
        anchors = await page.query_selector_all('a[href]')

        for anchor in anchors:
            try:
                href = await anchor.get_attribute('href')
                if href:
                    # Convert relative to absolute
                    full_url = urljoin(base_url, href)

                    if is_internal_url(full_url) and is_valid_page_url(full_url):
                        normalized = normalize_url(full_url)
                        links.add(normalized)
            except Exception:
                continue
    except Exception as e:
        print(f"  Error extracting links: {e}")

    return links


async def crawl_page(page, url):
    """Crawl a single page and extract links."""
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(2000)  # Wait for JS rendering

        links = await extract_links(page, url)
        return links, True
    except Exception as e:
        print(f"  Error crawling {url}: {e}")
        return set(), False


async def deep_crawl():
    """Perform deep crawl of the website."""
    print("=" * 60)
    print("Deep Crawl - Finding Missing Pages")
    print("=" * 60)

    # Load existing data
    scraped_urls = load_scraped_urls()
    sitemap_urls = load_sitemap_urls()

    print(f"\nAlready scraped: {len(scraped_urls)} URLs")
    print(f"From sitemaps: {len(sitemap_urls)} URLs")

    # Normalize all known URLs
    known_urls = set()
    for url in scraped_urls:
        known_urls.add(normalize_url(url))
    for url in sitemap_urls:
        known_urls.add(normalize_url(url))

    # BFS crawl
    visited = set()
    discovered = set()
    queue = deque([BASE_URL])
    visited.add(normalize_url(BASE_URL))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        crawl_count = 0
        max_pages = 500  # Safety limit

        print("\nStarting deep crawl...")
        print("-" * 60)

        while queue and crawl_count < max_pages:
            url = queue.popleft()
            crawl_count += 1

            print(f"\n[{crawl_count}] Crawling: {url[:70]}...")

            links, success = await crawl_page(page, url)

            if success:
                discovered.add(normalize_url(url))

                # Add new links to queue
                new_links = 0
                for link in links:
                    normalized = normalize_url(link)
                    if normalized not in visited:
                        visited.add(normalized)
                        queue.append(link)
                        new_links += 1

                print(f"  Found {len(links)} links, {new_links} new")

            # Rate limiting
            await page.wait_for_timeout(300)

        await browser.close()

    # Find missing URLs (discovered but not in sitemaps/scraped)
    missing_urls = discovered - known_urls

    # Also check which sitemap URLs weren't discovered (orphaned)
    orphaned_urls = sitemap_urls - discovered

    print("\n" + "=" * 60)
    print("DEEP CRAWL RESULTS")
    print("=" * 60)
    print(f"  Pages crawled: {crawl_count}")
    print(f"  Total discovered: {len(discovered)}")
    print(f"  Known URLs: {len(known_urls)}")
    print(f"  Missing (not in sitemaps): {len(missing_urls)}")
    print(f"  Orphaned (in sitemap but not linked): {len(orphaned_urls)}")

    # Save results
    results = {
        'crawl_date': datetime.now().isoformat(),
        'pages_crawled': crawl_count,
        'total_discovered': len(discovered),
        'known_urls': len(known_urls),
        'missing_urls': sorted(list(missing_urls)),
        'orphaned_urls': sorted(list(orphaned_urls)),
        'all_discovered': sorted(list(discovered))
    }

    output_file = DATA_DIR / "deep_crawl_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")

    if missing_urls:
        print("\n" + "-" * 60)
        print("MISSING URLS (need to scrape):")
        print("-" * 60)
        for url in sorted(missing_urls)[:30]:  # Show first 30
            print(f"  - {url}")
        if len(missing_urls) > 30:
            print(f"  ... and {len(missing_urls) - 30} more")

    return results


if __name__ == "__main__":
    asyncio.run(deep_crawl())
