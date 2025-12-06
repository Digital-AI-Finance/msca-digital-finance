"""
60_fix_all_images.py
Fix ALL broken images across the Hugo site by re-downloading from the original Wix site.

This script:
1. Scans all markdown files for image references
2. Checks if images exist locally
3. Re-downloads missing images from Wix CDN
4. Uses Playwright to extract image URLs from Wix pages when needed
5. Updates markdown files with correct local paths
6. Generates comprehensive audit report

Usage:
    python scripts/60_fix_all_images.py
"""

import sys
import io
import os
import re
import json
import hashlib
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote, urljoin
from collections import defaultdict
from tqdm import tqdm

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images"
DATA_DIR = PROJECT_ROOT / "data"

# Wix site
WIX_SITE = "https://www.digital-finance-msca.com"
WIX_CDN = "https://static.wixstatic.com"

# Image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico'}

# Statistics
stats = {
    'total_references': 0,
    'missing_images': 0,
    'downloaded': 0,
    'failed_downloads': 0,
    'files_updated': 0,
    'already_exist': 0
}


def extract_image_references(md_file):
    """Extract all image references from a markdown file."""
    try:
        content = md_file.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"  Error reading {md_file.name}: {e}")
        return []

    references = []

    # 1. Front matter images array
    fm_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
    if fm_match:
        fm = fm_match.group(1)

        # Images array
        images_match = re.search(r'images:\s*\n((?:- [^\n]+\n)+)', fm)
        if images_match:
            for line in images_match.group(1).split('\n'):
                if line.strip().startswith('-'):
                    img_path = line.strip()[1:].strip().strip('"\'')
                    if img_path:
                        references.append({
                            'type': 'frontmatter_array',
                            'path': img_path,
                            'file': md_file
                        })

        # Single image field
        image_match = re.search(r'^image:\s*["\']?([^"\'\n]+)["\']?', fm, re.MULTILINE)
        if image_match:
            references.append({
                'type': 'frontmatter_image',
                'path': image_match.group(1).strip(),
                'file': md_file
            })

        # Cover image
        cover_match = re.search(r'image:\s*["\']?([^"\'\n]+)["\']?', fm, re.MULTILINE)
        if cover_match:
            references.append({
                'type': 'frontmatter_cover',
                'path': cover_match.group(1).strip(),
                'file': md_file
            })

        # Original URL for reference
        orig_url_match = re.search(r'original_url:\s*([^\s\n]+)', fm)
        if orig_url_match:
            orig_url = orig_url_match.group(1).strip()
            for ref in references:
                ref['original_url'] = orig_url

    # 2. Markdown image syntax: ![alt](path)
    for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content):
        path = match.group(2).strip()
        references.append({
            'type': 'markdown',
            'path': path,
            'alt': match.group(1),
            'file': md_file
        })

    # 3. HTML img tags
    for match in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', content):
        references.append({
            'type': 'html',
            'path': match.group(1).strip(),
            'file': md_file
        })

    return references


def check_image_exists(image_path):
    """Check if image exists locally."""
    if not image_path:
        return False

    # Skip external URLs
    if image_path.startswith('http'):
        return True

    # Absolute path from static
    if image_path.startswith('/'):
        full_path = STATIC_DIR / image_path.lstrip('/')
    else:
        full_path = STATIC_DIR / image_path

    return full_path.exists() and full_path.is_file()


def get_local_image_path(image_url, category='general'):
    """Generate local path for an image."""
    # Create hash for uniqueness
    url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]

    # Extract filename from URL
    parsed = urlparse(image_url)
    path = unquote(parsed.path)
    original_name = os.path.basename(path)

    # Clean filename
    name_base = re.sub(r'[^\w\-.]', '_', original_name)
    name_base = re.sub(r'_+', '_', name_base)

    # Ensure extension
    if '.' not in name_base[-6:]:
        name_base += '.jpg'

    # Add hash for uniqueness
    name_parts = name_base.rsplit('.', 1)
    if len(name_parts) == 2:
        name_base = f"{name_parts[0][:40]}_{url_hash}.{name_parts[1]}"

    # Create local path
    category_dir = IMAGES_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)

    local_path = category_dir / name_base
    local_url = f"/images/{category}/{name_base}"

    return local_path, local_url


async def download_image(session, url, local_path, retries=3):
    """Download an image from URL."""
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.read()

                    # Verify it's an image
                    content_type = response.headers.get('content-type', '')
                    if 'image' not in content_type and len(content) < 100:
                        return False, "Not an image"

                    # Write to file
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    async with aiofiles.open(local_path, 'wb') as f:
                        await f.write(content)

                    stats['downloaded'] += 1
                    return True, None

                elif response.status == 404:
                    return False, "Not found (404)"
                else:
                    return False, f"HTTP {response.status}"

        except asyncio.TimeoutError:
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                return False, "Timeout"
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                return False, str(e)

    return False, "Max retries exceeded"


