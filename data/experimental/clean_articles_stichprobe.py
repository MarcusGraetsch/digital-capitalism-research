#!/usr/bin/env python3
"""
⚠️  DEPRECATED - Dieses Script wird nicht mehr verwendet!

Article Cleaner - Stichprobe
Cleans scraped articles by removing navigation/paywall noise
Uses LLM to detect if article has real content or just paywall

STATUS: Experimental / Archiviert
GRUND: Zu langsam, LLM-Rate-Limits, unzuverlässig
ERSATZ: ../clean_smart.py (Heuristiken statt LLM)

Dieses Script bleibt als Referenz im Git, wird aber nicht ausgeführt.
Für Produktion verwende clean_smart.py
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# OpenClaw session tool to call LLM
import subprocess

RESEARCH_DIR = Path('/root/.openclaw/workspace/research')
DB_FILE = RESEARCH_DIR / 'articles.db'
FULLTEXT_DIR = RESEARCH_DIR / 'fulltext'

def get_sample_articles(limit=25):
    """Get sample of articles with paywall=1 and status=saved"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, url, domain, title, fulltext_path, word_count, category
        FROM articles
        WHERE paywall = 1 AND content_status = 'saved'
        ORDER BY RANDOM()
        LIMIT ?
    ''', (limit,))
    return cursor.fetchall()

def read_article(fulltext_path):
    """Read article content from file"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def clean_with_llm(title, content):
    """Use LLM to clean article and detect if it's paywall-only"""
    
    # Extract just the content after the metadata header
    lines = content.split('\n')
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            content_start = i + 1
            break
    
    article_text = '\n'.join(lines[content_start:]).strip()
    
    # Limit text length for API
    article_text = article_text[:6000]
    
    prompt = f"""Analyze this scraped article. Extract ONLY the actual article content (headline + body text). Remove navigation, ads, share buttons, related links, and paywall prompts.

TITLE: {title}

CONTENT:
{article_text}

Respond in JSON format:
{{
    "has_real_content": true/false,
    "cleaned_text": "the cleaned article text (empty if only paywall)",
    "removed_elements": ["list of what was removed"],
    "quality_score": 1-10,
    "reasoning": "brief explanation"
}}

has_real_content=false if the text contains ONLY: paywall messages, login prompts, navigation menus, "subscribe now", "login to read", cookie banners, or empty placeholder text.
has_real_content=true if there's actual article paragraphs with information."""

    # Write prompt to file for manual processing or external LLM
    prompt_file = RESEARCH_DIR / 'cleaning_prompts' / f'prompt_{hash(title) % 10000}.txt'
    prompt_file.parent.mkdir(exist_ok=True)
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    # For now, return placeholder - actual LLM processing would be done via sessions_spawn
    return {
        "has_real_content": None,  # Needs LLM
        "prompt_file": str(prompt_file),
        "original_text": article_text[:2000]
    }

def update_database(article_id, has_content, cleaned_text=None):
    """Update database entry"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if not has_content:
        # Only paywall - mark as such
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'paywall_only', 
                abstract = 'Paywall - no content extracted',
                word_count = 0
            WHERE id = ?
        ''', (article_id,))
    else:
        # Has content - update abstract with cleaned version
        abstract = cleaned_text[:500] + '...' if len(cleaned_text) > 500 else cleaned_text
        word_count = len(cleaned_text.split())
        cursor.execute('''
            UPDATE articles 
            SET abstract = ?,
                word_count = ?,
                content_status = 'cleaned'
            WHERE id = ?
        ''', (abstract, word_count, article_id))
    
    conn.commit()
    conn.close()

def delete_md_file(fulltext_path):
    """Delete the markdown file"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    if file_path.exists():
        file_path.unlink()
        return True
    return False

def save_cleaned_version(fulltext_path, cleaned_text, original_content):
    """Save cleaned version back to file"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    # Extract metadata from original
    lines = original_content.split('\n')
    metadata_end = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            metadata_end = i + 1
            break
    
    metadata = '\n'.join(lines[:metadata_end])
    
    # Add cleaning notice to metadata
    metadata = metadata.rstrip()
    if metadata.endswith('---'):
        metadata = metadata[:-3].rstrip()
    metadata += f"\ncleaned_at: {datetime.now().isoformat()}"
    metadata += "\ncleaned_by: llm"
    metadata += "\n---"
    
    # Write cleaned version
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(metadata + '\n\n' + cleaned_text)
    
    return True

def main():
    print("="*60)
    print("Article Cleaner - Stichprobe")
    print("="*60)
    
    # Get sample
    print("\n📋 Selecting 25 random paywall articles...")
    samples = get_sample_articles(25)
    print(f"✅ Selected {len(samples)} articles\n")
    
    results = {
        'paywall_only': 0,
        'cleaned': 0,
        'errors': 0,
        'details': []
    }
    
    for idx, (article_id, url, domain, title, fulltext_path, word_count, category) in enumerate(samples, 1):
        print(f"\n[{idx}/25] Processing: {title[:60]}...")
        print(f"       Domain: {domain}")
        
        # Read original
        content = read_article(fulltext_path)
        if not content:
            print("       ❌ File not found")
            results['errors'] += 1
            continue
        
        # Clean with LLM
        print("       🤖 LLM analyzing...")
        result = clean_with_llm(title, content)
        
        if not result['has_real_content']:
            # Paywall only - delete and update
            print(f"       🗑️  Paywall only - deleting file")
            deleted = delete_md_file(fulltext_path)
            update_database(article_id, False)
            results['paywall_only'] += 1
            results['details'].append({
                'id': article_id,
                'domain': domain,
                'action': 'deleted',
                'reason': result['reasoning']
            })
        else:
            # Has content - save cleaned version
            print(f"       ✅ Real content found (score: {result['quality_score']}/10)")
            save_cleaned_version(fulltext_path, result['cleaned_text'], content)
            update_database(article_id, True, result['cleaned_text'])
            results['cleaned'] += 1
            results['details'].append({
                'id': article_id,
                'domain': domain,
                'action': 'cleaned',
                'quality': result['quality_score'],
                'removed': result['removed_elements']
            })
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Paywall only (deleted): {results['paywall_only']}")
    print(f"Cleaned and saved:      {results['cleaned']}")
    print(f"Errors:                 {results['errors']}")
    print("\nDetails:")
    for detail in results['details']:
        print(f"  - {detail['domain']}: {detail['action']}")
    
    # Save report
    report_file = RESEARCH_DIR / f'cleaning_report_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Report saved: {report_file}")

if __name__ == '__main__':
    main()
