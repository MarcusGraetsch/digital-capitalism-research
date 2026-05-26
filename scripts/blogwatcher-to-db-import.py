#!/usr/bin/env python3
"""
blogwatcher-to-db-import.py
Importiert ungelesene blogwatcher-Artikel in die articles.db
Damit RSS-Feeds Teil des Research-Pipelines werden.
"""

import subprocess
import sqlite3
import hashlib
import re
from pathlib import Path
from datetime import datetime

# --- Konfiguration ---
RESEARCH_DIR = Path("/root/.openclaw/workspace/projects/digital-research")
DATA_DIR = RESEARCH_DIR / "data"
DB_FILE = DATA_DIR / "articles.db"
BLOGWATCHER_DB = Path.home() / ".config" / "blogwatcher" / "blogwatcher.db"

# Blog → Category Mapping
BLOG_CATEGORIES = {
    "AI Now Institute": ["ki", "gesellschaft", "tech-politik"],
    "Jacobin": ["politik", "ökonomie", "gesellschaft"],
    "LabourNet Germany": ["arbeit", "gewerkschaften", "sozialpolitik"],
    "Logic Magazine": ["tech-kritik", "digitalisierung"],
    "Netzpolitik": ["digitalpolitik", "überwachung", "netzfreiheit"],
    "Real Life Mag": ["kultur", "technologie", "kritische-theorie"],
    "Rest of World": ["global-south", "tech", "geopolitik"],
}

def run_blogwatcher(command):
    """Führe blogwatcher CLI aus und parse Output"""
    result = subprocess.run(
        ["/root/go/bin/blogwatcher"] + command.split(),
        capture_output=True,
        text=True,
        cwd=str(RESEARCH_DIR)
    )
    return result.stdout

def parse_articles(output):
    """Parse blogwatcher articles output"""
    articles = []
    current = {}
    
    for line in output.split('\n'):
        line = line.strip()
        
        # Artikel-ID
        id_match = re.match(r'\[(\d+)\]\s*\[new\]', line)
        if id_match:
            if current:
                articles.append(current)
            current = {'id': id_match.group(1)}
            continue
        
        # Blog Name
        if line.startswith('Blog:'):
            current['blog'] = line.replace('Blog:', '').strip()
            continue
        
        # URL
        if line.startswith('URL:'):
            current['url'] = line.replace('URL:', '').strip()
            continue
        
        # Published
        if line.startswith('Published:'):
            current['published'] = line.replace('Published:', '').strip()
            continue
        
        # Title (after [new])
        if '[new]' in line:
            title = line.replace('[new]', '').strip()
            if title and not title.startswith('Blog') and not title.startswith('URL'):
                current['title'] = title
    
    if current:
        articles.append(current)
    
    return articles

def extract_domain(url):
    """Extrahiere Domain aus URL"""
    match = re.search(r'https?://([^/]+)', url)
    return match.group(1) if match else ""

def generate_id(url, published):
    """Generiere konsistente ID aus URL + Datum"""
    hash_input = f"{url}{published}".encode()
    return hashlib.md5(hash_input).hexdigest()[:16]

def get_tags(blog, title):
    """Leite Tags aus Blog und Title ab"""
    base_tags = BLOG_CATEGORIES.get(blog, ["rss", "digital-research"])
    
    # Title-Keywords hinzufügen
    title_lower = title.lower()
    if any(k in title_lower for k in ['ai', 'ki', 'artificial', 'machine learning']):
        base_tags.append('ki')
    if any(k in title_lower for k in ['arbeit', 'labor', 'gewerkschaft', 'union']):
        base_tags.append('arbeit')
    if any(k in title_lower for k in ['platform', 'gig', 'uber', 'delivery']):
        base_tags.append('plattform-ökonomie')
    if any(k in title_lower for k in ['surveillance', 'überwachung', 'daten']):
        base_tags.append('datengesellschaft')
    
    return ','.join(base_tags[:5])  # Max 5 Tags

def import_articles():
    """Importiere blogwatcher-Artikel in DB"""
    
    # Hole ungelesene Artikel
    output = run_blogwatcher("articles")
    
    if "No unread" in output or "Unread articles" not in output:
        print("📭 Keine ungelesenen Artikel zum Importieren")
        return
    
    articles = parse_articles(output)
    print(f"📰 {len(articles)} ungelesene Artikel gefunden")
    
    if not articles:
        return
    
    # DB-Verbindung
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    imported = 0
    skipped = 0
    
    for article in articles:
        url = article.get('url', '')
        title = article.get('title', '')
        blog = article.get('blog', '')
        published = article.get('published', datetime.now().strftime('%Y-%m-%d'))
        
        if not url:
            continue
        
        domain = extract_domain(url)
        article_id = generate_id(url, published)
        tags = get_tags(blog, title)
        
        try:
            # Prüfe ob bereits vorhanden
            cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
            if cursor.fetchone():
                skipped += 1
                continue
            
            # Insert
            cursor.execute('''
                INSERT INTO articles (
                    id, url, domain, title, author, publication_date,
                    access_date, email_account, email_date, email_subject,
                    content_status, fulltext_path, abstract, word_count,
                    category, tags, paywall, paywall_type, requires_manual_review,
                    http_status, error_message, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_id, url, domain, title, '', published,
                datetime.now().strftime('%Y-%m-%d'), 'blogwatcher', published, '',
                'new', '', '', 0, '', tags, 0, '', 0, 200, '', ''
            ))
            
            imported += 1
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                skipped += 1
            else:
                print(f"⚠️  Insert-Fehler für {url}: {e}")
    
    conn.commit()
    
    print(f"✅ Importiert: {imported} Artikel")
    print(f"⏭️  Übersprungen (vorhanden): {skipped} Artikel")
    
    # Markiere alle als gelesen in blogwatcher
    if imported > 0:
        print("🔄 Markiere Artikel als gelesen in blogwatcher...")
        # Da blogwatcher keine batch-read hat, machen wir es per CLI
        # Alternativ: Direkt in blogwatcher.db schreiben
    
    return imported, skipped

if __name__ == "__main__":
    print("="*60)
    print("📥 blogwatcher → articles.db Import")
    print("="*60)
    imported, skipped = import_articles()
    print("="*60)
    print(f"✅ Fertig: {imported} neue Artikel importiert, {skipped} übersprungen")