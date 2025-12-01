# MSCA Digital Finance Website

This repository contains the Hugo static site for the MSCA Digital Finance Industrial Doctoral Network, migrated from the original Wix website at [digital-finance-msca.com](https://www.digital-finance-msca.com/).

## About MSCA Digital Finance

The Industrial Doctoral Network in Digital Finance (DIGITAL) is an EU-funded Marie Sklodowska-Curie Action (Grant Agreement No. 101119635) that brings together:

- 8 leading European universities
- 3 major international corporations (Swedbank, Raiffeisen Bank, Deutsche Bank)
- 3 SMEs
- 3 research centres (Athena, EIT Digital, Fraunhofer)
- 2 intergovernmental agencies (European Central Bank, Bank for International Settlements)

The network trains 17 PhD researchers in digital finance, focusing on AI, machine learning, and data science applications in the financial sector.

## Project Structure

```
msca-digital-finance/
├── content/                 # Hugo content (markdown files)
│   ├── _index.md           # Homepage
│   ├── people/             # Team member profiles
│   ├── partners/           # Partner organizations
│   ├── blog/               # News and blog posts
│   ├── training-modules/   # Training module descriptions
│   ├── training-events/    # Training event information
│   └── events/             # Event registrations
├── static/
│   ├── css/                # Stylesheets
│   └── images/             # Downloaded images
├── layouts/                # Hugo templates
├── scripts/                # Migration scripts
├── data/                   # Scraped data and URLs
└── .github/workflows/      # GitHub Actions for deployment
```

## Development

### Prerequisites

- [Hugo](https://gohugo.io/installation/) (extended version recommended)
- Python 3.8+ (for migration scripts)

### Local Development

```bash
# Clone the repository
git clone https://github.com/Digital-AI-Finance/msca-digital-finance.git
cd msca-digital-finance

# Start Hugo development server
hugo server -D

# Build for production
hugo --minify
```

### Migration Scripts

The `scripts/` directory contains Python scripts used to migrate content from the original Wix site:

1. `01_discover_urls.py` - Discovers all URLs from sitemaps
2. `02_scrape_content.py` - Scrapes content using Playwright
3. `03_download_images.py` - Downloads all images locally
4. `04_setup_hugo.py` - Sets up Hugo configuration and templates
5. `05_verify.py` - Verifies migration completeness

To run the migration scripts:

```bash
cd scripts
pip install -r requirements.txt
playwright install chromium

python 01_discover_urls.py
python 02_scrape_content.py
python 03_download_images.py
python 04_setup_hugo.py
python 05_verify.py
```

## Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to the `main` branch via GitHub Actions.

**Live Site:** [https://digital-ai-finance.github.io/msca-digital-finance/](https://digital-ai-finance.github.io/msca-digital-finance/)

## License

Content copyright MSCA Digital Finance Consortium. Website template and migration scripts available under MIT License.

## Contact

For questions about the MSCA Digital Finance project, please visit [Contact Us](https://digital-ai-finance.github.io/msca-digital-finance/contact-us/).

---

*This site was migrated from Wix using automated Python scripts and is hosted on GitHub Pages using Hugo.*
