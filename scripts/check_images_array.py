"""Check images array in frontmatter"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
import re

missing_count = 0
exists_count = 0
missing_files = []

for f in Path('content').rglob('*.md'):
    try:
        content = f.read_text(encoding='utf-8', errors='replace')

        # Extract frontmatter
        fm_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        if not fm_match:
            continue

        fm = fm_match.group(1)

        # Find images array
        images_match = re.search(r'images:\s*\n((?:- [^\n]+\n)+)', fm)
        if not images_match:
            continue

        # Extract each image path
        for line in images_match.group(1).split('\n'):
            if not line.strip().startswith('-'):
                continue

            img = line.strip()[1:].strip().strip('"\'')
            if not img or img.startswith('http'):
                continue

            # Check if exists
            if img.startswith('/'):
                full_path = Path('static') / img.lstrip('/')
            else:
                full_path = Path('static') / img

            if full_path.exists():
                exists_count += 1
            else:
                missing_count += 1
                if len(missing_files) < 50:
                    missing_files.append((str(f.relative_to(Path('.'))), img))

    except Exception as e:
        pass

print(f"Images in frontmatter arrays:")
print(f"  Exist: {exists_count}")
print(f"  Missing: {missing_count}")
print()
print("First 50 missing images:")
for f, img in missing_files:
    print(f"  {f}")
    print(f"    -> {img}")
