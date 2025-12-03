"""
42_create_theme.py
Create a custom Hugo theme for MSCA Digital Finance website.
Replicates professional EU-funded academic project design.

Usage:
    python scripts/42_create_theme.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
THEMES_DIR = PROJECT_ROOT / "themes"
THEME_NAME = "msca-digital-finance"
THEME_DIR = THEMES_DIR / THEME_NAME

# ============================================================================
# THEME TEMPLATES
# ============================================================================

THEME_TOML = """# MSCA Digital Finance Theme
name = "MSCA Digital Finance"
license = "MIT"
licenselink = "https://github.com/Digital-AI-Finance/msca-digital-finance"
description = "Custom Hugo theme for MSCA Digital Finance project"
homepage = "https://digital-ai-finance.github.io/msca-digital-finance/"
tags = ["academic", "eu-funded", "research", "responsive"]
features = ["responsive", "mobile-friendly", "eu-branding"]
min_version = "0.100.0"

[author]
  name = "Digital Finance Consortium"
  homepage = "https://www.digital-finance-msca.com/"
"""

BASEOF_HTML = """<!DOCTYPE html>
<html lang="{{ .Site.Language.Lang | default "en" }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ if .IsHome }}{{ .Site.Title }}{{ else }}{{ .Title }} | {{ .Site.Title }}{{ end }}</title>
    <meta name="description" content="{{ with .Description }}{{ . }}{{ else }}{{ .Site.Params.description }}{{ end }}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ "css/style.css" | relURL }}">
    {{ partial "head.html" . }}
</head>
<body>
    {{ partial "header.html" . }}
    <main>
        {{ block "main" . }}{{ end }}
    </main>
    {{ partial "footer.html" . }}
    <script src="{{ "js/main.js" | relURL }}"></script>
</body>
</html>
"""

HEADER_HTML = """<header class="site-header">
    <div class="container header-inner">
        <a href="{{ .Site.BaseURL }}" class="logo">
            <span class="logo-text">MSCA Digital Finance</span>
        </a>
        <button class="menu-toggle" aria-label="Toggle menu" aria-expanded="false">
            <span class="hamburger"></span>
        </button>
        <nav class="main-nav" id="main-nav">
            {{ range .Site.Menus.main }}
            <a href="{{ .URL | relURL }}" class="nav-link{{ if $.IsMenuCurrent "main" . }} active{{ end }}">{{ .Name }}</a>
            {{ end }}
        </nav>
    </div>
</header>
"""

FOOTER_HTML = """<footer class="site-footer">
    <div class="container">
        <div class="eu-funding">
            <p>This project has received funding from the European Union's Horizon Europe research and innovation programme under Marie Sklodowska-Curie grant agreement No. 101119635.</p>
        </div>
        <div class="footer-grid">
            <div class="footer-col">
                <h4>Quick Links</h4>
                <ul>
                    <li><a href="{{ "about-the-project/" | relURL }}">About</a></li>
                    <li><a href="{{ "people/" | relURL }}">People</a></li>
                    <li><a href="{{ "partners/" | relURL }}">Partners</a></li>
                    <li><a href="{{ "blog/" | relURL }}">News</a></li>
                </ul>
            </div>
            <div class="footer-col">
                <h4>Training</h4>
                <ul>
                    <li><a href="{{ "training-modules/" | relURL }}">Modules</a></li>
                    <li><a href="{{ "training-events/" | relURL }}">Events</a></li>
                </ul>
            </div>
            <div class="footer-col">
                <h4>Contact</h4>
                <p>j.osterrieder@utwente.nl</p>
                <p>University of Twente</p>
            </div>
        </div>
        <div class="copyright">
            <p>&copy; {{ now.Year }} MSCA Digital Finance Consortium</p>
        </div>
    </div>
