"""
16_download_all.py
Step 2: Download ALL missing pages from the collected URLs.
Reads from all_discovered_urls.json and downloads any missing content.
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import re
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote

try:
    from playwright.async_api import async_playwright
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "playwright"])
    subprocess.run(["playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images" / "general"

BASE_URL = "https://www.digital-finance-msca.com"


def load_missing_urls():
    """Load missing URLs from Step 1 output."""
    urls_file = DATA_DIR / "all_discovered_urls.json"
    if not urls_file.exists():
        print("ERROR: Run 15_collect_all_urls.py first!")
        return []

    with open(urls_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get('missing_urls', [])


def url_to_filepath(url):
    """Convert URL to local file path."""
    parsed = urlparse(url)
    path = unquote(parsed.path.strip('/'))

    if not path:
        return CONTENT_DIR / "_index.md"

    parts = path.split('/')

    # Handle different URL patterns
    if len(parts) == 1:
        return CONTENT_DIR / f"{parts[0]}.md"
    elif parts[0] in ['people', 'partner-new', 'partners', 'blog', 'post',
                       'training-modules', 'training-events', 'events',
                       'event-details-registration', 'members-area']:
        category = parts[0]
        if category == 'partner-new':
            category = 'partners'
        elif category == 'post':
            category = 'blog'
        elif category == 'event-details-registration':
            category = 'events'

        slug = parts[-1]
        return CONTENT_DIR / category / f"{slug}.md"
    else:
        return CONTENT_DIR / f"{path.replace('/', '_')}.md"


def extract_content(html, url):
    """Extract content from HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove unwanted elements
    for element in soup(['script', 'style', 'noscript', 'iframe']):
        element.decompose()

    # Find title
    title = ""
    title_elem = soup.select_one('h1') or soup.select_one('title')
    if title_elem:
        title = title_elem.get_text(strip=True)

    # Find main content
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

    # Extract text
    text_content = main_content.get_text(separator='\n', strip=True)
    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    text_content = '\n\n'.join(lines)

    # Extract images
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


def create_markdown(data, url, filepath):
    """Create markdown file."""
    front_matter = f"""---
title: "{data['title'].replace('"', '\\"')}"
date: {datetime.now().strftime('%Y-%m-%d')}
original_url: "{url}"
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


async def scrape_and_save(page, url, session):
    """Scrape a URL and save content."""
    filepath = url_to_filepath(url)

    # Skip if already exists
    if filepath.exists():
        return {'url': url, 'status': 'exists', 'file': str(filepath)}

    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(3000)

        # Scroll to load lazy content
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(1000)

        html = await page.content()
        data = extract_content(html, url)

        if data['content'] and len(data['content']) > 20:
            create_markdown(data, url, filepath)

            # Download images
            images_downloaded = 0
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            for img_url in data['images'][:10]:  # Limit images per page
                result = await download_image(session, img_url, IMAGES_DIR)
                if result:
                    images_downloaded += 1

            return {
                'url': url,
                'status': 'downloaded',
                'file': str(filepath.relative_to(PROJECT_ROOT)),
                'title': data['title'][:50],
                'content_length': len(data['content']),
                'images': images_downloaded
            }
        else:
            return {'url': url, 'status': 'empty', 'content_length': len(data.get('content', ''))}

    except Exception as e:
        return {'url': url, 'status': 'error', 'error': str(e)[:50]}


async def main():
    print("=" * 70)
    print("STEP 2: DOWNLOADING ALL MISSING PAGES")
    print("=" * 70)

    # Load missing URLs
    missing_urls = load_missing_urls()

    if not missing_urls:
        print("\nNo missing URLs to download!")
        print("All pages are already downloaded.")
        return

    print(f"\nFound {len(missing_urls)} URLs to download")

    results = {
        'download_date': datetime.now().isoformat(),
        'total_urls': len(missing_urls),
        'downloaded': [],
        'exists': [],
        'empty': [],
        'errors': []
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        async with aiohttp.ClientSession() as session:
            print("\n" + "-" * 70)
            print("Downloading...")
            print("-" * 70)

            for i, url in enumerate(missing_urls, 1):
                print(f"\n[{i}/{len(missing_urls)}] {url[:60]}...")

                result = await scrape_and_save(page, url, session)

                if result['status'] == 'downloaded':
                    results['downloaded'].append(result)
                    print(f"  OK: {result.get('file', 'saved')} ({result.get('content_length', 0)} chars)")
                elif result['status'] == 'exists':
                    results['exists'].append(result)
                    print(f"  Already exists")
                elif result['status'] == 'empty':
                    results['empty'].append(result)
                    print(f"  Empty/minimal content")
                else:
                    results['errors'].append(result)
                    print(f"  Error: {result.get('error', 'unknown')}")

                # Rate limiting
                await page.wait_for_timeout(1000)

        await browser.close()

    # Save results
    output_file = DATA_DIR / "download_complete_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"  Total URLs: {len(missing_urls)}")
    print(f"  Downloaded: {len(results['downloaded'])}")
    print(f"  Already existed: {len(results['exists'])}")
    print(f"  Empty content: {len(results['empty'])}")
    print(f"  Errors: {len(results['errors'])}")

    total_content = sum(r.get('content_length', 0) for r in results['downloaded'])
    total_images = sum(r.get('images', 0) for r in results['downloaded'])
    print(f"\n  Total content downloaded: {total_content:,} characters")
    print(f"  Total images downloaded: {total_images}")

    print(f"\nReport saved to: {output_file}")

    if results['errors']:
        print("\n" + "-" * 70)
        print("ERRORS:")
        print("-" * 70)
        for err in results['errors'][:10]:
            print(f"  - {err['url'][:50]}... : {err.get('error', 'unknown')}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
