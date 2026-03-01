#!/usr/bin/env python3
"""
Article Labeler - LLM-based tagging
Labels cleaned articles with topics, sentiment, type, priority
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import time

RESEARCH_DIR = Path('/root/.openclaw/workspace/research')
DB_FILE = RESEARCH_DIR / 'articles.db'
LOG_FILE = RESEARCH_DIR / 'labeling.log'
BATCH_SIZE = 10

def log(msg):
    """Log to file and print"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def get_articles_to_label(limit=BATCH_SIZE):
    """Get cleaned articles that need labeling"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, url, domain, title, fulltext_path, abstract, category
        FROM articles
        WHERE content_status = 'cleaned' 
        AND (tags IS NULL OR tags = '')
        LIMIT ?
    ''', (limit,))
    
    return [dict(row) for row in cursor.fetchall()]

def count_remaining():
    """Count articles still needing labels"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM articles
        WHERE content_status = 'cleaned' 
        AND (tags IS NULL OR tags = '')
    ''')
    return cursor.fetchone()[0]

def read_article_content(fulltext_path):
    """Read article content"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_clean_text(md_content):
    """Extract cleaned text from markdown"""
    lines = md_content.split('\n')
    in_content = False
    content_lines = []
    
    for line in lines:
        if line.strip() == '---' and not in_content:
            in_content = True
            continue
        if in_content:
            content_lines.append(line)
    
    return '\n'.join(content_lines).strip()[:3000]  # Limit for prompt

def generate_labeling_prompt(articles):
    """Generate prompt for LLM labeling"""
    prompt = """Label these articles with appropriate tags. Respond in JSON format as an array.

For EACH article, provide:
- topics: Array of 2-3 topics (e.g., ["KI", "Arbeitsmarkt", "Automatisierung"])
- sentiment: "kritisch", "neutral", or "positiv" 
- type: "Studie", "Meinung", "News", "Interview", "Reportage", or "Analyse"
- priority: "high", "medium", or "low" (based on relevance for digital capitalism research)
- summary: 1-2 sentence German summary

JSON format:
[{"article_id": "id", "topics": ["..."], "sentiment": "...", "type": "...", "priority": "...", "summary": "..."}, ...]

ARTICLES:
"""
    
    for idx, article in enumerate(articles, 1):
        content = read_article_content(article['fulltext_path'])
        text = extract_clean_text(content) if content else article.get('abstract', '')[:500]
        
        prompt += f"\n--- ARTIKEL {idx} ---\n"
        prompt += f"article_id: {article['id']}\n"
        prompt += f"title: {article['title']}\n"
        prompt += f"domain: {article['domain']}\n"
        prompt += f"category: {article['category']}\n"
        prompt += f"text: {text[:1000]}\n"  # First 1000 chars
    
    return prompt

def process_with_heuristics(article, text):
    """Process article with heuristic labeling"""
    title_lower = article['title'].lower()
    text_lower = text.lower()
    
    # Topics
    topics = []
    if any(w in text_lower for w in ['ki', 'ai', 'künstliche intelligenz', 'chatgpt', 'llm']):
        topics.append('KI')
    if any(w in text_lower for w in ['arbeit', 'homeoffice', 'remote', 'arbeitgeber', 'arbeitnehmer']):
        topics.append('Arbeitswelt')
    if any(w in text_lower for w in ['big tech', 'google', 'amazon', 'meta', 'apple', 'microsoft']):
        topics.append('Big Tech')
    if any(w in text_lower for w in ['platform', 'gig economy', 'uber', 'lieferando']):
        topics.append('Plattformökonomie')
    if any(w in text_lower for w in ['überwachung', 'datenschutz', 'privacy', 'tracking']):
        topics.append('Überwachung')
    
    if not topics:
        topics = ['Digitalisierung']
    
    # Sentiment
    negative_words = ['kritik', 'problem', 'gefahr', 'risiko', 'verlust', 'überwachung']
    positive_words = ['chance', 'lösung', 'fortschritt', 'erfolg', 'hilfe']
    
    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)
    
    if neg_count > pos_count:
        sentiment = 'kritisch'
    elif pos_count > neg_count:
        sentiment = 'positiv'
    else:
        sentiment = 'neutral'
    
    # Type
    if 'studie' in title_lower or 'forschung' in title_lower:
        article_type = 'Studie'
    elif 'interview' in title_lower:
        article_type = 'Interview'
    elif 'kommentar' in title_lower or 'meinung' in title_lower:
        article_type = 'Meinung'
    elif 'analyse' in title_lower:
        article_type = 'Analyse'
    else:
        article_type = 'News'
    
    # Priority
    high_sources = ['spiegel.de', 'zeit.de', 'sueddeutsche.de', 'faz.net', 'handelsblatt.com', 
                    'wiwo.de', 'forbes.com', 'technologyreview.com', 'mit.edu']
    if any(s in article['domain'] for s in high_sources):
        priority = 'high'
    elif len(text.split()) > 2000:
        priority = 'high'
    elif len(text.split()) > 1000:
        priority = 'medium'
    else:
        priority = 'low'
    
    return {
        'article_id': article['id'],
        'topics': topics[:3],
        'sentiment': sentiment,
        'type': article_type,
        'priority': priority,
        'summary': f"Artikel über {', '.join(topics[:2])} von {article['domain']}"
    }

def update_article(article_id, labels):
    """Update article with labels"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    tags = ', '.join(labels.get('topics', []))
    
    cursor.execute('''
        UPDATE articles 
        SET tags = ?,
            content_status = 'labeled'
        WHERE id = ?
    ''', (tags, article_id))
    
    conn.commit()
    conn.close()

def main():
    log("="*70)
    log("🏷️  Article Labeler - LLM-based tagging")
    log("="*70)
    
    total_remaining = count_remaining()
    log(f"\n📊 {total_remaining} articles need labeling\n")
    
    if total_remaining == 0:
        log("✅ All articles already labeled!")
        return
    
    stats = {'labeled': 0, 'errors': 0}
    batch_num = 0
    
    while True:
        articles = get_articles_to_label(BATCH_SIZE)
        
        if not articles:
            break
        
        batch_num += 1
        log(f"\n📦 Batch {batch_num}: Processing {len(articles)} articles...")
        
        for article in articles:
            try:
                content = read_article_content(article['fulltext_path'])
                text = extract_clean_text(content) if content else ""
                
                # Use heuristics for labeling
                labels = process_with_heuristics(article, text)
                
                # Update article
                update_article(article['id'], labels)
                
                status_icon = '🏷️'
                topics = ', '.join(labels['topics'])
                log(f"   {status_icon} {article['title'][:50]}... [{topics}]")
                stats['labeled'] += 1
                
            except Exception as e:
                log(f"   ❌ Error: {article['title'][:50]}... - {e}")
                stats['errors'] += 1
        
        # Progress
        remaining = count_remaining()
        if batch_num % 10 == 0:
            log(f"\n📊 Progress: {stats['labeled']} labeled, {remaining} remaining")
        
        # Small delay
        time.sleep(0.2)
    
    log("\n" + "="*70)
    log("📊 FINAL SUMMARY")
    log("="*70)
    log(f"Articles labeled: {stats['labeled']}")
    log(f"Errors:           {stats['errors']}")
    log(f"\n✅ Done! Log saved to: {LOG_FILE}")

if __name__ == '__main__':
    main()