</footer>
"""

HEAD_HTML = """<link rel="icon" href="{{ "images/favicon.ico" | relURL }}" type="image/x-icon">
<meta property="og:title" content="{{ .Title }}">
<meta property="og:description" content="{{ with .Description }}{{ . }}{{ else }}{{ .Site.Params.description }}{{ end }}">
<meta property="og:type" content="website">
<meta property="og:url" content="{{ .Permalink }}">
{{ with .Params.image }}<meta property="og:image" content="{{ . | absURL }}">{{ end }}
"""

INDEX_HTML = """{{ define "main" }}
<section class="hero">
    <div class="container">
        <h1 class="hero-title">Digital Finance</h1>
        <p class="hero-subtitle">Reaching New Frontiers</p>
        <p class="hero-desc">A Horizon Europe MSCA Doctoral Network funded by the European Union</p>
        <div class="hero-badge">Grant Agreement No. 101119635</div>
    </div>
</section>

<section class="research-domains">
    <div class="container">
        <h2>Research Domains</h2>
        <div class="domain-grid">
            <div class="domain-card">
                <div class="domain-icon">1</div>
                <h3>European Financial Data Space</h3>
                <p>Building infrastructure for financial data sharing across Europe</p>
            </div>
            <div class="domain-card">
                <div class="domain-icon">2</div>
                <h3>AI in Financial Markets</h3>
                <p>Applying machine learning to trading and risk management</p>
            </div>
            <div class="domain-card">
                <div class="domain-icon">3</div>
                <h3>Explainable AI Decisions</h3>
                <p>Making AI transparent and fair in financial applications</p>
            </div>
            <div class="domain-card">
                <div class="domain-icon">4</div>
                <h3>Blockchain Innovations</h3>
                <p>DeFi, cryptocurrencies, and distributed ledger technology</p>
            </div>
            <div class="domain-card">
                <div class="domain-icon">5</div>
                <h3>Sustainable Digital Finance</h3>
                <p>ESG investing and green fintech solutions</p>
            </div>
        </div>
    </div>
</section>

<section class="latest-news">
    <div class="container">
        <h2>Latest News</h2>
        <div class="news-grid">
            {{ range first 3 (where .Site.RegularPages "Section" "blog") }}
            <article class="news-card">
                {{ with .Params.image }}
                <img src="{{ . }}" alt="{{ $.Title }}" class="news-image">
                {{ end }}
                <div class="news-content">
                    <time>{{ .Date.Format "January 2, 2006" }}</time>
                    <h3><a href="{{ .Permalink }}">{{ .Title }}</a></h3>
                    <p>{{ .Summary | truncate 120 }}</p>
                </div>
            </article>
            {{ end }}
        </div>
        <a href="{{ "blog/" | relURL }}" class="btn">View All News</a>
    </div>
</section>

<section class="partners-preview">
    <div class="container">
        <h2>Our Partners</h2>
        <div class="partners-logos">
            {{ range first 8 (where .Site.RegularPages "Section" "partners") }}
            <a href="{{ .Permalink }}" class="partner-logo-link" title="{{ .Title }}">
                {{ with .Params.image }}
                <img src="{{ . }}" alt="{{ $.Title }}" class="partner-logo">
                {{ else }}
                <span class="partner-name">{{ $.Title }}</span>
                {{ end }}
            </a>
            {{ end }}
        </div>
        <a href="{{ "partners/" | relURL }}" class="btn btn-outline">View All Partners</a>
    </div>
</section>
{{ end }}
"""

LIST_HTML = """{{ define "main" }}
<section class="page-header">
    <div class="container">
        <h1>{{ .Title }}</h1>
        {{ with .Description }}<p class="lead">{{ . }}</p>{{ end }}
    </div>
</section>

<section class="content-section">
    <div class="container">
        {{ .Content }}

        {{ if .Pages }}
        <div class="card-grid">
            {{ range .Pages }}
            <article class="card">
                {{ with .Params.image }}
                <img src="{{ . }}" alt="{{ $.Title }}" class="card-image">
                {{ end }}
                <div class="card-body">
                    <h3><a href="{{ .Permalink }}">{{ .Title }}</a></h3>
                    {{ with .Params.role }}<p class="role">{{ . }}</p>{{ end }}
                    {{ with .Params.institution }}<p class="institution">{{ . }}</p>{{ end }}
                    <p>{{ .Summary | truncate 100 }}</p>
                </div>
            </article>
            {{ end }}
        </div>
        {{ end }}
    </div>
