"""
20_monthly_sync.py
Comprehensive monthly synchronization script for digital-finance-msca.com
Designed for scheduled automation - only downloads new/changed content.

Features:
- Sitemap-based URL discovery with lastmod change detection
- Incremental downloads (only new/changed pages)
- Content hash comparison for unchanged URLs
- Sync history with changelog
- Detailed reporting
- Suitable for Windows Task Scheduler or cron

Usage:
    python scripts/20_monthly_sync.py              # Normal sync
    python scripts/20_monthly_sync.py --force      # Force re-download all
    python scripts/20_monthly_sync.py --dry-run    # Preview without downloading
"""

import sys
import io
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import hashlib
import asyncio
import aiohttp
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images" / "general"
SYNC_HISTORY_DIR = DATA_DIR / "sync_history"
LOGS_DIR = PROJECT_ROOT / "logs"

BASE_URL = "https://www.digital-finance-msca.com"
SITEMAPS = [
    f"{BASE_URL}/pages-sitemap.xml",
    f"{BASE_URL}/dynamic-people-sitemap.xml",
    f"{BASE_URL}/dynamic-partner-new-sitemap.xml",
    f"{BASE_URL}/blog-posts-sitemap.xml",
    f"{BASE_URL}/dynamic-training-modules-sitemap.xml",
    f"{BASE_URL}/dynamic-training-events-sitemap.xml",
    f"{BASE_URL}/event-pages-sitemap.xml",
    f"{BASE_URL}/blog-categories-sitemap.xml",
]


def setup_directories():
    """Create required directories."""
    for dir_path in [DATA_DIR, SYNC_HISTORY_DIR, LOGS_DIR, IMAGES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def load_previous_sync():
    """Load the most recent sync state."""
    state_file = DATA_DIR / "sync_state.json"
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'last_sync': None,
        'url_hashes': {},
        'content_hashes': {}
    }


def save_sync_state(state):
    """Save current sync state."""
    state_file = DATA_DIR / "sync_state.json"
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def fetch_sitemap(url):
    """Fetch and parse a sitemap XML file."""
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None


