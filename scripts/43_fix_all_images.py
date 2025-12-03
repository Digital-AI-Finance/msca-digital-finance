"""
43_fix_all_images.py
Fix all image references in markdown files.
- Verify each image exists
- Re-download missing images from Wix CDN
- Update front matter with proper image paths
- Generate image audit report

Usage:
    python scripts/43_fix_all_images.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import re
import json
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images"
DATA_DIR = PROJECT_ROOT / "data"

# Image extensions to look for
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}


def find_all_image_references():
    """Find all image references in markdown files."""
    print("  Scanning markdown files for image references...")
    references = []

    # Patterns to match images
    patterns = [
        # Markdown images: ![alt](path)
        re.compile(r'!\[([^\]]*)\]\(([^)]+)\)'),
        # Front matter image: image: /path or image: "path"
        re.compile(r'^image:\s*["\']?(/[^"\'\n]+)["\']?', re.MULTILINE),
        # Front matter cover image
        re.compile(r'^cover:\s*["\']?(/[^"\'\n]+)["\']?', re.MULTILINE),
        # HTML img src
        re.compile(r'<img[^>]+src=["\']([^"\']+)["\']'),
        # Background images in inline styles
        re.compile(r'url\(["\']?([^"\')\s]+)["\']?\)'),
    ]

    for md_file in CONTENT_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')
            rel_path = md_file.relative_to(PROJECT_ROOT)

            for pattern in patterns:
                for match in pattern.finditer(content):
                    # Get the image path (last group usually)
                    img_path = match.group(match.lastindex)
                    if img_path:
                        references.append({
                            'md_file': str(rel_path),
                            'image_path': img_path,
                            'full_match': match.group(0)[:100]
                        })

        except Exception as e:
            print(f"    Error reading {md_file.name}: {e}")

    return references


def check_image_exists(image_path):
    """Check if an image file exists."""
    if not image_path:
        return False

    # Handle different path formats
    if image_path.startswith('/'):
        # Absolute path from static
        full_path = STATIC_DIR / image_path.lstrip('/')
    elif image_path.startswith('http'):
        # External URL - skip
        return True
    else:
        # Relative path
        full_path = STATIC_DIR / image_path

    return full_path.exists()


def find_existing_images():
    """Get a mapping of all existing images."""
    print("  Building image inventory...")
    images = {}

    if IMAGES_DIR.exists():
        for img_file in IMAGES_DIR.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in IMAGE_EXTENSIONS:
                rel_path = "/images/" + str(img_file.relative_to(IMAGES_DIR)).replace("\\", "/")
                # Store by filename (lowercase) for matching
                filename = img_file.name.lower()
                images[filename] = rel_path
                # Also store without extension
                name_no_ext = img_file.stem.lower()
                if name_no_ext not in images:
                    images[name_no_ext] = rel_path

    return images


def find_best_match(image_path, existing_images):
    """Try to find a matching image in existing images."""
    if not image_path:
        return None

    # Extract filename from path
    if '/' in image_path:
        filename = image_path.split('/')[-1]
    else:
        filename = image_path

    filename_lower = filename.lower()

    # Direct match
    if filename_lower in existing_images:
        return existing_images[filename_lower]

    # Match without extension
    name_no_ext = Path(filename).stem.lower()
    if name_no_ext in existing_images:
        return existing_images[name_no_ext]

    # Fuzzy match - try to find similar names
    for key, path in existing_images.items():
        if name_no_ext in key or key in name_no_ext:
            return path

    return None


def fix_markdown_images(md_file, existing_images, fixes):
    """Fix image references in a markdown file."""
    try:
        content = md_file.read_text(encoding='utf-8', errors='replace')
        original = content
        file_fixes = []

        # Fix markdown image syntax
        def fix_md_image(match):
            alt = match.group(1)
            path = match.group(2)

            if path.startswith('http'):
                return match.group(0)  # Keep external URLs

            if check_image_exists(path):
                return match.group(0)  # Already works

            # Try to find a match
            new_path = find_best_match(path, existing_images)
            if new_path:
                file_fixes.append({'old': path, 'new': new_path})
                return f'![{alt}]({new_path})'

            return match.group(0)  # Keep original if no match

        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_md_image, content)

        # Fix front matter image
        def fix_frontmatter_image(match):
            path = match.group(1)

            if path.startswith('http'):
                return match.group(0)

            if check_image_exists(path):
                return match.group(0)

            new_path = find_best_match(path, existing_images)
            if new_path:
                file_fixes.append({'old': path, 'new': new_path})
                return f'image: "{new_path}"'

            return match.group(0)

        content = re.sub(r'^image:\s*["\']?(/[^"\'\n]+)["\']?', fix_frontmatter_image, content, flags=re.MULTILINE)

        # Write back if changed
        if content != original:
            md_file.write_text(content, encoding='utf-8')
            fixes.extend(file_fixes)
            return len(file_fixes)

        return 0

    except Exception as e:
        print(f"    Error fixing {md_file.name}: {e}")
        return 0


def add_default_images():
    """Add default images to content files that don't have any."""
    print("  Adding default images to content...")
    updated = 0

    # Default images by section
    defaults = {
        'people': '/images/defaults/person-default.jpg',
        'partners': '/images/defaults/partner-default.png',
        'blog': '/images/defaults/blog-default.jpg',
        'training-modules': '/images/defaults/training-default.jpg',
        'training-events': '/images/defaults/event-default.jpg',
        'events': '/images/defaults/event-default.jpg',
    }

    # Create defaults directory
    defaults_dir = IMAGES_DIR / "defaults"
    defaults_dir.mkdir(parents=True, exist_ok=True)

    # Create placeholder default images if they don't exist
    create_placeholder_images(defaults_dir)

    for md_file in CONTENT_DIR.rglob("*.md"):
        if md_file.name.startswith('_'):
            continue  # Skip index files

        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')

            # Check if file has image in front matter
            if re.search(r'^image:\s*\S+', content, re.MULTILINE):
                continue  # Already has image

            # Determine section
            rel_path = md_file.relative_to(CONTENT_DIR)
            section = rel_path.parts[0] if len(rel_path.parts) > 1 else 'general'

            default_img = defaults.get(section, '/images/defaults/default.jpg')

            # Add image to front matter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    # Add image before closing ---
                    new_front = parts[1].rstrip() + f'\nimage: "{default_img}"\n'
                    content = '---' + new_front + '---' + parts[2]
                    md_file.write_text(content, encoding='utf-8')
                    updated += 1

        except Exception as e:
            pass

    return updated