</section>
{{ end }}
"""

SINGLE_HTML = """{{ define "main" }}
<article class="single-page">
    <header class="page-header">
        <div class="container">
            <h1>{{ .Title }}</h1>
            {{ with .Params.date }}<time>{{ . | time.Format "January 2, 2006" }}</time>{{ end }}
        </div>
    </header>

    <section class="page-content">
        <div class="container">
            {{ with .Params.image }}
            <figure class="featured-image">
                <img src="{{ . }}" alt="{{ $.Title }}">
            </figure>
            {{ end }}

            <div class="content-body">
                {{ .Content }}
            </div>

            {{ with .Params.email }}
            <div class="contact-info">
                <p><strong>Email:</strong> <a href="mailto:{{ . }}">{{ . }}</a></p>
            </div>
            {{ end }}
        </div>
    </section>
</article>
{{ end }}
"""

PEOPLE_LIST_HTML = """{{ define "main" }}
<section class="page-header">
    <div class="container">
        <h1>{{ .Title }}</h1>
        <p class="lead">Meet our researchers, supervisors, and partners</p>
    </div>
</section>

<section class="people-section">
    <div class="container">
        {{ .Content }}

        <div class="people-grid">
            {{ range .Pages }}
            <article class="person-card">
                {{ with .Params.image }}
                <img src="{{ . }}" alt="{{ $.Title }}" class="person-photo">
                {{ else }}
                <div class="person-photo placeholder"></div>
                {{ end }}
                <div class="person-info">
                    <h3><a href="{{ .Permalink }}">{{ .Title }}</a></h3>
                    {{ with .Params.role }}<p class="role">{{ . }}</p>{{ end }}
                    {{ with .Params.institution }}<p class="institution">{{ . }}</p>{{ end }}
                </div>
            </article>
            {{ end }}
        </div>
    </div>
</section>
{{ end }}
"""

PEOPLE_SINGLE_HTML = """{{ define "main" }}
<article class="person-profile">
    <header class="profile-header">
        <div class="container">
            <div class="profile-top">
                {{ with .Params.image }}
                <img src="{{ . }}" alt="{{ $.Title }}" class="profile-photo">
                {{ else }}
                <div class="profile-photo placeholder"></div>
                {{ end }}
                <div class="profile-meta">
                    <h1>{{ .Title }}</h1>
                    {{ with .Params.role }}<p class="role">{{ . }}</p>{{ end }}
                    {{ with .Params.institution }}<p class="institution">{{ . }}</p>{{ end }}
                    {{ with .Params.email }}<p class="email"><a href="mailto:{{ . }}">{{ . }}</a></p>{{ end }}
                </div>
            </div>
        </div>
    </header>

    <section class="profile-content">
        <div class="container">
            {{ .Content }}
        </div>
    </section>
</article>
{{ end }}
"""

PARTNERS_LIST_HTML = """{{ define "main" }}
<section class="page-header">
    <div class="container">
        <h1>{{ .Title }}</h1>
        <p class="lead">Our consortium members and associated partners</p>
    </div>
</section>

<section class="partners-section">
    <div class="container">
        {{ .Content }}

        <div class="partners-grid">
            {{ range .Pages }}
            <article class="partner-card">
                {{ with .Params.image }}
                <img src="{{ . }}" alt="{{ $.Title }}" class="partner-image">
                {{ else }}
                <div class="partner-image placeholder">{{ substr $.Title 0 2 | upper }}</div>
                {{ end }}
                <div class="partner-info">
                    <h3><a href="{{ .Permalink }}">{{ .Title }}</a></h3>
                    {{ with .Params.country }}<p class="country">{{ . }}</p>{{ end }}
                </div>
            </article>
            {{ end }}
        </div>
    </div>
