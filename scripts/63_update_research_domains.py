"""
Update Research Domain Content
===============================
The Research Domains page is nearly empty. This script enhances the content
for WP1-WP5 research domain pages based on existing content structure.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content"

# Research domain content (extracted from existing WP1 and enhanced)
RESEARCH_DOMAINS = {
    "wp1-financial-data-space": {
        "title": "Towards a European financial data space",
        # Already has good content
    },
    "wp2-ai-financial-markets": {
        "title": "AI for Financial Markets",
        "overview": """Work Package 2 focuses on developing advanced AI methodologies for financial market analysis and prediction. This research stream explores cutting-edge machine learning and deep learning techniques to understand market dynamics, predict trends, and support decision-making in complex financial environments.

The work package addresses critical challenges in applying AI to financial markets, including handling high-frequency data, managing non-stationary patterns, and developing models that are both accurate and interpretable. Research topics span from agent-based modeling to advanced neural network architectures specifically designed for financial time series.""",
        "description": "Under this research stream, doctoral candidates explore innovative AI applications in financial markets, covering topics from high-frequency trading to market microstructure analysis, reinforcement learning for portfolio optimization, and explainable AI for financial decision support."
    },
    "wp3-explainable-fair-ai": {
        "title": "Explainable and Fair AI",
        "overview": """Work Package 3 tackles the critical challenge of making AI systems in finance both transparent and fair. As AI increasingly influences financial decisions affecting millions of people, ensuring these systems are explainable and free from bias becomes paramount.

This research stream develops methodologies for interpreting complex AI models, detecting and mitigating algorithmic bias, and creating frameworks for fair AI in financial contexts. The work balances the need for model accuracy with the requirements for transparency, accountability, and fairness that are essential in regulated financial environments.""",
        "description": "Doctoral candidates in this work package investigate explainable AI techniques for finance, fairness-aware machine learning, algorithmic bias detection, and develop tools for making black-box models interpretable to regulators, practitioners, and affected individuals."
    },
    "wp4-digital-innovation-blockchain": {
        "title": "Digital Innovation and Blockchain",
        "overview": """Work Package 4 explores the transformative potential of blockchain and distributed ledger technologies in financial services. This research stream investigates how these technologies can create more efficient, transparent, and secure financial systems while addressing challenges of scalability, privacy, and regulatory compliance.

The work package covers a broad spectrum of topics including smart contract development, decentralized finance (DeFi) protocols, tokenization of assets, consensus mechanisms, and the integration of blockchain with traditional financial infrastructure. Research emphasizes both theoretical foundations and practical implementations.""",
        "description": "Under this research stream, doctoral candidates examine blockchain applications in finance, from cryptocurrency market analysis to enterprise blockchain solutions, smart contract security, decentralized autonomous organizations (DAOs), and the regulatory implications of distributed financial systems."
    },
    "wp5-sustainability-digital-finance": {
        "title": "Sustainability and Digital Finance",
        "overview": """Work Package 5 addresses the critical intersection of digital finance and environmental sustainability. As financial institutions increasingly focus on ESG (Environmental, Social, Governance) factors, this research stream develops AI-driven approaches to measure, predict, and optimize sustainability outcomes in financial decision-making.

The work package investigates how digital technologies can accelerate the transition to a sustainable economy, including green credit scoring, climate risk modeling, sustainable investment strategies, and the environmental impact of digital financial technologies themselves. Research combines machine learning, network analysis, and sustainability science.""",
        "description": "Doctoral candidates in this work package develop innovative approaches to green finance, including AI models for ESG rating prediction, climate risk assessment, sustainable portfolio optimization, carbon footprint analysis of digital currencies, and frameworks for evaluating the environmental impact of fintech innovations."
    }
}

def update_wp_content(wp_key, wp_data):
    """Update a work package content file."""
    wp_file = CONTENT_DIR / f"{wp_key}.md"

    if not wp_file.exists():
        print(f"File not found: {wp_file}")
        return False

    with open(wp_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if it already has substantial content
    if len(content) > 2000:
        print(f"{wp_key}: Already has substantial content, skipping")
        return False

    # Only update if we have overview text
    if "overview" not in wp_data:
        print(f"{wp_key}: Using existing content")
        return False

    # Split front matter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"{wp_key}: Invalid format, skipping")
        return False

    front_matter = parts[1]
    body = parts[2]

    # Check if already has overview section
    if "## Overview" in body and len(body) > 500:
        print(f"{wp_key}: Already has overview, skipping")
        return False

    # Build enhanced content
    new_body = f"""
## Overview

{wp_data['overview']}

{wp_data['description']}

## Research Topics

Details about specific research topics and doctoral candidates working in this area will be added as the projects progress.

## Team

Information about the WP{wp_key[2]} team members and their roles.

## News and Updates

Latest developments and achievements from this work package.
"""

    # Write back
    new_content = f"---{front_matter}---{new_body}"
    with open(wp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"{wp_key}: Content updated successfully")
    return True

def update_all_research_domains():
    """Update all research domain pages."""
    updated_count = 0

    for wp_key, wp_data in RESEARCH_DOMAINS.items():
        if update_wp_content(wp_key, wp_data):
            updated_count += 1

    print(f"\nUpdated {updated_count} research domain pages")

if __name__ == "__main__":
    print("Updating Research Domain Content...")
    print("=" * 60)
    update_all_research_domains()
    print("=" * 60)
    print("Research domain content updated successfully!")
