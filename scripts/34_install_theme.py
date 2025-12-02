"""
34_install_theme.py
Install and configure PaperMod Hugo theme.
Handles theme download, configuration, and content migration.

Usage:
    python scripts/34_install_theme.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import re
import shutil
import subprocess
import zipfile
import tempfile
import requests
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
THEMES_DIR = PROJECT_ROOT / "themes"
CONTENT_DIR = PROJECT_ROOT / "content"
CONFIG_FILE = PROJECT_ROOT / "hugo.toml"
CONFIG_FILE_ALT = PROJECT_ROOT / "config.toml"

PAPERMOD_ZIP_URL = "https://github.com/adityatelange/hugo-PaperMod/archive/refs/heads/master.zip"

HUGO_CONFIG = """# Hugo Configuration for MSCA Digital Finance
# Theme: PaperMod
# Generated: {date}

baseURL = "https://digital-ai-finance.github.io/msca-digital-finance/"
languageCode = "en-us"
title = "MSCA Digital Finance"
theme = "PaperMod"

# Build settings
enableRobotsTXT = true
buildDrafts = false
buildFuture = false
buildExpired = false
enableEmoji = false

# Pagination
paginate = 20

# Minify output
minify.disableXML = true
minify.minifyOutput = true

[params]
env = "production"
title = "MSCA Digital Finance"
description = "Digital Finance - Reaching New Frontiers | EU Horizon MSCA Doctoral Network"
keywords = ["Digital Finance", "Fintech", "AI", "Machine Learning", "Blockchain", "EU Research"]
author = "MSCA Digital Finance Consortium"
DateFormat = "January 2, 2006"
defaultTheme = "light"
disableThemeToggle = false
ShowReadingTime = false
ShowShareButtons = false
ShowPostNavLinks = true
ShowBreadCrumbs = true
ShowCodeCopyButtons = true
ShowWordCount = false
ShowRssButtonInSectionTermList = false
UseHugoToc = true
disableSpecial1stPost = true
disableScrollToTop = false
hidemeta = false
hideSummary = false
showtoc = false
tocopen = false

[params.homeInfoParams]
Title = "MSCA Digital Finance"
Content = "Digital Finance - Reaching New Frontiers. A Horizon Europe MSCA Doctoral Network funded by the European Union."

[[params.socialIcons]]
name = "github"
url = "https://github.com/Digital-AI-Finance"

[[params.socialIcons]]
name = "email"
url = "mailto:j.osterrieder@utwente.nl"

[params.cover]
hidden = false
hiddenInList = false
hiddenInSingle = false

[params.fuseOpts]
isCaseSensitive = false
shouldSort = true
location = 0
distance = 1000
threshold = 0.4
minMatchCharLength = 0
keys = ["title", "permalink", "summary", "content"]

# Menu
[menu]
[[menu.main]]
identifier = "home"
name = "Home"
url = "/"
weight = 1

[[menu.main]]
identifier = "about"
name = "About"
url = "/about-the-project/"
weight = 10

[[menu.main]]
identifier = "people"
name = "People"
url = "/people/"
weight = 20

[[menu.main]]
identifier = "partners"
name = "Partners"
url = "/partners/"
weight = 30

[[menu.main]]
identifier = "training"
name = "Training"
url = "/training-modules/"
weight = 40

[[menu.main]]
identifier = "events"
name = "Events"
url = "/training-events/"
weight = 50

[[menu.main]]
identifier = "blog"
name = "News"
url = "/blog/"
weight = 60

[[menu.main]]
identifier = "eu-data"
name = "EU Data"
url = "/eu-cordis-project/"
weight = 70

# Outputs
[outputs]
home = ["HTML", "RSS", "JSON"]

# Taxonomies
[taxonomies]
category = "categories"
tag = "tags"
series = "series"