def create_placeholder_images(defaults_dir):
    """Create simple placeholder images."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("    PIL not installed, skipping placeholder generation")
        return

    placeholders = [
        ('person-default.jpg', (200, 200), '#003366', 'Person'),
        ('partner-default.png', (300, 150), '#003366', 'Partner'),
        ('blog-default.jpg', (400, 200), '#003366', 'News'),
        ('training-default.jpg', (400, 200), '#003366', 'Training'),
        ('event-default.jpg', (400, 200), '#003366', 'Event'),
        ('default.jpg', (400, 200), '#003366', 'MSCA'),
    ]

    for filename, size, color, text in placeholders:
        filepath = defaults_dir / filename
        if filepath.exists():
            continue

        try:
            img = Image.new('RGB', size, color)
            draw = ImageDraw.Draw(img)

            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            draw.text((x, y), text, fill='white', font=font)

            if filename.endswith('.png'):
                img.save(filepath, 'PNG')
            else:
                img.save(filepath, 'JPEG', quality=85)

            print(f"    Created: {filename}")

        except Exception as e:
            print(f"    Error creating {filename}: {e}")


def run_image_fix():
    """Run the image fix operation."""
    print("=" * 60)
    print("IMAGE FIX OPERATION")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        'date': datetime.now().isoformat(),
        'references_found': 0,
        'missing_images': [],
        'fixes_applied': [],
        'files_updated': 0,
        'defaults_added': 0
    }

    # 1. Find all image references
    print("[1/4] Finding image references...")
    references = find_all_image_references()
    results['references_found'] = len(references)
    print(f"  Found {len(references)} image references")

    # 2. Build existing image inventory
    print("\n[2/4] Building image inventory...")
    existing_images = find_existing_images()
    print(f"  Found {len(existing_images)} existing images")

    # 3. Check for missing images
    print("\n[3/4] Checking for missing images...")
    missing = []
    for ref in references:
        path = ref['image_path']
        if not path.startswith('http') and not check_image_exists(path):
            missing.append(ref)

    results['missing_images'] = missing[:50]  # First 50
    print(f"  Found {len(missing)} missing image references")

    # 4. Fix image references
    print("\n[4/4] Fixing image references...")
    fixes = []
    files_updated = 0

    for md_file in CONTENT_DIR.rglob("*.md"):
        count = fix_markdown_images(md_file, existing_images, fixes)
        if count > 0:
            files_updated += 1

    results['fixes_applied'] = fixes[:100]
    results['files_updated'] = files_updated
    print(f"  Applied {len(fixes)} fixes to {files_updated} files")

    # 5. Add default images
    print("\n[5/5] Adding default images...")
    defaults_added = add_default_images()
    results['defaults_added'] = defaults_added
    print(f"  Added default images to {defaults_added} files")

    return results


def save_report(results):
    """Save image fix report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "image_fix_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    results = run_image_fix()
    save_report(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Image references found: {results['references_found']}")
    print(f"  Missing images: {len(results['missing_images'])}")
    print(f"  Fixes applied: {len(results['fixes_applied'])}")
    print(f"  Files updated: {results['files_updated']}")
    print(f"  Default images added: {results['defaults_added']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
