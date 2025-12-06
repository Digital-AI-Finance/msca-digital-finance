"""
verify_image_fix.py
Verify that all image references in Hugo templates use | relURL
"""

import sys
import io
import re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
LAYOUTS_DIR = PROJECT_ROOT / "layouts"

def check_template_images():
    """Check all templates for image tags without relURL."""
    print("=" * 80)
    print("VERIFY IMAGE FIX - HUGO TEMPLATES")
    print("=" * 80)
    print()

    issues = []
    good = []
    all_img_tags = []

    for template in LAYOUTS_DIR.rglob("*.html"):
        try:
            content = template.read_text(encoding='utf-8', errors='replace')
            rel_path = template.relative_to(PROJECT_ROOT)

            # Find all img src tags
            pattern = r'<img[^>]+src="{{[^}]+}}"[^>]*>'
            matches = re.finditer(pattern, content)

            for match in matches:
                img_tag = match.group(0)
                all_img_tags.append((str(rel_path), img_tag))

                # Check if it has relURL or absURL
                if '| relURL' in img_tag or '| absURL' in img_tag:
                    good.append((str(rel_path), img_tag))
                elif '{{' in img_tag and '}}' in img_tag:
                    # Only flag it if it's a template variable
                    issues.append((str(rel_path), img_tag))

        except Exception as e:
            print(f"Error reading {template.name}: {e}")

    # Print results
    if issues:
        print("ISSUES FOUND:")
        print("-" * 80)
        for file, tag in issues:
            print(f"\nFile: {file}")
            print(f"Tag:  {tag[:100]}")
        print()
    else:
        print("NO ISSUES FOUND - All image tags use | relURL or | absURL")
        print()

    print(f"Templates checked: {len(list(LAYOUTS_DIR.rglob('*.html')))}")
    print(f"Image tags found: {len(good) + len(issues)}")
    print(f"Correct: {len(good)}")
    print(f"Issues: {len(issues)}")
    print("=" * 80)

    return len(issues) == 0

if __name__ == "__main__":
    success = check_template_images()
    sys.exit(0 if success else 1)
