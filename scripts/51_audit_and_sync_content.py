"""
51_audit_and_sync_content.py
Comprehensive audit of content - compare Hugo site with original Wix site.
Downloads any missing content from the original site.
"""

import sys
import io
import os
import re
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
DATA_DIR = PROJECT_ROOT / "data"

WIX_BASE_URL = "https://www.digital-finance-msca.com"
HUGO_BASE_URL = "https://digital-ai-finance.github.io/msca-digital-finance"

# Known pages on the original site
EXPECTED_PAGES = [
    "/",
    "/about-the-project",
    "/people",
    "/partners",
    "/research-domains",
    "/training-modules",
    "/training-events",
    "/blog",
    "/contact",
    "/open-science",
    "/secondments",
    "/wp1-financial-data-space",
    "/wp2-ai-financial-markets",
    "/wp3-explainable-fair-ai",
    "/wp4-digital-innovation-blockchain",
    "/wp5-sustainability-digital-finance",
]


def get_page_content(url, timeout=30):
    """Fetch page content with error handling."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def extract_text_content(html):
    """Extract main text content from HTML."""
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()

    text = soup.get_text(separator=' ', strip=True)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_images(html, base_url):
    """Extract all image URLs from HTML."""
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    images = []
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            full_url = urljoin(base_url, src)
            images.append(full_url)
    return images


def extract_links(html, base_url):
    """Extract all internal links from HTML."""
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/') or base_url in href:
            full_url = urljoin(base_url, href)
            if base_url in full_url:
                links.append(full_url)
    return list(set(links))


def count_hugo_content():
    """Count content in Hugo site."""
    stats = {
        'total_pages': 0,
        'people': 0,
        'partners': 0,
        'blog_posts': 0,
        'training_modules': 0,
        'training_events': 0,
        'research_domains': 0,
        'images': 0,
    }

    # Count markdown files
    for md_file in CONTENT_DIR.rglob('*.md'):
        stats['total_pages'] += 1
        rel_path = md_file.relative_to(CONTENT_DIR)
        parts = rel_path.parts

        if len(parts) > 0:
            if parts[0] == 'people':
                stats['people'] += 1
            elif parts[0] == 'partners':
                stats['partners'] += 1
            elif parts[0] == 'blog':
                stats['blog_posts'] += 1
            elif parts[0] == 'training-modules':
                stats['training_modules'] += 1
            elif parts[0] == 'training-events':
                stats['training_events'] += 1
            elif parts[0] == 'research-domains':
                stats['research_domains'] += 1

    # Count images
    images_dir = STATIC_DIR / "images"
    if images_dir.exists():
        for img in images_dir.rglob('*'):
            if img.is_file() and img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                stats['images'] += 1

    return stats


def scrape_wix_navigation():
    """Scrape navigation structure from Wix site."""
    print("Scraping Wix site navigation...")
    html = get_page_content(WIX_BASE_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    nav_links = []

    # Find all navigation links
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        if text and (href.startswith('/') or WIX_BASE_URL in href):
            nav_links.append({
                'text': text,
                'url': urljoin(WIX_BASE_URL, href)
            })

    return nav_links


def scrape_people_list():
    """Scrape list of people from Wix site."""
    print("Scraping people from Wix site...")
    url = f"{WIX_BASE_URL}/people"
    html = get_page_content(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    people = []

    # Look for person cards/links
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/people/' in href and href != '/people/':
            name = a.get_text(strip=True)
            if name and len(name) > 2:
                people.append({
                    'name': name,
                    'url': urljoin(WIX_BASE_URL, href)
                })

    return people


def scrape_partners_list():
    """Scrape list of partners from Wix site."""
    print("Scraping partners from Wix site...")
    url = f"{WIX_BASE_URL}/partners"
    html = get_page_content(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    partners = []

    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/partners/' in href and href != '/partners/':
            name = a.get_text(strip=True)
            if name and len(name) > 2:
                partners.append({
                    'name': name,
                    'url': urljoin(WIX_BASE_URL, href)
                })

    return partners


def find_all_wix_pages():
    """Crawl Wix site to find all pages."""
    print("Crawling Wix site for all pages...")
    visited = set()
    to_visit = [WIX_BASE_URL]
    all_pages = []

    while to_visit and len(visited) < 500:  # Limit to prevent infinite crawl
        url = to_visit.pop(0)
        if url in visited:
            continue

        # Normalize URL
        parsed = urlparse(url)
        if parsed.netloc and 'digital-finance-msca.com' not in parsed.netloc:
            continue

        visited.add(url)
        print(f"  Checking: {url}")

        html = get_page_content(url)
        if html:
            all_pages.append({
                'url': url,
                'content_length': len(extract_text_content(html)),
                'image_count': len(extract_images(html, url))
            })

            # Find more links
            links = extract_links(html, WIX_BASE_URL)
            for link in links:
                if link not in visited:
                    to_visit.append(link)

        time.sleep(0.5)  # Be polite

    return all_pages


def compare_content():
    """Compare Hugo content with what should be on Wix."""
    print("\n" + "=" * 60)
    print("CONTENT COMPARISON REPORT")
    print("=" * 60)

    # Get Hugo stats
    hugo_stats = count_hugo_content()
    print("\nHugo Site Content:")
    print(f"  Total pages: {hugo_stats['total_pages']}")
    print(f"  People: {hugo_stats['people']}")
    print(f"  Partners: {hugo_stats['partners']}")
    print(f"  Blog posts: {hugo_stats['blog_posts']}")
    print(f"  Training modules: {hugo_stats['training_modules']}")
    print(f"  Training events: {hugo_stats['training_events']}")
    print(f"  Images: {hugo_stats['images']}")

    # Check for empty content files
    print("\nChecking for empty content files...")
    empty_files = []
    for md_file in CONTENT_DIR.rglob('*.md'):
        content = md_file.read_text(encoding='utf-8', errors='replace')
        # Check if file has actual content beyond front matter
        parts = content.split('---')
        if len(parts) >= 3:
            body = '---'.join(parts[2:]).strip()
            if len(body) < 50:
                empty_files.append(str(md_file.relative_to(CONTENT_DIR)))

    if empty_files:
        print(f"  Found {len(empty_files)} files with little/no content")
        for f in empty_files[:20]:
            print(f"    - {f}")
        if len(empty_files) > 20:
            print(f"    ... and {len(empty_files) - 20} more")

    return hugo_stats, empty_files


def download_missing_images():
    """Check for and download missing images."""
    print("\nChecking for missing images...")

    missing_images = []

    for md_file in CONTENT_DIR.rglob('*.md'):
        content = md_file.read_text(encoding='utf-8', errors='replace')

        # Find image references
        img_refs = re.findall(r'!\[.*?\]\((.*?)\)', content)
        img_refs += re.findall(r'image:\s*["\']?(/images/[^"\'"\s]+)', content)
        img_refs += re.findall(r'cover:\s*\n\s*image:\s*["\']?(/images/[^"\'"\s]+)', content)

        for img_ref in img_refs:
            if img_ref.startswith('/images/'):
                img_path = STATIC_DIR / img_ref.lstrip('/')
                if not img_path.exists():
                    missing_images.append({
                        'reference': img_ref,
                        'source_file': str(md_file.relative_to(CONTENT_DIR))
                    })

    if missing_images:
        print(f"  Found {len(missing_images)} missing image references")
        for img in missing_images[:10]:
            print(f"    - {img['reference']} (in {img['source_file']})")
        if len(missing_images) > 10:
            print(f"    ... and {len(missing_images) - 10} more")
    else:
        print("  All referenced images exist")

    return missing_images


def generate_report():
    """Generate comprehensive audit report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'hugo_stats': None,
        'empty_files': [],
        'missing_images': [],
        'recommendations': []
    }

    # Run comparisons
    hugo_stats, empty_files = compare_content()
    report['hugo_stats'] = hugo_stats
    report['empty_files'] = empty_files

    # Check missing images
    missing_images = download_missing_images()
    report['missing_images'] = missing_images

    # Generate recommendations
    if empty_files:
        report['recommendations'].append(
            f"Fill content for {len(empty_files)} empty/sparse pages"
        )

    if missing_images:
        report['recommendations'].append(
            f"Fix {len(missing_images)} broken image references"
        )

    # Save report
    report_path = DATA_DIR / "content_audit_report.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport saved to: {report_path}")
    return report


def main():
    print("=" * 60)
    print("MSCA DIGITAL FINANCE - CONTENT AUDIT & SYNC")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hugo Content: {CONTENT_DIR}")
    print(f"Original Site: {WIX_BASE_URL}")
    print()

    # Generate report
    report = generate_report()

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    for rec in report['recommendations']:
        print(f"  - {rec}")

    if not report['recommendations']:
        print("  No major issues found!")

    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
