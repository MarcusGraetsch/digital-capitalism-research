#!/usr/bin/env python3
"""
⚠️  DEPRECATED - Dieses Script wird nicht mehr verwendet!

Article Cleaner - Batch Processing
Cleans all articles using LLM in batches
Updates database and deletes paywall-only files

STATUS: Experimental / Archiviert
GRUND: Würde Stunden dauern, zu teuer, instabil
ERSATZ: ../clean_smart.py (Heuristiken statt LLM)

Dieses Script bleibt als Referenz im Git, wird aber nicht ausgeführt.
Für Produktion verwende clean_smart.py
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import subprocess
import time

RESEARCH_DIR = Path('/root/.openclaw/workspace/research')
DB_FILE = RESEARCH_DIR / 'articles.db'
FULLTEXT_DIR = RESEARCH_DIR / 'fulltext'
BATCH_SIZE = 10  # Process 10 articles per subagent call

def get_articles_to_clean():
    """Get all articles with status 'saved' that haven't been cleaned yet"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get articles that are saved but not yet cleaned or marked as paywall_only
    cursor.execute('''
        SELECT id, url, domain, title, fulltext_path, word_count, category, paywall
        FROM articles
        WHERE content_status = 'saved'
        ORDER BY paywall DESC, word_count DESC
    ''')
    
    return [dict(row) for row in cursor.fetchall()]

def read_article_content(fulltext_path):
    """Read article content from file"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_content_only(md_content):
    """Extract just the article text from markdown, skip frontmatter"""
    lines = md_content.split('\n')
    in_content = False
    content_lines = []
    
    for line in lines:
        if line.strip() == '---' and not in_content:
            in_content = True
            continue
        if in_content:
            # Skip the title/header repetition
            if line.startswith('# ') or line.startswith('**URL:**') or line.startswith('**Domain:**'):
                continue
            if line.startswith('**Category:**') or line.startswith('**Scanned:**') or line.startswith('**Word Count:**'):
                continue
            if line.strip() == '---':
                continue
            content_lines.append(line)
    
    return '\n'.join(content_lines).strip()

def create_batch_prompt(articles):
    """Create prompt for cleaning a batch of articles"""
    prompt_parts = ["Bereinige diese Artikel. Extrahiere für JEDEN Artikel nur den eigentlichen Text (Überschrift + Autor + Datum + Hauptinhalt). Entferne Navigation, Werbung, Paywall-Hinweise, Login-Buttons."]
    prompt_parts.append("\nAntworte im JSON-Format als Array:")
    prompt_parts.append("[{\"id\": \"article_id\", \"has_content\": true/false, \"cleaned_text\": \"...\", \"removed\": [\"...\"], \"quality\": 1-10}, ...]")
    prompt_parts.append("\nhas_content=false wenn NUR Paywall/Login/Navigation.\n")
    
    for idx, article in enumerate(articles, 1):
        content = read_article_content(article['fulltext_path'])
        if not content:
            continue
        
        text_only = extract_content_only(content)[:3000]  # Limit length
        
        prompt_parts.append(f"\n--- ARTIKEL {idx} ---")
        prompt_parts.append(f"ID: {article['id']}")
        prompt_parts.append(f"TITEL: {article['title']}")
        prompt_parts.append(f"DOMAIN: {article['domain']}")
        prompt_parts.append(f"TEXT:\n{text_only}\n")
    
    return '\n'.join(prompt_parts)

def process_batch_with_llm(articles):
    """Send batch to LLM for cleaning"""
    prompt = create_batch_prompt(articles)
    
    # Write prompt to temp file
    batch_id = hash(prompt) % 10000
    prompt_file = RESEARCH_DIR / 'cleaning_batches' / f'batch_{batch_id}_{datetime.now().strftime("%H%M%S")}.txt'
    prompt_file.parent.mkdir(exist_ok=True)
    
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    # For now, return None to indicate manual processing needed
    # In production, this would call the LLM
    print(f"   📝 Batch prompt saved: {prompt_file}")
    return None

def update_article_in_db(article_id, has_content, cleaned_text, word_count=None):
    """Update database entry"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if not has_content:
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'paywall_only',
                abstract = 'Paywall - no usable content',
                word_count = 0,
                error_message = 'Only paywall/login content found'
            WHERE id = ?
        ''', (article_id,))
    else:
        abstract = cleaned_text[:500] + '...' if len(cleaned_text) > 500 else cleaned_text
        wc = word_count or len(cleaned_text.split())
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'cleaned',
                abstract = ?,
                word_count = ?
            WHERE id = ?
        ''', (abstract, wc, article_id))
    
    conn.commit()
    conn.close()

