"""
50_check_live_css.py
Check if the live site has the new CSS with header styles.
"""

import sys
import io
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CSS_URL = "https://digital-ai-finance.github.io/msca-digital-finance/css/style.css"

def main():
    print("=" * 60)
    print("LIVE CSS CHECK")
    print("=" * 60)
    print()

    # Add cache-busting header
    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }

    response = requests.get(CSS_URL, headers=headers)
    css_content = response.text

    print(f"CSS URL: {CSS_URL}")
    print(f"Status: {response.status_code}")
    print(f"Content-Length: {len(css_content)} bytes")
    print()

    # Check for key new styles
    checks = [
        (".site-header", "Site header styling"),
        (".header-top", "Header top (EU banner)"),
        (".header-main", "Header main"),
        (".eu-banner", "EU banner"),
        (".logo-icon", "Logo icon"),
        (".logo-text", "Logo text"),
        (".main-nav", "Main navigation"),
        (".nav-link", "Nav links"),
        (".menu-toggle", "Menu toggle"),
        (".hamburger-line", "Hamburger lines"),
    ]

    print("Checking for new styles:")
    for selector, description in checks:
        found = selector in css_content
        status = "FOUND" if found else "MISSING"
        print(f"  {description}: {status}")

    print()
    print("First 1000 chars of CSS:")
    print("-" * 40)
    print(css_content[:1000])
    print("-" * 40)
    print()
    print("Last 500 chars of CSS:")
    print("-" * 40)
    print(css_content[-500:])
    print("-" * 40)

    # Check homepage HTML for new header
    print()
    print("Checking homepage header structure...")
    html_response = requests.get("https://digital-ai-finance.github.io/msca-digital-finance/", headers=headers)
    html = html_response.text

    header_checks = [
        ("header-top", "Header top div"),
        ("header-main", "Header main div"),
        ("eu-banner", "EU banner"),
        ("logo-icon", "Logo icon"),
        ("main-nav", "Main nav"),
    ]

    for class_name, description in header_checks:
        found = class_name in html
        status = "FOUND" if found else "MISSING"
        print(f"  {description}: {status}")


if __name__ == "__main__":
    main()
