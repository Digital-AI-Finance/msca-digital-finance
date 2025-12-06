"""
52_screenshot_sidebar.py
Take screenshots of the live site to verify the new left sidebar layout.
"""

import sys
import io
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.sync_api import sync_playwright

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "data" / "screenshots" / "sidebar_layout"

LIVE_URL = "https://digital-ai-finance.github.io/msca-digital-finance"

PAGES_TO_CHECK = [
    ("", "homepage"),
    ("about-the-project/", "about"),
    ("people/", "people"),
    ("research-domains/", "research"),
    ("training-events/", "events"),
]


def take_screenshots():
    """Take screenshots of the live site."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SCREENSHOT CAPTURE - LEFT SIDEBAR LAYOUT")
    print("=" * 60)
    print(f"URL: {LIVE_URL}")
    print(f"Output: {SCREENSHOTS_DIR}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for page_path, name in PAGES_TO_CHECK:
            url = f"{LIVE_URL}/{page_path}"
            print(f"Capturing: {name} ({url})")

            # Desktop screenshot (wide to show sidebar)
            try:
                context = browser.new_context(viewport={"width": 1400, "height": 900})
                page = context.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)  # Wait for CSS to load

                screenshot_path = SCREENSHOTS_DIR / f"{name}_desktop.png"
                page.screenshot(path=str(screenshot_path), full_page=False)
                print(f"  - Desktop: {screenshot_path.name}")
                context.close()
            except Exception as e:
                print(f"  - Desktop ERROR: {e}")

            # Mobile screenshot
            try:
                context = browser.new_context(viewport={"width": 375, "height": 812})
                page = context.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)

                screenshot_path = SCREENSHOTS_DIR / f"{name}_mobile.png"
                page.screenshot(path=str(screenshot_path), full_page=False)
                print(f"  - Mobile: {screenshot_path.name}")
                context.close()
            except Exception as e:
                print(f"  - Mobile ERROR: {e}")

        browser.close()

    print()
    print("=" * 60)
    print("SCREENSHOTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    take_screenshots()
