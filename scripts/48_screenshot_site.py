"""
48_screenshot_site.py
Take screenshots of the live website for review and improvement.
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "data" / "screenshots"

BASE_URL = "https://digital-ai-finance.github.io/msca-digital-finance"

PAGES_TO_SCREENSHOT = [
    ("/", "homepage"),
    ("/people/", "people"),
    ("/partners/", "partners"),
    ("/blog/", "blog"),
    ("/training-modules/", "training-modules"),
    ("/training-events/", "training-events"),
    ("/about-the-project/", "about"),
]


def main():
    print("=" * 60)
    print("WEBSITE SCREENSHOT CAPTURE")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {BASE_URL}")
    print()

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Desktop viewport
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print("Taking desktop screenshots...")
        for url_path, name in PAGES_TO_SCREENSHOT:
            url = BASE_URL + url_path
            try:
                print(f"  {name}...", end=" ")
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(1000)  # Wait for animations

                filepath = SCREENSHOTS_DIR / f"{name}_desktop.png"
                page.screenshot(path=str(filepath), full_page=True)
                print(f"OK - {filepath.name}")
            except Exception as e:
                print(f"ERROR: {e}")

        context.close()

        # Mobile viewport
        context = browser.new_context(viewport={'width': 375, 'height': 812})
        page = context.new_page()

        print("\nTaking mobile screenshots...")
        for url_path, name in PAGES_TO_SCREENSHOT[:3]:  # Just first 3 for mobile
            url = BASE_URL + url_path
            try:
                print(f"  {name}...", end=" ")
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(1000)

                filepath = SCREENSHOTS_DIR / f"{name}_mobile.png"
                page.screenshot(path=str(filepath), full_page=True)
                print(f"OK - {filepath.name}")
            except Exception as e:
                print(f"ERROR: {e}")

        browser.close()

    print("\n" + "=" * 60)
    print(f"Screenshots saved to: {SCREENSHOTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
