"""
11_scrape_missing.py
Scrapes missing pages discovered by deep crawl, including members-only pages.
Uses password authentication for protected content.
"""

import sys
import io

# Fix Windows console encoding for Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import re
import asyncio
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote

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
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"

BASE_URL = "https://www.digital-finance-msca.com"
MEMBER_PASSWORD = "DIGITAL2023"


def load_missing_urls():
    """Load missing URLs from deep crawl results."""
    crawl_file = DATA_DIR / "deep_crawl_results.json"
    if crawl_file.exists():
        with open(crawl_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('missing_urls', [])
    return []


def url_to_filepath(url):
    """Convert URL to content filepath."""
    parsed = urlparse(url)
    path = unquote(parsed.path.strip('/'))

    if not path:
        return CONTENT_DIR / "_index.md"

    # Handle special URL patterns
    parts = path.split('/')

    if len(parts) == 1:
        # Root level page
        slug = parts[0]
        return CONTENT_DIR / f"{slug}.md"
    elif parts[0] == 'members-area':
        # Members area pages: /members-area/username/type
        if len(parts) >= 3:
            username = parts[1]
            page_type = parts[2]
            return CONTENT_DIR / "members-area" / username / f"{page_type}.md"
        elif len(parts) == 2:
            username = parts[1]
            return CONTENT_DIR / "members-area" / f"{username}.md"
        else:
            return CONTENT_DIR / "members-area" / "_index.md"
    elif parts[0] == 'partners-area':
        return CONTENT_DIR / "partners-area" / "_index.md"
    else:
        # Category pages
        category = parts[0]
        slug = parts[-1]
        return CONTENT_DIR / category / f"{slug}.md"


def extract_content(html, url):
    """Extract content from HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'noscript', 'iframe']):
        element.decompose()

    # Try to find main content area
    content_selectors = [
        'main',
        '[data-testid="richTextElement"]',
        '.wixui-rich-text',
        '[data-hook="post-content"]',
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

    # Extract title
    title = ""
    title_elem = soup.select_one('h1') or soup.select_one('title')
    if title_elem:
        title = title_elem.get_text(strip=True)

    # Extract text content
    text_content = main_content.get_text(separator='\n', strip=True)

    # Clean up excessive whitespace
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
    """Create markdown file with front matter."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')

    # Determine content type
    content_type = "page"
    if 'members-area' in path_parts:
        content_type = "members"
    elif 'work-package' in path_parts[0] if path_parts else False:
        content_type = "work-package"

    # Create front matter
    front_matter = f"""---
title: "{data['title'].replace('"', '\\"')}"
date: {datetime.now().strftime('%Y-%m-%d')}
type: "{content_type}"
original_url: "{url}"
draft: false
---

"""

    content = front_matter + data['content']

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


async def login_to_members_area(page):
    """Attempt to log in to members area."""
    print("Attempting to log in to members area...")

    try:
        # Navigate to members area
        await page.goto(f"{BASE_URL}/members-area", wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(3000)

        # Look for password input field
        password_selectors = [
            'input[type="password"]',
            '[data-testid="passwordInput"]',
            'input[name="password"]',
            '#password',
            '.password-input'
        ]

        password_input = None
        for selector in password_selectors:
            try:
                password_input = await page.wait_for_selector(selector, timeout=5000)
                if password_input:
                    break
            except:
                continue

        if password_input:
            print(f"  Found password field, entering password...")
            await password_input.fill(MEMBER_PASSWORD)

            # Look for submit button
            submit_selectors = [
                'button[type="submit"]',
                '[data-testid="submit"]',
                'button:has-text("Enter")',
                'button:has-text("Submit")',
                'button:has-text("Login")',
                'input[type="submit"]'
            ]

            for selector in submit_selectors:
                try:
                    submit_btn = await page.query_selector(selector)
                    if submit_btn:
                        await submit_btn.click()
                        await page.wait_for_timeout(3000)
                        print("  Login submitted!")
                        return True
                except:
                    continue

            # Try pressing Enter if no button found
            await password_input.press('Enter')
            await page.wait_for_timeout(3000)
            print("  Login attempted via Enter key")
            return True
        else:
            print("  No password field found - page may not require login")
            return False

    except Exception as e:
        print(f"  Login error: {e}")
        return False


async def scrape_page(page, url):
    """Scrape a single page."""
    try:
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(2000)

        # Scroll to load lazy content
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(1000)

        html = await page.content()
        return extract_content(html, url)

    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return None


async def main():
    print("=" * 60)
    print("Scraping Missing Pages (Including Members-Only)")
    print("=" * 60)

    # Load missing URLs
    missing_urls = load_missing_urls()
    print(f"\nFound {len(missing_urls)} missing URLs to scrape")

    if not missing_urls:
        print("No missing URLs found. Run 06_deep_crawl.py first.")
        return

    results = {
        'scrape_date': datetime.now().isoformat(),
        'total_urls': len(missing_urls),
        'scraped': [],
        'failed': []
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        # Attempt login for members-only pages
        has_members_pages = any('/members-area/' in url for url in missing_urls)
        if has_members_pages:
            await login_to_members_area(page)

        print("\n" + "-" * 60)
        print("Scraping missing pages...")
        print("-" * 60)

        for i, url in enumerate(missing_urls, 1):
            print(f"\n[{i}/{len(missing_urls)}] {url}")

            data = await scrape_page(page, url)

            if data and data['content']:
                filepath = url_to_filepath(url)

                # Skip if file already exists
                if filepath.exists():
                    print(f"  Already exists: {filepath.relative_to(PROJECT_ROOT)}")
                    results['scraped'].append({
                        'url': url,
                        'status': 'exists',
                        'file': str(filepath.relative_to(PROJECT_ROOT))
                    })
                    continue

                create_markdown(data, url, filepath)
                print(f"  Created: {filepath.relative_to(PROJECT_ROOT)}")
                print(f"  Title: {data['title'][:50]}...")
                print(f"  Content: {len(data['content'])} chars, {len(data['images'])} images")

                results['scraped'].append({
                    'url': url,
                    'status': 'scraped',
                    'file': str(filepath.relative_to(PROJECT_ROOT)),
                    'title': data['title'],
                    'content_length': len(data['content']),
                    'images': len(data['images'])
                })
            else:
                print(f"  Failed to extract content")
                results['failed'].append({
                    'url': url,
                    'error': 'No content extracted'
                })

            # Rate limiting
            await page.wait_for_timeout(1000)

        await browser.close()

    # Save results
    output_file = DATA_DIR / "missing_pages_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("SCRAPING RESULTS")
    print("=" * 60)
    scraped_count = sum(1 for r in results['scraped'] if r['status'] == 'scraped')
    exists_count = sum(1 for r in results['scraped'] if r['status'] == 'exists')
    print(f"  Total URLs: {len(missing_urls)}")
    print(f"  Newly scraped: {scraped_count}")
    print(f"  Already existed: {exists_count}")
    print(f"  Failed: {len(results['failed'])}")
    print(f"\nResults saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
