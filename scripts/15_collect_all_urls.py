"""
15_collect_all_urls.py
Step 1: Collect ALL URLs from the live site via deep crawl.
Does not download content - just discovers and saves URLs.
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import asyncio
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote, urljoin
from collections import deque

try:
    from playwright.async_api import async_playwright
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "playwright"])
    subprocess.run(["playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"

BASE_URL = "https://www.digital-finance-msca.com"
BASE_DOMAIN = "digital-finance-msca.com"


def get_local_pages():
    """Get list of pages we already have locally."""
    local_slugs = set()

    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)

        if md_file.name == "_index.md":
            if md_file.parent == CONTENT_DIR:
                slug = ""
            else:
                slug = str(rel_path.parent).replace("\\", "/")
        else:
            slug = str(rel_path.with_suffix("")).replace("\\", "/")

        local_slugs.add(slug.lower())

    return local_slugs


def normalize_url(url):
    """Normalize URL for comparison."""
    parsed = urlparse(url)
    path = unquote(parsed.path.strip('/'))
    return path.lower()


def is_valid_page_url(url):
    """Check if URL is a valid page (not an asset)."""
    if not url:
        return False

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

    skip_patterns = [
        '/_functions/', '/_api/', '/sitemap', '/robots.txt',
        '/favicon', '/_partials/', '#'
    ]

    for pattern in skip_patterns:
        if pattern in url:
            return False

    return True


def is_internal_url(url):
    """Check if URL is internal to our domain."""
    if not url:
        return False
    parsed = urlparse(url)
    if not parsed.netloc:
        return True
    return BASE_DOMAIN in parsed.netloc


async def collect_all_urls(max_pages=1000):
    """Crawl site and collect ALL internal URLs."""
    print("=" * 70)
    print("STEP 1: COLLECTING ALL URLs FROM LIVE SITE")
    print("=" * 70)
    print(f"Starting from: {BASE_URL}")
    print(f"Max pages to crawl: {max_pages}")
    print()

    visited = set()
    discovered_urls = set()
    queue = deque([BASE_URL])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        page_count = 0

        print("-" * 70)
        print("Crawling...")
        print("-" * 70)

        while queue and page_count < max_pages:
            url = queue.popleft()
            slug = normalize_url(url)

            if slug in visited:
                continue

            visited.add(slug)
            page_count += 1

            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)

                # Check if page exists (not 404)
                title = await page.title()
                if "404" not in title:
                    discovered_urls.add(url)
                    print(f"  [{page_count}] Found: {url[:70]}...")

                # Extract all internal links
                links = await page.evaluate('''() => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        const href = a.href;
                        if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:')) {
                            links.push(href);
                        }
                    });
                    return [...new Set(links)];
                }''')

                for link in links:
                    if is_internal_url(link) and is_valid_page_url(link):
                        link_slug = normalize_url(link)
                        if link_slug not in visited:
                            full_url = urljoin(BASE_URL, link) if not link.startswith('http') else link
                            queue.append(full_url)

            except Exception as e:
                print(f"  [{page_count}] Error: {url[:50]}... - {str(e)[:30]}")

            await page.wait_for_timeout(300)

        await browser.close()

    return discovered_urls


def compare_with_local(discovered_urls, local_slugs):
    """Compare discovered URLs with local content."""
    discovered_slugs = {normalize_url(url) for url in discovered_urls}

    already_have = discovered_slugs & local_slugs
    missing = discovered_slugs - local_slugs
    extra_local = local_slugs - discovered_slugs

    return {
        'discovered': len(discovered_slugs),
        'already_have': len(already_have),
        'missing': len(missing),
        'extra_local': len(extra_local),
        'missing_urls': sorted([url for url in discovered_urls if normalize_url(url) in missing]),
        'extra_local_slugs': sorted(list(extra_local))
    }


async def main():
    # Get local pages
    print("Loading local pages...")
    local_slugs = get_local_pages()
    print(f"Found {len(local_slugs)} local pages\n")

    # Crawl site
    discovered_urls = await collect_all_urls(max_pages=1000)

    # Compare
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)

    comparison = compare_with_local(discovered_urls, local_slugs)

    print(f"  URLs discovered on live site: {comparison['discovered']}")
    print(f"  Already downloaded locally: {comparison['already_have']}")
    print(f"  MISSING (need to download): {comparison['missing']}")
    print(f"  Extra local (not on live site): {comparison['extra_local']}")

    coverage = (comparison['already_have'] / comparison['discovered'] * 100) if comparison['discovered'] > 0 else 0
    print(f"\n  Current coverage: {coverage:.1f}%")

    # Save results
    results = {
        'crawl_date': datetime.now().isoformat(),
        'total_discovered': len(discovered_urls),
        'all_urls': sorted(list(discovered_urls)),
        'comparison': {
            'discovered': comparison['discovered'],
            'already_have': comparison['already_have'],
            'missing': comparison['missing'],
            'coverage_percent': coverage
        },
        'missing_urls': comparison['missing_urls'],
        'extra_local_slugs': comparison['extra_local_slugs']
    }

    output_file = DATA_DIR / "all_discovered_urls.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")

    if comparison['missing_urls']:
        print("\n" + "-" * 70)
        print(f"MISSING URLs ({len(comparison['missing_urls'])}):")
        print("-" * 70)
        for url in comparison['missing_urls'][:30]:
            print(f"  - {url}")
        if len(comparison['missing_urls']) > 30:
            print(f"  ... and {len(comparison['missing_urls']) - 30} more")

    print("\n" + "=" * 70)
    print("STEP 1 COMPLETE")
    print("=" * 70)
    print(f"Run 'python scripts/16_download_all.py' to download missing pages")


if __name__ == "__main__":
    asyncio.run(main())
