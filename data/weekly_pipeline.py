#!/usr/bin/env python3
"""
Weekly Email Pipeline - Complete workflow
Scrapes new emails, cleans articles, labels them
Run once per week (e.g., Sunday)
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import subprocess
import time

RESEARCH_DIR = Path(os.environ.get('RESEARCH_DIR', '/root/.openclaw/workspace/research'))
DB_FILE = RESEARCH_DIR / 'articles.db'
LOG_FILE = RESEARCH_DIR / 'weekly_pipeline.log'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def count_new_articles():
    """Count articles that need cleaning/labeling"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE content_status = "saved"')
    saved = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE content_status = "cleaned" AND (tags IS NULL OR tags = "")')
    needs_label = cursor.fetchone()[0]
    
    conn.close()
    return saved, needs_label

def run_scan():
    """Run email scan"""
    log("📧 Starting email scan...")
    try:
        result = subprocess.run(
            ['python3', str(RESEARCH_DIR / 'scan_v5.py')],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )
        log(f"   ✅ Scan complete")
        return True
    except Exception as e:
        log(f"   ❌ Scan failed: {e}")
        return False

def run_rss_scan():
    """Run RSS feed scan"""
    log("📡 Starting RSS feed scan...")
    try:
        result = subprocess.run(
            ['python3', str(RESEARCH_DIR / 'scan_rss.py')],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )
        log(f"   ✅ RSS scan complete")
        return True
    except Exception as e:
        log(f"   ❌ RSS scan failed: {e}")
        return False

def run_clean():
    """Run article cleaning"""
    log("🧹 Starting article cleaning...")
    try:
        result = subprocess.run(
            ['python3', str(RESEARCH_DIR / 'clean_smart.py')],
            capture_output=True,
            text=True,
            timeout=1800  # 30 min max
        )
        log(f"   ✅ Cleaning complete")
        return True
    except Exception as e:
        log(f"   ❌ Cleaning failed: {e}")
        return False

def run_label():
    """Run article labeling"""
    log("🏷️  Starting article labeling...")
    try:
        result = subprocess.run(
            ['python3', str(RESEARCH_DIR / 'label_articles.py')],
            capture_output=True,
            text=True,
            timeout=1800  # 30 min max
        )
        log(f"   ✅ Labeling complete")
        return True
    except Exception as e:
        log(f"   ❌ Labeling failed: {e}")
        return False

def run_summarize():
    """Run article summarization"""
    log("📝 Starting article summarization...")
    try:
        result = subprocess.run(
            ['python3', str(RESEARCH_DIR / 'summarize_articles.py')],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max (LLM calls are slow)
        )
        log(f"   ✅ Summarization complete")
        return True
    except Exception as e:
        log(f"   ❌ Summarization failed: {e}")
        return False

def run_extract_quotes():
    """Run quote & discourse mention extraction from articles"""
    log("💬 Starting quote & mention extraction...")
    try:
        result = subprocess.run(
            ['python3', str(RESEARCH_DIR / 'extract_article_quotes.py')],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max (LLM calls)
        )
        log(f"   ✅ Quote/mention extraction complete")
        return True
    except Exception as e:
        log(f"   ❌ Quote extraction failed: {e}")
        return False


def run_digest():
    """Generate weekly digest"""
    log("📰 Generating weekly digest...")
    try:
        result = subprocess.run(
            ['python3', str(RESEARCH_DIR / 'generate_digest.py')],
            capture_output=True,
            text=True,
            timeout=300  # 5 min max
        )
        log(f"   ✅ Digest generated")
        if result.stdout:
            log(f"   {result.stdout.strip()}")
        return True
    except Exception as e:
        log(f"   ❌ Digest generation failed: {e}")
        return False

