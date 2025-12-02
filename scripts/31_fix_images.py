"""
31_fix_images.py
Fix image references in markdown files.
Scans for missing images and optionally re-downloads from Wix CDN.

Usage:
    python scripts/31_fix_images.py
    python scripts/31_fix_images.py --download-missing
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import re
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images"
DATA_DIR = PROJECT_ROOT / "data"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Patterns to find images in markdown
MD_IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
HTML_IMG_PATTERN = re.compile(r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>')
FRONTMATTER_IMG_PATTERN = re.compile(r'^images?:\s*["\']?([^"\'>\n]+)["\']?', re.MULTILINE)
COVER_IMG_PATTERN = re.compile(r'image:\s*["\']?(/[^"\'>\n]+)["\']?', re.MULTILINE)


def get_all_markdown_files():
    """Get all markdown files in content directory."""
    return list(CONTENT_DIR.rglob("*.md"))


def get_all_static_images():
    """Get all image files in static directory."""
    images = {}
    if IMAGES_DIR.exists():
        for f in IMAGES_DIR.rglob("*"):
            if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                rel_path = "/images/" + str(f.relative_to(IMAGES_DIR)).replace("\\", "/")
                images[rel_path.lower()] = str(f)
    return images


def extract_images_from_file(md_file):
    """Extract all image references from a markdown file."""
    images = []
    try:
        content = md_file.read_text(encoding='utf-8', errors='replace')

        # Find markdown images
        for match in MD_IMG_PATTERN.finditer(content):
            alt_text, url = match.groups()
            images.append({
                'type': 'markdown',
                'url': url.strip(),
                'alt': alt_text,
                'file': str(md_file)
            })

        # Find HTML images
        for match in HTML_IMG_PATTERN.finditer(content):
            url = match.group(1)
            images.append({
                'type': 'html',
                'url': url.strip(),
                'alt': '',
                'file': str(md_file)
            })

        # Find frontmatter images
        for match in COVER_IMG_PATTERN.finditer(content):
            url = match.group(1)
            if url.startswith('/'):
                images.append({
                    'type': 'frontmatter',
                    'url': url.strip(),
                    'alt': '',
                    'file': str(md_file)
                })

    except Exception as e:
        print(f"  Error reading {md_file}: {e}")

    return images


def download_image(url, save_path):
    """Download an image from URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"    Failed to download {url}: {e}")
        return False


def fix_image_path(old_path, existing_images):
    """Try to find a matching image for a broken path."""
    # Normalize the path
    normalized = old_path.lower().replace("\\", "/")

    # Direct match
    if normalized in existing_images:
        return old_path

    # Try without leading slash
    if normalized.startswith("/"):
        without_slash = normalized[1:]
        for img_path in existing_images:
            if img_path.endswith(without_slash):
                return img_path

    # Try just the filename
    filename = Path(old_path).name.lower()
    for img_path, full_path in existing_images.items():
        if Path(img_path).name.lower() == filename:
            return img_path

    return None


def check_and_fix_images(download_missing=False):
    """Main function to check and fix image references."""
    print("=" * 60)
    print("IMAGE REFERENCE CHECKER")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get existing images
    print("[1/3] Indexing existing images...")
    existing_images = get_all_static_images()
    print(f"  Found {len(existing_images)} images in static/images/")

    # Extract all image references
    print("[2/3] Extracting image references from markdown files...")
    md_files = get_all_markdown_files()
    all_images = []
    for md_file in md_files:
        images = extract_images_from_file(md_file)
        all_images.extend(images)
    print(f"  Found {len(all_images)} image references")

    # Check each image
    print("[3/3] Checking image references...")
    results = {
        'total': len(all_images),
        'found': [],
        'missing': [],
        'external': [],
        'fixed': [],
        'downloaded': []
    }

    for img in all_images:
        url = img['url']

        # Skip external images
        if url.startswith(('http://', 'https://', '//')):
            results['external'].append(img)
            continue

        # Skip data URLs
        if url.startswith('data:'):
            continue

        # Check if image exists
        normalized = url.lower()
        if normalized in existing_images:
            results['found'].append(img)
        else:
            # Try to find a match
            fixed_path = fix_image_path(url, existing_images)
            if fixed_path:
                img['fixed_path'] = fixed_path
                results['fixed'].append(img)
            else:
                results['missing'].append(img)

    return results


def update_markdown_files(results):
    """Update markdown files with fixed image paths."""
    print("\nUpdating markdown files with fixed paths...")
    updated_files = set()

    for img in results['fixed']:
        file_path = Path(img['file'])
        try:
            content = file_path.read_text(encoding='utf-8', errors='replace')
            old_url = img['url']
            new_url = img['fixed_path']

            if old_url != new_url:
                content = content.replace(old_url, new_url)
                file_path.write_text(content, encoding='utf-8')
                updated_files.add(str(file_path))
        except Exception as e:
            print(f"  Error updating {file_path}: {e}")

    print(f"  Updated {len(updated_files)} files")
    return list(updated_files)


def remove_broken_image_refs(results):
    """Remove or comment out broken image references."""
    print("\nRemoving broken image references...")
    updated_files = set()

    # Group missing images by file
    by_file = {}
    for img in results['missing']:
        file_path = img['file']
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(img)

    for file_path, images in by_file.items():
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='replace')
            original_content = content

            for img in images:
                url = img['url']
                # Remove markdown image syntax
                pattern = rf'!\[[^\]]*\]\({re.escape(url)}\)'
                content = re.sub(pattern, '', content)
                # Remove HTML img tags
                pattern = rf'<img[^>]*src=["\']?{re.escape(url)}["\']?[^>]*/?>'
                content = re.sub(pattern, '', content)

            if content != original_content:
                Path(file_path).write_text(content, encoding='utf-8')
                updated_files.add(file_path)

        except Exception as e:
            print(f"  Error updating {file_path}: {e}")

    print(f"  Cleaned {len(updated_files)} files")
    return list(updated_files)


def save_report(results):
    """Save the image check report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        'date': datetime.now().isoformat(),
        'summary': {
            'total_references': results['total'],
            'found': len(results['found']),
            'missing': len(results['missing']),
            'external': len(results['external']),
            'fixed': len(results['fixed'])
        },
        'missing_images': [{'url': img['url'], 'file': Path(img['file']).name} for img in results['missing'][:100]],
        'fixed_images': [{'old': img['url'], 'new': img['fixed_path'], 'file': Path(img['file']).name} for img in results['fixed'][:50]]
    }

    output_file = DATA_DIR / "image_check_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    download_missing = '--download-missing' in sys.argv

    results = check_and_fix_images(download_missing)

    # Update files with fixed paths
    if results['fixed']:
        update_markdown_files(results)

    # Remove broken references
    if results['missing']:
        remove_broken_image_refs(results)

    save_report(results)

    print("\n" + "=" * 60)
    print("IMAGE CHECK SUMMARY")
    print("=" * 60)
    print(f"  Total image references: {results['total']}")
    print(f"  Found (OK): {len(results['found'])}")
    print(f"  External (skipped): {len(results['external'])}")
    print(f"  Fixed paths: {len(results['fixed'])}")
    print(f"  Missing (removed): {len(results['missing'])}")

    if results['missing']:
        print(f"\n  Sample missing images:")
        for img in results['missing'][:5]:
            print(f"    - {img['url']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
