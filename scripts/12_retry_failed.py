"""
12_retry_failed.py
Retry failed pages with longer timeout and different approach.
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import asyncio
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

# Failed URLs from previous run
FAILED_URLS = [
    "https://www.digital-finance-msca.com/copy-of-home",
    "https://www.digital-finance-msca.com/event-details-registration/msca-network-event-rb-event-2024-ai-in-financial-markets-research-forum",
    "https://www.digital-finance-msca.com/members-area/b-vanbraak/profile",
    "https://www.digital-finance-msca.com/members-area/brankahm/profile",
    "https://www.digital-finance-msca.com/members-area/f-s-bernard/profile",
    "https://www.digital-finance-msca.com/work-package-1",
    "https://www.digital-finance-msca.com/work-package-4",
    "https://www.digital-finance-msca.com/work-package-5",
]


def url_to_filepath(url):
    parsed = urlparse(url)
    path = unquote(parsed.path.strip('/'))

    if not path:
        return CONTENT_DIR / "_index.md"

    parts = path.split('/')

    if len(parts) == 1:
        return CONTENT_DIR / f"{parts[0]}.md"
    elif parts[0] == 'members-area':
        if len(parts) >= 3:
            return CONTENT_DIR / "members-area" / parts[1] / f"{parts[2]}.md"
        elif len(parts) == 2:
            return CONTENT_DIR / "members-area" / f"{parts[1]}.md"
        else:
            return CONTENT_DIR / "members-area" / "_index.md"
    elif parts[0] == 'event-details-registration':
        return CONTENT_DIR / "events" / f"{parts[-1]}.md"
    else:
        return CONTENT_DIR / f"{parts[-1]}.md"


def extract_content(html, url):
    soup = BeautifulSoup(html, 'html.parser')

    for element in soup(['script', 'style', 'noscript', 'iframe']):
        element.decompose()

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

    title = ""
    title_elem = soup.select_one('h1') or soup.select_one('title')
    if title_elem:
        title = title_elem.get_text(strip=True)

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


def create_markdown(data, url, filepath):
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


async def scrape_page_with_retry(page, url, max_retries=2):
    for attempt in range(max_retries):
        try:
            # Use domcontentloaded instead of networkidle for faster loading
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(5000)  # Wait for JS to render

            # Scroll to trigger lazy loading
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)

            html = await page.content()
            return extract_content(html, url)
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {str(e)[:50]}")
            if attempt < max_retries - 1:
                await page.wait_for_timeout(2000)
    return None


async def main():
    print("=" * 60)
    print("Retrying Failed Pages with Extended Timeout")
    print("=" * 60)
    print(f"\n{len(FAILED_URLS)} pages to retry")

    results = {'retried': [], 'still_failed': []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        for i, url in enumerate(FAILED_URLS, 1):
            print(f"\n[{i}/{len(FAILED_URLS)}] {url}")

            data = await scrape_page_with_retry(page, url)

            if data and data['content']:
                filepath = url_to_filepath(url)

                if filepath.exists():
                    print(f"  Already exists, skipping")
                    continue

                create_markdown(data, url, filepath)
                print(f"  Created: {filepath.relative_to(PROJECT_ROOT)}")
                print(f"  Title: {data['title'][:50]}...")
                print(f"  Content: {len(data['content'])} chars")

                results['retried'].append({
                    'url': url,
                    'file': str(filepath.relative_to(PROJECT_ROOT)),
                    'content_length': len(data['content'])
                })
            else:
                print(f"  Still failed")
                results['still_failed'].append(url)

            await page.wait_for_timeout(1000)

        await browser.close()

    print("\n" + "=" * 60)
    print("RETRY RESULTS")
    print("=" * 60)
    print(f"  Successfully retried: {len(results['retried'])}")
    print(f"  Still failed: {len(results['still_failed'])}")

    if results['still_failed']:
        print("\nStill failing URLs:")
        for url in results['still_failed']:
            print(f"  - {url}")

    output_file = DATA_DIR / "retry_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
