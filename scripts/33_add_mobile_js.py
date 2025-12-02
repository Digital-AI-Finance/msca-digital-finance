"""
33_add_mobile_js.py
Add mobile menu JavaScript and update layout templates.
Creates responsive hamburger menu functionality.

Usage:
    python scripts/33_add_mobile_js.py
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
JS_DIR = STATIC_DIR / "js"
LAYOUTS_DIR = PROJECT_ROOT / "layouts"

MAIN_JS = """/*
 * Main JavaScript for MSCA Digital Finance
 * Generated: {date}
 */

(function() {{
    'use strict';

    // Mobile menu toggle
    function initMobileMenu() {{
        const menuToggle = document.querySelector('.menu-toggle');
        const nav = document.querySelector('nav, .main-nav');

        if (!menuToggle || !nav) return;

        menuToggle.addEventListener('click', function(e) {{
            e.preventDefault();
            nav.classList.toggle('active');
            this.classList.toggle('active');

            // Update aria-expanded
            const expanded = nav.classList.contains('active');
            this.setAttribute('aria-expanded', expanded);

            // Update icon
            this.innerHTML = expanded ? '&#10005;' : '&#9776;';
        }});

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {{
            if (!nav.contains(e.target) && !menuToggle.contains(e.target)) {{
                nav.classList.remove('active');
                menuToggle.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
                menuToggle.innerHTML = '&#9776;';
            }}
        }});

        // Close menu on escape key
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape' && nav.classList.contains('active')) {{
                nav.classList.remove('active');
                menuToggle.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
                menuToggle.innerHTML = '&#9776;';
            }}
        }});
    }}

    // Smooth scroll for anchor links
    function initSmoothScroll() {{
        document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {{
            anchor.addEventListener('click', function(e) {{
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;

                const target = document.querySelector(targetId);
                if (target) {{
                    e.preventDefault();
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});
    }}

    // Lazy load images
    function initLazyLoad() {{
        if ('IntersectionObserver' in window) {{
            const imageObserver = new IntersectionObserver(function(entries) {{
                entries.forEach(function(entry) {{
                    if (entry.isIntersecting) {{
                        const img = entry.target;
                        if (img.dataset.src) {{
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }}
                        imageObserver.unobserve(img);
                    }}
                }});
            }});

            document.querySelectorAll('img[data-src]').forEach(function(img) {{
                imageObserver.observe(img);
            }});
        }} else {{
            // Fallback for older browsers
            document.querySelectorAll('img[data-src]').forEach(function(img) {{
                img.src = img.dataset.src;
            }});
        }}
    }}

    // Active navigation highlighting
    function initActiveNav() {{
        const currentPath = window.location.pathname;
        document.querySelectorAll('nav a, .main-nav a').forEach(function(link) {{
            const href = link.getAttribute('href');
            if (href && currentPath.startsWith(href) && href !== '/') {{
                link.classList.add('active');
            }} else if (href === '/' && currentPath === '/') {{
                link.classList.add('active');
            }}
        }});
    }}

    // Back to top button
    function initBackToTop() {{
        const btn = document.createElement('button');
        btn.innerHTML = '&#8593;';
        btn.className = 'back-to-top';
        btn.setAttribute('aria-label', 'Back to top');
        btn.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #003366;
            color: white;
            border: none;
            cursor: pointer;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s, visibility 0.3s;
            z-index: 1000;
            font-size: 18px;
        `;

        document.body.appendChild(btn);

        window.addEventListener('scroll', function() {{
            if (window.pageYOffset > 300) {{
                btn.style.opacity = '1';
                btn.style.visibility = 'visible';
            }} else {{
                btn.style.opacity = '0';
                btn.style.visibility = 'hidden';
            }}
        }});

        btn.addEventListener('click', function() {{
            window.scrollTo({{
                top: 0,
                behavior: 'smooth'
            }});
        }});
    }}

    // Initialize on DOM ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', init);
    }} else {{
        init();
    }}

    function init() {{
        initMobileMenu();
        initSmoothScroll();
        initLazyLoad();
        initActiveNav();
        initBackToTop();
    }}
}})();
"""


def generate_javascript():
    """Generate the main JavaScript file."""
    print("=" * 60)
    print("MOBILE JS GENERATOR")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create JS directory
    JS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate JS with current date
    js_content = MAIN_JS.format(date=datetime.now().strftime('%Y-%m-%d'))

    # Write JS file
    js_file = JS_DIR / "main.js"
    js_file.write_text(js_content, encoding='utf-8')
    print(f"  Created: {js_file}")

    return js_file


def update_baseof_template():
    """Update baseof.html to include the JS file."""
    baseof_path = LAYOUTS_DIR / "_default" / "baseof.html"

    if not baseof_path.exists():
        print("  Warning: baseof.html not found, creating basic template")
        baseof_path.parent.mkdir(parents=True, exist_ok=True)

        baseof_content = """<!DOCTYPE html>
<html lang="{{ .Site.Language.Lang | default "en" }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ if .IsHome }}{{ .Site.Title }}{{ else }}{{ .Title }} | {{ .Site.Title }}{{ end }}</title>
    <meta name="description" content="{{ with .Description }}{{ . }}{{ else }}{{ .Site.Params.description }}{{ end }}">
    <link rel="stylesheet" href="/css/style.css">
    {{ partial "head.html" . }}
</head>
<body>
    {{ partial "header.html" . }}
    <main class="container">
        {{ block "main" . }}{{ end }}
    </main>
    {{ partial "footer.html" . }}
    <script src="/js/main.js"></script>
</body>
</html>
"""
        baseof_path.write_text(baseof_content, encoding='utf-8')
        print(f"  Created: {baseof_path}")
        return

    # Update existing file
    content = baseof_path.read_text(encoding='utf-8', errors='replace')

    # Check if JS already included
    if '/js/main.js' in content:
        print(f"  JS already included in {baseof_path.name}")
        return

    # Add script before </body>
    if '</body>' in content:
        content = content.replace('</body>', '    <script src="/js/main.js"></script>\n</body>')
        baseof_path.write_text(content, encoding='utf-8')
        print(f"  Updated: {baseof_path}")
    else:
        print(f"  Warning: Could not find </body> in {baseof_path.name}")


def update_header_template():
    """Update header.html to include menu toggle button."""
    header_path = LAYOUTS_DIR / "partials" / "header.html"

    if not header_path.exists():
        print("  Warning: header.html not found, creating basic template")
        header_path.parent.mkdir(parents=True, exist_ok=True)

        header_content = """<header class="site-header">
    <div class="header-inner container">
        <a href="/" class="site-title">{{ .Site.Title }}</a>
        <button class="menu-toggle" aria-label="Toggle menu" aria-expanded="false">&#9776;</button>
        <nav class="main-nav">
            {{ range .Site.Menus.main }}
            <a href="{{ .URL }}" class="nav-link{{ if $.IsMenuCurrent "main" . }} active{{ end }}">{{ .Name }}</a>
            {{ end }}
        </nav>
    </div>
</header>
"""
        header_path.write_text(header_content, encoding='utf-8')
        print(f"  Created: {header_path}")
        return

    # Update existing file
    content = header_path.read_text(encoding='utf-8', errors='replace')

    # Check if menu toggle already exists
    if 'menu-toggle' in content:
        print(f"  Menu toggle already in {header_path.name}")
        return

    # Try to add menu toggle before nav
    if '<nav' in content:
        content = content.replace('<nav', '<button class="menu-toggle" aria-label="Toggle menu" aria-expanded="false">&#9776;</button>\n        <nav')
        header_path.write_text(content, encoding='utf-8')
        print(f"  Updated: {header_path}")
    else:
        print(f"  Warning: Could not find <nav in {header_path.name}")


def main():
    js_file = generate_javascript()
    update_baseof_template()
    update_header_template()

    print("\n" + "=" * 60)
    print("MOBILE JS COMPLETE")
    print("=" * 60)
    print(f"  JavaScript: {js_file}")
    print()
    print("  Features added:")
    print("    - Mobile hamburger menu toggle")
    print("    - Smooth scroll for anchor links")
    print("    - Lazy loading for images")
    print("    - Active navigation highlighting")
    print("    - Back to top button")
    print("=" * 60)


if __name__ == "__main__":
    main()
