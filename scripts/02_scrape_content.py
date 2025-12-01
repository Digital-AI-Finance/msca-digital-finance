"""
02_scrape_content.py
Scrapes content from all discovered URLs using Playwright for JavaScript rendering.
Saves content as Hugo-compatible markdown files with YAML front matter.
"""

import sys
import io

# Fix Windows console encoding for Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import re
import time
import asyncio
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote
import yaml

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.run(["pip", "install", "playwright"])
    subprocess.run(["playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

from bs4 import BeautifulSoup
import html2text

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# HTML to Markdown converter
H2T = html2text.HTML2Text()
H2T.ignore_links = False
H2T.ignore_images = False
H2T.ignore_emphasis = False
H2T.body_width = 0  # Don't wrap text


def load_urls():
    """Load discovered URLs from JSON file."""
    urls_file = DATA_DIR / "urls.json"
    with open(urls_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_progress():
    """Load scraping progress from checkpoint file."""
    progress_file = DATA_DIR / "scrape_progress.json"
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'scraped_urls': [], 'failed_urls': [], 'last_update': None}


def save_progress(progress):
    """Save scraping progress to checkpoint file."""
    progress['last_update'] = datetime.now().isoformat()
    progress_file = DATA_DIR / "scrape_progress.json"
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def sanitize_filename(name):
    """Sanitize a string for use as a filename."""
    # URL decode
    name = unquote(name)
    # Remove or replace special characters
    name = re.sub(r'[<>:"/\\|?*]', '-', name)
    name = re.sub(r'\s+', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name.lower()


def get_content_path(category, slug):
    """Get the content file path for a given category and slug."""
    safe_slug = sanitize_filename(slug)

    if category == 'homepage':
        return CONTENT_DIR / "_index.md"
    elif category == 'pages':
        return CONTENT_DIR / f"{safe_slug}.md"
    else:
        category_dir = CONTENT_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)
        return category_dir / f"{safe_slug}.md"


def extract_meta_content(soup):
    """Extract metadata from page head."""
    meta = {}

    # Title
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()
        # Remove site name suffix if present
        title = re.sub(r'\s*\|\s*.*$', '', title)
        meta['title'] = title

    # Meta description
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    if desc_tag and desc_tag.get('content'):
        meta['description'] = desc_tag['content']

    # OG tags
    og_image = soup.find('meta', attrs={'property': 'og:image'})
    if og_image and og_image.get('content'):
        meta['og_image'] = og_image['content']

    og_title = soup.find('meta', attrs={'property': 'og:title'})
    if og_title and og_title.get('content'):
        meta['og_title'] = og_title['content']

    return meta


def extract_main_content(soup, category):
    """Extract main content from the page."""
    # Remove unwanted elements
    for element in soup.find_all(['script', 'style', 'noscript', 'iframe']):
        element.decompose()

    # Remove Wix-specific elements
    for element in soup.find_all(class_=re.compile(r'wix-ads|cookie-banner|popup|modal')):
        element.decompose()

    # Try to find main content area
    main_content = None

    # Look for specific Wix content containers
    content_selectors = [
        'main',
        '[data-testid="mesh-container-content"]',
        '#PAGES_CONTAINER',
        '.page-content',
        '[role="main"]',
        'article',
    ]

    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break

    if not main_content:
        # Fall back to body
        main_content = soup.find('body')

    return main_content


def extract_images(soup):
    """Extract all image URLs from the page."""
    images = []
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            # Skip base64 images and tracking pixels
            if src.startswith('data:') or '1x1' in src:
                continue
            images.append({
                'src': src,
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
    return images


def extract_person_data(soup, meta):
    """Extract structured data for person pages."""
    person_data = {}

    # Try to find role/position
    role_selectors = ['.role', '.position', '.job-title', '[data-testid*="role"]']
    for selector in role_selectors:
        elem = soup.select_one(selector)
        if elem:
            person_data['role'] = elem.get_text().strip()
            break

    # Try to find institution
    inst_selectors = ['.institution', '.organization', '.company', '[data-testid*="institution"]']
    for selector in inst_selectors:
        elem = soup.select_one(selector)
        if elem:
            person_data['institution'] = elem.get_text().strip()
            break

    # Try to find email
    email_link = soup.find('a', href=re.compile(r'^mailto:'))
    if email_link:
        person_data['email'] = email_link['href'].replace('mailto:', '')

    # Try to find LinkedIn
    linkedin_link = soup.find('a', href=re.compile(r'linkedin\.com'))
    if linkedin_link:
        person_data['linkedin'] = linkedin_link['href']

    return person_data


def extract_event_data(soup, meta):
    """Extract structured data for event pages."""
    event_data = {}

    # Try to find date
    date_selectors = ['.event-date', '.date', '[data-testid*="date"]', 'time']
    for selector in date_selectors:
        elem = soup.select_one(selector)
        if elem:
            event_data['event_date'] = elem.get_text().strip()
            break

    # Try to find location
    loc_selectors = ['.event-location', '.location', '.venue', '[data-testid*="location"]']
    for selector in loc_selectors:
        elem = soup.select_one(selector)
        if elem:
            event_data['location'] = elem.get_text().strip()
            break

    return event_data


def html_to_markdown(html_content):
    """Convert HTML content to Markdown."""
    if not html_content:
        return ""

    # Convert to string if BeautifulSoup object
    if hasattr(html_content, 'decode_contents'):
        html_str = str(html_content)
    else:
        html_str = html_content

    # Clean up Wix-specific markup
    html_str = re.sub(r'<wix-[^>]*>', '', html_str)
    html_str = re.sub(r'</wix-[^>]*>', '', html_str)

    # Convert to markdown
    markdown = H2T.handle(html_str)

    # Clean up excessive whitespace
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    markdown = markdown.strip()

    return markdown


def create_front_matter(meta, category, url, additional_data=None):
    """Create YAML front matter for Hugo."""
    front_matter = {
        'title': meta.get('title', 'Untitled'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'draft': False,
        'type': category if category != 'pages' else None,
        'original_url': url,
    }

    if meta.get('description'):
        front_matter['description'] = meta['description']

    if meta.get('og_image'):
        front_matter['image'] = meta['og_image']

    if additional_data:
        front_matter.update(additional_data)

    # Remove None values
    front_matter = {k: v for k, v in front_matter.items() if v is not None}

    return front_matter


def save_markdown(content_path, front_matter, content):
    """Save content as markdown file with YAML front matter."""
    # Ensure parent directory exists
    content_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the markdown content
    yaml_str = yaml.dump(front_matter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    markdown_content = f"---\n{yaml_str}---\n\n{content}"

    with open(content_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)


async def scrape_page(page, url, category, slug, retries=2):
    """Scrape a single page using Playwright."""
    for attempt in range(retries):
        try:
            # Navigate to page - use domcontentloaded for faster loading
            # Wix pages have many background requests that prevent networkidle
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # Wait for Wix content to render (fixed delay)
            await page.wait_for_timeout(3000)

            # Get page HTML
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Extract metadata
            meta = extract_meta_content(soup)

            # Extract main content
            main_content = extract_main_content(soup, category)

            # Extract images
            images = extract_images(soup)

            # Extract category-specific data
            additional_data = {}
            if category == 'people':
                additional_data = extract_person_data(soup, meta)
            elif category in ['events', 'training-events']:
                additional_data = extract_event_data(soup, meta)

            # Add images to additional data
            if images:
                additional_data['images'] = [img['src'] for img in images[:10]]  # Limit to 10

            # Convert to markdown
            markdown_content = html_to_markdown(main_content)

            # Create front matter
            front_matter = create_front_matter(meta, category, url, additional_data)

            # Get content path
            content_path = get_content_path(category, slug)

            # Save markdown file
            save_markdown(content_path, front_matter, markdown_content)

            return {
                'success': True,
                'url': url,
                'path': str(content_path),
                'title': meta.get('title', 'Untitled'),
                'images_count': len(images)
            }

        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt + 1}/{retries} for {url}: {e}")
                await page.wait_for_timeout(2000 * (attempt + 1))
            else:
                return {
                    'success': False,
                    'url': url,
                    'error': str(e)
                }


async def main():
    print("=" * 60)
    print("Content Scraper for digital-finance-msca.com")
    print("=" * 60)

    # Load URLs
    urls_data = load_urls()
    progress = load_progress()

    # Collect all URLs to scrape
    all_urls = []
    for category, urls in urls_data['categories'].items():
        for url_entry in urls:
            if url_entry['url'] not in progress['scraped_urls']:
                all_urls.append({
                    'url': url_entry['url'],
                    'slug': url_entry['slug'],
                    'category': category
                })

    print(f"\nTotal URLs to scrape: {len(all_urls)}")
    print(f"Already scraped: {len(progress['scraped_urls'])}")
    print(f"Previously failed: {len(progress['failed_urls'])}")
    print("\n" + "-" * 60)

    if not all_urls:
        print("No URLs to scrape. All done!")
        return

    # Create category index files
    for category in urls_data['categories'].keys():
        if category not in ['homepage', 'pages']:
            category_dir = CONTENT_DIR / category
            category_dir.mkdir(parents=True, exist_ok=True)
            index_path = category_dir / "_index.md"
            if not index_path.exists():
                index_front_matter = {
                    'title': category.replace('-', ' ').title(),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'draft': False,
                }
                save_markdown(index_path, index_front_matter, f"# {category.replace('-', ' ').title()}\n")

    # Launch browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        success_count = 0
        fail_count = 0

        for i, url_data in enumerate(all_urls):
            url = url_data['url']
            category = url_data['category']
            slug = url_data['slug']

            print(f"\n[{i+1}/{len(all_urls)}] Scraping: {url}")
            print(f"  Category: {category}, Slug: {slug}")

            result = await scrape_page(page, url, category, slug)

            if result['success']:
                print(f"  OK: {result['title']}")
                print(f"  Saved to: {result['path']}")
                progress['scraped_urls'].append(url)
                success_count += 1
            else:
                print(f"  FAILED: {result['error']}")
                progress['failed_urls'].append({'url': url, 'error': result['error']})
                fail_count += 1

            # Save progress after each page
            save_progress(progress)

            # Rate limiting - short delay between pages
            await page.wait_for_timeout(500)

        await browser.close()

    print("\n" + "=" * 60)
    print("Scraping Complete!")
    print("=" * 60)
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Total scraped: {len(progress['scraped_urls'])}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
