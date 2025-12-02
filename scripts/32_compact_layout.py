"""
32_compact_layout.py
Generate compact CSS to reduce whitespace and spacing.
Creates a minimal, clean layout for the Hugo site.

Usage:
    python scripts/32_compact_layout.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STATIC_DIR = PROJECT_ROOT / "static"
CSS_DIR = STATIC_DIR / "css"

COMPACT_CSS = """/*
 * Compact Layout CSS for MSCA Digital Finance
 * Generated: {date}
 * Purpose: Minimal whitespace, clean professional look
 */

/* ==================== RESET & BASE ==================== */
*, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

html {{
    font-size: 16px;
    scroll-behavior: smooth;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.5;
    color: #333;
    background: #fff;
}}

/* ==================== LAYOUT ==================== */
.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 15px;
}}

.page-wrapper {{
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}}

main {{
    flex: 1;
    padding: 20px 0;
}}

/* ==================== HEADER ==================== */
header, .site-header {{
    background: #003366;
    color: #fff;
    padding: 10px 0;
    position: sticky;
    top: 0;
    z-index: 1000;
}}

.header-inner {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 15px;
}}

.site-title, .logo {{
    font-size: 1.25rem;
    font-weight: 600;
    color: #fff;
    text-decoration: none;
}}

.site-title:hover {{
    opacity: 0.9;
}}

/* ==================== NAVIGATION ==================== */
nav, .main-nav {{
    display: flex;
    gap: 5px;
}}

nav a, .nav-link {{
    color: #fff;
    text-decoration: none;
    padding: 5px 10px;
    font-size: 0.9rem;
    border-radius: 3px;
    transition: background 0.2s;
}}

nav a:hover, .nav-link:hover {{
    background: rgba(255,255,255,0.1);
}}

nav a.active {{
    background: rgba(255,255,255,0.2);
}}

/* Mobile menu toggle */
.menu-toggle {{
    display: none;
    background: none;
    border: none;
    color: #fff;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 5px;
}}

/* ==================== CONTENT ==================== */
article {{
    padding: 15px 0;
}}

.page-title, h1 {{
    font-size: 1.75rem;
    margin-bottom: 15px;
    color: #003366;
    line-height: 1.2;
}}

h2 {{
    font-size: 1.4rem;
    margin: 20px 0 10px;
    color: #003366;
}}

h3 {{
    font-size: 1.15rem;
    margin: 15px 0 8px;
    color: #444;
}}

h4, h5, h6 {{
    font-size: 1rem;
    margin: 10px 0 5px;
}}

p {{
    margin-bottom: 10px;
}}

/* ==================== CARDS & GRIDS ==================== */
.card-grid, .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 15px;
    margin: 15px 0;
}}

.card {{
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 5px;
    padding: 12px;
    transition: box-shadow 0.2s;
}}

