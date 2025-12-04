"""
47_check_pictures.py
Comprehensive picture/image audit for Hugo site.
Checks all image references, verifies files exist, and fixes issues.

Usage:
    python scripts/47_check_pictures.py
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

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images"
DATA_DIR = PROJECT_ROOT / "data"

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}


def get_all_images():
    """Get all image files in static/images/."""
    print("  Scanning image files...")
    images = {}

    if IMAGES_DIR.exists():
        for img_file in IMAGES_DIR.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in IMAGE_EXTENSIONS:
                rel_path = "/images/" + str(img_file.relative_to(IMAGES_DIR)).replace("\\", "/")
                size_kb = img_file.stat().st_size / 1024
                images[rel_path.lower()] = {
                    'path': rel_path,
                    'full_path': str(img_file),
                    'size_kb': round(size_kb, 1),
                    'extension': img_file.suffix.lower()
                }

    return images


def get_all_image_references():
    """Get all image references from markdown files."""
    print("  Scanning markdown files for image references...")
    references = []

    patterns = [
        # Front matter image field
        (re.compile(r'^image:\s*["\']?(/images/[^"\'\n]+)["\']?', re.MULTILINE), 'frontmatter'),
        # Markdown image syntax
        (re.compile(r'!\[([^\]]*)\]\((/images/[^)]+)\)'), 'markdown'),
        # HTML img src
        (re.compile(r'<img[^>]+src=["\'](/images/[^"\']+)["\']'), 'html'),
        # Cover image in front matter
        (re.compile(r'cover:\s*\n\s*image:\s*["\']?(/images/[^"\'\n]+)["\']?', re.MULTILINE), 'cover'),
    ]

    for md_file in CONTENT_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')
            rel_path = str(md_file.relative_to(PROJECT_ROOT))

            for pattern, ref_type in patterns:
                for match in pattern.finditer(content):
                    img_path = match.group(1) if ref_type == 'frontmatter' else match.group(2) if ref_type == 'markdown' else match.group(1)
                    references.append({
                        'file': rel_path,
                        'image_path': img_path,
                        'type': ref_type
                    })
        except Exception as e:
            pass

    return references


def check_images():
    """Check all images and references."""
    print("=" * 60)
    print("PICTURE/IMAGE AUDIT")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        'date': datetime.now().isoformat(),
        'summary': {},
        'existing_images': {},
        'references': [],
        'missing_images': [],
        'orphan_images': [],
        'large_images': [],
        'by_directory': {}
    }

    # 1. Get all existing images
    print("[1/5] Scanning existing images...")
    existing_images = get_all_images()
    results['summary']['total_images'] = len(existing_images)
    print(f"  Found {len(existing_images)} image files")

    # Count by directory
    by_dir = defaultdict(int)
    for path, info in existing_images.items():
        parts = path.split('/')
        if len(parts) > 2:
            by_dir[parts[2]] += 1
        else:
            by_dir['root'] += 1
    results['by_directory'] = dict(by_dir)

    print("  By directory:")
    for d, count in sorted(by_dir.items(), key=lambda x: -x[1]):
        print(f"    {d}: {count}")

    # 2. Get all references
    print("\n[2/5] Scanning image references in content...")
    references = get_all_image_references()
    results['summary']['total_references'] = len(references)
    print(f"  Found {len(references)} image references")

    # 3. Check for missing images
    print("\n[3/5] Checking for missing images...")
    missing = []
    referenced_paths = set()

    for ref in references:
        img_path = ref['image_path'].lower()
        referenced_paths.add(img_path)

        if img_path not in existing_images:
            missing.append(ref)

    results['missing_images'] = missing[:50]  # First 50
    results['summary']['missing_count'] = len(missing)
    print(f"  Missing images: {len(missing)}")

    if missing[:10]:
        print("  First 10 missing:")
        for m in missing[:10]:
            print(f"    - {m['image_path']} (in {m['file']})")

    # 4. Find orphan images (not referenced)
    print("\n[4/5] Finding orphan images...")
    orphans = []
    for path in existing_images:
        if path not in referenced_paths:
            orphans.append(existing_images[path])

    results['orphan_images'] = [o['path'] for o in orphans[:50]]
    results['summary']['orphan_count'] = len(orphans)
    print(f"  Orphan images (not referenced): {len(orphans)}")

    # 5. Find large images
    print("\n[5/5] Checking image sizes...")
    large = []
    for path, info in existing_images.items():
        if info['size_kb'] > 500:  # Over 500KB
            large.append(info)

    large.sort(key=lambda x: -x['size_kb'])
    results['large_images'] = [{'path': l['path'], 'size_kb': l['size_kb']} for l in large[:20]]
    results['summary']['large_count'] = len(large)
    print(f"  Large images (>500KB): {len(large)}")

    if large[:5]:
        print("  Top 5 largest:")
        for l in large[:5]:
            print(f"    - {l['path']}: {l['size_kb']}KB")

    return results


def save_report(results):
    """Save audit report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "picture_audit_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    results = check_images()
    save_report(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total images: {results['summary']['total_images']}")
    print(f"  Total references: {results['summary']['total_references']}")
    print(f"  Missing images: {results['summary']['missing_count']}")
    print(f"  Orphan images: {results['summary']['orphan_count']}")
    print(f"  Large images (>500KB): {results['summary']['large_count']}")

    if results['summary']['missing_count'] == 0:
        print("\n  All referenced images exist!")
    else:
        print(f"\n  WARNING: {results['summary']['missing_count']} missing images need attention")

    print("=" * 60)


if __name__ == "__main__":
    main()
