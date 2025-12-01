"""
03_download_images.py
Downloads all images referenced in the scraped markdown files.
Updates image paths in markdown to local references.
"""

import json
import re
import os
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from urllib.parse import urlparse, unquote, urljoin
import hashlib
from tqdm import tqdm

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
IMAGES_DIR = STATIC_DIR / "images"
DATA_DIR = PROJECT_ROOT / "data"

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def get_image_extension(url, content_type=None):
    """Determine image extension from URL or content type."""
    # Try to get from URL
    parsed = urlparse(url)
    path = parsed.path.lower()

    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico']:
        if ext in path:
            return ext

    # Try from content type
    if content_type:
        type_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
        }
        for mime, ext in type_map.items():
            if mime in content_type:
                return ext

    return '.jpg'  # Default


def extract_images_from_markdown(md_path):
    """Extract image URLs from a markdown file."""
    images = []

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract from front matter (images array)
    front_matter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if front_matter_match:
        fm_content = front_matter_match.group(1)
        # Find images in front matter
        image_matches = re.findall(r'https?://[^\s\'">\]]+(?:\.(?:jpg|jpeg|png|gif|webp|svg)|\?.*)', fm_content, re.IGNORECASE)
        images.extend(image_matches)

        # Also look for og_image or image field
        image_field_match = re.search(r'(?:image|og_image):\s*[\'"]?(https?://[^\s\'"]+)[\'"]?', fm_content)
        if image_field_match:
            images.append(image_field_match.group(1))

    # Extract from markdown content
    # Markdown image syntax: ![alt](url)
    md_images = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', content)
    images.extend(md_images)

    # HTML img tags
    html_images = re.findall(r'<img[^>]+src=[\'"]?(https?://[^\'">\s]+)[\'"]?', content)
    images.extend(html_images)

    # Generic URLs that look like images
    generic_images = re.findall(r'(https?://[^\s\'"<>\]]+(?:\.(?:jpg|jpeg|png|gif|webp))[^\s\'"<>\]]*)', content, re.IGNORECASE)
    images.extend(generic_images)

    # Wix static URLs
    wix_images = re.findall(r'(https?://static\.wixstatic\.com/[^\s\'"<>\]]+)', content)
    images.extend(wix_images)

    # Remove duplicates while preserving order
    seen = set()
    unique_images = []
    for img in images:
        # Clean URL
        img = img.strip().rstrip(')')
        if img not in seen and img.startswith('http'):
            seen.add(img)
            unique_images.append(img)

    return unique_images


def get_category_from_path(md_path):
    """Determine category from markdown file path."""
    relative = md_path.relative_to(CONTENT_DIR)
    parts = relative.parts

    if len(parts) > 1:
        return parts[0]
    return 'general'


def generate_local_filename(url, category):
    """Generate a local filename for an image."""
    # Create a hash of the URL for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    # Try to get original filename
    parsed = urlparse(url)
    path = unquote(parsed.path)
    original_name = os.path.basename(path)

    # Clean the filename
    name_base = re.sub(r'[^\w\-.]', '_', original_name)
    name_base = re.sub(r'_+', '_', name_base)

    # Ensure it has an extension
    if '.' not in name_base[-6:]:
        name_base += get_image_extension(url)

    # Limit length and add hash
    if len(name_base) > 50:
        name_parts = name_base.rsplit('.', 1)
        name_base = name_parts[0][:40] + '_' + url_hash + '.' + name_parts[1] if len(name_parts) > 1 else name_parts[0][:50]
    else:
        name_parts = name_base.rsplit('.', 1)
        if len(name_parts) > 1:
            name_base = name_parts[0] + '_' + url_hash + '.' + name_parts[1]

    return name_base


async def download_image(session, url, local_path, retries=3):
    """Download a single image."""
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.read()

                    # Verify it's actually image content
                    content_type = response.headers.get('content-type', '')
                    if 'image' not in content_type and 'octet-stream' not in content_type:
                        return False, f"Not an image: {content_type}"

                    # Ensure directory exists
                    local_path.parent.mkdir(parents=True, exist_ok=True)

                    async with aiofiles.open(local_path, 'wb') as f:
                        await f.write(content)

                    return True, None
                else:
                    return False, f"HTTP {response.status}"
        except asyncio.TimeoutError:
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                return False, "Timeout"
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                return False, str(e)

    return False, "Max retries exceeded"


def update_markdown_image_paths(md_path, url_mapping):
    """Update image URLs in markdown file to local paths."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False
    for old_url, new_path in url_mapping.items():
        if old_url in content:
            content = content.replace(old_url, new_path)
            modified = True

    if modified:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return modified


async def main():
    print("=" * 60)
    print("Image Downloader for MSCA Digital Finance")
    print("=" * 60)

    # Find all markdown files
    md_files = list(CONTENT_DIR.rglob('*.md'))
    print(f"\nFound {len(md_files)} markdown files")

    # Collect all images
    all_images = {}  # url -> {categories, md_files}

    for md_file in md_files:
        category = get_category_from_path(md_file)
        images = extract_images_from_markdown(md_file)

        for img_url in images:
            if img_url not in all_images:
                all_images[img_url] = {
                    'categories': set(),
                    'md_files': []
                }
            all_images[img_url]['categories'].add(category)
            all_images[img_url]['md_files'].append(md_file)

    print(f"Found {len(all_images)} unique images to download")

    if not all_images:
        print("No images found!")
        return

    # Create download tasks
    download_tasks = []
    url_to_local = {}  # Maps original URL to local path

    for url, info in all_images.items():
        # Use the first category for organizing
        category = sorted(info['categories'])[0]

        # Create local path
        category_dir = IMAGES_DIR / category
        local_filename = generate_local_filename(url, category)
        local_path = category_dir / local_filename

        # Store mapping
        local_url_path = f"/images/{category}/{local_filename}"
        url_to_local[url] = {
            'local_path': local_path,
            'local_url': local_url_path,
            'md_files': info['md_files']
        }

        download_tasks.append((url, local_path))

    # Download images with concurrency limit
    print("\nDownloading images...")

    success_count = 0
    fail_count = 0

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i, (url, local_path) in enumerate(tqdm(download_tasks, desc="Downloading")):
            # Skip if already exists
            if local_path.exists():
                success_count += 1
                continue

            success, error = await download_image(session, url, local_path)

            if success:
                success_count += 1
            else:
                fail_count += 1
                if error:
                    tqdm.write(f"  Failed: {url[:60]}... - {error}")

            # Small delay to be nice to servers
            await asyncio.sleep(0.1)

    print(f"\n\nDownload complete: {success_count} success, {fail_count} failed")

    # Update markdown files with local paths
    print("\nUpdating markdown files with local image paths...")

    updated_files = 0
    for url, info in url_to_local.items():
        local_path = info['local_path']
        local_url = info['local_url']

        # Only update if image was downloaded
        if local_path.exists():
            for md_file in info['md_files']:
                if update_markdown_image_paths(md_file, {url: local_url}):
                    updated_files += 1

    print(f"Updated {updated_files} markdown file references")

    # Save image mapping for reference
    mapping_file = DATA_DIR / "image_mapping.json"
    mapping_data = {
        url: {
            'local_path': str(info['local_path']),
            'local_url': info['local_url'],
            'exists': info['local_path'].exists()
        }
        for url, info in url_to_local.items()
    }

    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, indent=2, ensure_ascii=False)

    print(f"\nImage mapping saved to: {mapping_file}")

    print("\n" + "=" * 60)
    print("Image Download Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
