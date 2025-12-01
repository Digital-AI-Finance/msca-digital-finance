"""
04_setup_hugo.py
Sets up Hugo configuration, templates, and theme for the migrated site.
"""

import os
from pathlib import Path
from datetime import datetime

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
LAYOUTS_DIR = PROJECT_ROOT / "layouts"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Hugo config template
HUGO_CONFIG = '''
baseURL = "https://digital-ai-finance.github.io/msca-digital-finance/"
languageCode = "en-us"
title = "MSCA Digital Finance"
theme = ""

# Enable URL-based permalinks
[permalinks]
  pages = "/:slug/"
  people = "/people/:slug/"
  partners = "/partners/:slug/"
  blog = "/blog/:slug/"
  training-modules = "/training-modules/:slug/"
  training-events = "/training-events/:slug/"
  events = "/events/:slug/"

[params]
  description = "MSCA Industrial Doctoral Network in Digital Finance - Training the next generation of researchers in AI, finance, and data science"
  author = "MSCA Digital Finance Consortium"
  dateFormat = "January 2, 2006"
  showReadingTime = false
  showDate = true

[menu]
  [[menu.main]]
    name = "Home"
    url = "/"
    weight = 1
  [[menu.main]]
    name = "About"
    url = "/about-us/"
    weight = 2
  [[menu.main]]
    name = "People"
    url = "/people/"
    weight = 3
  [[menu.main]]
    name = "Partners"
    url = "/partners/"
    weight = 4
  [[menu.main]]
    name = "Research"
    url = "/individual-research-projects/"
    weight = 5
  [[menu.main]]
    name = "Training"
    url = "/trainings/"
    weight = 6
  [[menu.main]]
    name = "Events"
    url = "/events/"
    weight = 7
  [[menu.main]]
    name = "Blog"
    url = "/blog/"
    weight = 8

[markup]
  [markup.goldmark]
    [markup.goldmark.renderer]
      unsafe = true
  [markup.highlight]
    style = "monokai"

[outputs]
  home = ["HTML", "RSS"]
  section = ["HTML", "RSS"]
  taxonomy = ["HTML"]
  term = ["HTML"]

# Build settings
[build]
  writeStats = true

# Minify output
[minify]
  disableCSS = false
  disableHTML = false
  disableJS = false
  disableJSON = false
  disableSVG = false
  disableXML = false
  minifyOutput = true
'''

# Base template
BASEOF_HTML = '''<!DOCTYPE html>
<html lang="{{ .Site.LanguageCode }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ if .IsHome }}{{ .Site.Title }}{{ else }}{{ .Title }} | {{ .Site.Title }}{{ end }}</title>
    <meta name="description" content="{{ with .Description }}{{ . }}{{ else }}{{ .Site.Params.description }}{{ end }}">

    <!-- Open Graph -->
    <meta property="og:title" content="{{ .Title }}">
    <meta property="og:description" content="{{ with .Description }}{{ . }}{{ else }}{{ .Site.Params.description }}{{ end }}">
    <meta property="og:type" content="{{ if .IsPage }}article{{ else }}website{{ end }}">
    <meta property="og:url" content="{{ .Permalink }}">
    {{ with .Params.image }}<meta property="og:image" content="{{ . | absURL }}">{{ end }}

    <!-- Styles -->
    <link rel="stylesheet" href="{{ "css/style.css" | relURL }}">

    {{ block "head" . }}{{ end }}
</head>
<body>
    {{ partial "header.html" . }}

    <main class="main-content">
        {{ block "main" . }}{{ end }}
    </main>

    {{ partial "footer.html" . }}

    {{ block "scripts" . }}{{ end }}
</body>
</html>
'''

# Header partial
HEADER_HTML = '''<header class="site-header">
    <nav class="navbar">
        <div class="container">
            <a href="{{ .Site.BaseURL }}" class="logo">
                <span class="logo-text">MSCA Digital Finance</span>
            </a>

            <button class="nav-toggle" aria-label="Toggle navigation">
                <span class="hamburger"></span>
            </button>

            <ul class="nav-menu">
                {{ range .Site.Menus.main }}
                <li class="nav-item{{ if $.IsMenuCurrent "main" . }} active{{ end }}">
                    <a href="{{ .URL }}" class="nav-link">{{ .Name }}</a>
                </li>
                {{ end }}
            </ul>
        </div>
    </nav>
</header>
'''

