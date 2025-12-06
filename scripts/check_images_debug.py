"""Quick script to debug image references"""
from pathlib import Path
import re

refs = []
for f in Path('content').rglob('*.md'):
    try:
        content = f.read_text(encoding='utf-8', errors='replace')
        # Look for image field
        match = re.search(r'^image:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
        if match:
            img = match.group(1).strip()
            refs.append((str(f.relative_to(Path('.'))), img))
    except:
        pass

# Show first 30
print("First 30 image references:")
for i, (f, img) in enumerate(refs[:30]):
    # Check if exists
    if img.startswith('/'):
        full_path = Path('static') / img.lstrip('/')
    else:
        full_path = Path('static') / img

    exists = "EXISTS" if full_path.exists() else "MISSING"
    print(f"{exists}: {f} -> {img}")
