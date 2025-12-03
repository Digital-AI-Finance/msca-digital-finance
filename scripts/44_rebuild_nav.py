"""
44_rebuild_nav.py
Rebuild navigation structure for Hugo site.
- Create consistent menu structure
- Update hugo.toml with proper menu items
- Ensure all sections have _index.md files
- Fix breadcrumbs

Usage:
    python scripts/44_rebuild_nav.py
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

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_DIR = PROJECT_ROOT / "content"
CONFIG_FILE = PROJECT_ROOT / "hugo.toml"
DATA_DIR = PROJECT_ROOT / "data"

# Main navigation structure
MAIN_MENU = [
    {"name": "Home", "url": "/", "weight": 10},
    {"name": "About", "url": "/about-the-project/", "weight": 20},
    {"name": "People", "url": "/people/", "weight": 30},
    {"name": "Partners", "url": "/partners/", "weight": 40},
    {"name": "Research", "url": "/research-domains/", "weight": 50},
    {"name": "Training", "url": "/training-modules/", "weight": 60},
    {"name": "Events", "url": "/training-events/", "weight": 70},
    {"name": "News", "url": "/blog/", "weight": 80},
    {"name": "Contact", "url": "/contact/", "weight": 90},
]

# Footer navigation
FOOTER_MENU = [
    {"name": "About", "url": "/about-the-project/", "weight": 10},
    {"name": "Contact", "url": "/contact/", "weight": 20},
    {"name": "Privacy", "url": "/privacy/", "weight": 30},
    {"name": "Legal", "url": "/legal/", "weight": 40},
]

# Section descriptions for _index.md files
SECTION_INFO = {
    "people": {
        "title": "People",
        "description": "Meet the researchers and staff involved in the MSCA Digital Finance project.",
        "layout": "people-list"
    },
    "partners": {
        "title": "Partners",
        "description": "Our partner institutions and organizations across Europe.",
        "layout": "partners-list"
    },
    "blog": {
        "title": "News & Updates",
        "description": "Latest news, publications, and updates from the MSCA Digital Finance project.",
        "layout": "blog-list"
    },
    "training-modules": {
        "title": "Training Modules",
        "description": "Educational modules and learning materials for digital finance.",
        "layout": "list"
    },
    "training-events": {
        "title": "Training Events",
        "description": "Workshops, seminars, and training sessions.",
        "layout": "list"
    },
    "events": {
        "title": "Events",
        "description": "Conferences, meetings, and events related to the project.",
        "layout": "list"
    },
    "research-domains": {
        "title": "Research Domains",
        "description": "Our five key research areas in digital finance.",
        "layout": "list"
    },
}


def update_hugo_config():
    """Update hugo.toml with navigation menus."""
    print("  Updating hugo.toml...")

    # Read current config
    if CONFIG_FILE.exists():
        content = CONFIG_FILE.read_text(encoding='utf-8', errors='replace')
    else:
        content = ""

    # Remove existing menu sections
    content = re.sub(r'\[\[menu\.main\]\].*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)
    content = re.sub(r'\[\[menu\.footer\]\].*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)
    content = re.sub(r'\[menu\].*?(?=\n\[|\Z)', '', content, flags=re.DOTALL)

    # Clean up extra newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Build new config
    new_config = content.rstrip() + "\n\n"

    # Add main menu
    new_config += "# Main Navigation Menu\n"
    for item in MAIN_MENU:
        new_config += f'''[[menu.main]]
  name = "{item['name']}"
  url = "{item['url']}"
  weight = {item['weight']}

'''

    # Add footer menu
    new_config += "# Footer Navigation Menu\n"
    for item in FOOTER_MENU:
        new_config += f'''[[menu.footer]]
  name = "{item['name']}"
  url = "{item['url']}"
  weight = {item['weight']}

'''

    # Write updated config
    CONFIG_FILE.write_text(new_config, encoding='utf-8')
    print(f"    Updated: {CONFIG_FILE.name}")

    return True


def ensure_section_indexes():
    """Ensure all sections have proper _index.md files."""
    print("  Creating section index files...")
    created = 0

    for section, info in SECTION_INFO.items():
        section_dir = CONTENT_DIR / section
        index_file = section_dir / "_index.md"

        # Create directory if needed
        section_dir.mkdir(parents=True, exist_ok=True)

        # Create or update _index.md
        if not index_file.exists():
            content = f'''---
title: "{info['title']}"
description: "{info['description']}"
layout: "{info['layout']}"
type: "{section}"
---

{info['description']}
'''
            index_file.write_text(content, encoding='utf-8')
            created += 1
            print(f"    Created: {section}/_index.md")
        else:
            # Update existing if missing layout
            existing = index_file.read_text(encoding='utf-8', errors='replace')
            if 'layout:' not in existing:
                # Add layout to front matter
                if existing.startswith('---'):
                    parts = existing.split('---', 2)
                    if len(parts) >= 3:
                        new_front = parts[1].rstrip() + f'\nlayout: "{info["layout"]}"\n'
                        existing = '---' + new_front + '---' + parts[2]
                        index_file.write_text(existing, encoding='utf-8')
                        print(f"    Updated: {section}/_index.md")

    return created


def create_homepage():
    """Create or update the homepage _index.md."""
    print("  Creating homepage...")
    homepage = CONTENT_DIR / "_index.md"

    content = '''---
title: "MSCA Digital Finance"
description: "Marie Sklodowska-Curie Actions - Doctoral Network in Digital Finance"
layout: "index"
---

Welcome to the MSCA Digital Finance project, a Marie Sklodowska-Curie Actions Doctoral Network bringing together leading researchers and institutions to advance the field of digital finance.

## Our Mission

The MSCA Digital Finance project aims to train the next generation of researchers in digital finance, covering emerging topics such as:

- Artificial Intelligence in Finance
- Blockchain and Cryptocurrencies
- Sustainable Finance and ESG
- Risk Management and Regulation
- Financial Data Science

## Funding

This project has received funding from the European Union's Horizon Europe research and innovation programme under the Marie Sklodowska-Curie grant agreement.
'''

    homepage.write_text(content, encoding='utf-8')
    print(f"    Created: _index.md")

    return True


def verify_navigation_links():
    """Verify all navigation links resolve to content."""
    print("  Verifying navigation links...")
    issues = []

    all_menu_items = MAIN_MENU + FOOTER_MENU

    for item in all_menu_items:
        url = item['url'].strip('/')
        if not url:
            # Homepage
            content_path = CONTENT_DIR / "_index.md"
        else:
            content_path = CONTENT_DIR / url

        # Check for content
        exists = (
            (content_path / "_index.md").exists() or
            (content_path / "index.md").exists() or
            content_path.with_suffix('.md').exists() or
            (CONTENT_DIR / f"{url}.md").exists()
        )

        if not exists:
            issues.append({
                'name': item['name'],
                'url': item['url'],
                'expected_path': str(content_path)
            })
            print(f"    Missing: {item['name']} -> {item['url']}")
        else:
            print(f"    OK: {item['name']} -> {item['url']}")

    return issues


def create_missing_pages():
    """Create placeholder pages for missing navigation items."""
    print("  Creating missing pages...")
    created = 0

    missing_pages = [
        ("contact", "Contact Us", "Get in touch with the MSCA Digital Finance team."),
        ("privacy", "Privacy Policy", "Information about how we handle your data."),
        ("legal", "Legal Notice", "Legal information and disclaimers."),
        ("about-the-project", "About the Project", "Learn more about the MSCA Digital Finance project."),
        ("research-domains", "Research Domains", "Our five key research areas."),
    ]

    for slug, title, description in missing_pages:
        page_path = CONTENT_DIR / f"{slug}.md"
        if not page_path.exists():
            content = f'''---
title: "{title}"
description: "{description}"
date: {datetime.now().strftime('%Y-%m-%d')}
draft: false
---

{description}

*This page is under construction.*
'''
            page_path.write_text(content, encoding='utf-8')
            created += 1
            print(f"    Created: {slug}.md")

    return created


def run_nav_rebuild():
    """Run the navigation rebuild."""
    print("=" * 60)
    print("NAVIGATION REBUILD")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        'date': datetime.now().isoformat(),
        'config_updated': False,
        'indexes_created': 0,
        'pages_created': 0,
        'navigation_issues': []
    }

    # 1. Update Hugo config
    print("[1/5] Updating Hugo configuration...")
    results['config_updated'] = update_hugo_config()

    # 2. Create section indexes
    print("\n[2/5] Creating section index files...")
    results['indexes_created'] = ensure_section_indexes()

    # 3. Create homepage
    print("\n[3/5] Creating homepage...")
    create_homepage()

    # 4. Create missing pages
    print("\n[4/5] Creating missing pages...")
    results['pages_created'] = create_missing_pages()

    # 5. Verify navigation
    print("\n[5/5] Verifying navigation links...")
    results['navigation_issues'] = verify_navigation_links()

    return results


def save_report(results):
    """Save navigation report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "navigation_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    results = run_nav_rebuild()
    save_report(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Config updated: {results['config_updated']}")
    print(f"  Section indexes created: {results['indexes_created']}")
    print(f"  Missing pages created: {results['pages_created']}")
    print(f"  Navigation issues: {len(results['navigation_issues'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