</section>
{{ end }}
"""

BLOG_LIST_HTML = """{{ define "main" }}
<section class="page-header">
    <div class="container">
        <h1>{{ .Title }}</h1>
        <p class="lead">Latest news and updates from our network</p>
    </div>
</section>

<section class="blog-section">
    <div class="container">
        <div class="blog-grid">
            {{ range .Pages }}
            <article class="blog-card">
                {{ with .Params.image }}
                <img src="{{ . }}" alt="{{ $.Title }}" class="blog-image">
                {{ end }}
                <div class="blog-content">
                    <time>{{ .Date.Format "January 2, 2006" }}</time>
                    <h3><a href="{{ .Permalink }}">{{ .Title }}</a></h3>
                    <p>{{ .Summary | truncate 150 }}</p>
                    <a href="{{ .Permalink }}" class="read-more">Read more</a>
                </div>
            </article>
            {{ end }}
        </div>
    </div>
</section>
{{ end }}
"""

# ============================================================================
# CSS STYLES
# ============================================================================

STYLE_CSS = """/*
 * MSCA Digital Finance Theme
 * Custom Hugo theme for EU-funded research network
 * Generated: {date}
 */

/* ==================== VARIABLES ==================== */
:root {{
    --eu-blue: #003399;
    --eu-gold: #FFD700;
    --primary: #003399;
    --secondary: #0055CC;
    --accent: #FFD700;
    --text: #333333;
    --text-light: #666666;
    --bg: #FFFFFF;
    --bg-light: #F5F7FA;
    --border: #E0E4E8;
    --shadow: rgba(0, 51, 153, 0.1);
    --radius: 8px;
    --transition: 0.3s ease;
}}

/* ==================== RESET ==================== */
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
    font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
    color: var(--text);
    background: var(--bg);
}}

/* ==================== LAYOUT ==================== */
.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}}

/* ==================== HEADER ==================== */
.site-header {{
    background: var(--eu-blue);
    color: white;
    padding: 15px 0;
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 2px 10px var(--shadow);
}}

.header-inner {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    text-decoration: none;
    color: white;
}}

.logo-text {{
    font-size: 1.25rem;
    font-weight: 700;
}}

.main-nav {{
    display: flex;
    gap: 5px;
}}

.nav-link {{
    color: white;
    text-decoration: none;
    padding: 8px 12px;
    border-radius: var(--radius);
    font-size: 0.9rem;
    transition: background var(--transition);
}}

.nav-link:hover,
.nav-link.active {{
    background: rgba(255, 255, 255, 0.15);
}}

.menu-toggle {{
    display: none;
    background: none;
    border: none;
    cursor: pointer;
    padding: 10px;
}}

.hamburger {{
    display: block;
    width: 24px;
    height: 2px;
    background: white;
    position: relative;
}}

.hamburger::before,
.hamburger::after {{
    content: '';
    position: absolute;
    width: 24px;
    height: 2px;
    background: white;
    left: 0;
}}

.hamburger::before {{ top: -8px; }}
.hamburger::after {{ top: 8px; }}

/* ==================== HERO ==================== */
.hero {{
    background: linear-gradient(135deg, var(--eu-blue) 0%, #001a4d 100%);
    color: white;
    padding: 80px 0;
    text-align: center;
}}

.hero-title {{
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 10px;
}}

.hero-subtitle {{
    font-size: 1.5rem;
    font-weight: 300;
    margin-bottom: 20px;
    color: var(--eu-gold);
}}

.hero-desc {{
    font-size: 1.1rem;
    opacity: 0.9;
    max-width: 600px;
    margin: 0 auto 20px;
}}

.hero-badge {{
    display: inline-block;
    background: var(--eu-gold);
    color: var(--eu-blue);
    padding: 8px 20px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
}}

/* ==================== SECTIONS ==================== */
section {{
    padding: 60px 0;
}}

section:nth-child(even) {{
    background: var(--bg-light);
}}

section h2 {{
    font-size: 2rem;
    color: var(--eu-blue);
    text-align: center;
    margin-bottom: 40px;
}}

.page-header {{
    background: var(--eu-blue);
    color: white;
    padding: 40px 0;
    text-align: center;
}}

.page-header h1 {{
    font-size: 2.5rem;
    margin-bottom: 10px;
}}

.page-header .lead {{
    font-size: 1.1rem;
    opacity: 0.9;
}}

/* ==================== RESEARCH DOMAINS ==================== */
.domain-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
}}

