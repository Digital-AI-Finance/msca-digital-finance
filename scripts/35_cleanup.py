"""
35_cleanup.py
Clean up orphan files, duplicates, and standardize file naming.
Final cleanup before deployment.

Usage:
    python scripts/35_cleanup.py
    python scripts/35_cleanup.py --dry-run
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import re
import os
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
DATA_DIR = PROJECT_ROOT / "data"

# Files/folders to clean up
CLEANUP_PATTERNS = [
    "*.backup*",
    "*.bak",
    "*~",
    "*.tmp",
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
]

# Folders that might be orphaned/legacy
LEGACY_FOLDERS = [
    "content/partner-new",  # Should be content/partners
    "content/post",  # Should be content/blog
]


def get_file_hash(filepath):
    """Get MD5 hash of file content."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None


def find_duplicates(directory, extension=".md"):
    """Find duplicate files by content hash."""
    print(f"  Scanning {directory} for duplicates...")
    hashes = defaultdict(list)

    for filepath in Path(directory).rglob(f"*{extension}"):
        file_hash = get_file_hash(filepath)
        if file_hash:
            hashes[file_hash].append(filepath)

    duplicates = {h: files for h, files in hashes.items() if len(files) > 1}
    return duplicates


def find_empty_files(directory):
    """Find empty or near-empty markdown files."""
    empty_files = []

    for filepath in Path(directory).rglob("*.md"):
        try:
            content = filepath.read_text(encoding='utf-8', errors='replace')
            # Remove frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    body = parts[2].strip()
                else:
                    body = content
            else:
                body = content

            # Check if body is essentially empty
            body_clean = re.sub(r'\s+', '', body)
            if len(body_clean) < 50:  # Less than 50 chars of actual content
                empty_files.append({
                    'path': filepath,
                    'body_length': len(body_clean)
                })
        except:
            pass

    return empty_files


def find_backup_files(directory):
    """Find backup and temporary files."""
    backup_files = []

    for pattern in CLEANUP_PATTERNS:
        for filepath in Path(directory).rglob(pattern):
            backup_files.append(filepath)

    return backup_files


def find_orphan_images(content_dir, static_dir):
    """Find images in static that are not referenced in content."""
    print("  Scanning for orphan images...")

    # Get all image references in content
    referenced_images = set()
    for md_file in Path(content_dir).rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')
            # Find all image references
            for match in re.finditer(r'/images/[^\s"\'\)]+', content):
                img_path = match.group(0).lower()
                referenced_images.add(img_path)
        except:
            pass

    # Get all images in static
    images_dir = Path(static_dir) / "images"
    all_images = set()
    if images_dir.exists():
        for img_file in images_dir.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                rel_path = "/images/" + str(img_file.relative_to(images_dir)).replace("\\", "/")
                all_images.add(rel_path.lower())

    # Find orphans
    orphan_images = all_images - referenced_images
    return list(orphan_images)


def standardize_filenames(directory, dry_run=True):
    """Standardize file naming (lowercase, hyphens instead of underscores)."""
    print("  Checking filenames...")
    renames = []

    for filepath in Path(directory).rglob("*.md"):
        old_name = filepath.name
        new_name = old_name.lower()
        new_name = new_name.replace('_', '-')
        new_name = re.sub(r'[^\w\-.]', '-', new_name)
        new_name = re.sub(r'-+', '-', new_name)
        new_name = new_name.strip('-')

        if old_name != new_name:
            renames.append({
                'old': filepath,
                'new': filepath.parent / new_name
            })

    return renames


def cleanup_frontmatter(directory, dry_run=True):
    """Clean up frontmatter in all markdown files."""
    print("  Cleaning frontmatter...")
    cleaned_count = 0

    for md_file in Path(directory).rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')
            original = content

            # Remove empty image arrays
            content = re.sub(r'^images:\s*\[\s*\]\s*\n', '', content, flags=re.MULTILINE)
            content = re.sub(r'^images:\s*""\s*\n', '', content, flags=re.MULTILINE)

            # Remove empty fields
            content = re.sub(r'^[a-z_]+:\s*""\s*\n', '', content, flags=re.MULTILINE)
            content = re.sub(r'^[a-z_]+:\s*\[\s*\]\s*\n', '', content, flags=re.MULTILINE)

            # Fix common frontmatter issues
            content = re.sub(r'date:\s*(\d{4})-(\d{2})-(\d{2})T', r'date: \1-\2-\3T', content)

            if content != original:
                if not dry_run:
                    md_file.write_text(content, encoding='utf-8')
                cleaned_count += 1

        except Exception as e:
            print(f"    Error cleaning {md_file.name}: {e}")

    return cleaned_count


