#!/usr/bin/env python3
"""
Weekly Telegram Digest - Hybrid Approach
1. Algorithmic pre-selection (Top 20)
2. Manual curation (You pick Top 5)
3. Learning from ratings (Long-term)
"""

import sqlite3
import os
from datetime import datetime

RESEARCH_DIR = "/root/.openclaw/workspace/research"

def get_algorithmic_candidates(limit=20):
    """Get algorithmically pre-selected candidates"""
    conn = sqlite3.connect(f'{RESEARCH_DIR}/articles.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, author, domain, category, word_count, tags, abstract, url
        FROM articles
        WHERE created_at >= datetime('now', '-7 days')
        AND word_count > 1000
        ORDER BY 
            CASE 
                WHEN category IN ('surveillance', 'tech-criticism', 'tech-policy') THEN 5
                WHEN category IN ('ai-policy', 'labor-de') THEN 4
                ELSE 2
            END DESC,
            word_count DESC
        LIMIT ?
    ''', (limit,))
    
    candidates = cursor.fetchall()
    conn.close()
    return candidates

def show_candidates_for_curation():
    """Show candidates for manual selection"""
    candidates = get_algorithmic_candidates(20)
    
    print("📋 ALGORITHMISCHE VORAUSWAHL (Top 20)")
    print("=" * 60)
    print("Wähle deine Top 5 aus (Nummern eingeben, z.B.: 1,3,5,7,12)")
    print()
    
    for i, (id_, title, author, domain, category, word_count, tags, abstract, url) in enumerate(candidates, 1):
        # Short reasoning
        reasons = []
        
        top_authors = ['doctorow', 'zuboff', 'srnicek', 'marx', 'fraser']
        if any(a in str(author).lower() for a in top_authors):
            reasons.append("⭐ Top-Autor")
        
        top_sources = ['pluralistic.net', 'verfassungsblog.de', 'jacobin.com', 
                      'netzpolitik.org', 'newleftreview.org']
        if any(s in str(domain).lower() for s in top_sources):
            reasons.append("✅ Premium-Quelle")
        
        if category in ['surveillance', 'tech-criticism']:
            reasons.append("🎯 Kern-Thema")
        
        reason_str = " | ".join(reasons) if reasons else "📄 Standard"
        
        print(f"{i:2}. {title[:50]}...")
        print(f"    Von: {author or 'N/A'} ({domain})")
        print(f"    Warum: {reason_str}")
        print(f"    URL: {url[:60]}...")
        print()
    
    print("=" * 60)
    print("💡 Tipp: Öffne URLs kurz, um Qualität zu prüfen")
    print("📧 Antworte mit: 'DIGEST: 1,3,5,12,18'")
    
    return candidates

def generate_final_digest(selected_indices, candidates):
    """Generate final digest from manually selected articles"""
    selected = [candidates[i-1] for i in selected_indices if 1 <= i <= len(candidates)]
    
    message = f"📊 WEEKLY RESEARCH DIGEST (Manuell kuratiert)\n"
    message += f"📅 {datetime.now().strftime('%d.%m.%Y')}\n"
    message += "=" * 50 + "\n\n"
    message += "🔥 TOP 5 (Deine Auswahl):\n\n"
    
    for i, (id_, title, author, domain, category, word_count, tags, abstract, url) in enumerate(selected, 1):
        message += f"{i}. {title[:55]}...\n"
        message += f"   👤 {author or 'N/A'} ({domain})\n"
        message += f"   🔗 {url}\n\n"
    
    message += "=" * 50 + "\n"
    message += "💡 Nächste Woche: Antworte mit Bewertungen (1-5 Sterne)\n"
    message += "   Damit lernen wir, was dir gefällt!"
    
    return message

def save_rating(article_id, rating, notes=""):
    """Save manual rating for future learning"""
    conn = sqlite3.connect(f'{RESEARCH_DIR}/articles.db')
    cursor = conn.cursor()
    
    # Add ratings table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS article_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            rating INTEGER,  -- 1-5 stars
            rated_at TEXT,
            notes TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        )
    ''')
    
    cursor.execute('''
        INSERT INTO article_ratings (article_id, rating, rated_at, notes)
        VALUES (?, ?, datetime('now'), ?)
    ''', (article_id, rating, notes))
    
    conn.commit()
    conn.close()
    print(f"✅ Rating gespeichert: Artikel {article_id} = {rating} Sterne")

if __name__ == "__main__":
    # Show candidates for curation
    candidates = show_candidates_for_curation()
    
    # In real usage, you would respond with selected indices
    # For now, just showing the interface
    print("\n⏳ Warte auf deine Auswahl...")
    print("   Format: 'DIGEST: 1,3,5,7,12'")
