"""
21_fetch_eu_data.py
Fetches official EU CORDIS data for the Digital Finance project.
Downloads project info, participants, and publications from EU sources.

Usage:
    python scripts/21_fetch_eu_data.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CONTENT_DIR = PROJECT_ROOT / "content"

PROJECT_ID = "101119635"
CORDIS_BASE = "https://cordis.europa.eu/project/id"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def fetch_cordis_page(url):
    """Fetch a CORDIS page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None


def parse_project_info(html):
    """Parse basic project information."""
    soup = BeautifulSoup(html, 'html.parser')

    info = {
        'title': '',
        'acronym': '',
        'eu_contribution': '',
        'start_date': '',
        'end_date': '',
        'coordinator': '',
        'objective': ''
    }

    # Extract title
    title_elem = soup.select_one('h1')
    if title_elem:
        info['title'] = title_elem.get_text(strip=True)

    # Extract from definition lists
    for dt in soup.find_all('dt'):
        term = dt.get_text(strip=True).lower()
        dd = dt.find_next_sibling('dd')
        if dd:
            value = dd.get_text(strip=True)
            if 'contribution' in term:
                info['eu_contribution'] = value
            elif 'start date' in term:
                info['start_date'] = value
            elif 'end date' in term:
                info['end_date'] = value
            elif 'coordinator' in term:
                info['coordinator'] = value

    # Extract objective
    objective_section = soup.find(string=lambda t: t and 'objective' in t.lower())
    if objective_section:
        parent = objective_section.find_parent()
        if parent:
            next_p = parent.find_next('p')
            if next_p:
                info['objective'] = next_p.get_text(strip=True)[:500]

    return info


def parse_participants(html):
    """Parse participant information."""
    soup = BeautifulSoup(html, 'html.parser')
    participants = []

    # Look for participant tables or lists
    for table in soup.find_all('table'):
        for row in table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                participants.append({
                    'name': cells[0].get_text(strip=True),
                    'country': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                    'contribution': cells[2].get_text(strip=True) if len(cells) > 2 else ''
                })

    return participants


def fetch_all_eu_data():
    """Fetch all EU data for the project."""
    print("=" * 60)
    print("FETCHING EU CORDIS DATA")
    print("=" * 60)
    print(f"Project ID: {PROJECT_ID}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {
        'project_id': PROJECT_ID,
        'fetch_date': datetime.now().isoformat(),
        'sources': [],
        'data': {}
    }

    # Fetch main project page
    print("[1/3] Fetching main project page...")
    main_url = f"{CORDIS_BASE}/{PROJECT_ID}"
    main_html = fetch_cordis_page(main_url)
    if main_html:
        results['data']['project_info'] = parse_project_info(main_html)
        results['sources'].append(main_url)
        print("  OK")
    else:
        print("  FAILED")

    # Fetch participants page
    print("[2/3] Fetching participants page...")
    participants_url = f"{CORDIS_BASE}/{PROJECT_ID}/en"
    participants_html = fetch_cordis_page(participants_url)
    if participants_html:
        results['data']['participants'] = parse_participants(participants_html)
        results['sources'].append(participants_url)
        print("  OK")
    else:
        print("  FAILED")

    # Fetch results page
    print("[3/3] Fetching results page...")
    results_url = f"{CORDIS_BASE}/{PROJECT_ID}/results"
    results_html = fetch_cordis_page(results_url)
    if results_html:
        soup = BeautifulSoup(results_html, 'html.parser')
        # Count publications
        pub_count = len(soup.find_all('article'))
        results['data']['publications_count'] = pub_count
        results['sources'].append(results_url)
        print(f"  OK ({pub_count} items found)")
    else:
        print("  FAILED")

    return results


def save_results(results):
    """Save fetched data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save JSON
    output_file = DATA_DIR / "eu_cordis_latest.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {output_file}")

    # Save history
    history_file = DATA_DIR / f"eu_cordis_{datetime.now().strftime('%Y%m%d')}.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"History saved to: {history_file}")

    return output_file


def main():
    results = fetch_all_eu_data()
    save_results(results)

    print("\n" + "=" * 60)
    print("EU DATA FETCH COMPLETE")
    print("=" * 60)

    if results['data'].get('project_info'):
        info = results['data']['project_info']
        print(f"  Title: {info.get('title', 'N/A')[:50]}")
        print(f"  EU Contribution: {info.get('eu_contribution', 'N/A')}")
        print(f"  Coordinator: {info.get('coordinator', 'N/A')}")

    print(f"  Sources fetched: {len(results['sources'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
