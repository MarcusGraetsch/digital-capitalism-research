#!/usr/bin/env python3
"""
⚠️  DEPRECATED - Dieses Script wird nicht mehr verwendet!

Article Cleaner - LLM Batch Processing
Processes articles in batches using LLM for cleaning

STATUS: Experimental / Archiviert
GRUND: Subagent-Aufrufe funktionierten nicht zuverlässig
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
BATCH_SIZE = 5

def get_articles_batch(limit=BATCH_SIZE):
    """Get next batch of articles to clean"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, url, domain, title, fulltext_path, word_count, category
        FROM articles
        WHERE content_status = 'saved'
        LIMIT ?
    ''', (limit,))
    
    return [dict(row) for row in cursor.fetchall()]

def read_article_content(fulltext_path):
    """Read article content"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract text after frontmatter
    lines = content.split('\n')
    in_content = False
    content_lines = []
    
    for line in lines:
        if line.strip() == '---' and not in_content:
            in_content = True
            continue
        if in_content:
            if line.startswith('# ') or line.startswith('**URL:**') or line.startswith('**Domain:**'):
                continue
            if line.startswith('**Category:**') or line.startswith('**Scanned:**') or line.startswith('**Word Count:**'):
                continue
            if line.strip() == '---':
                continue
            content_lines.append(line)
    
    return '\n'.join(content_lines).strip()

def process_batch_with_subagent(articles):
    """Process a batch using subagent"""
    
    # Build the task for subagent
    task_parts = ["Bereinige diese gescrapten Artikel. Extrahiere für JEDEN Artikel NUR den eigentlichen Artikeltext (Überschrift + Autor + Datum + Hauptinhalt). Entferne Navigation, Werbung, Paywall-Hinweise, Login-Buttons, Cookie-Banner, "Mehr aus unserem Netzwerk", etc.\n"]
    task_parts.append("Antworte im JSON-Format als Array:")
    task_parts.append('[{"article_id": "id", "has_content": true/false, "cleaned_text": "...", "removed": ["..."], "quality": 1-10}]')
    task_parts.append('has_content=false wenn der Text NUR aus Paywall/Login/Navigation besteht.\n')
    
    for idx, article in enumerate(articles, 1):
        content = read_article_content(article['fulltext_path'])
        if not content:
            content = "[FILE NOT FOUND]"
        
        # Truncate very long content
        content = content[:4000] if len(content) > 4000 else content
        
        task_parts.append(f"\n--- ARTIKEL {idx} ---")
        task_parts.append(f"article_id: {article['id']}")
        task_parts.append(f"title: {article['title']}")
        task_parts.append(f"domain: {article['domain']}")
        task_parts.append(f"content:\n{content}\n")
    
    task = '\n'.join(task_parts)
    
    # Save task to file for reference
    batch_id = datetime.now().strftime("%H%M%S")
    task_file = RESEARCH_DIR / 'cleaning_batches' / f'task_{batch_id}.txt'
    task_file.parent.mkdir(exist_ok=True)
    with open(task_file, 'w') as f:
        f.write(task)
    
    print(f"   📝 Task saved: {task_file}")
    print(f"   🤖 Starting subagent...")
    
    # Call subagent
    try:
        result = subprocess.run([
            'openclaw', 'sessions', 'spawn',
            '--runtime', 'subagent',
            '--mode', 'run',
            '--task', task
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Try to extract JSON from result
            output = result.stdout
            # Find JSON array in output
            start = output.find('[')
            end = output.rfind(']')
            if start != -1 and end != -1:
                try:
                    return json.loads(output[start:end+1])
                except:
                    return None
        return None
    except Exception as e:
        print(f"   ❌ Subagent error: {e}")
        return None

def update_and_save(article, result):
    """Update database and file based on LLM result"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if not result.get('has_content', True):
        # Paywall only - delete file and update DB
        print(f"      🗑️  Paywall only - deleting {article['title'][:40]}...")
        file_path = Path(article['fulltext_path'])
        if not file_path.is_absolute():
            file_path = RESEARCH_DIR / article['fulltext_path']
        
        try:
            if file_path.exists():
                file_path.unlink()
        except:
            pass
        
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'paywall_only',
                abstract = 'Paywall - no usable content',
                word_count = 0,
                error_message = ?
            WHERE id = ?
        ''', (result.get('removed', ['Paywall only'])[0] if result.get('removed') else 'Paywall only', article['id']))
        
    else:
        # Has content - save cleaned version
        print(f"      ✅ Cleaned (quality: {result.get('quality', '?')}/10) {article['title'][:40]}...")
        
        cleaned_text = result.get('cleaned_text', '')
        word_count = len(cleaned_text.split())
        
        # Update file
        file_path = Path(article['fulltext_path'])
        if not file_path.is_absolute():
            file_path = RESEARCH_DIR / article['fulltext_path']
        
        if file_path.exists():
            # Read original for metadata
            with open(file_path, 'r') as f:
                original = f.read()
            
            lines = original.split('\n')
            metadata_end = 0
            for i, line in enumerate(lines):
                if line.strip() == '---' and i > 0:
                    metadata_end = i + 1
                    break
            
            metadata = '\n'.join(lines[:metadata_end]).rstrip()
            if metadata.endswith('---'):
                metadata = metadata[:-3].rstrip()
            
            new_metadata = metadata + f"\ncleaned_at: {datetime.now().isoformat()}"
            new_metadata += "\ncleaned_by: llm"
            new_metadata += f"\nquality_score: {result.get('quality', 'unknown')}"
            new_metadata += "\n---"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_metadata + '\n\n' + cleaned_text)
        
        # Update DB
        abstract = cleaned_text[:500] + '...' if len(cleaned_text) > 500 else cleaned_text
        cursor.execute('''
            UPDATE articles 
            SET content_status = 'cleaned',
                abstract = ?,
                word_count = ?
            WHERE id = ?
        ''', (abstract, word_count, article['id']))
    
    conn.commit()
    conn.close()

def main():
    print("="*70)
    print("🧹 Article Cleaner - LLM Batch Processing")
    print("="*70)
    
    stats = {'processed': 0, 'cleaned': 0, 'deleted': 0, 'errors': 0}
    
    while True:
        # Get next batch
        articles = get_articles_batch(BATCH_SIZE)
        
        if not articles:
            print("\n✅ All articles processed!")
            break
        
        print(f"\n🔄 Processing batch of {len(articles)} articles...")
        
        # Process with LLM
        results = process_batch_with_subagent(articles)
        
        if results and isinstance(results, list):
            # Match results to articles
            for article in articles:
                article_result = next((r for r in results if r.get('article_id') == article['id']), None)
                
                if article_result:
                    update_and_save(article, article_result)
                    if article_result.get('has_content', True):
                        stats['cleaned'] += 1
                    else:
                        stats['deleted'] += 1
                else:
                    print(f"   ⚠️  No result for {article['id']}")
                    stats['errors'] += 1
                
                stats['processed'] += 1
        else:
            print(f"   ❌ Batch processing failed")
            stats['errors'] += len(articles)
        
        # Progress summary
        print(f"   📊 Progress: {stats['processed']} processed, {stats['cleaned']} cleaned, {stats['deleted']} deleted")
        
        # Small delay between batches
        time.sleep(2)
    
    # Final summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    print(f"Total processed: {stats['processed']}")
    print(f"Cleaned:         {stats['cleaned']}")
    print(f"Deleted (junk):  {stats['deleted']}")
    print(f"Errors:          {stats['errors']}")

if __name__ == '__main__':
    main()