.domain-card {{
    background: white;
    padding: 30px 20px;
    border-radius: var(--radius);
    text-align: center;
    box-shadow: 0 2px 10px var(--shadow);
    transition: transform var(--transition);
}}

.domain-card:hover {{
    transform: translateY(-5px);
}}

.domain-icon {{
    width: 50px;
    height: 50px;
    background: var(--eu-blue);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 auto 15px;
}}

.domain-card h3 {{
    font-size: 1.1rem;
    color: var(--eu-blue);
    margin-bottom: 10px;
}}

.domain-card p {{
    font-size: 0.9rem;
    color: var(--text-light);
}}

/* ==================== CARDS ==================== */
.card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 25px;
}}

.card {{
    background: white;
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: 0 2px 10px var(--shadow);
    transition: transform var(--transition);
}}

.card:hover {{
    transform: translateY(-3px);
}}

.card-image {{
    width: 100%;
    height: 180px;
    object-fit: cover;
}}

.card-body {{
    padding: 20px;
}}

.card h3 {{
    font-size: 1.1rem;
    margin-bottom: 8px;
}}

.card h3 a {{
    color: var(--eu-blue);
    text-decoration: none;
}}

.card h3 a:hover {{
    text-decoration: underline;
}}

.card .role {{
    color: var(--secondary);
    font-size: 0.9rem;
    margin-bottom: 3px;
}}

.card .institution {{
    color: var(--text-light);
    font-size: 0.85rem;
}}

/* ==================== PEOPLE ==================== */
.people-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 25px;
}}

.person-card {{
    background: white;
    border-radius: var(--radius);
    padding: 25px 15px;
    text-align: center;
    box-shadow: 0 2px 10px var(--shadow);
    transition: transform var(--transition);
}}

.person-card:hover {{
    transform: translateY(-3px);
}}

.person-photo {{
    width: 120px;
    height: 120px;
    border-radius: 50%;
    object-fit: cover;
    margin: 0 auto 15px;
    border: 3px solid var(--eu-blue);
}}

.person-photo.placeholder {{
    background: var(--bg-light);
    display: flex;
    align-items: center;
    justify-content: center;
}}

.person-info h3 {{
    font-size: 1rem;
    margin-bottom: 5px;
}}

.person-info h3 a {{
    color: var(--eu-blue);
    text-decoration: none;
}}

.person-info .role {{
    color: var(--secondary);
    font-size: 0.85rem;
}}

.person-info .institution {{
    color: var(--text-light);
    font-size: 0.8rem;
}}

/* ==================== PROFILE ==================== */
.profile-header {{
    background: var(--eu-blue);
    color: white;
    padding: 50px 0;
}}

.profile-top {{
    display: flex;
    gap: 30px;
    align-items: center;
}}

.profile-photo {{
    width: 180px;
    height: 180px;
    border-radius: 50%;
    object-fit: cover;
    border: 4px solid white;
    flex-shrink: 0;
}}

.profile-meta h1 {{
    font-size: 2rem;
    margin-bottom: 10px;
}}

.profile-meta .role {{
    font-size: 1.1rem;
    color: var(--eu-gold);
}}

.profile-meta .institution {{
    opacity: 0.9;
}}

.profile-meta .email a {{
    color: white;
}}

.profile-content {{
    padding: 40px 0;
}}

/* ==================== PARTNERS ==================== */
.partners-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 25px;
}}

.partner-card {{
    background: white;
    border-radius: var(--radius);
    padding: 25px;
    text-align: center;
    box-shadow: 0 2px 10px var(--shadow);
}}

.partner-image {{
    width: 100px;
    height: 100px;
    object-fit: contain;
    margin: 0 auto 15px;
}}