# Markup settings
[markup]
[markup.highlight]
noClasses = false
style = "dracula"
[markup.goldmark.renderer]
unsafe = true
"""


def download_theme():
    """Download PaperMod theme."""
    print("[1/4] Downloading PaperMod theme...")

    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    theme_dir = THEMES_DIR / "PaperMod"

    # Check if theme already exists
    if theme_dir.exists():
        print(f"  Theme already exists at {theme_dir}")
        print("  Backing up and re-downloading...")
        backup_dir = THEMES_DIR / f"PaperMod_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        theme_dir.rename(backup_dir)

    # Try git clone first
    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", "https://github.com/adityatelange/hugo-PaperMod.git", str(theme_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print(f"  Cloned theme to {theme_dir}")
            # Remove .git folder to avoid submodule issues
            git_dir = theme_dir / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)
            return True
    except Exception as e:
        print(f"  Git clone failed: {e}")

    # Fallback to ZIP download
    print("  Falling back to ZIP download...")
    try:
        response = requests.get(PAPERMOD_ZIP_URL, timeout=60)
        response.raise_for_status()

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "papermod.zip"
            with open(zip_path, 'wb') as f:
                f.write(response.content)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)

            # Find extracted folder
            extracted = list(Path(tmp_dir).glob("hugo-PaperMod-*"))
            if extracted:
                shutil.move(str(extracted[0]), str(theme_dir))
                print(f"  Downloaded and extracted to {theme_dir}")
                return True

    except Exception as e:
        print(f"  ZIP download failed: {e}")
        return False

    return False


def update_config():
    """Update Hugo configuration for PaperMod."""
    print("[2/4] Updating Hugo configuration...")

    config_content = HUGO_CONFIG.format(date=datetime.now().strftime('%Y-%m-%d'))

    # Backup existing config
    for config_path in [CONFIG_FILE, CONFIG_FILE_ALT]:
        if config_path.exists():
            backup_path = config_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.toml")
            config_path.rename(backup_path)
            print(f"  Backed up {config_path.name} to {backup_path.name}")

    # Write new config
    CONFIG_FILE.write_text(config_content, encoding='utf-8')
    print(f"  Created {CONFIG_FILE}")

    return True


def update_content_frontmatter():
    """Update content front matter for PaperMod compatibility."""
    print("[3/4] Updating content front matter...")

    updated_count = 0
    md_files = list(CONTENT_DIR.rglob("*.md"))

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')

            # Skip if already has PaperMod-specific fields
            if 'ShowToc:' in content or 'cover:' in content:
                continue

            # Find frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]

                    # Add PaperMod fields
                    new_fields = []

                    # Check for image field and convert to cover
                    image_match = re.search(r'^image:\s*["\']?([^"\'\n]+)["\']?\s*$', frontmatter, re.MULTILINE)
                    if image_match:
                        image_url = image_match.group(1).strip()
                        if image_url and image_url != '""':
                            new_fields.append(f'cover:\n  image: "{image_url}"\n  alt: "Cover image"\n  hidden: false')
                            # Remove old image field
                            frontmatter = re.sub(r'^image:.*\n?', '', frontmatter, flags=re.MULTILINE)

                    # Add ShowToc for longer pages
                    if len(body) > 3000:
                        new_fields.append('ShowToc: true')

                    if new_fields:
                        frontmatter = frontmatter.rstrip() + '\n' + '\n'.join(new_fields) + '\n'
                        new_content = f'---{frontmatter}---{body}'
                        md_file.write_text(new_content, encoding='utf-8')
                        updated_count += 1

        except Exception as e:
            print(f"  Error updating {md_file.name}: {e}")

    print(f"  Updated {updated_count} content files")
    return updated_count


def create_homepage():
    """Create or update the homepage for PaperMod."""
    print("[4/4] Updating homepage...")

    homepage = CONTENT_DIR / "_index.md"

    homepage_content = """---
title: "MSCA Digital Finance"
layout: "home"
description: "Digital Finance - Reaching New Frontiers | EU Horizon MSCA Doctoral Network"
---

## Welcome to MSCA Digital Finance

**Digital Finance - Reaching New Frontiers** is a prestigious Horizon Europe MSCA Doctoral Network funded by the European Union (Grant Agreement No. 101119635).

Our research initiative addresses five key domains:
- European Financial Data Space
- AI in Financial Markets
- Explainable and Fair AI Decisions
- Blockchain Innovations
- Sustainable Digital Finance

### Quick Links

- [About the Project](/about-the-project/) - Learn about our mission and objectives
- [People](/people/) - Meet our researchers and supervisors
- [Partners](/partners/) - Our consortium members
- [Training Modules](/training-modules/) - Educational resources
- [Events](/training-events/) - Upcoming events and workshops
- [EU CORDIS Data](/eu-cordis-project/) - Official EU project information

---

*This project has received funding from the European Union's Horizon Europe research and innovation programme under Marie Sklodowska-Curie grant agreement No. 101119635.*
"""

    homepage.write_text(homepage_content, encoding='utf-8')
    print(f"  Updated {homepage}")

    return True


def main():
    print("=" * 60)
    print("PAPERMOD THEME INSTALLER")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Download theme
    if not download_theme():
        print("\nERROR: Failed to download theme")
        return

    # Step 2: Update config
    update_config()

    # Step 3: Update content
    update_content_frontmatter()

    # Step 4: Update homepage
    create_homepage()

    print("\n" + "=" * 60)
    print("PAPERMOD INSTALLATION COMPLETE")
    print("=" * 60)
    print()
    print("  Theme installed at: themes/PaperMod")
    print("  Config updated: hugo.toml")
    print()
    print("  To test locally:")
    print("    cd msca-digital-finance")
    print("    hugo server -D")
    print()
    print("  Features enabled:")
    print("    - Light/dark mode toggle")
    print("    - Search functionality")
    print("    - Breadcrumbs navigation")
    print("    - Code copy buttons")
    print("    - Responsive design")
    print("=" * 60)


if __name__ == "__main__":
    main()
