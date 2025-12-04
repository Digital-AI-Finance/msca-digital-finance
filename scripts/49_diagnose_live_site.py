"""
49_diagnose_live_site.py
Diagnose why CSS and layouts are not rendering properly on the live site.
"""

import sys
import io
import requests
from pathlib import Path
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "https://digital-ai-finance.github.io/msca-digital-finance"

def main():
    print("=" * 60)
    print("LIVE SITE DIAGNOSIS")
    print("=" * 60)
    print()

    # Fetch homepage HTML
    print("1. Fetching homepage HTML...")
    response = requests.get(BASE_URL + "/")
    html = response.text

    # Check for CSS links
    print("\n2. Looking for CSS links in HTML...")
    css_links = re.findall(r'<link[^>]*href=["\']([^"\']*\.css)["\'][^>]*>', html, re.IGNORECASE)
    css_links += re.findall(r'<link[^>]*stylesheet[^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)

    if css_links:
        print(f"   Found {len(css_links)} CSS link(s):")
        for link in set(css_links):
            print(f"   - {link}")
            # Try to fetch CSS
            if link.startswith('http'):
                css_url = link
            elif link.startswith('/'):
                css_url = "https://digital-ai-finance.github.io" + link
            else:
                css_url = BASE_URL + "/" + link

            try:
                css_resp = requests.head(css_url, timeout=5)
                status = "OK" if css_resp.status_code == 200 else f"ERROR ({css_resp.status_code})"
                print(f"     URL: {css_url} -> {status}")
            except Exception as e:
                print(f"     URL: {css_url} -> ERROR: {e}")
    else:
        print("   NO CSS LINKS FOUND!")

    # Check for JS links
    print("\n3. Looking for JS links...")
    js_links = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
    if js_links:
        print(f"   Found {len(js_links)} JS link(s):")
        for link in js_links[:5]:
            print(f"   - {link}")
    else:
        print("   NO JS LINKS FOUND!")

    # Check header structure
    print("\n4. Checking header structure...")
    header_match = re.search(r'<header[^>]*>(.*?)</header>', html, re.DOTALL)
    if header_match:
        header_html = header_match.group(1)
        print(f"   Header found, length: {len(header_html)} chars")

        # Check for nav
        nav_match = re.search(r'<nav[^>]*>(.*?)</nav>', header_html, re.DOTALL)
        if nav_match:
            nav_html = nav_match.group(1)
            nav_links = re.findall(r'<a[^>]*>([^<]+)</a>', nav_html)
            print(f"   Nav found with {len(nav_links)} links: {nav_links}")
        else:
            print("   NO NAV ELEMENT IN HEADER!")
            # Check if there are any anchor tags
            all_links = re.findall(r'<a[^>]*>([^<]+)</a>', header_html)
            print(f"   Links in header: {all_links[:10]}")
    else:
        print("   NO HEADER FOUND!")

    # Check nav class
    print("\n5. Checking nav element classes...")
    nav_elements = re.findall(r'<nav[^>]*class=["\']([^"\']*)["\'][^>]*>', html)
    print(f"   Nav classes found: {nav_elements}")

    # Check for main-nav
    if 'main-nav' in html:
        print("   'main-nav' class FOUND in HTML")
    else:
        print("   'main-nav' class NOT FOUND!")

    # Print first 2000 chars of head section
    print("\n6. HEAD section content:")
    head_match = re.search(r'<head>(.*?)</head>', html, re.DOTALL | re.IGNORECASE)
    if head_match:
        head_content = head_match.group(1)[:2000]
        print(head_content)
    else:
        print("   NO HEAD FOUND!")

    # Try to fetch the CSS directly
    print("\n7. Checking CSS file availability...")
    css_urls = [
        BASE_URL + "/css/style.css",
        BASE_URL + "css/style.css",
        "https://digital-ai-finance.github.io/msca-digital-finance/css/style.css",
    ]
    for url in css_urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                print(f"   {url} -> OK ({len(resp.text)} bytes)")
                print(f"   First 500 chars of CSS:")
                print(resp.text[:500])
            else:
                print(f"   {url} -> {resp.status_code}")
        except Exception as e:
            print(f"   {url} -> ERROR: {e}")

    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