def get_final_stats():
    """Get final statistics"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT content_status, COUNT(*) FROM articles GROUP BY content_status')
    stats = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) FROM articles')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE content_status = "labeled"')
    labeled = cursor.fetchone()[0]
    
    conn.close()
    return total, labeled, stats

def main():
    log("="*70)
    log("📅 WEEKLY EMAIL PIPELINE")
    log("="*70)
    
    start_time = datetime.now()
    
    # Check initial state
    saved_before, needs_label_before = count_new_articles()
    log(f"\n📊 Before: {saved_before} articles to clean, {needs_label_before} to label")
    
    # Step 1a: Email scan
    if not run_scan():
        log("❌ Pipeline aborted at email scan step")
        return

    # Step 1b: RSS feed scan
    time.sleep(2)
    if not run_rss_scan():
        log("⚠️  RSS scan had issues, continuing...")

    # Step 2: Clean
    time.sleep(2)
    if not run_clean():
        log("⚠️  Cleaning had issues, continuing...")
    
    # Step 3: Label
    time.sleep(2)
    if not run_label():
        log("⚠️  Labeling had issues, continuing...")

    # Step 4: Summarize
    time.sleep(2)
    if not run_summarize():
        log("⚠️  Summarization had issues, continuing...")

    # Step 5: Extract quotes & discourse mentions from articles
    time.sleep(2)
    if not run_extract_quotes():
        log("⚠️  Quote/mention extraction had issues, continuing...")

    # Step 6: Generate digest
    time.sleep(2)
    if not run_digest():
        log("⚠️  Digest generation had issues, continuing...")

    # Step 7: Update dashboard
    time.sleep(2)
    log("📊 Updating ontology dashboard...")
    try:
        subprocess.run(
            ['python3', str(RESEARCH_DIR / 'update_dashboard.py')],
            check=True,
            timeout=60
        )
        log("   ✅ Dashboard updated")
    except Exception as e:
        log(f"   ⚠️  Dashboard update failed: {e}")

    # Step 7b: Discourse dashboard
    log("🕸️  Updating discourse dashboard...")
    try:
        subprocess.run(
            ['python3', 'generate_discourse_dashboard.py'],
            check=True,
            timeout=60
        )
        log("   ✅ Discourse dashboard updated")
        # Copy to website repo
        website_dest = Path(os.environ.get('WEBSITE_REPO', '/mnt/d/Develop/myWebsite/marcus-cyborg'))
        dest_file = website_dest / 'src' / 'graph' / 'discourse-dashboard.html'
        if dest_file.parent.exists():
            import shutil
            shutil.copy2('discourse-dashboard.html', dest_file)
            log(f"   ✅ Copied to website: {dest_file}")
        else:
            log(f"   ⚠️  Website repo not found at {website_dest}")
    except Exception as e:
        log(f"   ⚠️  Discourse dashboard failed: {e}")

    # Step 7c: Literature discovery
    log("🔍 Running literature discovery...")
    try:
        subprocess.run(
            ['python3', 'discover_literature.py', '--limit', '20'],
            check=True,
            timeout=600
        )
        log("   ✅ Literature discovery complete")
    except Exception as e:
        log(f"   ⚠️  Literature discovery failed: {e}")

    # Final stats
    total, labeled, stats = get_final_stats()
    
    duration = (datetime.now() - start_time).total_seconds() / 60
    
    log("\n" + "="*70)
    log("📊 FINAL STATISTICS")
    log("="*70)
    log(f"Duration: {duration:.1f} minutes")
    log(f"Total articles in DB: {total}")
    log(f"Fully processed: {labeled}")
    log("\nStatus breakdown:")
    for status, count in sorted(stats, key=lambda x: x[1], reverse=True):
        log(f"  {status}: {count}")
    
        
    # Step 9: Generate Telegram Digest (NEW)
    log("\n📱 Generating Telegram weekly digest...")
    try:
        result = subprocess.run(
            ['python3', str(RESEARCH_DIR / 'weekly_telegram_digest.py')],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            log("   ✅ Telegram digest generated")
            # Save output to file
            digest_file = RESEARCH_DIR / 'briefings' / f'telegram_{datetime.now().strftime("%Y%m%d")}.txt'
            digest_file.parent.mkdir(exist_ok=True)
            with open(digest_file, 'w') as f:
                f.write(result.stdout)
            log(f"   📝 Digest saved: {digest_file}")
        else:
            log(f"   ⚠️  Telegram digest warning: {result.stderr}")
    except Exception as e:
        log(f"   ⚠️  Telegram digest failed: {e}")
log("\n✅ Weekly pipeline complete!")
    log("="*70)
    
    # Step 7: Generate self-improvement report
    log("\n🔄 Generating self-improvement report...")
    try:
        workspace = RESEARCH_DIR.parent  # Go up to workspace
        result = subprocess.run(
            ['python3', str(workspace / 'skills' / 'xiucheng-self-improving-agent' / 'self_improving.py'), '--report'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            log("   ✅ Self-improvement report generated")
            # Save report to file
            report_file = workspace / 'memory' / 'self_improvement_weekly_report.md'
            with open(report_file, 'w') as f:
                f.write(result.stdout)
            log(f"   📝 Report saved: {report_file}")
        else:
            log(f"   ⚠️  Report generation warning: {result.stderr}")
    except Exception as e:
        log(f"   ⚠️  Self-improvement report failed: {e}")
    
    # Step 8: Generate weekly research briefing
    log("\n📝 Generating weekly research briefing...")
    try:
        workspace = RESEARCH_DIR.parent
        result = subprocess.run(
            ['python3', str(workspace / 'generate_weekly_briefing.py')],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            log("   ✅ Weekly briefing generated")
            # Extract summary from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'new articles' in line.lower():
                    log(f"   📊 {line.strip()}")
                    break
            log(f"   📄 Briefing saved: briefings/briefing_{datetime.now().strftime('%Y%m%d')}.md")
        else:
            log(f"   ⚠️  Briefing generation warning: {result.stderr}")
    except Exception as e:
        log(f"   ⚠️  Weekly briefing failed: {e}")

if __name__ == '__main__':
    main()
