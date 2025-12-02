"""
30_check_links.py
Check all internal and external links in markdown files.
Generates a report of broken links.

Usage:
    python scripts/30_check_links.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import re
import json
import requests
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
DATA_DIR = PROJECT_ROOT / "data"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Patterns to find links in markdown
MD_LINK_PATTERN = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
HTML_LINK_PATTERN = re.compile(r'href=["\']([^"\']+)["\']')
IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
HTML_IMG_PATTERN = re.compile(r'src=["\']([^"\']+)["\']')


def get_all_markdown_files():
    """Get all markdown files in content directory."""
    return list(CONTENT_DIR.rglob("*.md"))


def get_all_content_paths():
    """Get all valid content paths (for internal link validation)."""
    paths = set()
    for md_file in get_all_markdown_files():
        rel_path = md_file.relative_to(CONTENT_DIR)
        # Convert to URL path
        url_path = "/" + str(rel_path).replace("\\", "/").replace(".md", "/")
        url_path = url_path.replace("/_index/", "/")
        paths.add(url_path.lower())
        # Also add without trailing slash
        paths.add(url_path.rstrip("/").lower())
    return paths


def get_all_static_files():
    """Get all static files (images, etc.)."""
    files = set()
    if STATIC_DIR.exists():
        for f in STATIC_DIR.rglob("*"):
            if f.is_file():
                rel_path = "/" + str(f.relative_to(STATIC_DIR)).replace("\\", "/")
                files.add(rel_path.lower())
    return files


def extract_links_from_file(md_file):
    """Extract all links from a markdown file."""
    links = []
    try:
        content = md_file.read_text(encoding='utf-8', errors='replace')

        # Find markdown links
        for match in MD_LINK_PATTERN.finditer(content):
            link_text, url = match.groups()
            links.append({
                'type': 'markdown',
                'url': url.strip(),
                'text': link_text,
                'file': str(md_file)
            })

        # Find HTML links
        for match in HTML_LINK_PATTERN.finditer(content):
            url = match.group(1)
            links.append({
                'type': 'html',
                'url': url.strip(),
                'text': '',
                'file': str(md_file)
            })

        # Find markdown images
        for match in IMG_PATTERN.finditer(content):
            alt_text, url = match.groups()
            links.append({
                'type': 'image',
                'url': url.strip(),
                'text': alt_text,
                'file': str(md_file)
            })

        # Find HTML images
        for match in HTML_IMG_PATTERN.finditer(content):
            url = match.group(1)
            if not any(url == l['url'] for l in links):  # Avoid duplicates
                links.append({
                    'type': 'image',
                    'url': url.strip(),
                    'text': '',
                    'file': str(md_file)
                })
    except Exception as e:
        print(f"  Error reading {md_file}: {e}")

    return links


def check_external_link(url, timeout=10):
    """Check if an external URL is accessible."""
    try:
        response = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code == 405:  # Method not allowed, try GET
            response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except requests.RequestException:
        return False


def categorize_link(url):
    """Categorize a link as internal, external, or special."""
    if not url:
        return 'empty'
    if url.startswith('#'):
        return 'anchor'
    if url.startswith('mailto:'):
        return 'email'
    if url.startswith('tel:'):
        return 'phone'
    if url.startswith('javascript:'):
        return 'javascript'
    if url.startswith(('http://', 'https://', '//')):
        return 'external'
    if url.startswith('/'):
        return 'internal_absolute'
    return 'internal_relative'


def check_all_links():
    """Main function to check all links."""
    print("=" * 60)
    print("LINK CHECKER")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get all content and static paths
    print("[1/4] Indexing content files...")
    content_paths = get_all_content_paths()
    print(f"  Found {len(content_paths)} content paths")

    print("[2/4] Indexing static files...")
    static_files = get_all_static_files()
    print(f"  Found {len(static_files)} static files")

    # Extract all links
    print("[3/4] Extracting links from markdown files...")
    md_files = get_all_markdown_files()
    all_links = []
    for md_file in md_files:
        links = extract_links_from_file(md_file)
        all_links.extend(links)
    print(f"  Found {len(all_links)} total links")

    # Categorize and check links
    print("[4/4] Checking links...")
    results = {
        'total': len(all_links),
        'by_category': {},
        'broken': [],
        'working': [],
        'skipped': [],
        'external_checked': 0,
        'external_broken': []
    }

    # Categorize
    categorized = {}
    for link in all_links:
        category = categorize_link(link['url'])
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(link)

    results['by_category'] = {k: len(v) for k, v in categorized.items()}
    print(f"  Categories: {results['by_category']}")

    # Check internal absolute links
    internal_abs = categorized.get('internal_absolute', [])
    print(f"\n  Checking {len(internal_abs)} internal absolute links...")
    for link in internal_abs:
        url = link['url'].lower()
        # Check if it's a static file
        if url.startswith('/images/') or url.startswith('/css/') or url.startswith('/js/'):
            if url in static_files:
                results['working'].append(link)
            else:
                link['reason'] = 'Static file not found'
                results['broken'].append(link)
        else:
            # Check content path
            check_url = url.rstrip('/')
            if check_url in content_paths or (check_url + '/') in content_paths:
                results['working'].append(link)
            else:
                link['reason'] = 'Content page not found'
                results['broken'].append(link)

    # Check external links (sample - limit to avoid rate limiting)
    external = categorized.get('external', [])
    unique_external = list({l['url']: l for l in external}.values())  # Deduplicate
    print(f"\n  Checking {len(unique_external)} unique external links (sampling max 50)...")

    sample_external = unique_external[:50]  # Limit to avoid rate limiting
    results['external_checked'] = len(sample_external)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_external_link, link['url']): link for link in sample_external}
        for future in as_completed(futures):
            link = futures[future]
            try:
                is_valid = future.result()
                if is_valid:
                    results['working'].append(link)
                else:
                    link['reason'] = 'External URL not accessible'
                    results['external_broken'].append(link)
            except Exception as e:
                link['reason'] = f'Error checking: {str(e)}'
                results['external_broken'].append(link)

    # Skip anchors, emails, etc.
    for category in ['anchor', 'email', 'phone', 'javascript', 'empty']:
        for link in categorized.get(category, []):
            link['reason'] = f'Skipped ({category})'
            results['skipped'].append(link)

    return results


def save_report(results):
    """Save the link check report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        'date': datetime.now().isoformat(),
        'summary': {
            'total_links': results['total'],
            'broken_internal': len(results['broken']),
            'broken_external': len(results['external_broken']),
            'working': len(results['working']),
            'skipped': len(results['skipped']),
            'by_category': results['by_category']
        },
        'broken_internal': results['broken'][:100],  # Limit output
        'broken_external': results['external_broken']
    }

    output_file = DATA_DIR / "link_check_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    results = check_all_links()
    save_report(results)

    print("\n" + "=" * 60)
    print("LINK CHECK SUMMARY")
    print("=" * 60)
    print(f"  Total links found: {results['total']}")
    print(f"  Broken internal: {len(results['broken'])}")
    print(f"  Broken external: {len(results['external_broken'])}")
    print(f"  Working: {len(results['working'])}")
    print(f"  Skipped: {len(results['skipped'])}")

    if results['broken']:
        print(f"\n  Top 10 broken internal links:")
        for link in results['broken'][:10]:
            print(f"    - {link['url']}")
            print(f"      in: {Path(link['file']).name}")

    if results['external_broken']:
        print(f"\n  Broken external links:")
        for link in results['external_broken'][:10]:
            print(f"    - {link['url']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
