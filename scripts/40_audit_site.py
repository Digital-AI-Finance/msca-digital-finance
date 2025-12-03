"""
40_audit_site.py
Comprehensive audit of the current Hugo site state.
Counts content files, verifies images, checks navigation.

Usage:
    python scripts/40_audit_site.py
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
THEMES_DIR = PROJECT_ROOT / "themes"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_FILE = PROJECT_ROOT / "hugo.toml"

def count_content_files():
    """Count content files by section."""
    sections = defaultdict(int)
    total = 0

    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)
        parts = rel_path.parts

        if len(parts) == 1:
            section = "root"
        else:
            section = parts[0]

        sections[section] += 1
        total += 1

    return dict(sections), total

def count_images():
    """Count image files by directory."""
    image_dirs = defaultdict(int)
    total = 0
    extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}

    if IMAGES_DIR.exists():
        for img_file in IMAGES_DIR.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in extensions:
                rel_path = img_file.relative_to(IMAGES_DIR)
                if len(rel_path.parts) > 1:
                    subdir = rel_path.parts[0]
                else:
                    subdir = "root"
                image_dirs[subdir] += 1
                total += 1

    return dict(image_dirs), total

def check_image_references():
    """Check if images referenced in markdown exist."""
    referenced = set()
    missing = []
    found = []

    img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)|src=["\']([^"\']+)["\']|image:\s*["\']?(/[^"\'>\n]+)["\']?')

    for md_file in CONTENT_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')
            for match in img_pattern.finditer(content):
                img_url = match.group(2) or match.group(3) or match.group(4)
                if img_url and img_url.startswith('/images/'):
                    referenced.add(img_url)
                    # Check if file exists
                    img_path = STATIC_DIR / img_url.lstrip('/')
                    if img_path.exists():
                        found.append(img_url)
                    else:
                        missing.append({
                            'url': img_url,
                            'file': str(md_file.relative_to(PROJECT_ROOT))
                        })
        except Exception as e:
            pass

    return len(referenced), len(found), missing

def check_navigation():
    """Check navigation menu configuration."""
    nav_items = []

    if CONFIG_FILE.exists():
        content = CONFIG_FILE.read_text(encoding='utf-8', errors='replace')

        # Parse menu items from TOML
        menu_pattern = re.compile(r'\[\[menu\.main\]\].*?name\s*=\s*["\']([^"\']+)["\'].*?url\s*=\s*["\']([^"\']+)["\']', re.DOTALL)

        for match in menu_pattern.finditer(content):
            name = match.group(1)
            url = match.group(2)

            # Check if URL resolves
            if url.startswith('/'):
                content_path = CONTENT_DIR / url.strip('/').replace('/', os.sep)
                # Check for index.md or _index.md or direct .md file
                exists = (
                    (content_path / '_index.md').exists() or
                    (content_path / 'index.md').exists() or
                    content_path.with_suffix('.md').exists()
                )
            else:
                exists = True  # External URL

            nav_items.append({
                'name': name,
                'url': url,
                'exists': exists
            })

    return nav_items

def check_theme():
    """Check theme installation."""
    themes = []

    if THEMES_DIR.exists():
        for theme_dir in THEMES_DIR.iterdir():
            if theme_dir.is_dir():
                has_layouts = (theme_dir / 'layouts').exists()
                themes.append({
                    'name': theme_dir.name,
                    'has_layouts': has_layouts,
                    'path': str(theme_dir)
                })

    return themes

def run_audit():
    """Run complete site audit."""
    print("=" * 60)
    print("SITE AUDIT REPORT")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        'date': datetime.now().isoformat(),
        'content': {},
        'images': {},
        'navigation': [],
        'themes': [],
        'issues': []
    }

    # 1. Content Files
    print("[1/5] Counting content files...")
    sections, total_content = count_content_files()
    results['content'] = {
        'total': total_content,
        'by_section': sections
    }
    print(f"  Total: {total_content} markdown files")
    for section, count in sorted(sections.items()):
        print(f"    {section}: {count}")

    # 2. Image Files
    print("\n[2/5] Counting image files...")
    image_dirs, total_images = count_images()
    results['images']['files'] = {
        'total': total_images,
        'by_directory': image_dirs
    }
    print(f"  Total: {total_images} image files")
    for subdir, count in sorted(image_dirs.items()):
        print(f"    {subdir}: {count}")

    # 3. Image References
    print("\n[3/5] Checking image references...")
    total_refs, found_refs, missing_imgs = check_image_references()
    results['images']['references'] = {
        'total': total_refs,
        'found': found_refs,
        'missing_count': len(missing_imgs),
        'missing': missing_imgs[:20]  # First 20
    }
    print(f"  Total references: {total_refs}")
    print(f"  Found: {found_refs}")
    print(f"  Missing: {len(missing_imgs)}")
    if missing_imgs:
        results['issues'].append(f"{len(missing_imgs)} missing images")

    # 4. Navigation
    print("\n[4/5] Checking navigation...")
    nav_items = check_navigation()
    results['navigation'] = nav_items
    broken_nav = [n for n in nav_items if not n['exists']]
    print(f"  Menu items: {len(nav_items)}")
    for item in nav_items:
        status = "OK" if item['exists'] else "MISSING"
        print(f"    {item['name']}: {item['url']} [{status}]")
    if broken_nav:
        results['issues'].append(f"{len(broken_nav)} broken navigation links")

    # 5. Theme
    print("\n[5/5] Checking themes...")
    themes = check_theme()
    results['themes'] = themes
    print(f"  Installed themes: {len(themes)}")
    for theme in themes:
        status = "OK" if theme['has_layouts'] else "NO LAYOUTS"
        print(f"    {theme['name']}: [{status}]")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Content files: {total_content}")
    print(f"  Image files: {total_images}")
    print(f"  Missing images: {len(missing_imgs)}")
    print(f"  Navigation items: {len(nav_items)}")
    print(f"  Broken nav links: {len(broken_nav)}")
    print(f"  Themes installed: {len(themes)}")

    if results['issues']:
        print(f"\n  ISSUES FOUND:")
        for issue in results['issues']:
            print(f"    - {issue}")
    else:
        print(f"\n  No major issues found.")

    return results

def save_report(results):
    """Save audit report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "site_audit_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file

def main():
    results = run_audit()
    save_report(results)
    print("=" * 60)

if __name__ == "__main__":
    main()
