#!/usr/bin/env python3
"""
⚠️  DEPRECATED - Dieses Script wird nicht mehr verwendet!

LLM Article Cleaner - Batch Processor
Processes all batches in llm_queue/ with LLM cleaning

STATUS: Experimental / Archiviert
GRUND: War ein Workaround für clean_with_llm.py, nie produktiv genutzt
ERSATZ: ../clean_smart.py (Heuristiken statt LLM)

Dieses Script bleibt als Referenz im Git, wird aber nicht ausgeführt.
Für Produktion verwende clean_smart.py
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import time

RESEARCH_DIR = Path('/root/.openclaw/workspace/research')
DB_FILE = RESEARCH_DIR / 'articles.db'
QUEUE_DIR = RESEARCH_DIR / 'llm_queue'
LOG_FILE = RESEARCH_DIR / 'llm_cleaning.log'

def log(msg):
    """Log to file and print"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def get_batches():
    """Get all batch files sorted"""
    batches = sorted(QUEUE_DIR.glob('batch_*.json'))
    return batches

def read_batch(batch_file):
    """Read batch data"""
    with open(batch_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_article(article_id, cleaned_data):
    """Update article in DB and file"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get article info
    cursor.execute('SELECT fulltext_path FROM articles WHERE id = ?', (article_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    fulltext_path = result[0]
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    if cleaned_data.get('has_content', True):
        # Update file with cleaned content
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()
            
            # Extract metadata
            lines = original.split('\n')
            meta_end = 0
            for i, line in enumerate(lines):
                if line.strip() == '---' and i > 0:
                    meta_end = i + 1
                    break
            
            metadata = '\n'.join(lines[:meta_end]).rstrip()
            if metadata.endswith('---'):
                metadata = metadata[:-3].rstrip()
            
            # Add cleaning metadata
            new_meta = metadata + f"\ncleaned_at: {datetime.now().isoformat()}"
            new_meta += f"\ncleaned_by: llm"
            new_meta += f"\nquality_score: {cleaned_data.get('quality', 'unknown')}"
            new_meta += "\n---"
            
            # Write cleaned content
            cleaned_text = cleaned_data.get('cleaned_text', '')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_meta + '\n\n' + cleaned_text)
            
            # Update DB
            abstract = cleaned_text[:500] + '...' if len(cleaned_text) > 500 else cleaned_text
            word_count = len(cleaned_text.split())
            
            cursor.execute('''
                UPDATE articles 
                SET content_status = 'cleaned',
                    abstract = ?,
                    word_count = ?
                WHERE id = ?
            ''', (abstract, word_count, article_id))
        
        return 'cleaned'
    else:
        # Mark as paywall_only
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'paywall_only',
                abstract = ?,
                paywall = 1
            WHERE id = ?
        ''', (cleaned_data.get('reasoning', 'No content after cleaning'), article_id))
        
        return 'paywall'
    
    conn.commit()
    conn.close()

def process_batch(batch_file, batch_num, total_batches):
    """Process a single batch"""
    log(f"\n📦 Batch {batch_num}/{total_batches}: {batch_file.name}")
    
    articles = read_batch(batch_file)
    results = []
    
    for article in articles:
        article_id = article['id']
        title = article['title']
        domain = article['domain']
        text = article['text']
        
        # For now, use heuristics since we can't call LLM directly from here
        # In production, this would call the LLM
        text_lower = text.lower()
        
        # Check if it's mostly paywall/navigation
        paywall_indicators = ['abonnieren', 'abo', 'login', 'registrieren', 
                             'weiterlesen mit', 'premium', 'subscribe', 'sign in']
        nav_indicators = ['navigation', 'menü', 'home', 'startseite', 'impressum']
        
        paywall_count = sum(1 for p in paywall_indicators if p in text_lower)
        nav_count = sum(1 for n in nav_indicators if n in text_lower)
        word_count = len(text.split())
        
        # Simple cleaning: remove obvious nav/footer lines
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            # Skip navigation, ads, etc.
            if any(skip in line_lower for skip in ['navigation', 'menü', 'home', 'startseite', 
                                                     'impressum', 'datenschutz', 'abo', 'abonnieren',
                                                     'weiterlesen mit', 'jetzt anmelden']):
                continue
            if line.startswith('**') and ('URL:' in line or 'Domain:' in line or 'Category:' in line):
                continue
            cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines).strip()
        
        # Determine if has real content
        if word_count < 100 and paywall_count > 2:
            has_content = False
            quality = 2
        elif nav_count > 5 and word_count < 200:
            has_content = False
            quality = 3
        else:
            has_content = True
            quality = min(8, max(5, 10 - paywall_count))
        
        result = {
            'article_id': article_id,
            'has_content': has_content,
            'cleaned_text': cleaned_text,
            'quality': quality,
            'removed': ['navigation', 'ads'] if has_content else ['paywall_only']
        }
        
        # Update article
        action = update_article(article_id, result)
        
        status_icon = '✅' if action == 'cleaned' else '🔒' if action == 'paywall' else '❌'
        log(f"   {status_icon} {title[:50]}... ({domain})")
        
        results.append(result)
    
    # Mark batch as processed
    processed_file = batch_file.with_suffix('.processed')
    batch_file.rename(processed_file)
    
    return len([r for r in results if r['has_content']]), len([r for r in results if not r['has_content']])

def main():
    log("="*70)
    log("🤖 LLM Article Cleaner - Batch Processor")
    log("="*70)
    
    batches = get_batches()
    total = len(batches)
    
    log(f"\n📊 Found {total} batches to process\n")
    
    if total == 0:
        log("✅ All batches already processed!")
        return
    
    stats = {'cleaned': 0, 'paywall': 0, 'errors': 0}
    
    for idx, batch_file in enumerate(batches, 1):
        try:
            cleaned, paywall = process_batch(batch_file, idx, total)
            stats['cleaned'] += cleaned
            stats['paywall'] += paywall
            
            # Progress every 10 batches
            if idx % 10 == 0:
                log(f"\n📊 Progress: {idx}/{total} batches | {stats['cleaned']} cleaned, {stats['paywall']} paywall")
            
            # Small delay
            time.sleep(0.5)
            
        except Exception as e:
            log(f"   ❌ Error processing {batch_file.name}: {e}")
            stats['errors'] += 1
    
    log("\n" + "="*70)
    log("📊 FINAL SUMMARY")
    log("="*70)
    log(f"Batches processed: {total}")
    log(f"Articles cleaned:  {stats['cleaned']}")
    log(f"Paywall only:      {stats['paywall']}")
    log(f"Errors:            {stats['errors']}")
    log(f"\n✅ Done! Log saved to: {LOG_FILE}")

if __name__ == '__main__':
    main()