def run_cleanup(dry_run=True):
    """Run all cleanup operations."""
    print("=" * 60)
    print("FILE CLEANUP")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    results = {
        'duplicates': [],
        'empty_files': [],
        'backup_files': [],
        'orphan_images': [],
        'renamed_files': [],
        'cleaned_frontmatter': 0,
        'deleted_files': 0
    }

    # 1. Find duplicates
    print("[1/6] Finding duplicate files...")
    duplicates = find_duplicates(CONTENT_DIR)
    for hash_val, files in duplicates.items():
        results['duplicates'].extend([str(f) for f in files[1:]])  # Keep first, list rest
    print(f"  Found {len(results['duplicates'])} duplicate files")

    # 2. Find empty files
    print("[2/6] Finding empty files...")
    empty_files = find_empty_files(CONTENT_DIR)
    results['empty_files'] = [str(f['path']) for f in empty_files]
    print(f"  Found {len(results['empty_files'])} empty/near-empty files")

    # 3. Find backup files
    print("[3/6] Finding backup/temp files...")
    backup_files = find_backup_files(PROJECT_ROOT)
    results['backup_files'] = [str(f) for f in backup_files]
    print(f"  Found {len(results['backup_files'])} backup/temp files")

    # 4. Find orphan images (info only, don't delete)
    print("[4/6] Finding orphan images...")
    orphan_images = find_orphan_images(CONTENT_DIR, STATIC_DIR)
    results['orphan_images'] = orphan_images[:100]  # Limit output
    print(f"  Found {len(orphan_images)} potentially orphan images")

    # 5. Standardize filenames
    print("[5/6] Checking filenames...")
    renames = standardize_filenames(CONTENT_DIR, dry_run)
    results['renamed_files'] = [{'old': str(r['old'].name), 'new': str(r['new'].name)} for r in renames]
    print(f"  Found {len(renames)} files to rename")

    # 6. Clean frontmatter
    print("[6/6] Cleaning frontmatter...")
    cleaned = cleanup_frontmatter(CONTENT_DIR, dry_run)
    results['cleaned_frontmatter'] = cleaned
    print(f"  Cleaned {cleaned} files")

    # Perform deletions if not dry run
    if not dry_run:
        # Delete backup files
        for filepath in backup_files:
            try:
                if filepath.is_file():
                    filepath.unlink()
                elif filepath.is_dir():
                    shutil.rmtree(filepath)
                results['deleted_files'] += 1
            except Exception as e:
                print(f"    Error deleting {filepath}: {e}")

        # Rename files
        for rename in renames:
            try:
                if rename['old'].exists() and not rename['new'].exists():
                    rename['old'].rename(rename['new'])
            except Exception as e:
                print(f"    Error renaming {rename['old']}: {e}")

    return results


def save_report(results, dry_run):
    """Save cleanup report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        'date': datetime.now().isoformat(),
        'mode': 'dry_run' if dry_run else 'live',
        'summary': {
            'duplicates_found': len(results['duplicates']),
            'empty_files_found': len(results['empty_files']),
            'backup_files_found': len(results['backup_files']),
            'orphan_images_found': len(results['orphan_images']),
            'files_renamed': len(results['renamed_files']),
            'frontmatter_cleaned': results['cleaned_frontmatter'],
            'files_deleted': results['deleted_files']
        },
        'details': {
            'duplicates': results['duplicates'][:20],
            'empty_files': results['empty_files'][:20],
            'backup_files': results['backup_files'][:20],
            'orphan_images': results['orphan_images'][:20],
            'renamed_files': results['renamed_files'][:20]
        }
    }

    output_file = DATA_DIR / "cleanup_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    results = run_cleanup(dry_run)
    save_report(results, dry_run)

    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"  Mode: {'DRY RUN (no changes made)' if dry_run else 'LIVE'}")
    print(f"  Duplicates found: {len(results['duplicates'])}")
    print(f"  Empty files found: {len(results['empty_files'])}")
    print(f"  Backup files found: {len(results['backup_files'])}")
    print(f"  Orphan images found: {len(results['orphan_images'])}")
    print(f"  Files to rename: {len(results['renamed_files'])}")
    print(f"  Frontmatter cleaned: {results['cleaned_frontmatter']}")

    if not dry_run:
        print(f"  Files deleted: {results['deleted_files']}")
    else:
        print()
        print("  To apply changes, run without --dry-run:")
        print("    python scripts/35_cleanup.py")

    print("=" * 60)


if __name__ == "__main__":
    main()
