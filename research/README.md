# Research Pipeline - Email to Labeled Articles

Complete workflow for collecting, cleaning, and labeling articles from email digests.

## Overview

This pipeline processes emails from 3 Gmail accounts, extracts article links, scrapes content, cleans noise, and labels topics.

## Accounts Monitored

- **bigtech** → b1gt3ch.5n5lysis@critical-theory.digital
- **newwork** → newworkculture.twentyone@critical-theory.digital  
- **aigen** → aichitchatter@critical-theory.digital

## Workflow Steps

### 1. Scan Emails (`scan_v5.py`)
- Scans ALL emails (not just first 100)
- Resumable - continues where it left off
- Extracts links from forwarded emails
- Fetches article content with paywall detection
- Stores in SQLite DB + Markdown files

Run: `python3 scan_v5.py`

### 2. Clean Articles (`clean_smart.py`)
- Removes navigation, ads, cookie banners
- Detects paywall-only previews
- Marks paywall articles for later re-scraping
- Saves cleaned content back to files

Run: `python3 clean_smart.py`

### 3. Label Articles (`label_articles.py`)
- Tags articles with topics (KI, Arbeitswelt, Big Tech, etc.)
- Assigns sentiment (kritisch/neutral/positiv)
- Sets type (Studie/Meinung/News/Interview/Analyse)
- Sets priority (high/medium/low)

Run: `python3 label_articles.py`

### 4. Weekly Pipeline (`weekly_pipeline.py`)
- Runs all 3 steps in sequence
- Designed for weekly cron execution
- Logs progress and statistics

Run: `python3 weekly_pipeline.py`

## Cron Setup

Weekly run (Sundays 08:00):
```
0 8 * * 0 cd /root/.openclaw/workspace/research && python3 weekly_pipeline.py >> cron.log 2>&1
```

## Database Schema

Articles stored in `articles.db` with fields:
- `id` - MD5 hash of URL
- `url`, `domain`, `title` - Article metadata
- `content_status` - saved/cleaned/labeled/paywall_only/error
- `category` - Email account (bigtech/newwork/aigen)
- `tags` - Comma-separated topics
- `paywall` - Boolean
- `fulltext_path` - Path to markdown file
- `abstract` - First 500 chars of cleaned text
- `word_count` - Article length

## Directory Structure

```
research/
├── articles.db              # SQLite database
├── fulltext/               # Markdown article files
│   └── 2026-03/
│       └── [hash]_[domain].md
├── scan_v5.py              # Email scanner
├── clean_smart.py          # Content cleaner
├── label_articles.py       # Topic labeler
├── weekly_pipeline.py      # Complete workflow
├── scan_state_v5.json      # Resume state
├── scan_v5.log            # Scanner log
└── llm_cleaning.log       # Cleaning log
```

## Current Statistics

- **Total articles collected:** 1,831 emails processed
- **Articles cleaned & labeled:** 697
- **Paywall previews (for later):** 29
- **Errors/blocked:** ~160

## Future Improvements

- [ ] Re-scrape paywall articles after subscription
- [ ] Add LLM-based summarization for abstracts
- [ ] Create RSS output for Obsidian/Dendron
- [ ] Add full-text search index

## Requirements

```
pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests beautifulsoup4
```

## Authentication

OAuth tokens stored in:
- `/root/.openclaw/.env.d/gmail-token-*.json`

Run `scan_v5.py` once manually to authenticate if tokens are missing.
