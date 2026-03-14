#!/usr/bin/env python3
"""
Dashboard Generator

Generates the ontology-dashboard.html from the current ontology state.
Called automatically after article processing to keep dashboard up-to-date.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

RESEARCH_DIR = Path('/root/.openclaw/workspace')
ONTOLOGY_FILE = RESEARCH_DIR / 'memory' / 'ontology' / 'graph.jsonl'
DASHBOARD_FILE = RESEARCH_DIR / 'ontology-dashboard.html'
ARTICLES_DB = RESEARCH_DIR / 'research' / 'articles.db'


def load_ontology():
    """Load all entities from ontology."""
    entries = []
    if ONTOLOGY_FILE.exists():
        with open(ONTOLOGY_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    return entries


def get_article_stats():
    """Get statistics from articles database."""
    conn = sqlite3.connect(ARTICLES_DB)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM articles')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE content_status = "labeled"')
    labeled = cursor.fetchone()[0]
    
    cursor.execute('SELECT category, COUNT(*) FROM articles GROUP BY category')
    categories = cursor.fetchall()
    
    cursor.execute('SELECT domain, COUNT(*) FROM articles GROUP BY domain ORDER BY COUNT(*) DESC LIMIT 10')
    top_sources = cursor.fetchall()
    
    conn.close()
    return {
        'total': total,
        'labeled': labeled,
        'categories': categories,
        'top_sources': top_sources
    }


def generate_graph_data(entries):
    """Generate D3.js graph data from ontology entries."""
    nodes = []
    links = []
    
    for entry in entries:
        if entry.get('op') == 'create' and 'entity' in entry:
            entity = entry['entity']
            node = {
                'id': entity['id'],
                'name': entity['properties'].get('name', entity['id']),
                'type': entity['type'],
                'group': 1 if entity['type'] == 'Concept' else 2 if entity['type'] == 'ResearchTask' else 3,
                'size': 30 if entity['type'] == 'Concept' else 22 if entity['type'] == 'ResearchTask' else 15
            }
            nodes.append(node)
        elif entry.get('op') == 'relate':
            link = {
                'source': entry['from'],
                'target': entry['to'],
                'type': entry.get('rel', 'related')
            }
            links.append(link)
    
    return {'nodes': nodes, 'links': links}


def update_dashboard():
    """Update the dashboard HTML with current data."""
    print("🔄 Updating dashboard...")
    
    # Load data
    entries = load_ontology()
    stats = get_article_stats()
    graph_data = generate_graph_data(entries)
    
    # Count entities
    concepts = [e for e in entries if e.get('entity', {}).get('type') == 'Concept']
    tasks = [e for e in entries if e.get('entity', {}).get('type') == 'ResearchTask']
    articles = [e for e in entries if e.get('entity', {}).get('type') == 'Article']
    
    # Read current dashboard
    with open(DASHBOARD_FILE, 'r') as f:
        html = f.read()
    
    # Update statistics
    html = html.replace(
        '<div class="number">1,104</div>',
        f'<div class="number">{stats["total"]:,}</div>'
    )
    
    html = html.replace(
        '<div class="number">12</div>',
        f'<div class="number">{len(concepts)}</div>'
    )
    
    html = html.replace(
        '<div class="number">7</div>',
        f'<div class="number">{len(tasks)}</div>'
    )
    
    # Update timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    html = html.replace(
        'Stand: 14. März 2026',
        f'Stand: {timestamp}'
    )
    
    # Write back
    with open(DASHBOARD_FILE, 'w') as f:
        f.write(html)
    
    print(f"✅ Dashboard updated:")
    print(f"   - {stats['total']} articles")
    print(f"   - {len(concepts)} concepts")
    print(f"   - {len(tasks)} tasks")
    print(f"   - {len(graph_data['links'])} relations")


if __name__ == '__main__':
    update_dashboard()
