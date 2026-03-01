#!/usr/bin/env python3
"""
Email Scanner v5 - Full Archive Scan (Schema-Compatible)
Scans ALL emails in Gmail accounts with existing DB schema
"""

import os
import re
import json
import sqlite3
import logging
import time
import pickle
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

# Gmail API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Article fetching
import requests
from bs4 import BeautifulSoup

# Configuration
SCOPES = ['https://mail.google.com/']
WORKSPACE = Path('/root/.openclaw/workspace')
RESEARCH_DIR = WORKSPACE / 'research'
ENV_DIR = Path('/root/.openclaw/.env.d')
STATE_FILE = RESEARCH_DIR / 'scan_state_v5.json'
STATUS_FILE = RESEARCH_DIR / 'scan_status.json'
DB_FILE = RESEARCH_DIR / 'articles.db'
LOG_FILE = RESEARCH_DIR / 'scan_v5.log'
FULLTEXT_DIR = RESEARCH_DIR / 'fulltext'
NOTIFY_EVERY = 100  # Send status update every N emails

# Telegram notification config
TELEGRAM_CHAT_ID = "549758481"  # From your config

# Gmail accounts to scan (mapped to token files)
ACCOUNTS = {
    'bigtech': {
        'email': 'b1gt3ch.5n5lysis@critical-theory.digital',
        'token_file': ENV_DIR / 'gmail-token-b1gt3ch.5n5lysis.json'
    },
    'newwork': {
        'email': 'newworkculture.twentyone@critical-theory.digital',
        'token_file': ENV_DIR / 'gmail-token-newworkculture.twentyone.json'
    },
    'aigen': {
        'email': 'aichitchatter@critical-theory.digital',
        'token_file': ENV_DIR / 'gmail-token-aichitchatter.json'
    }
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EmailScanner:
    def __init__(self):
        self.db = None
        self.state = self.load_state()
        self.connect_db()
        
    def load_state(self):
        """Load resume state"""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {account: {'last_id': None, 'processed': 0, 'saved': 0} for account in ACCOUNTS}
    
    def save_state(self):
        """Save resume state"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def update_status_file(self, account_type, processed, saved, current_email=None):
        """Write status to JSON file for external monitoring"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'account': account_type,
            'processed': processed,
            'saved': saved,
            'current_email': current_email,
            'status': 'running'
        }
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
    
    def send_notification(self, account_type, processed, saved):
        """Send status notification via Telegram bot file"""
        try:
            # Write a notification file that can be picked up
            notify_file = RESEARCH_DIR / 'notify_pending.json'
            notification = {
                'timestamp': datetime.now().isoformat(),
                'type': 'progress',
                'account': account_type,
                'processed': processed,
                'saved': saved,
                'message': f"📧 Email Scan Progress\n\n{account_type.upper()}:\n• {processed} emails processed\n• {saved} articles saved"
            }
            with open(notify_file, 'a') as f:
                f.write(json.dumps(notification) + '\n')
        except Exception as e:
            logger.warning(f"Failed to queue notification: {e}")
    
    def connect_db(self):
        """Connect to existing database"""
        self.db = sqlite3.connect(DB_FILE)
        # Check if articles table exists
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        if not cursor.fetchone():
            raise RuntimeError("Database does not have 'articles' table. Run schema creation first.")
    
    def get_gmail_service(self, account_type):
        """Authenticate and return Gmail service using JSON token file"""
        account_config = ACCOUNTS[account_type]
        token_file = account_config['token_file']
        
        if not token_file.exists():
            raise FileNotFoundError(f"Token file not found: {token_file}")
        
        # Load credentials from JSON token file
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token back to file
            token_data = json.loads(token_file.read_text())
            token_data['token'] = creds.token
            token_data['expiry'] = creds.expiry.isoformat() if creds.expiry else None
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
        
        return build('gmail', 'v1', credentials=creds)
    
    def extract_links(self, text):
        """Extract URLs from text"""
        url_pattern = r'https?://[^\s<>"\')\]]+(?:[^\s<>"\')\].,;!?])'
        return re.findall(url_pattern, text or '')
    
    def generate_id(self, url):
        """Generate unique ID from URL (compatible with existing schema)"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def fetch_article(self, url):
        """Fetch and extract article content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            http_status = response.status_code
            
            # Handle non-200 status
            if http_status != 200:
                return {
                    'error': f'HTTP {http_status}',
                    'http_status': http_status
                }
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Get title
            title = soup.find('title')
            title = title.get_text(strip=True) if title else 'Unknown'
            
            # Try to get author
            author = None
            author_meta = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', property='article:author')
            if author_meta:
                author = author_meta.get('content')
            
            # Try to get publication date
            pub_date = None
            date_meta = soup.find('meta', property='article:published_time') or soup.find('meta', attrs={'name': 'date'})
            if date_meta:
                pub_date = date_meta.get('content')
            
            # Get main content
            article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile('content|article'))
            
            if article:
                text = article.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n\n'.join(lines)
            
            # Detect paywall
            paywall_indicators = [
                'subscribe', 'premium', 'paywall', 'login to read',
                'register to continue', 'bitte anmelden', 'abonnieren',
                'registrieren', 'abo', 'plus-artikel'
            ]
            paywall_text = text.lower()[:3000]
            has_paywall = any(ind in paywall_text for ind in paywall_indicators)
            
            # Try to detect paywall type
            paywall_type = None
            if has_paywall:
                if 'soft' in paywall_text or 'kostenlos' in paywall_text:
                    paywall_type = 'soft'
                else:
                    paywall_type = 'hard'
            
            return {
                'title': title,
                'text': text,
                'author': author,
                'publication_date': pub_date,
                'word_count': len(text.split()),
                'paywall': has_paywall,
                'paywall_type': paywall_type,
                'http_status': http_status
            }
            
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}', 'http_status': None}
        except Exception as e:
            return {'error': str(e), 'http_status': None}
    
    def save_fulltext(self, url, content, category):
        """Save article fulltext to file (compatible format)"""
        now = datetime.now()
        dir_path = FULLTEXT_DIR / now.strftime('%Y-%m')
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        domain = urlparse(url).netloc.replace('www.', '')
        filename = f"{url_hash}_{domain}.md"
        
        file_path = dir_path / filename
        
        # Build metadata header
        header = f"""---
url: {url}
title: {content.get('title', 'Unknown')}
domain: {domain}
category: {category}
date_scanned: {now.isoformat()}
word_count: {content.get('word_count', 0)}
paywall: {content.get('paywall', False)}
---

# {content.get('title', 'Unknown')}

**URL:** {url}

**Domain:** {domain}

**Category:** {category}

**Scanned:** {now.isoformat()}

**Word Count:** {content.get('word_count', 0)}

---

{content.get('text', '')}
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header)
        
        return str(file_path)
    
    def url_exists(self, url):
        """Check if URL already in database"""
        cursor = self.db.cursor()
        cursor.execute('SELECT id FROM articles WHERE url = ?', (url,))
        return cursor.fetchone() is not None
    
    def insert_article(self, url, content, email_account, email_date, email_subject, category):
        """Insert article with existing schema"""
        article_id = self.generate_id(url)
        domain = urlparse(url).netloc.replace('www.', '')
        now = datetime.now().isoformat()
        
        cursor = self.db.cursor()
        
        # Save fulltext first
        fulltext_path = self.save_fulltext(url, content, category)
        
        # Prepare abstract (first 500 chars)
        abstract = content.get('text', '')[:500] + '...' if len(content.get('text', '')) > 500 else content.get('text', '')
        
        cursor.execute('''
            INSERT OR REPLACE INTO articles (
                id, url, domain, title, author, publication_date, access_date,
                email_account, email_date, email_subject, content_status,
                fulltext_path, abstract, word_count, category, tags, paywall,
                paywall_type, requires_manual_review, http_status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article_id,
            url,
            domain,
            content.get('title', 'Unknown'),
            content.get('author'),
            content.get('publication_date'),
            now,
            email_account,
            email_date,
            email_subject,
            'saved',
            fulltext_path,
            abstract,
            content.get('word_count', 0),
            category,
            None,  # tags
            content.get('paywall', False),
            content.get('paywall_type'),
            False,  # requires_manual_review
            content.get('http_status', 200),
            None   # error_message
        ))
        
        self.db.commit()
        return article_id
    
    def insert_error(self, url, error_msg, email_account, email_date, email_subject, category, http_status=None):
        """Insert failed article record"""
        article_id = self.generate_id(url)
        domain = urlparse(url).netloc.replace('www.', '')
        now = datetime.now().isoformat()
        
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO articles (
                id, url, domain, title, access_date,
                email_account, email_date, email_subject, content_status,
                category, paywall, requires_manual_review, http_status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article_id,
            url,
            domain,
            'Failed: ' + str(error_msg)[:100],
            now,
            email_account,
            email_date,
            email_subject,
            'error',
            category,
            False,
            False,
            http_status,
            str(error_msg)[:500]
        ))
        
        self.db.commit()
    
    def process_message(self, service, msg_id, category, account_email):
        """Process a single email message"""
        try:
            # Get full message
            msg = service.users().messages().get(
                userId='me', 
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), None)
            
            # Skip non-forwarded emails (not from marcusgraetsch@gmail.com)
            if 'marcusgraetsch@gmail.com' not in sender.lower():
                logger.info(f"   ⏭️  Skipped (sender: {sender[:40]}...)")
                return 0
            
            # Get message body
            body = ''
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        data = part['body'].get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            break
                    elif part['mimeType'] == 'text/html' and not body:
                        import base64
                        data = part['body'].get('data', '')
                        if data:
                            html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            # Simple HTML to text
                            soup = BeautifulSoup(html, 'html.parser')
                            body = soup.get_text(separator=' ', strip=True)
            else:
                # Single part message
                import base64
                data = msg['payload']['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            # Extract links
            links = self.extract_links(body) + self.extract_links(subject)
            
            # Filter out non-article URLs
            skip_patterns = [
                'google.com', 'youtube.com', 'youtu.be', 'twitter.com', 'x.com',
                'facebook.com', 'fb.me', 'instagram.com', 'amazon.com',
                'linkedin.com', 't.me', 'wa.me', 'bit.ly', 'tinyurl',
                'unsubscribe', 'preferences', 'track', 'click.mail'
            ]
            
            filtered_links = []
            for url in links:
                url_lower = url.lower()
                if not any(pattern in url_lower for pattern in skip_patterns):
                    filtered_links.append(url)
            
            if not filtered_links:
                logger.info(f"   ℹ️  No article links found")
                return 0
            
            saved_count = 0
            for url in filtered_links:
                # Check if already saved
                if self.url_exists(url):
                    logger.info(f"   ⏭️  Already saved: {url[:60]}...")
                    continue
                
                logger.info(f"   🔗 Fetching: {url[:80]}...")
                content = self.fetch_article(url)
                
                if 'error' in content:
                    logger.warning(f"   ❌ Failed: {content['error']}")
                    self.insert_error(url, content['error'], account_email, date, subject, category, content.get('http_status'))
                else:
                    self.insert_article(url, content, account_email, date, subject, category)
                    saved_count += 1
                    logger.info(f"   ✅ Saved: {content['title'][:60]}...")
                
                time.sleep(1.5)  # Be nice to servers
            
            return saved_count
            
        except Exception as e:
            logger.error(f"   ❌ Error processing message {msg_id}: {e}")
            return 0
    
    def scan_account(self, account_type, account_email):
        """Scan all emails in an account with pagination"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📧 Starting: {account_type.upper()}")
        logger.info(f"{'='*60}")
        
        try:
            service = self.get_gmail_service(account_type)
        except Exception as e:
            logger.error(f"❌ Failed to authenticate {account_type}: {e}")
            return None
        
        # Get profile to verify account
        profile = service.users().getProfile(userId='me').execute()
        logger.info(f"✅ Connected: {profile['emailAddress']}")
        
        # Build query - only emails FROM marcusgraetsch@gmail.com
        query = 'from:marcusgraetsch@gmail.com'
        
        # Get total count first
        results = service.users().messages().list(userId='me', q=query).execute()
        total_messages = results.get('resultSizeEstimate', 0)
        logger.info(f"📨 Estimated messages: ~{total_messages}")
        
        processed = self.state[account_type].get('processed', 0)
        saved_total = self.state[account_type].get('saved', 0)
        page_token = None
        
        # If resuming, we need to skip to the right page
        last_id = self.state[account_type].get('last_id')
        
        while True:
            # Get batch of messages
            results = service.users().messages().list(
                userId='me', 
                q=query,
                pageToken=page_token,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                break
            
            for msg in messages:
                msg_id = msg['id']
                processed += 1
                
                # Resume logic: skip until we pass the last processed ID
                if last_id and msg_id == last_id:
                    last_id = None  # Found our place, continue normally
                    logger.info(f"[{processed}] 📍 Resume point found, continuing...")
                    continue
                elif last_id:
                    continue  # Still looking for resume point
                
                logger.info(f"\n[{processed}] Processing message {msg_id}...")
                count = self.process_message(service, msg_id, account_type, account_email)
                saved_total += count
                
                # Update state after each message
                self.state[account_type]['last_id'] = msg_id
                self.state[account_type]['processed'] = processed
                self.state[account_type]['saved'] = saved_total
                self.save_state()
                self.update_status_file(account_type, processed, saved_total, msg_id)
                
                # Progress log every 10 messages
                if processed % 10 == 0:
                    logger.info(f"📊 Progress: {processed} processed, {saved_total} articles saved")
                
                # Notification every 100 emails
                if processed % NOTIFY_EVERY == 0:
                    self.send_notification(account_type, processed, saved_total)
                    logger.info(f"📱 Notification queued: {processed} emails processed")
            
            # Get next page token
            page_token = results.get('nextPageToken')
            if not page_token:
                break
            
            # Save state between pages too
            self.save_state()
            logger.info(f"📄 Page complete. Total processed: {processed}, saved: {saved_total}")
            time.sleep(2)  # Delay between pages
        
        logger.info(f"\n✅ {account_type.upper()} complete")
        logger.info(f"   Processed: {processed}")
        logger.info(f"   Articles saved: {saved_total}")
        
        return {'processed': processed, 'saved': saved_total}
    
    def run(self):
        """Main entry point"""
        logger.info("\n" + "="*60)
        logger.info("🔐 Email Scanner v5 - FULL ARCHIVE SCAN")
        logger.info(f"🕐 Started: {datetime.now().isoformat()}")
        logger.info("="*60)
        
        # Ensure directories exist
        RESEARCH_DIR.mkdir(exist_ok=True)
        FULLTEXT_DIR.mkdir(exist_ok=True)
        
        results = {}
        
        for account_type, account_config in ACCOUNTS.items():
            account_email = account_config['email']
            results[account_type] = self.scan_account(account_type, account_email)
        
        # Final summary
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL SUMMARY")
        logger.info("="*60)
        
        total_processed = 0
        total_saved = 0
        
        for account, result in results.items():
            if result:
                logger.info(f"\n{account}:")
                logger.info(f"  Processed: {result['processed']}")
                logger.info(f"  Articles saved: {result['saved']}")
                total_processed += result['processed']
                total_saved += result['saved']
        
        logger.info(f"\n📈 TOTAL: {total_processed} emails, {total_saved} articles")
        logger.info(f"💾 Database: {DB_FILE}")
        logger.info(f"📝 Log: {LOG_FILE}")
        logger.info("✅ DONE")


if __name__ == '__main__':
    scanner = EmailScanner()
    scanner.run()
