#!/usr/bin/env python3
"""
Article Cleaner - Smart Heuristics + Manual Queue
Identifies obvious paywall junk, queues rest for LLM cleaning
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

RESEARCH_DIR = Path('/root/.openclaw/workspace/research')
DB_FILE = RESEARCH_DIR / 'articles.db'
FULLTEXT_DIR = RESEARCH_DIR / 'fulltext'

def get_all_articles():
    """Get all uncleaned articles"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, url, domain, title, fulltext_path, word_count, category
        FROM articles
        WHERE content_status = 'saved'
        ORDER BY word_count ASC
    ''')
    
    return [dict(row) for row in cursor.fetchall()]

def read_article_content(fulltext_path):
    """Read article content"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_text_only(md_content):
    """Extract text without frontmatter"""
    lines = md_content.split('\n')
    in_content = False
    content_lines = []
    
    for line in lines:
        if line.strip() == '---' and not in_content:
            in_content = True
            continue
        if in_content:
            if line.startswith('**URL:**') or line.startswith('**Domain:**'):
                continue
            if line.startswith('**Category:**') or line.startswith('**Scanned:**'):
                continue
            if line.startswith('**Word Count:**'):
                continue
            content_lines.append(line)
    
    return '\n'.join(content_lines).strip()

def analyze_article(article):
    """Analyze article content"""
    content = read_article_content(article['fulltext_path'])
    if not content:
        return {'action': 'error', 'reason': 'File not found'}
    
    text = extract_text_only(content)
    text_lower = text.lower()
    
    # Paywall indicators
    paywall_words = [
        'abonnieren', 'abo', 'jetzt anmelden', 'anmelden', 'login', 'registrieren',
        'weiterlesen mit', 'premium', 'paywall', 'bitte melden sie sich an',
        'zugang zu allen artikeln', 'kostenlos testen', 'abonnement',
        'subscribe now', 'sign in', 'register', 'subscription', 'premium access',
        'login to read', 'create account', 'member exclusive'
    ]
    
    # Count paywall indicators
    paywall_count = sum(1 for word in paywall_words if word in text_lower)
    
    # Navigation indicators
    nav_words = ['navigation', 'menü', 'menu', 'home', 'startseite', 'impressum', 'datenschutz']
    nav_count = sum(1 for word in nav_words if word in text_lower)
    
    # Calculate ratios
    word_count = len(text.split())
    paywall_ratio = paywall_count / max(word_count, 1) * 100
    
    # Decision
    if word_count < 200 and paywall_count >= 2:
        return {'action': 'paywall_preview', 'reason': f'Paywall preview ({paywall_count} indicators, {word_count} words)'}
    
    if paywall_ratio > 10 and word_count < 500:
        return {'action': 'paywall_preview', 'reason': f'Paywall preview ({paywall_ratio:.1f}%)'}
    
    if nav_count > 5 and word_count < 300:
        return {'action': 'paywall_preview', 'reason': f'Mostly navigation ({nav_count} nav words)'}
    
    # Check for very short content
    if word_count < 50:
        return {'action': 'delete', 'reason': f'Too short ({word_count} words)'}
    
    return {'action': 'keep', 'reason': f'Looks valid ({word_count} words, {paywall_count} paywall indicators)', 'text': text[:2000]}

def process_article(article, analysis):
    """Process article based on analysis"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if analysis['action'] == 'paywall_preview':
        # Mark as paywall preview - keep file but mark in DB
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'paywall_preview',
                abstract = ?,
                paywall = 1
            WHERE id = ?
        ''', (analysis['reason'], article['id']))
        
        print(f"   🔒 {analysis['reason']}: {article['title'][:50]}...")
        return 'paywall'
        
    elif analysis['action'] == 'error':
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'error',
                error_message = ?
            WHERE id = ?
        ''', (analysis['reason'], article['id']))
        print(f"   ❌ {analysis['reason']}: {article['title'][:50]}...")
        return 'error'
    
    else:
        # Keep for LLM cleaning - mark as pending_clean
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'pending_clean'
            WHERE id = ?
        ''', (article['id'],))
        print(f"   ⏳ {analysis['reason']}: {article['title'][:50]}...")
        return 'pending'
    
    conn.commit()
    conn.close()

def create_llm_batches(articles, batch_size=5):
    """Create batch files for LLM processing"""
    queue_dir = RESEARCH_DIR / 'llm_queue'
    queue_dir.mkdir(exist_ok=True)
    
    batches = [articles[i:i+batch_size] for i in range(0, len(articles), batch_size)]
    
    for idx, batch in enumerate(batches, 1):
        batch_file = queue_dir / f'batch_{idx:04d}.json'
        
        batch_data = []
        for article in batch:
            content = read_article_content(article['fulltext_path'])
            text = extract_text_only(content) if content else ""
            
            batch_data.append({
                'id': article['id'],
                'title': article['title'],
                'domain': article['domain'],
                'url': article['url'],
                'text': text[:5000]  # Limit for JSON
            })
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
    
    return len(batches)

def main():
    print("="*70)
    print("🧹 Article Cleaner - Smart Processing")
    print("="*70)
    
    articles = get_all_articles()
    print(f"\n📊 Found {len(articles)} articles to analyze\n")
    
    stats = {'paywall': 0, 'error': 0, 'pending': 0}
    pending_articles = []
    
    for idx, article in enumerate(articles, 1):
        if idx % 50 == 0:
            print(f"\n   ... processed {idx}/{len(articles)} ...\n")
        
        analysis = analyze_article(article)
        result = process_article(article, analysis)
        
        stats[result] += 1
        
        if result == 'pending':
            pending_articles.append(article)
    
    print("\n" + "="*70)
    print("📊 HEURISTICS SUMMARY")
    print("="*70)
    print(f"Paywall previews:    {stats['paywall']}")
    print(f"Errors:              {stats['error']}")
    print(f"Ready for cleaning:  {stats['pending']}")
    
    if pending_articles:
        print(f"\n📝 Creating LLM batches for {len(pending_articles)} articles...")
        batch_count = create_llm_batches(pending_articles)
        print(f"   ✅ Created {batch_count} batches in llm_queue/")
        print(f"\n   Next step: Process batches with LLM")
        print(f"   Directory: {RESEARCH_DIR}/llm_queue/")

if __name__ == '__main__':
    main()
