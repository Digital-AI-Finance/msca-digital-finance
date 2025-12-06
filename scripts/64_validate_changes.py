"""
Validate Content & UX Improvements
===================================
Quick validation script to verify all changes were applied correctly.
"""

import os
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent.parent

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if filepath.exists():
        print(f"[OK] {description}: {filepath.name}")
        return True
    else:
        print(f"[MISSING] {description}: {filepath.name}")
        return False

def check_file_contains(filepath, pattern, description):
    """Check if a file contains a specific pattern."""
    if not filepath.exists():
        print(f"[MISSING FILE] {filepath.name}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if re.search(pattern, content, re.MULTILINE):
        print(f"[OK] {description}")
        return True
    else:
        print(f"[MISSING] {description}")
        return False

def validate_changes():
    """Run all validation checks."""
    print("=" * 70)
    print("MSCA Digital Finance - Content & UX Improvements Validation")
    print("=" * 70)

    checks_passed = 0
    checks_total = 0

    print("\n1. NEW FILES CREATED")
    print("-" * 70)

    files_to_check = [
        (BASE_DIR / "layouts/partials/breadcrumbs.html", "Breadcrumbs partial"),
        (BASE_DIR / "scripts/61_fix_event_dates.py", "Event dates script"),
        (BASE_DIR / "scripts/62_add_blog_excerpts.py", "Blog excerpts script"),
        (BASE_DIR / "scripts/63_update_research_domains.py", "Research domains script"),
        (BASE_DIR / "CONTENT_UX_IMPROVEMENTS_REPORT.md", "Improvements report"),
    ]

    for filepath, desc in files_to_check:
        checks_total += 1
        if check_file_exists(filepath, desc):
            checks_passed += 1

    print("\n2. BASEOF.HTML MODIFICATIONS")
    print("-" * 70)

    baseof = BASE_DIR / "layouts/_default/baseof.html"
    baseof_checks = [
        (r'partial "breadcrumbs\.html"', "Breadcrumbs partial included"),
        (r'id="back-to-top"', "Back to top button added"),
        (r'<svg.*?viewBox="0 0 20 20"', "Back to top SVG icon"),
    ]

    for pattern, desc in baseof_checks:
        checks_total += 1
        if check_file_contains(baseof, pattern, desc):
            checks_passed += 1

    print("\n3. MAIN.JS ENHANCEMENTS")
    print("-" * 70)

    mainjs = BASE_DIR / "static/js/main.js"
    js_checks = [
        (r'getElementById\([\'"]back-to-top[\'"]\)', "Back to top button handler"),
        (r'window\.pageYOffset > 300', "Scroll position check"),
        (r'window\.scrollTo', "Smooth scroll implementation"),
        (r'sidebar\.classList\.toggle\([\'"]active[\'"]\)', "Mobile menu toggle"),
    ]

    for pattern, desc in js_checks:
        checks_total += 1
        if check_file_contains(mainjs, pattern, desc):
            checks_passed += 1

    print("\n4. STYLE.CSS ADDITIONS")
    print("-" * 70)

    stylecss = BASE_DIR / "static/css/style.css"
    css_checks = [
        (r'\.breadcrumbs\s*\{', "Breadcrumbs CSS"),
        (r'\.back-to-top\s*\{', "Back to top CSS"),
        (r'@keyframes fadeIn', "Fade in animation"),
        (r'body\.sidebar-open::before', "Mobile overlay CSS"),
        (r'transform: translateX', "Mobile slide animation"),
    ]

    for pattern, desc in css_checks:
        checks_total += 1
        if check_file_contains(stylecss, pattern, desc):
            checks_passed += 1

    print("\n5. CONTENT UPDATES")
    print("-" * 70)

    # Check some sample event dates were updated
    sample_events = [
        BASE_DIR / "content/training-events/kickoff-meeting-and-technical-training.md",
        BASE_DIR / "content/events/1st-arc-training-week.md",
    ]

    for event_file in sample_events:
        checks_total += 1
        # Check if date is NOT 2025-12-01
        if check_file_contains(event_file, r"date:\s*['\"](?!2025-12-01)", f"Updated date in {event_file.name}"):
            checks_passed += 1

    # Check some blog posts have descriptions
    sample_blogs = [
        BASE_DIR / "content/blog/boundaries-of-explainable-ai-in-financial-time-series.md",
        BASE_DIR / "content/blog/digital-featured-by-wu-vienna.md",
    ]

    for blog_file in sample_blogs:
        checks_total += 1
        if check_file_contains(blog_file, r'description:\s*"', f"Description added to {blog_file.name}"):
            checks_passed += 1

    print("\n" + "=" * 70)
    print(f"VALIDATION RESULTS: {checks_passed}/{checks_total} checks passed")
    print("=" * 70)

    if checks_passed == checks_total:
        print("\n[SUCCESS] All validation checks passed!")
        return True
    else:
        print(f"\n[WARNING] {checks_total - checks_passed} checks failed")
        return False

if __name__ == "__main__":
    validate_changes()
