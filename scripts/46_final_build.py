"""
46_final_build.py
Final build and test of Hugo site.
- Run hugo build with verbose output
- Check for build errors
- Generate site statistics
- Open in browser for verification

Usage:
    python scripts/46_final_build.py
    python scripts/46_final_build.py --serve   # Start dev server
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import json
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
import shutil

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
PUBLIC_DIR = PROJECT_ROOT / "public"
CONTENT_DIR = PROJECT_ROOT / "content"
STATIC_DIR = PROJECT_ROOT / "static"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_FILE = PROJECT_ROOT / "hugo.toml"


def check_hugo_installed():
    """Check if Hugo is installed."""
    try:
        result = subprocess.run(['hugo', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  Hugo version: {version}")
            return True
    except FileNotFoundError:
        pass

    print("  ERROR: Hugo is not installed or not in PATH")
    print("  Install from: https://gohugo.io/installation/")
    return False


def update_config_for_custom_theme():
    """Update hugo.toml to use the custom theme."""
    print("  Updating config for custom theme...")

    if CONFIG_FILE.exists():
        content = CONFIG_FILE.read_text(encoding='utf-8', errors='replace')

        # Update theme setting
        if 'theme =' in content:
            content = re.sub(r'theme\s*=\s*["\'][^"\']+["\']', 'theme = "msca-digital-finance"', content)
        else:
            # Add theme setting after baseURL
            if 'baseURL' in content:
                content = content.replace('baseURL', 'theme = "msca-digital-finance"\nbaseURL', 1)

        CONFIG_FILE.write_text(content, encoding='utf-8')
        print("    Set theme to 'msca-digital-finance'")

    return True


def clean_public_dir():
    """Clean the public directory."""
    if PUBLIC_DIR.exists():
        print("  Cleaning public directory...")
        shutil.rmtree(PUBLIC_DIR)
        print("    Removed old public/")


def run_hugo_build():
    """Run Hugo build."""
    print("  Running Hugo build...")

    # Change to project directory
    os.chdir(PROJECT_ROOT)

    try:
        result = subprocess.run(
            ['hugo', '--minify', '--gc'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Print output
        if result.stdout:
            for line in result.stdout.strip().split('\n')[:20]:
                print(f"    {line}")

        if result.returncode == 0:
            print("  Build successful!")
            return True, result.stdout
        else:
            print("  Build failed!")
            if result.stderr:
                for line in result.stderr.strip().split('\n')[:20]:
                    print(f"    ERROR: {line}")
            return False, result.stderr

    except Exception as e:
        print(f"  Build error: {e}")
        return False, str(e)


def count_generated_pages():
    """Count pages in the generated site."""
    if not PUBLIC_DIR.exists():
        return 0

    html_files = list(PUBLIC_DIR.rglob("*.html"))
    return len(html_files)


def get_site_size():
    """Calculate total site size."""
    if not PUBLIC_DIR.exists():
        return 0

    total_size = 0
    for f in PUBLIC_DIR.rglob("*"):
        if f.is_file():
            total_size += f.stat().st_size

    return total_size


def count_assets():
    """Count assets in generated site."""
    if not PUBLIC_DIR.exists():
        return {}

    counts = {
        'html': 0,
        'css': 0,
        'js': 0,
        'images': 0,
        'other': 0
    }

    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}

    for f in PUBLIC_DIR.rglob("*"):
        if f.is_file():
            ext = f.suffix.lower()
            if ext == '.html':
                counts['html'] += 1
            elif ext == '.css':
                counts['css'] += 1
            elif ext == '.js':
                counts['js'] += 1
            elif ext in image_exts:
                counts['images'] += 1
            else:
                counts['other'] += 1

    return counts


def start_dev_server():
    """Start Hugo development server."""
    print("\n  Starting Hugo development server...")
    print("  Press Ctrl+C to stop")
    print()

    os.chdir(PROJECT_ROOT)

    try:
        # Open browser after short delay
        import threading
        def open_browser():
            import time
            time.sleep(2)
            webbrowser.open('http://localhost:1313')

        threading.Thread(target=open_browser, daemon=True).start()

        # Start server (blocking)
        subprocess.run(['hugo', 'server', '-D', '--navigateToChanged'])

    except KeyboardInterrupt:
        print("\n  Server stopped.")
    except Exception as e:
        print(f"  Server error: {e}")


def run_final_build():
    """Run the final build process."""
    print("=" * 60)
    print("FINAL BUILD")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        'date': datetime.now().isoformat(),
        'hugo_installed': False,
        'build_success': False,
        'build_output': '',
        'pages_generated': 0,
        'site_size_mb': 0,
        'asset_counts': {},
        'errors': []
    }

    # 1. Check Hugo
    print("[1/4] Checking Hugo installation...")
    results['hugo_installed'] = check_hugo_installed()
    if not results['hugo_installed']:
        results['errors'].append("Hugo not installed")
        return results

    # 2. Update config
    print("\n[2/4] Updating configuration...")
    import re  # Import here for update_config
    update_config_for_custom_theme()

    # 3. Clean and build
    print("\n[3/4] Building site...")
    clean_public_dir()
    success, output = run_hugo_build()
    results['build_success'] = success
    results['build_output'] = output[:2000] if output else ''

    if not success:
        results['errors'].append("Build failed")
        return results

    # 4. Generate statistics
    print("\n[4/4] Generating statistics...")
    results['pages_generated'] = count_generated_pages()
    results['site_size_mb'] = round(get_site_size() / (1024 * 1024), 2)
    results['asset_counts'] = count_assets()

    print(f"  Pages generated: {results['pages_generated']}")
    print(f"  Site size: {results['site_size_mb']} MB")
    print(f"  Assets: {results['asset_counts']}")

    return results


def save_report(results):
    """Save build report."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DATA_DIR / "final_build_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {output_file}")

    return output_file


def main():
    serve_mode = '--serve' in sys.argv or '-s' in sys.argv

    if serve_mode:
        # Just start the server
        check_hugo_installed()
        start_dev_server()
    else:
        # Full build
        results = run_final_build()
        save_report(results)

        print("\n" + "=" * 60)
        print("BUILD SUMMARY")
        print("=" * 60)
        print(f"  Hugo installed: {results['hugo_installed']}")
        print(f"  Build success: {results['build_success']}")
        print(f"  Pages generated: {results['pages_generated']}")
        print(f"  Site size: {results['site_size_mb']} MB")

        if results['asset_counts']:
            print(f"  HTML files: {results['asset_counts'].get('html', 0)}")
            print(f"  CSS files: {results['asset_counts'].get('css', 0)}")
            print(f"  JS files: {results['asset_counts'].get('js', 0)}")
            print(f"  Images: {results['asset_counts'].get('images', 0)}")

        if results['errors']:
            print("\n  ERRORS:")
            for error in results['errors']:
                print(f"    - {error}")
        else:
            print("\n  Build completed successfully!")
            print(f"  Output directory: {PUBLIC_DIR}")

            # Offer to start server
            print("\n  To preview the site, run:")
            print("    python scripts/46_final_build.py --serve")

        print("=" * 60)


if __name__ == "__main__":
    import re  # Need this for regex in update_config
    main()