.partner-image.placeholder {{
    background: var(--bg-light);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--eu-blue);
}}

.partner-info h3 {{
    font-size: 1rem;
}}

.partner-info h3 a {{
    color: var(--eu-blue);
    text-decoration: none;
}}

.partners-logos {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 30px;
    margin-bottom: 30px;
}}

.partner-logo {{
    height: 60px;
    width: auto;
    object-fit: contain;
    filter: grayscale(50%);
    transition: filter var(--transition);
}}

.partner-logo:hover {{
    filter: grayscale(0%);
}}

/* ==================== BLOG/NEWS ==================== */
.news-grid, .blog-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 25px;
}}

.news-card, .blog-card {{
    background: white;
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: 0 2px 10px var(--shadow);
}}

.news-image, .blog-image {{
    width: 100%;
    height: 180px;
    object-fit: cover;
}}

.news-content, .blog-content {{
    padding: 20px;
}}

.news-content time, .blog-content time {{
    font-size: 0.8rem;
    color: var(--text-light);
}}

.news-content h3, .blog-content h3 {{
    font-size: 1.1rem;
    margin: 8px 0;
}}

.news-content h3 a, .blog-content h3 a {{
    color: var(--eu-blue);
    text-decoration: none;
}}

.read-more {{
    color: var(--secondary);
    font-size: 0.9rem;
    font-weight: 600;
}}

/* ==================== CONTENT ==================== */
.content-body {{
    max-width: 800px;
    margin: 0 auto;
}}

.content-body h2, .content-body h3 {{
    color: var(--eu-blue);
    margin-top: 30px;
    margin-bottom: 15px;
}}

.content-body p {{
    margin-bottom: 15px;
}}

.content-body ul, .content-body ol {{
    margin-bottom: 15px;
    padding-left: 25px;
}}

.content-body li {{
    margin-bottom: 5px;
}}

.content-body a {{
    color: var(--secondary);
}}

.content-body img {{
    max-width: 100%;
    height: auto;
    border-radius: var(--radius);
    margin: 20px 0;
}}

.featured-image {{
    margin-bottom: 30px;
}}

.featured-image img {{
    width: 100%;
    max-height: 400px;
    object-fit: cover;
    border-radius: var(--radius);
}}

/* ==================== BUTTONS ==================== */
.btn {{
    display: inline-block;
    padding: 12px 30px;
    background: var(--eu-blue);
    color: white;
    text-decoration: none;
    border-radius: var(--radius);
    font-weight: 600;
    transition: background var(--transition);
}}

.btn:hover {{
    background: var(--secondary);
}}

.btn-outline {{
    background: transparent;
    border: 2px solid var(--eu-blue);
    color: var(--eu-blue);
}}

.btn-outline:hover {{
    background: var(--eu-blue);
    color: white;
}}

/* ==================== FOOTER ==================== */
.site-footer {{
    background: #1a1a2e;
    color: white;
    padding: 50px 0 30px;
}}

.eu-funding {{
    background: rgba(255, 215, 0, 0.1);
    border-left: 4px solid var(--eu-gold);
    padding: 15px 20px;
    margin-bottom: 40px;
    font-size: 0.9rem;
}}

.footer-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 30px;
    margin-bottom: 30px;
}}

.footer-col h4 {{
    color: var(--eu-gold);
    margin-bottom: 15px;
    font-size: 1rem;
}}

.footer-col ul {{
    list-style: none;
}}

.footer-col li {{
    margin-bottom: 8px;
}}

.footer-col a {{
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-size: 0.9rem;
}}

.footer-col a:hover {{
    color: white;
}}

.footer-col p {{
    font-size: 0.9rem;
    opacity: 0.8;
}}

.copyright {{
    text-align: center;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 0.85rem;
    opacity: 0.7;
}}