def delete_article_file(fulltext_path):
    """Delete the markdown file"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    try:
        if file_path.exists():
            file_path.unlink()
            return True
    except Exception as e:
        print(f"   ❌ Error deleting file: {e}")
    return False

def save_cleaned_article(fulltext_path, original_content, cleaned_text):
    """Save cleaned version back to file"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    # Extract original metadata
    lines = original_content.split('\n')
    metadata_end = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            metadata_end = i + 1
            break
    
    metadata = '\n'.join(lines[:metadata_end]).rstrip()
    if metadata.endswith('---'):
        metadata = metadata[:-3].rstrip()
    
    # Add cleaning metadata
    new_metadata = metadata + f"\ncleaned_at: {datetime.now().isoformat()}"
    new_metadata += "\ncleaned_by: llm_batch"
    new_metadata += "\n---"
    
    # Write cleaned file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_metadata + '\n\n# ' + cleaned_text[:100].split('\n')[0] + '\n\n')
        f.write(cleaned_text)
    
    return True

def clean_single_article(article):
    """Clean a single article by calling LLM"""
    content = read_article_content(article['fulltext_path'])
    if not content:
        return None, "File not found"
    
    text_only = extract_content_only(content)
    
    # Simple heuristics first
    paywall_indicators = [
        'abonnieren', 'jetzt anmelden', 'login', 'registrieren', 
        'weiterlesen mit', 'premium', 'abo', 'paywall',
        'subscribe now', 'sign in', 'register to read'
    ]
    
    # Check if it's mostly paywall
    text_lower = text_only.lower()
    paywall_count = sum(1 for ind in paywall_indicators if ind in text_lower)
    
    if paywall_count >= 3 and len(text_only) < 1000:
        return False, "Paywall detected by heuristics"
    
    # For now, mark as needing LLM review
    return None, "Needs LLM processing"

def main():
    print("="*70)
    print("🧹 Article Cleaner - Batch Processing")
    print("="*70)
    
    articles = get_articles_to_clean()
    total = len(articles)
    print(f"\n📊 Found {total} articles to process\n")
    
    if total == 0:
        print("✅ All articles already cleaned!")
        return
    
    stats = {
        'paywall_deleted': 0,
        'cleaned': 0,
        'errors': 0,
        'needs_llm': 0
    }
    
    # Process in batches
    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = articles[batch_start:batch_end]
        
        print(f"\n🔄 Processing batch {batch_start//BATCH_SIZE + 1}/{(total-1)//BATCH_SIZE + 1} (articles {batch_start+1}-{batch_end})")
        
        for article in batch:
            print(f"   📄 {article['title'][:50]}... ({article['domain']})")
            
            # Quick heuristic check
            result, reason = clean_single_article(article)
            
            if result == False:  # Paywall
                print(f"      🗑️  {reason}")
                delete_article_file(article['fulltext_path'])
                update_article_in_db(article['id'], False, None)
                stats['paywall_deleted'] += 1
                
            elif result == True:  # Cleaned
                print(f"      ✅ Cleaned")
                stats['cleaned'] += 1
                
            else:  # Needs LLM
                print(f"      ⏳ {reason}")
                stats['needs_llm'] += 1
        
        # Small delay between batches
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Total articles:        {total}")
    print(f"Paywall (deleted):     {stats['paywall_deleted']}")
    print(f"Cleaned (heuristics):  {stats['cleaned']}")
    print(f"Errors:                {stats['errors']}")
    print(f"Needs LLM review:      {stats['needs_llm']}")
    
    if stats['needs_llm'] > 0:
        print(f"\n⚠️  {stats['needs_llm']} articles need LLM processing.")
        print("   Run LLM cleaning script for detailed processing.")

if __name__ == '__main__':
    main()
