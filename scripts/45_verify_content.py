"""
45_verify_content.py
Verify all content from original Wix site is present in Hugo site.
- Compare original sitemap URLs vs Hugo content
- Check content quality (word count, images)
- Report missing or empty pages
- Verify internal links

Usage:
    python scripts/45_verify_content.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
DATA_DIR = PROJECT_ROOT / "data"

# Original Wix sitemap URLs file
URLS_FILE = DATA_DIR / "urls.json"


def load_original_urls():
    """Load URLs from original Wix sitemap."""
    if URLS_FILE.exists():
        with open(URLS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle different data formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                all_urls = []
                for key, urls in data.items():
                    if isinstance(urls, list):
                        all_urls.extend(urls)
                return all_urls
    return []


def get_hugo_content_urls():
    """Get all content URLs from Hugo site."""
    urls = []

    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)

        # Convert to URL path
        if md_file.name == "_index.md":
            # Section index
            url = "/" + str(rel_path.parent).replace("\\", "/") + "/"
            if url == "/./" or url == "/./":
                url = "/"
        elif md_file.name == "index.md":
            url = "/" + str(rel_path.parent).replace("\\", "/") + "/"
        else:
            # Regular page
            url = "/" + str(rel_path.with_suffix("")).replace("\\", "/") + "/"

        # Clean up path
        url = url.replace("//", "/")
        urls.append({
            'url': url,
            'file': str(md_file.relative_to(PROJECT_ROOT)),
            'name': md_file.stem
        })

    return urls


def analyze_content_quality():
    """Analyze content quality of all markdown files."""
    print("  Analyzing content quality...")
    quality_data = []

    for md_file in CONTENT_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')

            # Extract front matter
            front_matter = {}
            body = content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter_text = parts[1]
                    body = parts[2]

                    # Parse front matter
                    for line in front_matter_text.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            front_matter[key.strip()] = value.strip().strip('"\'')

            # Count words in body
            body_clean = re.sub(r'\s+', ' ', body)
            word_count = len(body_clean.split())

            # Check for images
            has_image = bool(re.search(r'!\[.*?\]\(.*?\)', content) or
                           front_matter.get('image'))

            # Check title
            has_title = bool(front_matter.get('title'))

            quality_data.append({
                'file': str(md_file.relative_to(PROJECT_ROOT)),
                'title': front_matter.get('title', 'No Title'),
                'word_count': word_count,
                'has_image': has_image,
                'has_title': has_title,
                'is_empty': word_count < 50,
                'section': md_file.relative_to(CONTENT_DIR).parts[0] if len(md_file.relative_to(CONTENT_DIR).parts) > 1 else 'root'
            })

        except Exception as e:
            print(f"    Error analyzing {md_file.name}: {e}")

    return quality_data


def check_internal_links():
    """Check for broken internal links."""
    print("  Checking internal links...")
    broken_links = []

    # Get all valid content paths
    valid_paths = set()
    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)

        if md_file.name in ("_index.md", "index.md"):
            path = "/" + str(rel_path.parent).replace("\\", "/")
        else:
            path = "/" + str(rel_path.with_suffix("")).replace("\\", "/")

        path = path.replace("//", "/").rstrip("/")
        valid_paths.add(path)
        valid_paths.add(path + "/")

    # Check links in all files
    link_pattern = re.compile(r'\[([^\]]+)\]\((/[^)]+)\)')

    for md_file in CONTENT_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')

            for match in link_pattern.finditer(content):
                link_text = match.group(1)
                link_url = match.group(2)

                # Skip external links and anchors
                if link_url.startswith('http') or link_url.startswith('#'):
                    continue

                # Skip image paths
                if link_url.startswith('/images/'):
                    continue

                # Remove anchor if present
                if '#' in link_url:
                    link_url = link_url.split('#')[0]

                # Check if path exists
                check_path = link_url.rstrip('/')
                if check_path not in valid_paths and check_path + "/" not in valid_paths:
                    broken_links.append({
                        'source_file': str(md_file.relative_to(PROJECT_ROOT)),
                        'link_text': link_text,
                        'link_url': link_url
                    })

        except Exception as e:
            pass

    return broken_links


def compare_with_original():
    """Compare Hugo content with original Wix URLs."""
    print("  Comparing with original Wix URLs...")

    original_urls = load_original_urls()
    hugo_urls = get_hugo_content_urls()

    # Normalize URLs for comparison
    def normalize_url(url):
        parsed = urlparse(url)
        path = parsed.path.strip('/').lower()
        return path

    original_set = set()
    for url in original_urls:
        if isinstance(url, str):
            original_set.add(normalize_url(url))
        elif isinstance(url, dict) and 'url' in url:
            original_set.add(normalize_url(url['url']))

    hugo_set = set(normalize_url(u['url']) for u in hugo_urls)

    # Find differences
    missing_in_hugo = original_set - hugo_set
    extra_in_hugo = hugo_set - original_set

    return {
        'original_count': len(original_set),
        'hugo_count': len(hugo_set),
        'missing_in_hugo': list(missing_in_hugo)[:50],  # First 50
        'extra_in_hugo': list(extra_in_hugo)[:50],
        'coverage_percent': round(len(hugo_set & original_set) / max(len(original_set), 1) * 100, 1)
    }


def get_section_stats():
    """Get statistics by content section."""
    print("  Calculating section statistics...")
    stats = defaultdict(lambda: {'count': 0, 'total_words': 0, 'with_images': 0})

    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)
        section = rel_path.parts[0] if len(rel_path.parts) > 1 else 'root'

        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')

            # Get body text
            if content.startswith('---'):
                parts = content.split('---', 2)
                body = parts[2] if len(parts) >= 3 else content
            else:
                body = content

            word_count = len(body.split())
            has_image = bool(re.search(r'!\[.*?\]\(.*?\)|^image:', content, re.MULTILINE))

            stats[section]['count'] += 1
            stats[section]['total_words'] += word_count
            if has_image:
                stats[section]['with_images'] += 1

        except:
            pass

    # Calculate averages
    for section in stats:
        if stats[section]['count'] > 0:
            stats[section]['avg_words'] = round(stats[section]['total_words'] / stats[section]['count'])

    return dict(stats)


def run_verification():
    """Run the content verification."""
    print("=" * 60)
    print("CONTENT VERIFICATION")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        'date': datetime.now().isoformat(),
        'quality': {},
        'comparison': {},
        'broken_links': [],
        'section_stats': {},
        'issues': []
    }

    # 1. Analyze content quality
    print("[1/4] Analyzing content quality...")
    quality_data = analyze_content_quality()

    empty_pages = [q for q in quality_data if q['is_empty']]
    no_title = [q for q in quality_data if not q['has_title']]
    no_image = [q for q in quality_data if not q['has_image']]

    results['quality'] = {
        'total_files': len(quality_data),
        'empty_pages': len(empty_pages),
        'no_title': len(no_title),
        'no_image': len(no_image),
        'empty_files': [q['file'] for q in empty_pages[:20]]
    }

    print(f"  Total files: {len(quality_data)}")
    print(f"  Empty pages: {len(empty_pages)}")
    print(f"  Missing titles: {len(no_title)}")
    print(f"  Missing images: {len(no_image)}")

    # 2. Compare with original
    print("\n[2/4] Comparing with original Wix site...")
    comparison = compare_with_original()
    results['comparison'] = comparison
    print(f"  Original URLs: {comparison['original_count']}")
    print(f"  Hugo content: {comparison['hugo_count']}")
    print(f"  Coverage: {comparison['coverage_percent']}%")
    print(f"  Missing in Hugo: {len(comparison['missing_in_hugo'])}")

    # 3. Check internal links
    print("\n[3/4] Checking internal links...")
    broken_links = check_internal_links()
    results['broken_links'] = broken_links[:50]  # First 50
    print(f"  Broken internal links: {len(broken_links)}")

    # 4. Section statistics
    print("\n[4/4] Calculating section statistics...")
    section_stats = get_section_stats()
    results['section_stats'] = section_stats

    print("  Section stats:")
    for section, stats in sorted(section_stats.items()):
        print(f"    {section}: {stats['count']} files, avg {stats.get('avg_words', 0)} words")

    # Compile issues
    if len(empty_pages) > 10:
        results['issues'].append(f"{len(empty_pages)} pages have very little content")
    if comparison['coverage_percent'] < 90:
        results['issues'].append(f"Content coverage is only {comparison['coverage_percent']}%")
    if len(broken_links) > 50:
        results['issues'].append(f"{len(broken_links)} broken internal links")

    return results


def save_report(results):
    """Save verification report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "content_verification_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    results = run_verification()
    save_report(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total content files: {results['quality']['total_files']}")
    print(f"  Empty pages: {results['quality']['empty_pages']}")
    print(f"  Content coverage: {results['comparison']['coverage_percent']}%")
    print(f"  Broken links: {len(results['broken_links'])}")

    if results['issues']:
        print("\n  ISSUES:")
        for issue in results['issues']:
            print(f"    - {issue}")
    else:
        print("\n  No major issues found.")

    print("=" * 60)


if __name__ == "__main__":
    main()
