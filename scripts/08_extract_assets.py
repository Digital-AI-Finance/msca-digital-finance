"""
08_extract_assets.py
Scans all scraped pages for PDFs, documents, and external resources.
Downloads assets and catalogs video embeds.
"""

import sys
import io

# Fix Windows console encoding for Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import re
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin
from collections import defaultdict

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
ASSETS_DIR = STATIC_DIR / "assets"

BASE_URL = "https://www.digital-finance-msca.com"


def find_all_markdown_files():
    """Find all markdown files in content directory."""
    return list(CONTENT_DIR.rglob("*.md"))


def extract_assets_from_markdown(filepath):
    """Extract all asset links from a markdown file."""
    assets = {
        'pdfs': [],
        'documents': [],
        'videos': [],
        'external_links': []
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all URLs in the content
    url_pattern = r'https?://[^\s\)\"\'<>]+'
    urls = re.findall(url_pattern, content)

    # Find markdown links: [text](url)
    md_links = re.findall(r'\[([^\]]*)\]\(([^\)]+)\)', content)
    for text, url in md_links:
        if url.startswith('http'):
            urls.append(url)

    for url in urls:
        url = url.rstrip('.,;:!?')  # Clean trailing punctuation
        try:
            parsed = urlparse(url)
            path_lower = parsed.path.lower()
        except ValueError:
            # Skip invalid URLs (e.g., malformed IPv6)
            continue

        # PDFs
        if path_lower.endswith('.pdf'):
            assets['pdfs'].append(url)

        # Office documents
        elif any(path_lower.endswith(ext) for ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
            assets['documents'].append(url)

        # Videos (YouTube, Vimeo)
        elif 'youtube.com' in url or 'youtu.be' in url or 'vimeo.com' in url:
            assets['videos'].append(url)

        # External links (not from our domain or wix)
        elif 'digital-finance-msca.com' not in url and 'wixstatic.com' not in url and 'wix.com' not in url:
            if parsed.scheme in ['http', 'https']:
                assets['external_links'].append(url)

    return assets


async def download_asset(session, url, output_dir, semaphore):
    """Download a single asset."""
    async with semaphore:
        try:
            parsed = urlparse(url)
            filename = Path(parsed.path).name
            if not filename:
                filename = 'unknown_file'

            # Clean filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

            output_path = output_dir / filename

            # Skip if already exists
            if output_path.exists():
                return {'url': url, 'status': 'exists', 'path': str(output_path)}

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    return {'url': url, 'status': 'downloaded', 'path': str(output_path), 'size': len(content)}
                else:
                    return {'url': url, 'status': 'failed', 'error': f'HTTP {response.status}'}

        except Exception as e:
            return {'url': url, 'status': 'error', 'error': str(e)}


async def download_all_assets(urls, output_dir, asset_type):
    """Download all assets of a given type."""
    if not urls:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(5)  # Limit concurrent downloads

    print(f"\nDownloading {len(urls)} {asset_type}...")

    async with aiohttp.ClientSession() as session:
        tasks = [download_asset(session, url, output_dir, semaphore) for url in urls]
        results = await asyncio.gather(*tasks)

    return results


async def main():
    print("=" * 60)
    print("Asset Extraction - PDFs, Documents, Videos")
    print("=" * 60)

    # Find all markdown files
    md_files = find_all_markdown_files()
    print(f"\nScanning {len(md_files)} markdown files...")

    # Extract assets from all files
    all_assets = {
        'pdfs': set(),
        'documents': set(),
        'videos': set(),
        'external_links': set()
    }

    file_assets = {}

    for filepath in md_files:
        assets = extract_assets_from_markdown(filepath)
        rel_path = filepath.relative_to(CONTENT_DIR)

        if any(assets[k] for k in assets):
            file_assets[str(rel_path)] = assets

        for key in all_assets:
            all_assets[key].update(assets[key])

    # Convert to sorted lists
    for key in all_assets:
        all_assets[key] = sorted(list(all_assets[key]))

    print(f"\nAssets found:")
    print(f"  PDFs: {len(all_assets['pdfs'])}")
    print(f"  Documents: {len(all_assets['documents'])}")
    print(f"  Videos: {len(all_assets['videos'])}")
    print(f"  External links: {len(all_assets['external_links'])}")

    # Download PDFs
    pdf_results = []
    if all_assets['pdfs']:
        pdf_dir = ASSETS_DIR / "pdfs"
        pdf_results = await download_all_assets(all_assets['pdfs'], pdf_dir, 'PDFs')

        downloaded = sum(1 for r in pdf_results if r['status'] == 'downloaded')
        exists = sum(1 for r in pdf_results if r['status'] == 'exists')
        failed = sum(1 for r in pdf_results if r['status'] in ['failed', 'error'])
        print(f"  Downloaded: {downloaded}, Already exist: {exists}, Failed: {failed}")

    # Download documents
    doc_results = []
    if all_assets['documents']:
        doc_dir = ASSETS_DIR / "documents"
        doc_results = await download_all_assets(all_assets['documents'], doc_dir, 'documents')

        downloaded = sum(1 for r in doc_results if r['status'] == 'downloaded')
        exists = sum(1 for r in doc_results if r['status'] == 'exists')
        failed = sum(1 for r in doc_results if r['status'] in ['failed', 'error'])
        print(f"  Downloaded: {downloaded}, Already exist: {exists}, Failed: {failed}")

    # Save results
    results = {
        'extraction_date': datetime.now().isoformat(),
        'files_scanned': len(md_files),
        'assets': {
            'pdfs': all_assets['pdfs'],
            'documents': all_assets['documents'],
            'videos': all_assets['videos'],
            'external_links': all_assets['external_links'][:100]  # Limit external links in output
        },
        'download_results': {
            'pdfs': pdf_results,
            'documents': doc_results
        },
        'files_with_assets': file_assets
    }

    output_file = DATA_DIR / "asset_extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")

    # Print video embeds (for manual review)
    if all_assets['videos']:
        print("\n" + "-" * 60)
        print("VIDEO EMBEDS (for reference):")
        print("-" * 60)
        for video in all_assets['videos'][:20]:
            print(f"  - {video}")
        if len(all_assets['videos']) > 20:
            print(f"  ... and {len(all_assets['videos']) - 20} more")

    print("\n" + "=" * 60)
    print("Asset Extraction Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
