"""
05_verify.py
Verifies the completeness of the migration and generates a report.
Checks for missing pages, broken links, and missing images.
"""

import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images"


def load_urls():
    """Load discovered URLs from JSON file."""
    urls_file = DATA_DIR / "urls.json"
    if urls_file.exists():
        with open(urls_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def count_markdown_files():
    """Count markdown files in content directory by category."""
    counts = {}
    total = 0

    for md_file in CONTENT_DIR.rglob('*.md'):
        relative = md_file.relative_to(CONTENT_DIR)
        parts = relative.parts

        if len(parts) > 1:
            category = parts[0]
        else:
            category = 'root'

        if category not in counts:
            counts[category] = 0
        counts[category] += 1
        total += 1

    return counts, total


def count_images():
    """Count downloaded images by category."""
    counts = {}
    total = 0

    if IMAGES_DIR.exists():
        for img_file in IMAGES_DIR.rglob('*'):
            if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                relative = img_file.relative_to(IMAGES_DIR)
                parts = relative.parts

                if len(parts) > 1:
                    category = parts[0]
                else:
                    category = 'root'

                if category not in counts:
                    counts[category] = 0
                counts[category] += 1
                total += 1

    return counts, total


def check_broken_internal_links():
    """Check for broken internal links in markdown files."""
    broken_links = []
    all_slugs = set()

    # Collect all slugs
    for md_file in CONTENT_DIR.rglob('*.md'):
        relative = md_file.relative_to(CONTENT_DIR)
        slug = str(relative.with_suffix('')).replace('\\', '/')
        all_slugs.add(slug)
        all_slugs.add('/' + slug + '/')

    # Check links in each file
    for md_file in CONTENT_DIR.rglob('*.md'):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find markdown links
        links = re.findall(r'\[([^\]]*)\]\((/[^\)]+)\)', content)

        for link_text, link_url in links:
            # Skip external links and anchors
            if link_url.startswith('http') or link_url.startswith('#'):
                continue

            # Check if link exists
            clean_url = link_url.rstrip('/')
            if clean_url not in all_slugs and clean_url + '/' not in all_slugs:
                broken_links.append({
                    'file': str(md_file.relative_to(CONTENT_DIR)),
                    'link': link_url,
                    'text': link_text
                })

    return broken_links


def check_missing_images():
    """Check for image references that don't have local files."""
    missing_images = []

    for md_file in CONTENT_DIR.rglob('*.md'):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find image references to local paths
        images = re.findall(r'!\[([^\]]*)\]\((/images/[^\)]+)\)', content)
        images += re.findall(r'src=[\'"]?(/images/[^\'">\s]+)[\'"]?', content)
        images += re.findall(r'image:\s*[\'"]?(/images/[^\'">\s]+)[\'"]?', content)

        for img in images:
            if isinstance(img, tuple):
                img_path = img[1]
            else:
                img_path = img

            # Convert URL path to file path
            local_path = STATIC_DIR / img_path.lstrip('/')

            if not local_path.exists():
                missing_images.append({
                    'file': str(md_file.relative_to(CONTENT_DIR)),
                    'image': img_path
                })

    return missing_images


def test_hugo_build():
    """Test if Hugo can build the site."""
    try:
        result = subprocess.run(
            ['hugo', '--minify'],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            # Parse build output for stats
            output = result.stderr + result.stdout
            return True, output
        else:
            return False, result.stderr
    except FileNotFoundError:
        return None, "Hugo not installed"
    except Exception as e:
        return False, str(e)


def generate_report():
    """Generate a comprehensive verification report."""
    print("=" * 60)
    print("Verification Report for MSCA Digital Finance Migration")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load discovered URLs
    urls_data = load_urls()
    expected_counts = {}
    total_expected = 0

    if urls_data:
        for category, urls in urls_data['categories'].items():
            expected_counts[category] = len(urls)
            total_expected += len(urls)

    # Count actual files
    actual_counts, total_actual = count_markdown_files()

    print("-" * 60)
    print("CONTENT FILES")
    print("-" * 60)
    print(f"{'Category':<25} {'Expected':<12} {'Actual':<12} {'Status'}")
    print("-" * 60)

    for category in sorted(set(list(expected_counts.keys()) + list(actual_counts.keys()))):
        expected = expected_counts.get(category, 0)
        actual = actual_counts.get(category, 0)

        if actual >= expected:
            status = "OK"
        elif actual == 0:
            status = "MISSING"
        else:
            status = f"PARTIAL ({actual}/{expected})"

        print(f"{category:<25} {expected:<12} {actual:<12} {status}")

    print("-" * 60)
    print(f"{'TOTAL':<25} {total_expected:<12} {total_actual:<12}")
    print()

    # Count images
    image_counts, total_images = count_images()

    print("-" * 60)
    print("IMAGES")
    print("-" * 60)
    print(f"Total downloaded images: {total_images}")
    for category, count in sorted(image_counts.items()):
        print(f"  {category}: {count}")
    print()

    # Check broken links
    print("-" * 60)
    print("INTERNAL LINKS CHECK")
    print("-" * 60)
    broken_links = check_broken_internal_links()
    if broken_links:
        print(f"Found {len(broken_links)} potentially broken links:")
        for bl in broken_links[:10]:  # Show first 10
            print(f"  {bl['file']}: {bl['link']}")
        if len(broken_links) > 10:
            print(f"  ... and {len(broken_links) - 10} more")
    else:
        print("No broken internal links found")
    print()

    # Check missing images
    print("-" * 60)
    print("MISSING IMAGES CHECK")
    print("-" * 60)
    missing_images = check_missing_images()
    if missing_images:
        print(f"Found {len(missing_images)} missing image references:")
        for mi in missing_images[:10]:  # Show first 10
            print(f"  {mi['file']}: {mi['image']}")
        if len(missing_images) > 10:
            print(f"  ... and {len(missing_images) - 10} more")
    else:
        print("All image references have local files")
    print()

    # Test Hugo build
    print("-" * 60)
    print("HUGO BUILD TEST")
    print("-" * 60)
    build_success, build_output = test_hugo_build()
    if build_success is None:
        print("Hugo not installed - skipping build test")
    elif build_success:
        print("Hugo build: SUCCESS")
        # Extract some stats from output
        if 'pages' in build_output.lower():
            for line in build_output.split('\n'):
                if 'page' in line.lower() or 'static' in line.lower():
                    print(f"  {line.strip()}")
    else:
        print("Hugo build: FAILED")
        print(f"Error: {build_output[:500]}")
    print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    issues = []
    if total_actual < total_expected:
        issues.append(f"Missing {total_expected - total_actual} content files")
    if broken_links:
        issues.append(f"{len(broken_links)} broken internal links")
    if missing_images:
        issues.append(f"{len(missing_images)} missing image files")
    if build_success is False:
        issues.append("Hugo build failed")

    if not issues:
        print("All checks passed! Migration looks complete.")
    else:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")

    print("=" * 60)

    # Save report to file
    report_file = DATA_DIR / "verification_report.txt"
    # Write report to file (simplified version)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Verification Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Expected: {total_expected}, Actual: {total_actual}\n")
        f.write(f"Images: {total_images}\n")
        f.write(f"Broken links: {len(broken_links)}\n")
        f.write(f"Missing images: {len(missing_images)}\n")
        f.write(f"Hugo build: {'Success' if build_success else 'Failed' if build_success is False else 'Not tested'}\n")

    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    generate_report()
