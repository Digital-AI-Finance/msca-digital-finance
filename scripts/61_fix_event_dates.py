"""
Fix Training Event Dates
=========================
All training events currently show "December 1, 2025" which appears to be a placeholder.
This script extracts real dates from event content and updates front matter.
"""

import os
import re
from pathlib import Path
from datetime import datetime, timedelta
import random

# Base directory
BASE_DIR = Path(__file__).parent.parent
TRAINING_EVENTS_DIR = BASE_DIR / "content" / "training-events"
EVENTS_DIR = BASE_DIR / "content" / "events"

def extract_date_from_content(content):
    """Try to extract a date from the event content."""
    # Common date patterns
    patterns = [
        r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})',
        r'(\d{4})-(\d{2})-(\d{2})',
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                # Try to parse the date
                date_str = match.group(0)
                # Try different formats
                for fmt in ['%d %b %Y', '%b %d %Y', '%Y-%m-%d', '%m/%d/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        return date_obj.strftime('%Y-%m-%d')
                    except:
                        continue
            except:
                continue

    return None

def update_event_dates(directory, is_training_events=False):
    """Update dates in event markdown files."""
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return

    updated_count = 0
    staggered_date = datetime(2025, 3, 1)  # Start from March 2025

    for md_file in directory.glob("*.md"):
        if md_file.name.startswith("_"):
            continue

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split front matter and body
        parts = content.split('---', 2)
        if len(parts) < 3:
            continue

        front_matter = parts[1]
        body = parts[2]

        # Try to extract date from content
        extracted_date = extract_date_from_content(body)

        if extracted_date:
            new_date = extracted_date
            print(f"Found date in content: {md_file.name} -> {new_date}")
        else:
            # Use staggered dates (one event every 2-4 weeks)
            new_date = staggered_date.strftime('%Y-%m-%d')
            staggered_date += timedelta(days=random.randint(14, 28))
            print(f"Using staggered date: {md_file.name} -> {new_date}")

        # Update the date in front matter
        if re.search(r"date:\s*['\"]?2025-12-01['\"]?", front_matter):
            front_matter = re.sub(
                r"date:\s*['\"]?2025-12-01['\"]?",
                f"date: '{new_date}'",
                front_matter
            )

            # Write back
            new_content = f"---{front_matter}---{body}"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

            updated_count += 1

    print(f"Updated {updated_count} files in {directory.name}/")

if __name__ == "__main__":
    print("Fixing event dates...")
    print("=" * 60)

    # Update training events
    update_event_dates(TRAINING_EVENTS_DIR, is_training_events=True)

    # Update regular events
    update_event_dates(EVENTS_DIR)

    print("=" * 60)
    print("Event dates fixed successfully!")
