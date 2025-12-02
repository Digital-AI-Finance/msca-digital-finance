"""
10_final_report.py
Generates a comprehensive verification report comparing
all discovered content against what was actually scraped.
"""

import sys
import io

# Fix Windows console encoding for Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"


def load_json_file(filepath):
    """Load a JSON file if it exists."""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def count_files_by_category():
    """Count markdown files by category."""
    categories = defaultdict(int)

    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)
        parts = rel_path.parts

        if len(parts) == 1:
            categories['root_pages'] += 1
        else:
            categories[parts[0]] += 1

    return dict(categories)


def count_images_by_category():
    """Count images by category."""
    categories = defaultdict(int)
    total_size = 0

    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']

    images_dir = STATIC_DIR / "images"
    if images_dir.exists():
        for img_path in images_dir.rglob("*"):
            if img_path.suffix.lower() in image_extensions:
                rel_path = img_path.relative_to(images_dir)
                parts = rel_path.parts

                if len(parts) == 1:
                    categories['root'] += 1
                else:
                    categories[parts[0]] += 1

                total_size += img_path.stat().st_size

    return dict(categories), total_size


def get_content_quality_metrics():
    """Calculate content quality metrics."""
    metrics = {
        'total_files': 0,
        'total_words': 0,
        'empty_content': [],
        'short_content': [],  # Less than 50 words
        'files_with_images': 0,
        'word_counts': {}
    }

    for md_file in CONTENT_DIR.rglob("*.md"):
        metrics['total_files'] += 1

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip front matter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]

        # Count words
        words = len(content.split())
        metrics['total_words'] += words

        rel_path = str(md_file.relative_to(CONTENT_DIR))
        metrics['word_counts'][rel_path] = words

        if words < 10:
            metrics['empty_content'].append(rel_path)
        elif words < 50:
            metrics['short_content'].append(rel_path)

        # Check for images
        if '![' in content or '<img' in content or 'image:' in content:
            metrics['files_with_images'] += 1

    return metrics