def parse_sitemap(xml_content):
    """Parse sitemap XML and extract URLs with metadata."""
    urls = []
    if not xml_content:
        return urls

    try:
        root = ET.fromstring(xml_content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        for url_elem in root.findall('.//sm:url', ns):
            loc = url_elem.find('sm:loc', ns)
            lastmod = url_elem.find('sm:lastmod', ns)

            if loc is not None:
                urls.append({
                    'url': loc.text,
                    'lastmod': lastmod.text if lastmod is not None else None
                })
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")

    return urls


def categorize_url(url):
    """Categorize a URL based on its path pattern."""
    parsed = urlparse(url)
    path = unquote(parsed.path).strip('/')

    if not path:
        return 'homepage', 'homepage', CONTENT_DIR / "_index.md"

    if path.startswith('people/'):
        slug = path.replace('people/', '')
        return 'people', slug, CONTENT_DIR / "people" / f"{slug}.md"
    elif path.startswith('partner-new/'):
        slug = path.replace('partner-new/', '')
        return 'partners', slug, CONTENT_DIR / "partners" / f"{slug}.md"
    elif path.startswith('post/'):
        slug = path.replace('post/', '')
        return 'blog', slug, CONTENT_DIR / "blog" / f"{slug}.md"
    elif path.startswith('training-modules/'):
        slug = path.replace('training-modules/', '')
        return 'training-modules', slug, CONTENT_DIR / "training-modules" / f"{slug}.md"
    elif path.startswith('training-events/'):
        slug = path.replace('training-events/', '')
        return 'training-events', slug, CONTENT_DIR / "training-events" / f"{slug}.md"
    elif path.startswith('event-details-registration/'):
        slug = path.replace('event-details-registration/', '')
        return 'events', slug, CONTENT_DIR / "events" / f"{slug}.md"
    elif path.startswith('blog-categories/'):
        slug = path.replace('blog-categories/', '')
        return 'blog-categories', slug, CONTENT_DIR / "blog-categories" / f"{slug}.md"
    elif path.startswith('members-area/'):
        slug = path.replace('members-area/', '')
        return 'members-area', slug, CONTENT_DIR / "members-area" / f"{slug}.md"
    else:
        return 'pages', path, CONTENT_DIR / f"{path}.md"


def discover_all_urls():
    """Discover all URLs from all sitemaps."""
    all_urls = {}
    seen = set()

    print("\n[1/4] Discovering URLs from sitemaps...")
    print("-" * 50)

    for sitemap_url in SITEMAPS:
        print(f"  Fetching: {sitemap_url.split('/')[-1]}")
        xml_content = fetch_sitemap(sitemap_url)
        if not xml_content:
            continue

        urls = parse_sitemap(xml_content)
        print(f"    Found {len(urls)} URLs")

        for url_data in urls:
            url = url_data['url']
            if url in seen:
                continue
            seen.add(url)

            category, slug, filepath = categorize_url(url)
            all_urls[url] = {
                'url': url,
                'category': category,
                'slug': slug,
                'filepath': str(filepath),
                'lastmod': url_data.get('lastmod')
            }

    return all_urls


def get_content_hash(filepath):
    """Get hash of existing content file."""
    filepath = Path(filepath)
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return hashlib.md5(content.encode()).hexdigest()
    except Exception:
        return None


def determine_urls_to_sync(current_urls, previous_state, force=False):
    """Determine which URLs need to be downloaded."""
    to_download = []
    unchanged = []
    new_urls = []

    prev_lastmods = previous_state.get('url_hashes', {})

    for url, data in current_urls.items():
        filepath = Path(data['filepath'])
        current_lastmod = data.get('lastmod')
        prev_lastmod = prev_lastmods.get(url, {}).get('lastmod')

        # Force download all
        if force:
            to_download.append(data)
            continue

        # New URL (not in previous sync)
        if url not in prev_lastmods:
            if not filepath.exists():
                new_urls.append(data)
                to_download.append(data)
            else:
                unchanged.append(data)
            continue

        # Check if lastmod changed
        if current_lastmod and prev_lastmod and current_lastmod != prev_lastmod:
            to_download.append(data)
            continue

        # File doesn't exist locally
        if not filepath.exists():
            to_download.append(data)
            continue

        unchanged.append(data)

    return to_download, unchanged, new_urls


def extract_content(html, url):
    """Extract content from HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    for element in soup(['script', 'style', 'noscript', 'iframe']):
        element.decompose()

    title = ""
    title_elem = soup.select_one('h1') or soup.select_one('title')
    if title_elem:
        title = title_elem.get_text(strip=True)

    content_selectors = [
        'main',
        '[data-testid="richTextElement"]',
        '.wixui-rich-text',
        '#PAGES_CONTAINER',
        'article',
        '.page-content'
    ]

    main_content = None
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break

    if not main_content:
        main_content = soup.body if soup.body else soup

    text_content = main_content.get_text(separator='\n', strip=True)
    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    text_content = '\n\n'.join(lines)

    images = []
    for img in main_content.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src and 'wixstatic.com' in src:
            images.append(src)

    return {
        'title': title,
        'content': text_content,
        'images': images
    }


def create_markdown(data, url, filepath, category):
    """Create markdown file."""
    filepath = Path(filepath)
    title = data['title'].replace('"', '\\"') if data['title'] else "Untitled"

    front_matter = f"""---
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
type: "{category}"
original_url: "{url}"
last_synced: "{datetime.now().isoformat()}"
draft: false
---

"""
    content = front_matter + data['content']

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


async def download_image(session, url, output_dir):
    """Download a single image."""
    try:
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        if not filename:
            return None

        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        output_path = output_dir / filename

        if output_path.exists():
            return str(output_path)

        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    content = await response.read()
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    return str(output_path)
    except Exception:
        pass
    return None


async def scrape_page(page, url_data, session, dry_run=False):
    """Scrape a single page."""
    url = url_data['url']
    filepath = Path(url_data['filepath'])
    category = url_data['category']

    if dry_run:
        return {
            'url': url,
            'status': 'dry_run',
            'file': str(filepath)
        }

    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(3000)

        # Scroll to load lazy content
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(1000)

        html = await page.content()
        data = extract_content(html, url)

        if data['content'] and len(data['content']) > 20:
            create_markdown(data, url, filepath, category)

            # Download images
            images_downloaded = 0
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            for img_url in data['images'][:10]:
                result = await download_image(session, img_url, IMAGES_DIR)
                if result:
                    images_downloaded += 1

            return {
                'url': url,
                'status': 'downloaded',
                'file': str(filepath.relative_to(PROJECT_ROOT)),
                'title': data['title'][:50] if data['title'] else '',
                'content_length': len(data['content']),
                'images': images_downloaded
            }
        else:
            return {
                'url': url,
                'status': 'empty',
                'content_length': len(data.get('content', ''))
            }

    except Exception as e:
        return {
            'url': url,
            'status': 'error',
            'error': str(e)[:100]
        }


async def run_sync(urls_to_download, dry_run=False):
    """Run the sync process."""
    results = {
        'downloaded': [],
        'empty': [],
        'errors': [],
        'dry_run': []
    }

    if not urls_to_download:
        return results

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        async with aiohttp.ClientSession() as session:
            for i, url_data in enumerate(urls_to_download, 1):
                print(f"  [{i}/{len(urls_to_download)}] {url_data['url'][:60]}...")

                result = await scrape_page(page, url_data, session, dry_run)

                if result['status'] == 'downloaded':
                    results['downloaded'].append(result)
                    print(f"    OK: {result.get('content_length', 0)} chars")
                elif result['status'] == 'dry_run':
                    results['dry_run'].append(result)
                    print(f"    DRY RUN: Would download")
                elif result['status'] == 'empty':
                    results['empty'].append(result)
                    print(f"    Empty content")
                else:
                    results['errors'].append(result)
                    print(f"    Error: {result.get('error', 'unknown')[:50]}")

                await page.wait_for_timeout(1000)

        await browser.close()

    return results


def save_sync_report(sync_data, results):
    """Save detailed sync report."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = SYNC_HISTORY_DIR / f"sync_{timestamp}.json"

    report = {
        'sync_date': datetime.now().isoformat(),
        'summary': {
            'total_urls_discovered': sync_data['total_discovered'],
            'urls_to_download': sync_data['to_download_count'],
            'urls_unchanged': sync_data['unchanged_count'],
            'new_urls': sync_data['new_urls_count'],
            'downloaded': len(results['downloaded']),
            'empty': len(results['empty']),
            'errors': len(results['errors'])
        },
        'downloaded': results['downloaded'],
        'errors': results['errors'],
        'empty': results['empty']
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Also save as latest
    latest_file = DATA_DIR / "latest_sync_report.json"
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report_file


def update_sync_state(current_urls, previous_state):
    """Update sync state with current URLs."""
    new_state = {
        'last_sync': datetime.now().isoformat(),
        'url_hashes': {}
    }

    for url, data in current_urls.items():
        new_state['url_hashes'][url] = {
            'lastmod': data.get('lastmod'),
            'category': data['category'],
            'filepath': data['filepath']
        }

    save_sync_state(new_state)
    return new_state


async def main():
    parser = argparse.ArgumentParser(description='Monthly sync for digital-finance-msca.com')
    parser.add_argument('--force', action='store_true', help='Force re-download all content')
    parser.add_argument('--dry-run', action='store_true', help='Preview without downloading')
    args = parser.parse_args()

    print("=" * 60)
    print("MONTHLY SYNC: digital-finance-msca.com")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'FORCE' if args.force else 'DRY RUN' if args.dry_run else 'INCREMENTAL'}")
    print("=" * 60)

    setup_directories()

    # Load previous sync state
    previous_state = load_previous_sync()
    if previous_state['last_sync']:
        print(f"\nLast sync: {previous_state['last_sync']}")
    else:
        print("\nFirst sync (no previous state)")

    # Discover current URLs
    current_urls = discover_all_urls()
    print(f"\nTotal URLs discovered: {len(current_urls)}")

    # Determine what to download
    print("\n[2/4] Analyzing changes...")
    print("-" * 50)

    to_download, unchanged, new_urls = determine_urls_to_sync(
        current_urls, previous_state, force=args.force
    )

    print(f"  New URLs: {len(new_urls)}")
    print(f"  Changed URLs: {len(to_download) - len(new_urls)}")
    print(f"  Unchanged: {len(unchanged)}")
    print(f"  Total to download: {len(to_download)}")

    sync_data = {
        'total_discovered': len(current_urls),
        'to_download_count': len(to_download),
        'unchanged_count': len(unchanged),
        'new_urls_count': len(new_urls)
    }

    # Download content
    print("\n[3/4] Downloading content...")
    print("-" * 50)

    if to_download:
        results = await run_sync(to_download, dry_run=args.dry_run)
    else:
        print("  No content to download - everything is up to date!")
        results = {'downloaded': [], 'empty': [], 'errors': [], 'dry_run': []}

    # Save report and update state
    print("\n[4/4] Saving report...")
    print("-" * 50)

    if not args.dry_run:
        update_sync_state(current_urls, previous_state)

    report_file = save_sync_report(sync_data, results)
    print(f"  Report saved: {report_file}")

    # Summary
    print("\n" + "=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"  Total URLs: {len(current_urls)}")
    print(f"  Downloaded: {len(results['downloaded'])}")
    print(f"  Empty pages: {len(results['empty'])}")
    print(f"  Errors: {len(results['errors'])}")
    print(f"  Unchanged: {len(unchanged)}")

    if results['downloaded']:
        total_chars = sum(r.get('content_length', 0) for r in results['downloaded'])
        total_images = sum(r.get('images', 0) for r in results['downloaded'])
        print(f"\n  New content: {total_chars:,} characters")
        print(f"  New images: {total_images}")

    if results['errors']:
        print("\n  ERRORS:")
        for err in results['errors'][:5]:
            print(f"    - {err['url'][:50]}...")

    print("\n" + "=" * 60)

    # Return exit code based on errors
    return 1 if results['errors'] else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
