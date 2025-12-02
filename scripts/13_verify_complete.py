"""
13_verify_complete.py
Deep verification that ALL content from the website was downloaded.
Compares live site crawl against local content.
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
from collections import defaultdict

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
STATIC_DIR = PROJECT_ROOT / "static"

BASE_URL = "https://www.digital-finance-msca.com"


def get_local_pages():
    """Get all local markdown files as URL slugs."""
    local_slugs = set()
    local_files = {}

    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)

        # Convert path to URL slug
        if md_file.name == "_index.md":
            if md_file.parent == CONTENT_DIR:
                slug = ""
            else:
                slug = str(rel_path.parent).replace("\\", "/")
        else:
            slug = str(rel_path.with_suffix("")).replace("\\", "/")

        local_slugs.add(slug.lower())
        local_files[slug.lower()] = md_file

    return local_slugs, local_files


def url_to_slug(url):
    """Convert URL to slug for comparison."""
    parsed = urlparse(url)
    path = unquote(parsed.path.strip('/'))
    return path.lower()


async def crawl_all_pages(max_pages=600):
    """Crawl the live site and collect all accessible pages."""
    print("Starting deep crawl of live site...")

    visited = set()
    discovered = set()
    queue = [BASE_URL]
    visited.add("")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        page_count = 0

        while queue and page_count < max_pages:
            url = queue.pop(0)
            slug = url_to_slug(url)

            if slug in visited:
                continue

            visited.add(slug)
            page_count += 1

            print(f"  [{page_count}] Crawling: {url[:70]}...")

            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)

                # Check if page loaded successfully (not 404)
                title = await page.title()
                if "404" not in title:
                    discovered.add(slug)

                # Extract all internal links
                links = await page.evaluate('''() => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        const href = a.href;
                        if (href.includes('digital-finance-msca.com') &&
                            !href.includes('#') &&
                            !href.match(/\\.(pdf|jpg|jpeg|png|gif|doc|docx|xlsx|pptx)$/i)) {
                            links.push(href);
                        }
                    });
                    return [...new Set(links)];
                }''')

                for link in links:
                    link_slug = url_to_slug(link)
                    if link_slug not in visited:
                        queue.append(link)

            except Exception as e:
                print(f"    Error: {str(e)[:50]}")

            await page.wait_for_timeout(300)

        await browser.close()

    return discovered


def compare_coverage(live_pages, local_slugs):
    """Compare live pages against local content."""

    # Normalize slugs for comparison
    live_normalized = set()
    for slug in live_pages:
        # Handle various URL patterns
        normalized = slug.lower().strip('/')
        live_normalized.add(normalized)

    local_normalized = set()
    for slug in local_slugs:
        normalized = slug.lower().strip('/')
        local_normalized.add(normalized)

    # Find differences
    missing_locally = live_normalized - local_normalized
    extra_locally = local_normalized - live_normalized
    matched = live_normalized & local_normalized

    return {
        'live_pages': len(live_normalized),
        'local_pages': len(local_normalized),
        'matched': len(matched),
        'missing_locally': sorted(list(missing_locally)),
        'extra_locally': sorted(list(extra_locally))
    }


def analyze_content_quality():
    """Analyze content quality of local files."""
    quality = {
        'total_files': 0,
        'total_words': 0,
        'empty_files': [],
        'short_files': [],
        'good_files': [],
        'by_category': defaultdict(lambda: {'count': 0, 'words': 0})
    }

    for md_file in CONTENT_DIR.rglob("*.md"):
        quality['total_files'] += 1

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip front matter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]

        words = len(content.split())
        quality['total_words'] += words

        rel_path = md_file.relative_to(CONTENT_DIR)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else 'root'
        quality['by_category'][category]['count'] += 1
        quality['by_category'][category]['words'] += words

        if words < 10:
            quality['empty_files'].append(str(rel_path))
        elif words < 50:
            quality['short_files'].append(str(rel_path))
        else:
            quality['good_files'].append(str(rel_path))

    return quality


def count_assets():
    """Count all downloaded assets."""
    assets = {
        'images': 0,
        'image_size_mb': 0,
        'pdfs': 0,
        'documents': 0
    }

    # Count images
    images_dir = STATIC_DIR / "images"
    if images_dir.exists():
        for img in images_dir.rglob("*"):
            if img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                assets['images'] += 1
                assets['image_size_mb'] += img.stat().st_size / (1024 * 1024)

    # Count PDFs
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        pdf_dir = assets_dir / "pdfs"
        if pdf_dir.exists():
            assets['pdfs'] = len(list(pdf_dir.glob("*.pdf")))

        doc_dir = assets_dir / "documents"
        if doc_dir.exists():
            assets['documents'] = len(list(doc_dir.rglob("*")))

    return assets


async def main():
    print("=" * 70)
    print("COMPREHENSIVE VERIFICATION - Is Everything Downloaded?")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Get local content
    print("-" * 70)
    print("1. ANALYZING LOCAL CONTENT")
    print("-" * 70)

    local_slugs, local_files = get_local_pages()
    print(f"   Local markdown files: {len(local_slugs)}")

    quality = analyze_content_quality()
    print(f"   Total words: {quality['total_words']:,}")
    print(f"   Empty/minimal files (<10 words): {len(quality['empty_files'])}")
    print(f"   Short files (<50 words): {len(quality['short_files'])}")
    print(f"   Good content files: {len(quality['good_files'])}")

    print("\n   Content by category:")
    for cat, data in sorted(quality['by_category'].items()):
        avg_words = data['words'] / data['count'] if data['count'] > 0 else 0
        print(f"     - {cat}: {data['count']} files, {data['words']:,} words (avg: {avg_words:.0f})")

    # 2. Count assets
    print("\n" + "-" * 70)
    print("2. DOWNLOADED ASSETS")
    print("-" * 70)

    assets = count_assets()
    print(f"   Images: {assets['images']} ({assets['image_size_mb']:.1f} MB)")
    print(f"   PDFs: {assets['pdfs']}")
    print(f"   Documents: {assets['documents']}")

    # 3. Deep crawl live site
    print("\n" + "-" * 70)
    print("3. DEEP CRAWLING LIVE SITE")
    print("-" * 70)

    live_pages = await crawl_all_pages(max_pages=500)
    print(f"\n   Accessible pages found on live site: {len(live_pages)}")

    # 4. Compare coverage
    print("\n" + "-" * 70)
    print("4. COVERAGE COMPARISON")
    print("-" * 70)

    comparison = compare_coverage(live_pages, local_slugs)

    coverage_pct = (comparison['matched'] / comparison['live_pages'] * 100) if comparison['live_pages'] > 0 else 0

    print(f"   Live site pages: {comparison['live_pages']}")
    print(f"   Local pages: {comparison['local_pages']}")
    print(f"   Matched: {comparison['matched']}")
    print(f"   Coverage: {coverage_pct:.1f}%")

    if comparison['missing_locally']:
        print(f"\n   MISSING LOCALLY ({len(comparison['missing_locally'])}):")
        for slug in comparison['missing_locally'][:20]:
            print(f"     - /{slug}")
        if len(comparison['missing_locally']) > 20:
            print(f"     ... and {len(comparison['missing_locally']) - 20} more")

    # 5. Final verdict
    print("\n" + "=" * 70)
    print("5. FINAL VERDICT")
    print("=" * 70)

    issues = []
    if coverage_pct < 95:
        issues.append(f"Coverage is {coverage_pct:.1f}% (below 95% threshold)")
    if len(quality['empty_files']) > 10:
        issues.append(f"{len(quality['empty_files'])} files have minimal content")
    if comparison['missing_locally']:
        issues.append(f"{len(comparison['missing_locally'])} pages not downloaded")

    if not issues:
        print("\n   [OK] ALL CONTENT SUCCESSFULLY DOWNLOADED!")
        print(f"   - {comparison['matched']} pages verified")
        print(f"   - {assets['images']} images downloaded")
        print(f"   - {assets['pdfs']} PDFs downloaded")
        print(f"   - {quality['total_words']:,} total words of content")
    else:
        print("\n   [!] ISSUES FOUND:")
        for issue in issues:
            print(f"     - {issue}")

    # Save detailed report
    report = {
        'verification_date': datetime.now().isoformat(),
        'local_content': {
            'files': len(local_slugs),
            'words': quality['total_words'],
            'empty_files': quality['empty_files'],
            'short_files': quality['short_files'],
            'by_category': dict(quality['by_category'])
        },
        'assets': assets,
        'live_crawl': {
            'pages_found': len(live_pages),
            'pages_list': sorted(list(live_pages))
        },
        'comparison': comparison,
        'coverage_percentage': coverage_pct,
        'verdict': 'COMPLETE' if not issues else 'ISSUES_FOUND',
        'issues': issues
    }

    output_file = DATA_DIR / "verification_complete.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n   Detailed report saved to: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