def generate_report():
    """Generate comprehensive verification report."""
    print("=" * 60)
    print("COMPREHENSIVE VERIFICATION REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    report = {
        'generated_at': datetime.now().isoformat(),
        'sections': {}
    }

    # 1. URL Coverage
    print("-" * 60)
    print("1. URL COVERAGE")
    print("-" * 60)

    urls_data = load_json_file(DATA_DIR / "urls.json")
    progress_data = load_json_file(DATA_DIR / "scrape_progress.json")
    crawl_data = load_json_file(DATA_DIR / "deep_crawl_results.json")

    sitemap_count = 0
    if urls_data:
        for category, urls in urls_data.get('categories', {}).items():
            sitemap_count += len(urls)
        print(f"  URLs from sitemaps: {sitemap_count}")

    scraped_count = 0
    failed_count = 0
    if progress_data:
        scraped_count = len(progress_data.get('scraped_urls', []))
        failed_count = len(progress_data.get('failed_urls', []))
        print(f"  URLs scraped: {scraped_count}")
        print(f"  URLs failed: {failed_count}")

    if crawl_data:
        print(f"  URLs discovered by deep crawl: {crawl_data.get('total_discovered', 0)}")
        print(f"  Missing pages (not in sitemaps): {len(crawl_data.get('missing_urls', []))}")
        print(f"  Orphaned pages (not linked): {len(crawl_data.get('orphaned_urls', []))}")

    report['sections']['url_coverage'] = {
        'sitemap_urls': sitemap_count,
        'scraped_urls': scraped_count,
        'failed_urls': failed_count,
        'deep_crawl': crawl_data
    }

    # 2. Content Statistics
    print()
    print("-" * 60)
    print("2. CONTENT STATISTICS")
    print("-" * 60)

    file_counts = count_files_by_category()
    total_files = sum(file_counts.values())
    print(f"  Total markdown files: {total_files}")
    print("  By category:")
    for category, count in sorted(file_counts.items()):
        print(f"    - {category}: {count}")

    report['sections']['content_stats'] = {
        'total_files': total_files,
        'by_category': file_counts
    }

    # 3. Image Statistics
    print()
    print("-" * 60)
    print("3. IMAGE STATISTICS")
    print("-" * 60)

    image_counts, total_size = count_images_by_category()
    total_images = sum(image_counts.values())
    print(f"  Total images: {total_images}")
    print(f"  Total size: {total_size / (1024*1024):.1f} MB")
    print("  By category:")
    for category, count in sorted(image_counts.items()):
        print(f"    - {category}: {count}")

    report['sections']['image_stats'] = {
        'total_images': total_images,
        'total_size_bytes': total_size,
        'by_category': image_counts
    }

    # 4. Content Quality
    print()
    print("-" * 60)
    print("4. CONTENT QUALITY")
    print("-" * 60)

    quality = get_content_quality_metrics()
    avg_words = quality['total_words'] / quality['total_files'] if quality['total_files'] > 0 else 0

    print(f"  Total words: {quality['total_words']:,}")
    print(f"  Average words per page: {avg_words:.0f}")
    print(f"  Pages with images: {quality['files_with_images']}")
    print(f"  Empty/minimal content (<10 words): {len(quality['empty_content'])}")
    print(f"  Short content (<50 words): {len(quality['short_content'])}")

    report['sections']['content_quality'] = {
        'total_words': quality['total_words'],
        'average_words': avg_words,
        'files_with_images': quality['files_with_images'],
        'empty_content': quality['empty_content'],
        'short_content': quality['short_content']
    }

    # 5. Asset Extraction
    print()
    print("-" * 60)
    print("5. ASSET EXTRACTION")
    print("-" * 60)

    asset_data = load_json_file(DATA_DIR / "asset_extraction_results.json")
    if asset_data:
        assets = asset_data.get('assets', {})
        print(f"  PDFs found: {len(assets.get('pdfs', []))}")
        print(f"  Documents found: {len(assets.get('documents', []))}")
        print(f"  Videos found: {len(assets.get('videos', []))}")
        print(f"  External links: {len(assets.get('external_links', []))}")

        report['sections']['assets'] = assets
    else:
        print("  (Run 08_extract_assets.py first)")

    # 6. Link Integrity
    print()
    print("-" * 60)
    print("6. LINK INTEGRITY")
    print("-" * 60)

    link_data = load_json_file(DATA_DIR / "link_fix_results.json")
    if link_data:
        print(f"  Links fixed: {link_data.get('total_fixes', 0)}")
        print(f"  Broken links remaining: {link_data.get('broken_remaining', 0)}")

        broken = link_data.get('broken_summary', {})
        print(f"    - Broken images: {len(broken.get('broken_images', []))}")
        print(f"    - Broken page links: {len(broken.get('broken_pages', []))}")

        report['sections']['links'] = {
            'fixed': link_data.get('total_fixes', 0),
            'broken': link_data.get('broken_remaining', 0),
            'broken_summary': broken
        }
    else:
        print("  (Run 09_fix_links.py first)")

    # 7. Summary & Recommendations
    print()
    print("=" * 60)
    print("7. SUMMARY & RECOMMENDATIONS")
    print("=" * 60)

    issues = []
    if failed_count > 0:
        issues.append(f"- {failed_count} URLs failed to scrape (review scrape_progress.json)")

    if crawl_data and crawl_data.get('missing_urls'):
        issues.append(f"- {len(crawl_data['missing_urls'])} pages found by crawl but not in sitemaps")

    if len(quality['empty_content']) > 0:
        issues.append(f"- {len(quality['empty_content'])} pages have minimal content")

    if link_data and link_data.get('broken_remaining', 0) > 0:
        issues.append(f"- {link_data['broken_remaining']} broken links need manual review")

    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n  All checks passed!")

    print("\nRecommendations:")
    print("  1. Review any failed URLs and retry scraping")
    print("  2. Check pages with minimal content for rendering issues")
    print("  3. Manually verify video embeds are preserved")
    print("  4. Test the Hugo site locally before pushing")

    report['sections']['summary'] = {
        'issues': issues,
        'status': 'needs_attention' if issues else 'complete'
    }

    # Save report
    report_file = DATA_DIR / "final_verification_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nFull report saved to: {report_file}")

    # Also save as readable text
    text_report = DATA_DIR / "VERIFICATION_REPORT.txt"
    with open(text_report, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("MSCA DIGITAL FINANCE - MIGRATION VERIFICATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("URL Coverage:\n")
        f.write(f"  - Sitemap URLs: {sitemap_count}\n")
        f.write(f"  - Scraped: {scraped_count}\n")
        f.write(f"  - Failed: {failed_count}\n\n")

        f.write("Content:\n")
        f.write(f"  - Total pages: {total_files}\n")
        f.write(f"  - Total images: {total_images}\n")
        f.write(f"  - Total words: {quality['total_words']:,}\n\n")

        f.write("Issues:\n")
        for issue in issues:
            f.write(f"  {issue}\n")

        if not issues:
            f.write("  No major issues found!\n")

    print(f"Text report saved to: {text_report}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    generate_report()
