"""
41_rescrape_wix.py
Capture reference screenshots from original Wix site for design comparison.
Download any missing images from Wix CDN.

Usage:
    python scripts/41_rescrape_wix.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import json
import asyncio
import hashlib
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images"
DATA_DIR = PROJECT_ROOT / "data"
REFERENCE_DIR = DATA_DIR / "reference_screenshots"

BASE_URL = "https://www.digital-finance-msca.com"

# Key pages to screenshot for design reference
KEY_PAGES = [
    "/",
    "/about-us",
    "/about-the-project",
    "/people",
    "/partners",
    "/blog",
    "/training-modules",
    "/training-events",
    "/contact",
    "/research-domains",
]


async def capture_screenshots():
    """Capture screenshots of key pages from original Wix site."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  Playwright not installed. Skipping screenshots.")
        print("  Install with: pip install playwright && playwright install chromium")
        return []

    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    screenshots = []

    print("  Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        for url_path in KEY_PAGES:
            url = BASE_URL + url_path
            slug = url_path.strip('/').replace('/', '-') or 'homepage'
            filename = f"{slug}.png"
            filepath = REFERENCE_DIR / filename

            try:
                print(f"    Capturing: {url_path}...")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for animations

                # Full page screenshot
                await page.screenshot(path=str(filepath), full_page=True)
                screenshots.append({
                    'url': url,
                    'path': str(filepath),
                    'slug': slug
                })
                print(f"      Saved: {filename}")
            except Exception as e:
                print(f"      Error: {e}")

        await browser.close()

    return screenshots


async def extract_missing_images():
    """Extract image URLs from Wix site that might be missing locally."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  Playwright not installed. Skipping image extraction.")
        return []

    all_images = set()

    print("  Extracting image URLs from Wix site...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url_path in KEY_PAGES[:5]:  # Check first 5 key pages
            url = BASE_URL + url_path
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(1000)

                # Extract all image sources
                images = await page.evaluate('''() => {
                    const imgs = Array.from(document.querySelectorAll('img'));
                    return imgs.map(img => img.src).filter(src => src);
                }''')

                for img_url in images:
                    if 'wixstatic.com' in img_url or 'static.wixstatic.com' in img_url:
                        all_images.add(img_url)

            except Exception as e:
                print(f"    Error on {url_path}: {e}")

        await browser.close()

    return list(all_images)


async def download_missing_images(image_urls):
    """Download images that don't exist locally."""
    import aiohttp

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = []

    print(f"  Checking {len(image_urls)} images...")

    async with aiohttp.ClientSession() as session:
        for url in image_urls[:50]:  # Limit to first 50
            try:
                # Generate filename from URL hash
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                # Try to get original filename
                parsed = urlparse(url)
                path_parts = parsed.path.split('/')
                original_name = path_parts[-1] if path_parts else 'image'
                if '.' not in original_name:
                    original_name = f"{url_hash}.jpg"
                else:
                    name, ext = original_name.rsplit('.', 1)
                    original_name = f"{name[:20]}_{url_hash[:6]}.{ext}"

                filepath = IMAGES_DIR / "wix" / original_name

                if filepath.exists():
                    continue

                filepath.parent.mkdir(parents=True, exist_ok=True)

                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        downloaded.append({
                            'url': url,
                            'local_path': str(filepath)
                        })
                        print(f"    Downloaded: {original_name}")

            except Exception as e:
                pass  # Skip failed downloads

    return downloaded


def run_rescrape():
    """Run the rescrape operation."""
    print("=" * 60)
    print("WIX SITE REFERENCE CAPTURE")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        'date': datetime.now().isoformat(),
        'screenshots': [],
        'images_found': [],
        'images_downloaded': []
    }

    # 1. Capture screenshots
    print("[1/3] Capturing reference screenshots...")
    try:
        screenshots = asyncio.run(capture_screenshots())
        results['screenshots'] = screenshots
        print(f"  Captured {len(screenshots)} screenshots")
    except Exception as e:
        print(f"  Error capturing screenshots: {e}")

    # 2. Extract image URLs
    print("\n[2/3] Extracting image URLs from Wix...")
    try:
        image_urls = asyncio.run(extract_missing_images())
        results['images_found'] = image_urls[:100]  # Save first 100
        print(f"  Found {len(image_urls)} Wix image URLs")
    except Exception as e:
        print(f"  Error extracting images: {e}")
        image_urls = []

    # 3. Download missing images
    print("\n[3/3] Downloading missing images...")
    try:
        downloaded = asyncio.run(download_missing_images(image_urls))
        results['images_downloaded'] = downloaded
        print(f"  Downloaded {len(downloaded)} new images")
    except Exception as e:
        print(f"  Error downloading images: {e}")

    return results


def save_report(results):
    """Save rescrape report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "wix_reference_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    results = run_rescrape()
    save_report(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Screenshots captured: {len(results.get('screenshots', []))}")
    print(f"  Wix images found: {len(results.get('images_found', []))}")
    print(f"  Images downloaded: {len(results.get('images_downloaded', []))}")
    print(f"  Reference folder: {REFERENCE_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