.card:hover {{
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.card-title {{
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 5px;
    color: #003366;
}}

.card-content {{
    font-size: 0.9rem;
    color: #666;
}}

.card img {{
    width: 100%;
    height: 150px;
    object-fit: cover;
    border-radius: 3px;
    margin-bottom: 8px;
}}

/* ==================== PEOPLE & PARTNERS ==================== */
.person-card, .partner-card {{
    display: flex;
    gap: 12px;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 5px;
    margin-bottom: 10px;
}}

.person-image, .partner-logo {{
    width: 80px;
    height: 80px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
}}

.partner-logo {{
    border-radius: 5px;
}}

.person-info, .partner-info {{
    flex: 1;
    min-width: 0;
}}

.person-name {{
    font-size: 1rem;
    font-weight: 600;
    color: #003366;
    margin-bottom: 3px;
}}

.person-role, .person-institution {{
    font-size: 0.85rem;
    color: #666;
}}

/* ==================== LISTS ==================== */
ul, ol {{
    margin: 10px 0;
    padding-left: 20px;
}}

li {{
    margin-bottom: 5px;
}}

/* List page */
.list-page ul {{
    list-style: none;
    padding: 0;
}}

.list-page li {{
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}}

.list-page li:last-child {{
    border-bottom: none;
}}

.list-page a {{
    color: #003366;
    text-decoration: none;
}}

.list-page a:hover {{
    text-decoration: underline;
}}

/* ==================== LINKS & BUTTONS ==================== */
a {{
    color: #0066cc;
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

.btn, button {{
    display: inline-block;
    padding: 8px 16px;
    background: #003366;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    text-decoration: none;
    transition: background 0.2s;
}}

.btn:hover, button:hover {{
    background: #004488;
    text-decoration: none;
}}

/* ==================== IMAGES ==================== */
img {{
    max-width: 100%;
    height: auto;
}}

figure {{
    margin: 15px 0;
}}

figcaption {{
    font-size: 0.85rem;
    color: #666;
    margin-top: 5px;
}}

/* ==================== TABLES ==================== */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 0.9rem;
}}

th, td {{
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}}

th {{
    background: #f8f9fa;
    font-weight: 600;
}}

tr:hover {{
    background: #f8f9fa;
}}

/* ==================== FOOTER ==================== */
footer, .site-footer {{
    background: #003366;
    color: #fff;
    padding: 20px 0;
    margin-top: auto;
}}

.footer-content {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}}

.footer-links {{
    display: flex;
    gap: 15px;
}}

.footer-links a {{
    color: rgba(255,255,255,0.8);
    font-size: 0.85rem;
}}

.footer-links a:hover {{
    color: #fff;
}}

.copyright {{
    font-size: 0.8rem;
    opacity: 0.7;
}}

/* ==================== UTILITIES ==================== */
.text-center {{ text-align: center; }}
.text-right {{ text-align: right; }}
.mt-1 {{ margin-top: 5px; }}
.mt-2 {{ margin-top: 10px; }}
.mt-3 {{ margin-top: 15px; }}
.mb-1 {{ margin-bottom: 5px; }}
.mb-2 {{ margin-bottom: 10px; }}
.mb-3 {{ margin-bottom: 15px; }}
.hidden {{ display: none; }}

/* ==================== EU FUNDING NOTICE ==================== */
.eu-funding {{
    background: #f0f4f8;
    border-left: 4px solid #003399;
    padding: 10px 15px;
    margin: 15px 0;
    font-size: 0.85rem;
}}

.eu-funding img {{
    height: 40px;
    margin-right: 10px;
    vertical-align: middle;
}}

/* ==================== RESPONSIVE ==================== */
@media (max-width: 768px) {{
    html {{
        font-size: 15px;
    }}

    .header-inner {{
        flex-wrap: wrap;
    }}

    .menu-toggle {{
        display: block;
    }}

    nav, .main-nav {{
        display: none;
        width: 100%;
        flex-direction: column;
        padding-top: 10px;
    }}

    nav.active, .main-nav.active {{
        display: flex;
    }}

    nav a, .nav-link {{
        padding: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }}

    .card-grid, .grid {{
        grid-template-columns: 1fr;
    }}

    .person-card, .partner-card {{
        flex-direction: column;
        align-items: center;
        text-align: center;
    }}

    .footer-content {{
        flex-direction: column;
        text-align: center;
    }}

    .footer-links {{
        flex-wrap: wrap;
        justify-content: center;
    }}

    table {{
        display: block;
        overflow-x: auto;
    }}
}}

@media (max-width: 480px) {{
    .page-title, h1 {{
        font-size: 1.5rem;
    }}

    h2 {{
        font-size: 1.25rem;
    }}
}}

/* ==================== PRINT ==================== */
@media print {{
    header, footer, nav, .menu-toggle {{
        display: none;
    }}

    body {{
        font-size: 12pt;
    }}

    a {{
        color: #000;
        text-decoration: underline;
    }}

    .card {{
        break-inside: avoid;
    }}
}}
"""


def generate_compact_css():
    """Generate the compact CSS file."""
    print("=" * 60)
    print("COMPACT LAYOUT GENERATOR")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create CSS directory
    CSS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate CSS with current date
    css_content = COMPACT_CSS.format(date=datetime.now().strftime('%Y-%m-%d'))

    # Backup existing CSS
    css_file = CSS_DIR / "style.css"
    if css_file.exists():
        backup_file = CSS_DIR / f"style_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.css"
        css_file.rename(backup_file)
        print(f"  Backed up existing CSS to: {backup_file.name}")

    # Write new CSS
    css_file.write_text(css_content, encoding='utf-8')
    print(f"  Created: {css_file}")

    # Calculate stats
    lines = len(css_content.split('\n'))
    size = len(css_content)
    print(f"  Size: {size:,} bytes ({lines} lines)")

    return css_file


def main():
    output_file = generate_compact_css()

    print("\n" + "=" * 60)
    print("COMPACT CSS GENERATED")
    print("=" * 60)
    print(f"  Output: {output_file}")
    print()
    print("  Features:")
    print("    - Minimal spacing and padding")
    print("    - Responsive mobile layout")
    print("    - Clean card grids")
    print("    - Professional color scheme")
    print("    - Mobile menu support")
    print("    - Print styles")
    print("=" * 60)


if __name__ == "__main__":
    main()
