"""
Add Blog Excerpts
==================
Ensure all blog posts have proper description or summary in front matter
for card displays. If missing, extract from first 150 characters of content.
"""

import os
import re
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent
BLOG_DIR = BASE_DIR / "content" / "blog"

def extract_excerpt(content_body):
    """Extract first 150 characters of meaningful content."""
    # Remove markdown headers
    body = re.sub(r'^#+\s+.*$', '', content_body, flags=re.MULTILINE)
    # Remove markdown links
    body = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', body)
    # Remove images
    body = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', body)
    # Remove extra whitespace
    body = ' '.join(body.split())

    # Get first 150 characters
    excerpt = body.strip()[:150]

    # Try to end at a word boundary
    if len(body) > 150:
        last_space = excerpt.rfind(' ')
        if last_space > 100:
            excerpt = excerpt[:last_space]
        excerpt += '...'

    return excerpt

def add_blog_excerpts():
    """Add descriptions to blog posts that don't have them."""
    if not BLOG_DIR.exists():
        print(f"Blog directory not found: {BLOG_DIR}")
        return

    updated_count = 0

    for md_file in BLOG_DIR.glob("*.md"):
        if md_file.name.startswith("_") or md_file.name == "index.md":
            continue

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split front matter and body
        parts = content.split('---', 2)
        if len(parts) < 3:
            continue

        front_matter = parts[1]
        body = parts[2]

        # Check if description exists
        has_description = bool(re.search(r'^description:\s*.+$', front_matter, re.MULTILINE))
        has_summary = bool(re.search(r'^summary:\s*.+$', front_matter, re.MULTILINE))

        if not has_description and not has_summary:
            excerpt = extract_excerpt(body)

            # Add description to front matter
            front_matter = front_matter.rstrip() + f"\ndescription: \"{excerpt}\"\n"

            # Write back
            new_content = f"---{front_matter}---{body}"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

            updated_count += 1
            print(f"Added excerpt to: {md_file.name}")

    print(f"\nAdded excerpts to {updated_count} blog posts")

if __name__ == "__main__":
    print("Adding blog excerpts...")
    print("=" * 60)
    add_blog_excerpts()
    print("=" * 60)
    print("Blog excerpts added successfully!")