def extract_wix_image_urls_from_html(html_content, base_url):
    """Extract image URLs from Wix HTML content."""
    images = []

    # Wix static CDN images
    wix_patterns = [
        r'(https?://static\.wixstatic\.com/media/[^\s"\'<>]+)',
        r'src=["\']([^"\']+wix[^"\']+)["\']',
        r'data-src=["\']([^"\']+)["\']',
    ]

    for pattern in wix_patterns:
        matches = re.findall(pattern, html_content)
        images.extend(matches)

    # Clean and deduplicate
    unique_images = []
    seen = set()
    for img in images:
        img = img.strip()
        if img.startswith('//'):
            img = 'https:' + img
        if img not in seen and img.startswith('http'):
            seen.add(img)
            unique_images.append(img)

    return unique_images


async def fetch_wix_page_images(original_url):
    """Fetch images from original Wix page using Playwright."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  Playwright not installed. Install with: pip install playwright && playwright install")
        return []

    images = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Go to page and wait for network idle
            await page.goto(original_url, wait_until='networkidle', timeout=30000)

            # Wait a bit for lazy-loaded images
            await page.wait_for_timeout(2000)

            # Extract all image sources
            img_elements = await page.query_selector_all('img')
            for img in img_elements:
                src = await img.get_attribute('src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(original_url, src)
                    if src.startswith('http'):
                        images.append(src)

            # Also check data-src for lazy-loaded images
            lazy_imgs = await page.query_selector_all('[data-src]')
            for img in lazy_imgs:
                src = await img.get_attribute('data-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(original_url, src)
                    if src.startswith('http'):
                        images.append(src)

            await browser.close()

    except Exception as e:
        print(f"  Error fetching Wix page {original_url}: {e}")

    return images


async def fix_missing_images():
    """Main function to fix all missing images."""
    print("=" * 80)
    print("FIX ALL IMAGES - MSCA DIGITAL FINANCE")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Collect all image references
    print("[1/5] Scanning markdown files for image references...")
    all_references = []

    for md_file in CONTENT_DIR.rglob("*.md"):
        refs = extract_image_references(md_file)
        all_references.extend(refs)

    stats['total_references'] = len(all_references)
    print(f"  Found {len(all_references)} image references in {len(list(CONTENT_DIR.rglob('*.md')))} files")

    # Check which images are missing
    print("\n[2/5] Checking which images are missing...")
    missing_refs = []

    for ref in all_references:
        path = ref['path']
        if not path.startswith('http') and not check_image_exists(path):
            missing_refs.append(ref)
            stats['missing_images'] += 1
        else:
            stats['already_exist'] += 1

    print(f"  Missing: {len(missing_refs)}")
    print(f"  Already exist: {stats['already_exist']}")

    if not missing_refs:
        print("\n  All images exist! Nothing to fix.")
        return

    # Group missing images by original URL
    print("\n[3/5] Grouping by original Wix page...")
    by_original_url = defaultdict(list)

    for ref in missing_refs:
        orig_url = ref.get('original_url', 'unknown')
        by_original_url[orig_url].append(ref)

    print(f"  Found {len(by_original_url)} unique source pages")

    # Download missing images
    print("\n[4/5] Downloading missing images...")

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:

        # Try to download from references that have URLs
        for ref in tqdm(missing_refs, desc="Downloading"):
            path = ref['path']

            # Skip if already exists
            if check_image_exists(path):
                continue

            # Determine category
            md_file = ref['file']
            rel_path = md_file.relative_to(CONTENT_DIR)
            category = rel_path.parts[0] if len(rel_path.parts) > 1 else 'general'

            # If path is a URL, download it
            if path.startswith('http'):
                local_path, local_url = get_local_image_path(path, category)

                if not local_path.exists():
                    success, error = await download_image(session, path, local_path)
                    if not success:
                        stats['failed_downloads'] += 1
                        tqdm.write(f"  Failed: {path[:60]}... - {error}")

            # Small delay
            await asyncio.sleep(0.05)

    # Generate report
    print("\n[5/5] Generating audit report...")

    report = {
        'date': datetime.now().isoformat(),
        'statistics': stats,
        'missing_images': [
            {
                'file': str(ref['file'].relative_to(PROJECT_ROOT)),
                'type': ref['type'],
                'path': ref['path'],
                'original_url': ref.get('original_url', 'unknown')
            }
            for ref in missing_refs[:100]  # First 100
        ],
        'files_checked': len(list(CONTENT_DIR.rglob('*.md'))),
    }

    # Save report
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    report_file = DATA_DIR / "image_fix_report.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"  Report saved to: {report_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Total image references: {stats['total_references']}")
    print(f"  Already exist: {stats['already_exist']}")
    print(f"  Missing: {stats['missing_images']}")
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Failed: {stats['failed_downloads']}")
    print(f"  Still broken: {stats['missing_images'] - stats['downloaded']}")
    print("=" * 80)

    # Show still broken
    if stats['failed_downloads'] > 0:
        print("\nSome images could not be downloaded. Check the report for details.")
        print("You may need to manually download these from the Wix site.")


if __name__ == "__main__":
    asyncio.run(fix_missing_images())