/* ==================== RESPONSIVE ==================== */
@media (max-width: 768px) {{
    .hero-title {{ font-size: 2rem; }}
    .hero-subtitle {{ font-size: 1.2rem; }}

    .menu-toggle {{ display: block; }}

    .main-nav {{
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--eu-blue);
        flex-direction: column;
        padding: 10px 20px 20px;
    }}

    .main-nav.active {{ display: flex; }}

    .nav-link {{
        padding: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .profile-top {{
        flex-direction: column;
        text-align: center;
    }}

    .people-grid {{ grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }}
    .person-photo {{ width: 100px; height: 100px; }}
}}
"""

# ============================================================================
# JAVASCRIPT
# ============================================================================

MAIN_JS = """/*
 * MSCA Digital Finance Theme - Main JavaScript
 */

(function() {
    'use strict';

    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const mainNav = document.querySelector('.main-nav');

    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('active');
            const expanded = mainNav.classList.contains('active');
            this.setAttribute('aria-expanded', expanded);
        });

        // Close on outside click
        document.addEventListener('click', function(e) {
            if (!menuToggle.contains(e.target) && !mainNav.contains(e.target)) {
                mainNav.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Active nav highlighting
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            link.classList.add('active');
        }
    });
})();
"""


def create_theme():
    """Create the custom Hugo theme."""
    print("=" * 60)
    print("CREATING CUSTOM THEME")
    print("=" * 60)
    print(f"Theme: {THEME_NAME}")
    print(f"Location: {THEME_DIR}")
    print()

    # Create directory structure
    dirs = [
        THEME_DIR / "layouts" / "_default",
        THEME_DIR / "layouts" / "partials",
        THEME_DIR / "layouts" / "people",
        THEME_DIR / "layouts" / "partners",
        THEME_DIR / "layouts" / "blog",
        THEME_DIR / "static" / "css",
        THEME_DIR / "static" / "js",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Create files
    files = [
        (THEME_DIR / "theme.toml", THEME_TOML),
        (THEME_DIR / "layouts" / "_default" / "baseof.html", BASEOF_HTML),
        (THEME_DIR / "layouts" / "_default" / "list.html", LIST_HTML),
        (THEME_DIR / "layouts" / "_default" / "single.html", SINGLE_HTML),
        (THEME_DIR / "layouts" / "index.html", INDEX_HTML),
        (THEME_DIR / "layouts" / "partials" / "header.html", HEADER_HTML),
        (THEME_DIR / "layouts" / "partials" / "footer.html", FOOTER_HTML),
        (THEME_DIR / "layouts" / "partials" / "head.html", HEAD_HTML),
        (THEME_DIR / "layouts" / "people" / "list.html", PEOPLE_LIST_HTML),
        (THEME_DIR / "layouts" / "people" / "single.html", PEOPLE_SINGLE_HTML),
        (THEME_DIR / "layouts" / "partners" / "list.html", PARTNERS_LIST_HTML),
        (THEME_DIR / "layouts" / "blog" / "list.html", BLOG_LIST_HTML),
        (THEME_DIR / "static" / "css" / "style.css", STYLE_CSS.format(date=datetime.now().strftime('%Y-%m-%d'))),
        (THEME_DIR / "static" / "js" / "main.js", MAIN_JS),
    ]

    print("Creating files:")
    for filepath, content in files:
        filepath.write_text(content, encoding='utf-8')
        print(f"  + {filepath.relative_to(THEME_DIR)}")

    # Update hugo.toml to use new theme
    config_file = PROJECT_ROOT / "hugo.toml"
    if config_file.exists():
        config_content = config_file.read_text(encoding='utf-8')
        if 'theme = "PaperMod"' in config_content:
            config_content = config_content.replace('theme = "PaperMod"', f'theme = "{THEME_NAME}"')
            config_file.write_text(config_content, encoding='utf-8')
            print(f"\nUpdated hugo.toml to use theme: {THEME_NAME}")

    print("\n" + "=" * 60)
    print("THEME CREATION COMPLETE")
    print("=" * 60)
    print(f"\nTheme location: {THEME_DIR}")
    print("\nNext steps:")
    print("  1. Run: hugo server -D")
    print("  2. View at: http://localhost:1313")
    print("=" * 60)


def main():
    create_theme()


if __name__ == "__main__":
    main()
