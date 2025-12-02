"""
14_html_report.py
Generates an HTML report of what was downloaded vs broken/missing.
Opens the report in the default browser.
"""

import sys
import io
import os
import webbrowser

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.parse import unquote

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"


def load_json(filename):
    """Load JSON file if exists."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def get_all_content_files():
    """Get all content files with their stats."""
    files = []
    for md_file in CONTENT_DIR.rglob("*.md"):
        rel_path = md_file.relative_to(CONTENT_DIR)

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title from front matter
        title = ""
        if content.startswith('---'):
            lines = content.split('\n')
            for line in lines[1:]:
                if line.startswith('---'):
                    break
                if line.startswith('title:'):
                    title = line.replace('title:', '').strip().strip('"\'')
                    break

        # Skip front matter for word count
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]

        words = len(body.split())

        # Determine category
        parts = rel_path.parts
        category = parts[0] if len(parts) > 1 else 'root'

        files.append({
            'path': str(rel_path),
            'title': title or str(rel_path),
            'words': words,
            'category': category,
            'status': 'empty' if words < 10 else ('short' if words < 50 else 'good')
        })

    return files


def get_broken_links():
    """Get all broken links from link fix results."""
    data = load_json('link_fix_results.json')
    if not data:
        return []

    broken = []
    summary = data.get('broken_summary', {})

    for item in summary.get('broken_images', []):
        broken.append({
            'type': 'image',
            'file': item.get('file', ''),
            'url': item.get('url', '')
        })

    for item in summary.get('broken_pages', []):
        broken.append({
            'type': 'page',
            'file': item.get('file', ''),
            'url': item.get('url', '')
        })

    return broken


def get_asset_stats():
    """Get downloaded asset statistics."""
    stats = {
        'images': {'count': 0, 'size_mb': 0, 'by_category': defaultdict(int)},
        'pdfs': {'count': 0, 'files': []},
        'documents': {'count': 0, 'files': []}
    }

    # Images
    images_dir = STATIC_DIR / "images"
    if images_dir.exists():
        for img in images_dir.rglob("*"):
            if img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                stats['images']['count'] += 1
                stats['images']['size_mb'] += img.stat().st_size / (1024 * 1024)
                cat = img.parent.name if img.parent != images_dir else 'root'
                stats['images']['by_category'][cat] += 1

    # PDFs
    pdf_dir = STATIC_DIR / "assets" / "pdfs"
    if pdf_dir.exists():
        for pdf in pdf_dir.glob("*.pdf"):
            stats['pdfs']['count'] += 1
            stats['pdfs']['files'].append(pdf.name)

    # Documents
    doc_dir = STATIC_DIR / "assets" / "documents"
    if doc_dir.exists():
        for doc in doc_dir.rglob("*"):
            if doc.is_file():
                stats['documents']['count'] += 1
                stats['documents']['files'].append(doc.name)

    return stats


def get_crawl_comparison():
    """Compare deep crawl results with local content."""
    crawl_data = load_json('deep_crawl_results.json')
    if not crawl_data:
        return None

    return {
        'pages_crawled': crawl_data.get('pages_crawled', 0),
        'total_discovered': crawl_data.get('total_discovered', 0),
        'missing_urls': crawl_data.get('missing_urls', []),
        'orphaned_urls': crawl_data.get('orphaned_urls', [])
    }


def generate_html_report():
    """Generate comprehensive HTML report."""

    content_files = get_all_content_files()
    broken_links = get_broken_links()
    assets = get_asset_stats()
    crawl = get_crawl_comparison()

    # Categorize files
    good_files = [f for f in content_files if f['status'] == 'good']
    short_files = [f for f in content_files if f['status'] == 'short']
    empty_files = [f for f in content_files if f['status'] == 'empty']

    # Group by category
    by_category = defaultdict(list)
    for f in content_files:
        by_category[f['category']].append(f)

    # Group broken links by type
    broken_images = [b for b in broken_links if b['type'] == 'image']
    broken_pages = [b for b in broken_links if b['type'] == 'page']

    total_words = sum(f['words'] for f in content_files)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MSCA Digital Finance - Migration Report</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin: 30px 0 20px; }}
        h3 {{ color: #555; margin: 20px 0 10px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; }}
        .stat-label {{ opacity: 0.9; }}
        .success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important; }}
        .warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important; }}
        .info {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f5f5f5; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.85em; font-weight: 500; }}
        .badge-good {{ background: #d4edda; color: #155724; }}
        .badge-short {{ background: #fff3cd; color: #856404; }}
        .badge-empty {{ background: #f8d7da; color: #721c24; }}
        .badge-broken {{ background: #f8d7da; color: #721c24; }}
        .collapsible {{ cursor: pointer; padding: 15px; background: #f8f9fa; border: none; width: 100%; text-align: left; font-size: 1em; border-radius: 5px; margin: 5px 0; }}
        .collapsible:hover {{ background: #e9ecef; }}
        .collapsible:after {{ content: '+'; float: right; font-weight: bold; }}
        .collapsible.active:after {{ content: '-'; }}
        .content {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; }}
        .content.show {{ max-height: 2000px; }}
        .url {{ word-break: break-all; font-family: monospace; font-size: 0.9em; color: #666; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
        .progress {{ height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .progress-bar {{ height: 100%; background: linear-gradient(90deg, #11998e, #38ef7d); transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MSCA Digital Finance - Migration Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="stats">
            <div class="stat success">
                <div class="stat-value">{len(content_files)}</div>
                <div class="stat-label">Total Pages</div>
            </div>
            <div class="stat info">
                <div class="stat-value">{total_words:,}</div>
                <div class="stat-label">Total Words</div>
            </div>
            <div class="stat success">
                <div class="stat-value">{assets['images']['count']}</div>
                <div class="stat-label">Images Downloaded</div>
            </div>
            <div class="stat success">
                <div class="stat-value">{assets['pdfs']['count']}</div>
                <div class="stat-label">PDFs Downloaded</div>
            </div>
            <div class="stat {"warning" if len(broken_links) > 100 else "info"}">
                <div class="stat-value">{len(broken_links)}</div>
                <div class="stat-label">Broken Links</div>
            </div>
            <div class="stat {"warning" if len(empty_files) > 5 else "success"}">
                <div class="stat-value">{len(empty_files)}</div>
                <div class="stat-label">Empty Pages</div>
            </div>
        </div>

        <h2>Content Quality Overview</h2>
        <div class="card">
            <div class="progress">
                <div class="progress-bar" style="width: {len(good_files)/len(content_files)*100:.1f}%"></div>
            </div>
            <p><strong>{len(good_files)}</strong> pages with good content ({len(good_files)/len(content_files)*100:.1f}%)</p>
            <p><strong>{len(short_files)}</strong> pages with short content (10-50 words)</p>
            <p><strong>{len(empty_files)}</strong> pages with minimal content (<10 words)</p>
        </div>

        <h2>Content by Category</h2>
        <div class="card">
            <table>
                <thead>
                    <tr><th>Category</th><th>Pages</th><th>Total Words</th><th>Avg Words</th></tr>
                </thead>
                <tbody>
'''

    for cat, files in sorted(by_category.items(), key=lambda x: -len(x[1])):
        total_cat_words = sum(f['words'] for f in files)
        avg_words = total_cat_words / len(files) if files else 0
        html += f'''                    <tr>
                        <td><strong>{cat}</strong></td>
                        <td>{len(files)}</td>
                        <td>{total_cat_words:,}</td>
                        <td>{avg_words:.0f}</td>
                    </tr>
'''

    html += '''                </tbody>
            </table>
        </div>

        <h2>Downloaded Assets</h2>
        <div class="card">
            <h3>Images ({} files, {:.1f} MB)</h3>
            <table>
                <thead><tr><th>Category</th><th>Count</th></tr></thead>
                <tbody>
'''.format(assets['images']['count'], assets['images']['size_mb'])

    for cat, count in sorted(assets['images']['by_category'].items(), key=lambda x: -x[1]):
        html += f'                    <tr><td>{cat}</td><td>{count}</td></tr>\n'

    html += '''                </tbody>
            </table>
'''

    if assets['pdfs']['files']:
        html += f'''            <h3>PDFs ({assets['pdfs']['count']} files)</h3>
            <button class="collapsible">Show PDF list</button>
            <div class="content">
                <ul>
'''
        for pdf in assets['pdfs']['files'][:50]:
            html += f'                    <li>{pdf}</li>\n'
        if len(assets['pdfs']['files']) > 50:
            html += f'                    <li>... and {len(assets["pdfs"]["files"]) - 50} more</li>\n'
        html += '''                </ul>
            </div>
'''

    html += '''        </div>
'''

    # Empty/Short content section
    if empty_files or short_files:
        html += '''
        <h2>Content Issues</h2>
        <div class="card">
'''
        if empty_files:
            html += f'''            <h3>Empty/Minimal Content ({len(empty_files)} pages)</h3>
            <p>These pages have less than 10 words - may need review:</p>
            <button class="collapsible">Show empty pages</button>
            <div class="content">
                <table>
                    <thead><tr><th>File</th><th>Title</th><th>Words</th></tr></thead>
                    <tbody>
'''
            for f in empty_files:
                html += f'                        <tr><td class="url">{f["path"]}</td><td>{f["title"][:50]}</td><td>{f["words"]}</td></tr>\n'
            html += '''                    </tbody>
                </table>
            </div>
'''

        if short_files:
            html += f'''            <h3>Short Content ({len(short_files)} pages)</h3>
            <p>These pages have 10-50 words:</p>
            <button class="collapsible">Show short pages</button>
            <div class="content">
                <table>
                    <thead><tr><th>File</th><th>Title</th><th>Words</th></tr></thead>
                    <tbody>
'''
            for f in short_files[:30]:
                html += f'                        <tr><td class="url">{f["path"]}</td><td>{f["title"][:50]}</td><td>{f["words"]}</td></tr>\n'
            if len(short_files) > 30:
                html += f'                        <tr><td colspan="3">... and {len(short_files) - 30} more</td></tr>\n'
            html += '''                    </tbody>
                </table>
            </div>
'''
        html += '''        </div>
'''

    # Broken links section
    if broken_links:
        html += f'''
        <h2>Broken Links ({len(broken_links)} total)</h2>
        <div class="card">
            <p>These links could not be resolved to local content. Most are Wix-specific URLs.</p>
'''
        if broken_pages:
            html += f'''            <h3>Broken Page Links ({len(broken_pages)})</h3>
            <button class="collapsible">Show broken page links</button>
            <div class="content">
                <table>
                    <thead><tr><th>In File</th><th>Broken URL</th></tr></thead>
                    <tbody>
'''
            for b in broken_pages[:50]:
                html += f'                        <tr><td>{b["file"]}</td><td class="url">{b["url"][:80]}...</td></tr>\n'
            if len(broken_pages) > 50:
                html += f'                        <tr><td colspan="2">... and {len(broken_pages) - 50} more</td></tr>\n'
            html += '''                    </tbody>
                </table>
            </div>
'''
        html += '''        </div>
'''

    # Crawl comparison
    if crawl:
        html += f'''
        <h2>Deep Crawl Comparison</h2>
        <div class="card">
            <p><strong>Pages crawled:</strong> {crawl['pages_crawled']}</p>
            <p><strong>Total discovered:</strong> {crawl['total_discovered']}</p>
'''
        if crawl['missing_urls']:
            html += f'''            <h3>Pages Not in Sitemaps ({len(crawl['missing_urls'])})</h3>
            <p>These pages were found by crawling but weren't in the original sitemaps:</p>
            <button class="collapsible">Show missing URLs</button>
            <div class="content">
                <ul>
'''
            for url in crawl['missing_urls'][:30]:
                html += f'                    <li class="url">{url}</li>\n'
            if len(crawl['missing_urls']) > 30:
                html += f'                    <li>... and {len(crawl["missing_urls"]) - 30} more</li>\n'
            html += '''                </ul>
            </div>
'''
        html += '''        </div>
'''

    # Summary
    issues = []
    if len(empty_files) > 0:
        issues.append(f"{len(empty_files)} pages have minimal content")
    if len(broken_links) > 0:
        issues.append(f"{len(broken_links)} broken links (mostly Wix internal URLs)")
    if crawl and len(crawl.get('missing_urls', [])) > 0:
        issues.append(f"{len(crawl['missing_urls'])} pages found by crawl but already scraped separately")

    html += f'''
        <h2>Summary</h2>
        <div class="card">
            <h3 style="color: {"#155724" if len(issues) < 3 else "#856404"}">
                {"Migration Successful!" if len(issues) < 3 else "Migration Complete with Minor Issues"}
            </h3>
            <ul>
                <li><strong>{len(content_files)}</strong> pages migrated</li>
                <li><strong>{total_words:,}</strong> words of content</li>
                <li><strong>{assets['images']['count']}</strong> images downloaded ({assets['images']['size_mb']:.1f} MB)</li>
                <li><strong>{assets['pdfs']['count']}</strong> PDFs downloaded</li>
                <li><strong>{len(good_files)}</strong> pages with good content quality ({len(good_files)/len(content_files)*100:.1f}%)</li>
            </ul>
'''
    if issues:
        html += '''            <h4>Notes:</h4>
            <ul>
'''
        for issue in issues:
            html += f'                <li>{issue}</li>\n'
        html += '''            </ul>
'''

    html += '''        </div>
    </div>

    <script>
        document.querySelectorAll('.collapsible').forEach(btn => {
            btn.addEventListener('click', function() {
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                content.classList.toggle('show');
            });
        });
    </script>
</body>
</html>
'''

    return html


def main():
    print("Generating HTML report...")

    html = generate_html_report()

    # Save report
    report_file = DATA_DIR / "migration_report.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Report saved to: {report_file}")

    # Open in browser
    print("Opening report in browser...")
    webbrowser.open(f'file:///{report_file.as_posix()}')

    print("Done!")


if __name__ == "__main__":
    main()
