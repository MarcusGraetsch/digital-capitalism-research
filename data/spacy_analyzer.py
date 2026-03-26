#!/usr/bin/env python3
"""
SpaCy NLP Integration for Article Processing
Automatically extracts entities, keywords, and concepts from articles
"""

import spacy
import sqlite3
from pathlib import Path
import re

RESEARCH_DIR = Path("/root/.openclaw/workspace/research")

# Load spaCy model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")

# Key scholars and concepts for Digital Capitalism research
KEY_SCHOLARS = {
    'zuboff': 'Shoshana Zuboff',
    'srnicek': 'Nick Srnicek',
    'harvey': 'David Harvey',
    'marx': 'Karl Marx',
    'morozov': 'Evgeny Morozov',
    'doctorow': 'Cory Doctorow',
    'fraser': 'Nancy Fraser',
    'marcuse': 'Herbert Marcuse',
    'habermas': 'Jürgen Habermas',
    'weizenbaum': 'Joseph Weizenbaum',
    'turkle': 'Sherry Turkle',
    'bostrom': 'Nick Bostrom',
    'tegmark': 'Max Tegmark'
}

KEY_CONCEPTS = [
    'platform capitalism',
    'surveillance capitalism',
    'gig economy',
    'algorithmic management',
    'digital labor',
    'data extractivism',
    'tech criticism',
    'artificial intelligence',
    'machine learning',
    'big tech',
    'platform economy'
]

def extract_entities(text):
    """Extract named entities from text"""
    if not text or len(text) < 100:
        return []
    
    # Limit text length for performance
    text = text[:10000]
    
    doc = nlp(text)
    
    entities = {
        'PERSON': [],
        'ORG': [],
        'WORK_OF_ART': [],
        'GPE': []  # Geopolitical entities
    }
    
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)
    
    return entities

def extract_keywords(text, top_n=10):
    """Extract important keywords from text"""
    if not text or len(text) < 100:
        return []
    
    text = text[:10000]
    doc = nlp(text)
    
    # Get nouns and proper nouns (excluding stopwords)
    keywords = []
    for token in doc:
        if (token.pos_ in ['NOUN', 'PROPN']) and not token.is_stop and len(token.text) > 2:
            keywords.append(token.lemma_.lower())
    
    # Count frequency
    from collections import Counter
    top_keywords = Counter(keywords).most_common(top_n)
    
    return [word for word, count in top_keywords]

def find_key_scholars(text):
    """Find mentions of key scholars in text"""
    if not text:
        return []
    
    text_lower = text.lower()
    found_scholars = []
    
    for scholar_key, scholar_name in KEY_SCHOLARS.items():
        if scholar_key in text_lower:
            found_scholars.append(scholar_name)
    
    return found_scholars

def find_key_concepts(text):
    """Find mentions of key concepts"""
    if not text:
        return []
    
    text_lower = text.lower()
    found_concepts = []
    
    for concept in KEY_CONCEPTS:
        if concept in text_lower:
            found_concepts.append(concept)
    
    return found_concepts

def analyze_article(article_id, text=None):
    """Analyze a single article and return NLP features"""
    if not text:
        # Load from database if text not provided
        conn = sqlite3.connect(RESEARCH_DIR / 'articles.db')
        cursor = conn.cursor()
        cursor.execute('SELECT abstract, title FROM articles WHERE id = ?', (article_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            text = f"{row[1]} {row[0] or ''}"
        else:
            return None
    
    # Run spaCy analysis
    entities = extract_entities(text)
    keywords = extract_keywords(text)
    scholars = find_key_scholars(text)
    concepts = find_key_concepts(text)
    
    return {
        'article_id': article_id,
        'entities': entities,
        'keywords': keywords,
        'scholars': scholars,
        'concepts': concepts
    }

def update_article_tags(article_id, analysis):
    """Update article with NLP-derived tags"""
    conn = sqlite3.connect(RESEARCH_DIR / 'articles.db')
    cursor = conn.cursor()
    
    # Build tags list
    tags = []
    
    # Add scholars
    if analysis['scholars']:
        tags.extend([f"scholar:{s}" for s in analysis['scholars'][:3]])
    
    # Add concepts
    if analysis['concepts']:
        tags.extend([f"concept:{c}" for c in analysis['concepts'][:3]])
    
    # Add top keywords
    if analysis['keywords']:
        tags.extend(analysis['keywords'][:5])
    
    # Join tags
    tag_string = ', '.join(tags)
    
    # Update database
    cursor.execute('''
        UPDATE articles 
        SET tags = CASE 
            WHEN tags IS NULL OR tags = '' THEN ?
            ELSE tags || ', ' || ?
        END
        WHERE id = ?
    ''', (tag_string, tag_string, article_id))
    
    conn.commit()
    conn.close()
    
    return tag_string

def batch_analyze_uncategorized(limit=50):
    """Analyze articles without proper tags"""
    conn = sqlite3.connect(RESEARCH_DIR / 'articles.db')
    cursor = conn.cursor()
    
    # Find articles with few or no tags
    cursor.execute('''
        SELECT id, title, abstract 
        FROM articles 
        WHERE (tags IS NULL OR tags = '' OR LENGTH(tags) < 20)
        AND (abstract IS NOT NULL OR title IS NOT NULL)
        LIMIT ?
    ''', (limit,))
    
    articles = cursor.fetchall()
    conn.close()
    
    print(f"🧠 Analyzing {len(articles)} articles with spaCy...")
    
    updated = 0
    for article_id, title, abstract in articles:
        text = f"{title or ''} {abstract or ''}"
        
        if len(text) < 50:
            continue
        
        analysis = analyze_article(article_id, text)
        
        if analysis and (analysis['scholars'] or analysis['concepts'] or analysis['keywords']):
            tags = update_article_tags(article_id, analysis)
            if tags:
                print(f"  ✓ Article {article_id}: {tags[:80]}...")
                updated += 1
    
    print(f"\n✅ Updated {updated} articles with NLP tags")
    return updated

if __name__ == "__main__":
    # Run batch analysis
    batch_analyze_uncategorized(limit=100)