# Footer partial
FOOTER_HTML = '''<footer class="site-footer">
    <div class="container">
        <div class="footer-content">
            <div class="footer-section">
                <h3>MSCA Digital Finance</h3>
                <p>Industrial Doctoral Network funded by the European Union's Horizon Europe research and innovation programme.</p>
                <p>Grant Agreement No. 101119635</p>
            </div>

            <div class="footer-section">
                <h3>Quick Links</h3>
                <ul>
                    <li><a href="/about-us/">About Us</a></li>
                    <li><a href="/people/">People</a></li>
                    <li><a href="/partners/">Partners</a></li>
                    <li><a href="/contact-us/">Contact</a></li>
                </ul>
            </div>

            <div class="footer-section">
                <h3>Connect</h3>
                <ul>
                    <li><a href="/open-science/">Open Science</a></li>
                    <li><a href="/blog/">News & Blog</a></li>
                    <li><a href="/events/">Events</a></li>
                </ul>
            </div>
        </div>

        <div class="footer-bottom">
            <p>&copy; {{ now.Year }} MSCA Digital Finance. All rights reserved.</p>
            <p><a href="/privacy-policy/">Privacy Policy</a></p>
        </div>
    </div>
</footer>
'''

# Single page template
SINGLE_HTML = '''{{ define "main" }}
<article class="single-page">
    <div class="container">
        <header class="page-header">
            <h1>{{ .Title }}</h1>
            {{ with .Params.description }}
            <p class="description">{{ . }}</p>
            {{ end }}
        </header>

        {{ with .Params.image }}
        <div class="featured-image">
            <img src="{{ . }}" alt="{{ $.Title }}">
        </div>
        {{ end }}

        <div class="content">
            {{ .Content }}
        </div>

        {{ if .Params.original_url }}
        <div class="original-link">
            <small>Original: <a href="{{ .Params.original_url }}" target="_blank" rel="noopener">{{ .Params.original_url }}</a></small>
        </div>
        {{ end }}
    </div>
</article>
{{ end }}
'''

# List page template
LIST_HTML = '''{{ define "main" }}
<section class="list-page">
    <div class="container">
        <header class="page-header">
            <h1>{{ .Title }}</h1>
            {{ with .Description }}
            <p class="description">{{ . }}</p>
            {{ end }}
        </header>

        <div class="content">
            {{ .Content }}
        </div>

        <div class="items-grid">
            {{ range .Pages }}
            <article class="item-card">
                {{ with .Params.image }}
                <div class="card-image">
                    <a href="{{ $.RelPermalink }}">
                        <img src="{{ . }}" alt="{{ $.Title }}">
                    </a>
                </div>
                {{ end }}
                <div class="card-content">
                    <h2><a href="{{ .RelPermalink }}">{{ .Title }}</a></h2>
                    {{ with .Description }}
                    <p>{{ . | truncate 150 }}</p>
                    {{ end }}
                </div>
            </article>
            {{ end }}
        </div>

        {{ template "_internal/pagination.html" . }}
    </div>
</section>
{{ end }}
'''

# Person single template
PERSON_SINGLE_HTML = '''{{ define "main" }}
<article class="person-profile">
    <div class="container">
        <div class="profile-header">
            {{ with .Params.image }}
            <div class="profile-image">
                <img src="{{ . }}" alt="{{ $.Title }}">
            </div>
            {{ end }}

            <div class="profile-info">
                <h1>{{ .Title }}</h1>
                {{ with .Params.role }}
                <p class="role">{{ . }}</p>
                {{ end }}
                {{ with .Params.institution }}
                <p class="institution">{{ . }}</p>
                {{ end }}

                <div class="contact-links">
                    {{ with .Params.email }}
                    <a href="mailto:{{ . }}" class="contact-link">Email</a>
                    {{ end }}
                    {{ with .Params.linkedin }}
                    <a href="{{ . }}" target="_blank" rel="noopener" class="contact-link">LinkedIn</a>
                    {{ end }}
                </div>
            </div>
        </div>

        <div class="content">
            {{ .Content }}
        </div>
    </div>
</article>
{{ end }}
'''

# Partner single template
PARTNER_SINGLE_HTML = '''{{ define "main" }}
<article class="partner-profile">
    <div class="container">
        <header class="page-header">
            {{ with .Params.image }}
            <div class="partner-logo">
                <img src="{{ . }}" alt="{{ $.Title }}">
            </div>
            {{ end }}
            <h1>{{ .Title }}</h1>
        </header>

        <div class="content">
            {{ .Content }}
        </div>

        {{ with .Params.website }}
        <div class="partner-link">
            <a href="{{ . }}" target="_blank" rel="noopener" class="btn">Visit Website</a>
        </div>
        {{ end }}
    </div>
</article>
{{ end }}
'''

