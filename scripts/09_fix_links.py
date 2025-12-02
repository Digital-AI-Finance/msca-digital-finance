"""
09_fix_links.py
Analyzes and fixes broken internal links in markdown files.
Updates image paths and internal page links to work with Hugo.
"""

import sys
import io

# Fix Windows console encoding for Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"

BASE_URL = "https://www.digital-finance-msca.com"


def find_all_markdown_files():
    """Find all markdown files in content directory."""
    return list(CONTENT_DIR.rglob("*.md"))


def find_all_images():
    """Find all images in static directory."""
    images = {}
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']

    for ext in image_extensions:
        for img_path in STATIC_DIR.rglob(f"*{ext}"):
            rel_path = img_path.relative_to(STATIC_DIR)
            filename = img_path.name.lower()
            images[filename] = f"/{rel_path}".replace("\\", "/")

    return images


def find_all_content_slugs():
    """Build a mapping of slugs to content paths."""
    slugs = {}

    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)
        slug = md_file.stem

        # Build the Hugo URL path
        if md_file.name == "_index.md":
            if md_file.parent == CONTENT_DIR:
                url_path = "/"
            else:
                url_path = f"/{md_file.parent.relative_to(CONTENT_DIR)}/"
        else:
            if md_file.parent == CONTENT_DIR:
                url_path = f"/{slug}/"
            else:
                category = md_file.parent.relative_to(CONTENT_DIR)
                url_path = f"/{category}/{slug}/"

        url_path = url_path.replace("\\", "/")
        slugs[slug.lower()] = url_path

    return slugs


def extract_links_from_markdown(content):
    """Extract all links from markdown content."""
    links = []

    # Markdown links: [text](url)
    md_pattern = r'\[([^\]]*)\]\(([^\)]+)\)'
    for match in re.finditer(md_pattern, content):
        text, url = match.groups()
        links.append({
            'type': 'markdown',
            'text': text,
            'url': url,
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0)
        })

    # Image tags in HTML: <img src="...">
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    for match in re.finditer(img_pattern, content):
        url = match.group(1)
        links.append({
            'type': 'img_tag',
            'url': url,
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0)
        })

    return links


def analyze_link(link, images, slugs):
    """Analyze a link and determine if it needs fixing."""
    url = link['url']

    # Skip external URLs
    if url.startswith('http') and 'digital-finance-msca.com' not in url and 'wixstatic.com' not in url:
        return {'status': 'external', 'url': url}

    # Check if it's an image link
    parsed = urlparse(url)
    path_lower = parsed.path.lower()

    if any(path_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
        # It's an image - check if we have it locally
        filename = Path(path_lower).name

        if filename in images:
            return {
                'status': 'fixable',
                'type': 'image',
                'original': url,
                'fixed': images[filename]
            }
        else:
            return {'status': 'broken_image', 'url': url}

    # Check if it's an internal page link
    if 'digital-finance-msca.com' in url or url.startswith('/'):
        path = parsed.path.strip('/').split('/')[-1] if parsed.path else ''
        slug = path.lower()

        if slug in slugs:
            return {
                'status': 'fixable',
                'type': 'internal_link',
                'original': url,
                'fixed': slugs[slug]
            }
        else:
            return {'status': 'broken_link', 'url': url}

    return {'status': 'unknown', 'url': url}


def fix_links_in_file(filepath, images, slugs, dry_run=False):
    """Fix links in a single markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    links = extract_links_from_markdown(content)

    fixes = []
    broken = []

    for link in links:
        analysis = analyze_link(link, images, slugs)

        if analysis['status'] == 'fixable':
            fixes.append({
                'original': analysis['original'],
                'fixed': analysis['fixed'],
                'type': analysis['type']
            })

            # Apply fix
            if link['type'] == 'markdown':
                old_link = f"]({analysis['original']})"
                new_link = f"]({analysis['fixed']})"
                content = content.replace(old_link, new_link)
            elif link['type'] == 'img_tag':
                content = content.replace(f'src="{analysis["original"]}"', f'src="{analysis["fixed"]}"')
                content = content.replace(f"src='{analysis['original']}'", f"src='{analysis['fixed']}'")

        elif analysis['status'] in ['broken_image', 'broken_link']:
            broken.append(analysis)

    # Write fixed content
    if fixes and not dry_run and content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return {
        'file': str(filepath.relative_to(CONTENT_DIR)),
        'fixes_applied': len(fixes),
        'broken_links': len(broken),
        'fixes': fixes,
        'broken': broken
    }


def main():
    print("=" * 60)
    print("Link Fixer - Analyzing and Fixing Internal Links")
    print("=" * 60)

    # Build reference maps
    print("\nBuilding reference maps...")
    images = find_all_images()
    print(f"  Found {len(images)} images in static/")

    slugs = find_all_content_slugs()
    print(f"  Found {len(slugs)} content pages")

    # Find all markdown files
    md_files = find_all_markdown_files()
    print(f"  Found {len(md_files)} markdown files to scan")

    # Analyze and fix links
    print("\nAnalyzing links...")
    print("-" * 60)

    all_results = []
    total_fixes = 0
    total_broken = 0
    files_fixed = 0

    for filepath in md_files:
        result = fix_links_in_file(filepath, images, slugs, dry_run=False)
        all_results.append(result)

        if result['fixes_applied'] > 0:
            files_fixed += 1
            total_fixes += result['fixes_applied']
            print(f"  Fixed {result['fixes_applied']} links in {result['file']}")

        total_broken += result['broken_links']

    print("\n" + "=" * 60)
    print("LINK FIX RESULTS")
    print("=" * 60)
    print(f"  Files scanned: {len(md_files)}")
    print(f"  Files modified: {files_fixed}")
    print(f"  Total links fixed: {total_fixes}")
    print(f"  Broken links remaining: {total_broken}")

    # Collect all broken links
    broken_summary = {
        'broken_images': [],
        'broken_pages': []
    }

    for result in all_results:
        for broken in result['broken']:
            if broken['status'] == 'broken_image':
                broken_summary['broken_images'].append({
                    'file': result['file'],
                    'url': broken['url']
                })
            else:
                broken_summary['broken_pages'].append({
                    'file': result['file'],
                    'url': broken['url']
                })

    # Save results
    results = {
        'fix_date': datetime.now().isoformat(),
        'files_scanned': len(md_files),
        'files_modified': files_fixed,
        'total_fixes': total_fixes,
        'broken_remaining': total_broken,
        'broken_summary': broken_summary,
        'detailed_results': all_results
    }

    output_file = DATA_DIR / "link_fix_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")

    # Print broken links summary
    if broken_summary['broken_images']:
        print("\n" + "-" * 60)
        print(f"BROKEN IMAGES ({len(broken_summary['broken_images'])}):")
        print("-" * 60)
        for item in broken_summary['broken_images'][:20]:
            print(f"  In {item['file']}: {item['url'][:60]}...")

    if broken_summary['broken_pages']:
        print("\n" + "-" * 60)
        print(f"BROKEN PAGE LINKS ({len(broken_summary['broken_pages'])}):")
        print("-" * 60)
        for item in broken_summary['broken_pages'][:20]:
            print(f"  In {item['file']}: {item['url'][:60]}...")

    print("\n" + "=" * 60)
    print("Link Fix Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
