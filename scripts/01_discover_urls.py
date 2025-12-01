"""
01_discover_urls.py
Discovers all URLs from the digital-finance-msca.com sitemaps.
Categorizes URLs and saves to data/urls.json
"""

import requests
import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime

BASE_URL = "https://www.digital-finance-msca.com"
SITEMAPS = [
    f"{BASE_URL}/sitemap.xml",  # Main sitemap index
    f"{BASE_URL}/pages-sitemap.xml",
    f"{BASE_URL}/dynamic-people-sitemap.xml",
    f"{BASE_URL}/dynamic-partner-new-sitemap.xml",
    f"{BASE_URL}/blog-posts-sitemap.xml",
    f"{BASE_URL}/dynamic-training-modules-sitemap.xml",
    f"{BASE_URL}/dynamic-training-events-sitemap.xml",
    f"{BASE_URL}/event-pages-sitemap.xml",
    f"{BASE_URL}/blog-categories-sitemap.xml",
]

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
URLS_DIR = DATA_DIR / "urls"


def fetch_sitemap(url):
    """Fetch and parse a sitemap XML file."""
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None


def parse_sitemap(xml_content):
    """Parse sitemap XML and extract URLs with metadata."""
    urls = []
    if not xml_content:
        return urls

    try:
        root = ET.fromstring(xml_content)
        # Handle namespace
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Check if this is a sitemap index
        sitemaps = root.findall('.//sm:sitemap', ns)
        if sitemaps:
            for sitemap in sitemaps:
                loc = sitemap.find('sm:loc', ns)
                if loc is not None:
                    urls.append({
                        'url': loc.text,
                        'type': 'sitemap_index',
                        'lastmod': None
                    })
            return urls

        # Parse regular sitemap
        for url_elem in root.findall('.//sm:url', ns):
            loc = url_elem.find('sm:loc', ns)
            lastmod = url_elem.find('sm:lastmod', ns)

            if loc is not None:
                urls.append({
                    'url': loc.text,
                    'lastmod': lastmod.text if lastmod is not None else None
                })
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")

    return urls


def categorize_url(url):
    """Categorize a URL based on its path pattern."""
    parsed = urlparse(url)
    path = unquote(parsed.path).strip('/')

    if not path or path == '':
        return 'homepage', 'homepage'

    # Check for specific patterns
    if path.startswith('people/'):
        slug = path.replace('people/', '')
        return 'people', slug
    elif path.startswith('partner-new/'):
        slug = path.replace('partner-new/', '')
        return 'partners', slug
    elif path.startswith('post/'):
        slug = path.replace('post/', '')
        return 'blog', slug
    elif path.startswith('training-modules/'):
        slug = path.replace('training-modules/', '')
        return 'training-modules', slug
    elif path.startswith('training-events/'):
        slug = path.replace('training-events/', '')
        return 'training-events', slug
    elif path.startswith('event-details-registration/'):
        slug = path.replace('event-details-registration/', '')
        return 'events', slug
    elif path.startswith('blog-categories/'):
        slug = path.replace('blog-categories/', '')
        return 'blog-categories', slug
    else:
        # Main pages
        return 'pages', path


def discover_all_urls():
    """Discover all URLs from all sitemaps."""
    all_urls = {
        'homepage': [],
        'pages': [],
        'people': [],
        'partners': [],
        'blog': [],
        'blog-categories': [],
        'training-modules': [],
        'training-events': [],
        'events': [],
    }

    seen_urls = set()

    for sitemap_url in SITEMAPS:
        xml_content = fetch_sitemap(sitemap_url)
        if not xml_content:
            continue

        urls = parse_sitemap(xml_content)
        print(f"  Found {len(urls)} URLs")

        for url_data in urls:
            url = url_data['url']

            # Skip sitemap index entries
            if url_data.get('type') == 'sitemap_index':
                continue

            # Skip duplicates
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Categorize
            category, slug = categorize_url(url)

            url_entry = {
                'url': url,
                'slug': slug,
                'lastmod': url_data.get('lastmod'),
                'scraped': False,
                'scrape_date': None
            }

            if category in all_urls:
                all_urls[category].append(url_entry)
            else:
                all_urls['pages'].append(url_entry)

    return all_urls


def save_urls(urls_data):
    """Save discovered URLs to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    URLS_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "urls.json"

    # Add metadata
    output = {
        'discovery_date': datetime.now().isoformat(),
        'base_url': BASE_URL,
        'categories': urls_data,
        'summary': {category: len(urls) for category, urls in urls_data.items()},
        'total_urls': sum(len(urls) for urls in urls_data.values())
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {output_file}")
    return output


def main():
    print("=" * 60)
    print("URL Discovery for digital-finance-msca.com")
    print("=" * 60)

    urls_data = discover_all_urls()
    output = save_urls(urls_data)

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for category, count in output['summary'].items():
        print(f"  {category}: {count}")
    print(f"\n  TOTAL: {output['total_urls']} URLs")
    print("=" * 60)


if __name__ == "__main__":
    main()