# Blog single template
BLOG_SINGLE_HTML = '''{{ define "main" }}
<article class="blog-post">
    <div class="container">
        <header class="post-header">
            <h1>{{ .Title }}</h1>
            <div class="post-meta">
                <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date.Format "January 2, 2006" }}</time>
            </div>
        </header>

        {{ with .Params.image }}
        <div class="featured-image">
            <img src="{{ . }}" alt="{{ $.Title }}">
        </div>
        {{ end }}

        <div class="content">
            {{ .Content }}
        </div>

        <nav class="post-navigation">
            {{ with .PrevInSection }}
            <a href="{{ .RelPermalink }}" class="prev-post">Previous: {{ .Title }}</a>
            {{ end }}
            {{ with .NextInSection }}
            <a href="{{ .RelPermalink }}" class="next-post">Next: {{ .Title }}</a>
            {{ end }}
        </nav>
    </div>
</article>
{{ end }}
'''

# CSS styles
STYLE_CSS = '''/* MSCA Digital Finance - Main Styles */

:root {
    --primary-color: #003366;
    --secondary-color: #0066cc;
    --accent-color: #ffcc00;
    --text-color: #333;
    --light-bg: #f5f7fa;
    --white: #fff;
    --border-color: #e0e0e0;
    --max-width: 1200px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background: var(--white);
}

.container {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 0 20px;
}

/* Header & Navigation */
.site-header {
    background: var(--primary-color);
    color: var(--white);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.navbar {
    padding: 15px 0;
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    color: var(--white);
    text-decoration: none;
    font-size: 1.5rem;
    font-weight: bold;
}

.nav-menu {
    display: flex;
    list-style: none;
    gap: 30px;
}

.nav-link {
    color: var(--white);
    text-decoration: none;
    font-weight: 500;
    transition: opacity 0.2s;
}

.nav-link:hover {
    opacity: 0.8;
}

.nav-toggle {
    display: none;
    background: none;
    border: none;
    cursor: pointer;
    padding: 10px;
}

.hamburger {
    display: block;
    width: 25px;
    height: 3px;
    background: var(--white);
    position: relative;
}

.hamburger::before,
.hamburger::after {
    content: "";
    position: absolute;
    width: 25px;
    height: 3px;
    background: var(--white);
    left: 0;
}

.hamburger::before { top: -8px; }
.hamburger::after { bottom: -8px; }

/* Main Content */
.main-content {
    min-height: calc(100vh - 200px);
}

.page-header {
    padding: 60px 0 40px;
    text-align: center;
}

.page-header h1 {
    font-size: 2.5rem;
    color: var(--primary-color);
    margin-bottom: 15px;
}

.page-header .description {
    font-size: 1.2rem;
    color: #666;
    max-width: 700px;
    margin: 0 auto;
}

/* Content Area */
.content {
    padding: 40px 0;
}

.content h2 {
    color: var(--primary-color);
    margin: 30px 0 15px;
}

.content h3 {
    color: var(--secondary-color);
    margin: 25px 0 12px;
}

.content p {
    margin-bottom: 15px;
}

.content ul, .content ol {
    margin: 15px 0;
    padding-left: 30px;
}

.content li {
    margin-bottom: 8px;
}

.content img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 20px 0;
}

.content a {
    color: var(--secondary-color);
}

/* Featured Image */
.featured-image {
    margin: 30px 0;
    text-align: center;
}

.featured-image img {
    max-width: 100%;
    max-height: 500px;
    object-fit: cover;
    border-radius: 8px;
}

/* Items Grid */
.items-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 30px;
    padding: 40px 0;
}

.item-card {
    background: var(--white);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.item-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
}

.card-image img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}

.card-content {
    padding: 20px;
}

.card-content h2 {
    font-size: 1.2rem;
    margin-bottom: 10px;
}

.card-content h2 a {
    color: var(--primary-color);
    text-decoration: none;
}

/* Person Profile */
.profile-header {
    display: flex;
    gap: 40px;
    align-items: flex-start;
    padding: 40px 0;
}

.profile-image img {
    width: 200px;
    height: 200px;
    object-fit: cover;
    border-radius: 50%;
}

.profile-info h1 {
    color: var(--primary-color);
    margin-bottom: 10px;
}

.role {
    font-size: 1.2rem;
    color: var(--secondary-color);
    margin-bottom: 5px;
}

.institution {
    color: #666;
    margin-bottom: 15px;
}

.contact-links {
    display: flex;
    gap: 15px;
}

.contact-link {
    display: inline-block;
    padding: 8px 20px;
    background: var(--secondary-color);
    color: var(--white);
    text-decoration: none;
    border-radius: 5px;
    font-size: 0.9rem;
}

/* Blog Post */
.post-meta {
    color: #666;
    font-size: 0.9rem;
    margin-top: 10px;
}

.post-navigation {
    display: flex;
    justify-content: space-between;
    padding: 40px 0;
    border-top: 1px solid var(--border-color);
    margin-top: 40px;
}

/* Footer */
.site-footer {
    background: var(--primary-color);
    color: var(--white);
    padding: 60px 0 30px;
    margin-top: 60px;
}

.footer-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 40px;
    margin-bottom: 40px;
}

.footer-section h3 {
    font-size: 1.1rem;
    margin-bottom: 20px;
    color: var(--accent-color);
}

.footer-section ul {
    list-style: none;
}

.footer-section li {
    margin-bottom: 10px;
}

.footer-section a {
    color: var(--white);
    text-decoration: none;
    opacity: 0.9;
}

.footer-section a:hover {
    opacity: 1;
    text-decoration: underline;
}

.footer-bottom {
    text-align: center;
    padding-top: 30px;
    border-top: 1px solid rgba(255,255,255,0.2);
}

.footer-bottom p {
    margin: 5px 0;
    font-size: 0.9rem;
    opacity: 0.8;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 12px 30px;
    background: var(--secondary-color);
    color: var(--white);
    text-decoration: none;
    border-radius: 5px;
    font-weight: 500;
    transition: background 0.2s;
}

.btn:hover {
    background: var(--primary-color);
}

/* Responsive */
@media (max-width: 768px) {
    .nav-toggle {
        display: block;
    }

    .nav-menu {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--primary-color);
        flex-direction: column;
        padding: 20px;
        gap: 15px;
        display: none;
    }

    .nav-menu.active {
        display: flex;
    }

    .profile-header {
        flex-direction: column;
        align-items: center;
        text-align: center;
    }

    .page-header h1 {
        font-size: 2rem;
    }

    .items-grid {
        grid-template-columns: 1fr;
    }
}
'''


def create_file(path, content):
    """Create a file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f"  Created: {path}")


def main():
    print("=" * 60)
    print("Hugo Setup for MSCA Digital Finance")
    print("=" * 60)

    # Create Hugo config
    print("\nCreating Hugo configuration...")
    create_file(PROJECT_ROOT / "config.toml", HUGO_CONFIG)

    # Create base template
    print("\nCreating layout templates...")
    create_file(LAYOUTS_DIR / "_default" / "baseof.html", BASEOF_HTML)
    create_file(LAYOUTS_DIR / "_default" / "single.html", SINGLE_HTML)
    create_file(LAYOUTS_DIR / "_default" / "list.html", LIST_HTML)

    # Create partials
    create_file(LAYOUTS_DIR / "partials" / "header.html", HEADER_HTML)
    create_file(LAYOUTS_DIR / "partials" / "footer.html", FOOTER_HTML)

    # Create section-specific templates
    create_file(LAYOUTS_DIR / "people" / "single.html", PERSON_SINGLE_HTML)
    create_file(LAYOUTS_DIR / "partners" / "single.html", PARTNER_SINGLE_HTML)
    create_file(LAYOUTS_DIR / "blog" / "single.html", BLOG_SINGLE_HTML)

    # Create CSS
    print("\nCreating stylesheets...")
    css_dir = PROJECT_ROOT / "static" / "css"
    create_file(css_dir / "style.css", STYLE_CSS)

    # Create archetypes
    print("\nCreating archetypes...")
    archetype_content = '''---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
draft: true
---
'''
    create_file(PROJECT_ROOT / "archetypes" / "default.md", archetype_content)

    # Create homepage if it doesn't exist
    homepage = PROJECT_ROOT / "content" / "_index.md"
    if not homepage.exists():
        print("\nCreating homepage...")
        homepage_content = '''---
title: "MSCA Digital Finance"
date: ''' + datetime.now().strftime('%Y-%m-%d') + '''
draft: false
---

# Welcome to MSCA Digital Finance

The Industrial Doctoral Network in Digital Finance (DIGITAL) is an EU-funded Marie Sklodowska-Curie Action that brings together academic institutions, financial companies, technology providers, and policy organizations to jointly train the next generation of researchers in digital finance.

## Our Mission

We aim to develop cutting-edge research in artificial intelligence, machine learning, and data science applications in finance, while training 17 PhD researchers who will shape the future of the financial industry.

## Key Areas

- **Financial Data Science** - Advanced analytics and AI for financial applications
- **Explainable AI** - Transparent and fair AI systems for finance
- **Blockchain & Digital Innovation** - Distributed ledger technologies
- **Sustainable Finance** - Green finance and ESG analytics

[Learn more about our project](/about-the-project/) | [Meet our team](/people/) | [View our partners](/partners/)
'''
        create_file(homepage, homepage_content)

    print("\n" + "=" * 60)
    print("Hugo Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run 'hugo server -D' to preview locally")
    print("  2. Run 'hugo' to build the site")
    print("=" * 60)


if __name__ == "__main__":
    main()
