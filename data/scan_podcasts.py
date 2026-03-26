#!/usr/bin/env python3
"""
Podcast Scanner & Transcription Pipeline
Fetches new episodes from configured podcast RSS feeds,
downloads audio, transcribes with Whisper (API or local),
and generates keyword-tagged summaries.

Usage:
    python3 research/scan_podcasts.py                    # Full run
    python3 research/scan_podcasts.py --scan-only        # Just check for new episodes
    python3 research/scan_podcasts.py --transcribe-only  # Transcribe downloaded but untranscribed episodes
    python3 research/scan_podcasts.py --podcast "The Dig" # Process single podcast
"""

import os
import re
import json
import sqlite3
import hashlib
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from xml.etree import ElementTree
from email.utils import parsedate_to_datetime

RESEARCH_DIR = Path(os.environ.get('RESEARCH_DIR', '/root/.openclaw/workspace/research'))
REPO_ROOT = RESEARCH_DIR.parent
CONFIG_FILE = RESEARCH_DIR / 'podcast_config.json'
DB_FILE = RESEARCH_DIR / 'podcasts.db'
LOG_FILE = RESEARCH_DIR / 'scan_podcasts.log'
STATE_FILE = RESEARCH_DIR / 'podcast_state.json'
REQUEST_DELAY = 2.0


def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_FILE}")
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS episodes (
    id TEXT PRIMARY KEY,
    podcast_name TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    audio_url TEXT,
    pub_date TEXT,
    duration_seconds INTEGER,
    description TEXT,
    category TEXT,
    status TEXT DEFAULT 'new',
    audio_path TEXT,
    transcript_path TEXT,
    summary TEXT,
    keywords TEXT,
    word_count INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def episode_exists(url):
    conn = get_connection()
    try:
        row = conn.execute('SELECT id FROM episodes WHERE url = ?', (url,)).fetchone()
        return row is not None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# RSS Parsing
# ---------------------------------------------------------------------------

def parse_podcast_feed(feed_url):
    """Parse a podcast RSS feed, extracting episodes with audio enclosures."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)',
            'Accept': 'application/rss+xml, application/xml, text/xml',
        }
        resp = requests.get(feed_url, headers=headers, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            return [], f"HTTP {resp.status_code}"

        root = ElementTree.fromstring(resp.content)
        episodes = []

        # iTunes namespace for duration
        ns = {
            'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
            'media': 'http://search.yahoo.com/mrss/',
        }

        for item in root.iter('item'):
            episode = _parse_episode(item, ns)
            if episode:
                episodes.append(episode)

        return episodes, None

    except ElementTree.ParseError as e:
        return [], f"XML parse error: {e}"
    except requests.RequestException as e:
        return [], f"Request failed: {e}"
    except Exception as e:
        return [], str(e)


def _parse_episode(item, ns):
    """Parse a single RSS item into an episode dict."""
    # Get audio enclosure
    enclosure = item.find('enclosure')
    if enclosure is None:
        return None

    audio_url = enclosure.get('url', '').strip()
    if not audio_url:
        return None

    audio_type = enclosure.get('type', '')
    if audio_type and 'audio' not in audio_type:
        return None

    # Episode URL (link or guid)
    link = _get_text(item, 'link') or _get_text(item, 'guid') or audio_url
    title = _get_text(item, 'title') or 'Untitled'

    # Publication date
    pub_date_str = _get_text(item, 'pubDate')
    pub_date = None
    if pub_date_str:
        try:
            pub_date = parsedate_to_datetime(pub_date_str)
        except Exception:
            pub_date = None

    # Duration
    duration = _parse_duration(item, ns)

    # Description
    description = _get_text(item, 'description') or ''
    # Strip HTML tags from description
    description = re.sub(r'<[^>]+>', '', description).strip()
    if len(description) > 1000:
        description = description[:1000] + '...'

    return {
        'url': link.strip(),
        'audio_url': audio_url,
        'title': title,
        'pub_date': pub_date.isoformat() if pub_date else None,
        'pub_date_dt': pub_date,
        'duration_seconds': duration,
        'description': description,
    }


def _parse_duration(item, ns):
    """Parse iTunes duration (HH:MM:SS, MM:SS, or seconds)."""
    dur_el = item.find('itunes:duration', ns)
    if dur_el is None or not dur_el.text:
        return None

    dur = dur_el.text.strip()
    if ':' in dur:
        parts = dur.split(':')
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            return None
    else:
        try:
            return int(dur)
        except ValueError:
            return None


def _get_text(element, tag):
    el = element.find(tag)
    return el.text.strip() if el is not None and el.text else None


# ---------------------------------------------------------------------------
# Audio Download
# ---------------------------------------------------------------------------

def download_audio(audio_url, output_path):
    """Download audio file from URL."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and output_path.stat().st_size > 0:
        log(f"   Audio already downloaded: {output_path.name}")
        return True

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'}
        resp = requests.get(audio_url, headers=headers, timeout=600, stream=True)
        if resp.status_code != 200:
            log(f"   Download failed: HTTP {resp.status_code}")
            return False

        total = int(resp.headers.get('content-length', 0))
        downloaded = 0

        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)

        size_mb = downloaded / (1024 * 1024)
        log(f"   Downloaded: {output_path.name} ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        log(f"   Download error: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe_episode(audio_path, output_path, config):
    """Transcribe audio file using Whisper (API or local)."""
    output_path = Path(output_path)
    if output_path.exists() and output_path.stat().st_size > 0:
        log(f"   Transcript already exists: {output_path.name}")
        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read()

    backend = config.get('settings', {}).get('transcription_backend', 'openai-api')

    if backend == 'openai-api':
        return _transcribe_openai_api(audio_path, output_path, config)
    elif backend == 'local':
        return _transcribe_local_whisper(audio_path, output_path, config)
    else:
        log(f"   Unknown transcription backend: {backend}")
        return None


def _transcribe_openai_api(audio_path, output_path, config):
    """Transcribe using OpenAI Whisper API."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        log("   OPENAI_API_KEY not set, skipping transcription")
        return None

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        audio_path = Path(audio_path)
        file_size = audio_path.stat().st_size
        max_size = 25 * 1024 * 1024  # 25MB API limit

        if file_size > max_size:
            log(f"   File too large for API ({file_size / 1024 / 1024:.0f} MB > 25 MB), splitting...")
            return _transcribe_chunked(audio_path, output_path, client, config)

        language = config.get('settings', {}).get('whisper_language', 'en')

        with open(audio_path, 'rb') as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
                response_format="text",
            )

        transcript = result if isinstance(result, str) else str(result)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript)

        word_count = len(transcript.split())
        log(f"   Transcribed: {word_count} words")
        return transcript

    except Exception as e:
        log(f"   Transcription error: {e}")
        return None


def _transcribe_chunked(audio_path, output_path, client, config):
    """Split large audio and transcribe in chunks using pydub."""
    try:
        from pydub import AudioSegment
    except ImportError:
        log("   pydub not installed, cannot split audio. pip install pydub")
        return None

    try:
        audio = AudioSegment.from_file(str(audio_path))
        chunk_length_ms = 10 * 60 * 1000  # 10 minutes per chunk
        chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

        language = config.get('settings', {}).get('whisper_language', 'en')
        full_transcript = []

        for i, chunk in enumerate(chunks):
            log(f"   Transcribing chunk {i + 1}/{len(chunks)}...")
            chunk_path = audio_path.parent / f"_chunk_{i}.mp3"
            chunk.export(str(chunk_path), format="mp3")

            try:
                with open(chunk_path, 'rb') as f:
                    result = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        language=language,
                        response_format="text",
                    )
                full_transcript.append(result if isinstance(result, str) else str(result))
            finally:
                chunk_path.unlink(missing_ok=True)

            time.sleep(1)  # Rate limit

        transcript = '\n\n'.join(full_transcript)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript)

        word_count = len(transcript.split())
        log(f"   Transcribed: {word_count} words ({len(chunks)} chunks)")
        return transcript

    except Exception as e:
        log(f"   Chunked transcription error: {e}")
        return None


def _transcribe_local_whisper(audio_path, output_path, config):
    """Transcribe using local whisper CLI."""
    import subprocess

    model = config.get('settings', {}).get('whisper_model', 'base')
    language = config.get('settings', {}).get('whisper_language', 'en')

    try:
        result = subprocess.run(
            ['whisper', str(audio_path),
             '--model', model,
             '--language', language,
             '--output_format', 'txt',
             '--output_dir', str(output_path.parent)],
            capture_output=True, text=True, timeout=3600
        )

        if result.returncode != 0:
            log(f"   Whisper CLI failed: {result.stderr[:200]}")
            return None

        # Whisper outputs as <filename>.txt
        whisper_out = output_path.parent / (Path(audio_path).stem + '.txt')
        if whisper_out.exists():
            whisper_out.rename(output_path)
            with open(output_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            log(f"   Transcribed: {len(transcript.split())} words")
            return transcript

        return None

    except FileNotFoundError:
        log("   whisper CLI not installed")
        return None
    except Exception as e:
        log(f"   Local transcription error: {e}")
        return None


# ---------------------------------------------------------------------------
# Summarization
# ---------------------------------------------------------------------------

def summarize_transcript(transcript, episode_title, config):
    """Generate a summary and keywords from transcript using Claude."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        log("   ANTHROPIC_API_KEY not set, skipping summarization")
        return None, None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Truncate very long transcripts
        max_chars = 80000
        text = transcript[:max_chars] if len(transcript) > max_chars else transcript

        prompt = f"""Summarize this podcast episode transcript for a researcher studying digital capitalism, platform labor, and political economy.

Episode title: {episode_title}

Provide:
1. A concise summary (3-5 paragraphs) covering the main arguments and key points
2. A list of 5-10 keywords/topics relevant to: digital capitalism, platform economy, labor, surveillance, AI, monopoly power, political economy
3. Notable quotes: 3-8 verbatim quotes from speakers that are especially quotable — sharp formulations, provocative claims, key definitions, or memorable lines. Include who said it if identifiable.
4. Key excerpts: 2-5 paraphrased distillations of the most important ideas or arguments made (in your own words, not verbatim).
5. Mentioned persons: scholars, thinkers, executives, politicians, or other named individuals discussed during the episode. Include name, how they're mentioned (discussion/critique/agreement/name_drop), and significance (major/moderate/minor).
6. Mentioned works: books, articles, reports, or studies explicitly referenced during the episode. Include title, authors if mentioned, and significance.

Format your response as JSON:
{{
  "summary": "...",
  "keywords": ["keyword1", "keyword2", ...],
  "quotes": [{{"text": "exact verbatim quote", "speaker": "name or Unknown", "quote_type": "core_concept|polemic|critique|definition|aphorism|empirical"}}],
  "excerpts": [{{"content": "paraphrased idea summary", "concept": "which concept this relates to"}}],
  "mentioned_persons": [{{"name": "full name", "mention_type": "discussion|critique|agreement|name_drop", "significance": "major|moderate|minor"}}],
  "mentioned_works": [{{"title": "...", "authors": [...], "year": null, "mention_type": "citation|discussion|data_source", "significance": "major|moderate|minor"}}]
}}

Transcript:
{text}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        # Strip markdown fences if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        data = json.loads(response_text)
        return (
            data.get('summary', ''),
            data.get('keywords', []),
            data.get('quotes', []),
            data.get('excerpts', []),
            data.get('mentioned_persons', []),
            data.get('mentioned_works', []),
        )

    except Exception as e:
        log(f"   Summarization error: {e}")
        return None, None, [], [], [], []


# ---------------------------------------------------------------------------
# Quote Storage (writes to literature_pipeline's quotes table)
# ---------------------------------------------------------------------------

def store_podcast_mentions(episode, mentioned_persons, mentioned_works):
    """Store extracted person/work mentions from podcast in discourse tables."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from literature_pipeline.db import (
            get_connection as get_lit_conn, init_db as init_lit_db,
            get_or_create_person, get_or_create_work, insert_mention,
        )

        init_lit_db()
        conn = get_lit_conn()
        stored = 0

        for item in mentioned_persons:
            name = item.get('name', '').strip()
            if not name:
                continue
            try:
                person_id = get_or_create_person(conn, name)
                insert_mention(
                    conn,
                    episode_id=episode.get('id', ''),
                    mentioned_person_id=person_id,
                    mention_type=item.get('mention_type', 'discussion'),
                    significance=item.get('significance', 'minor'),
                    extraction_method='llm',
                    confidence=0.6,
                )
                stored += 1
            except Exception:
                pass

        for item in mentioned_works:
            title = item.get('title', '').strip()
            if not title:
                continue
            try:
                work_id = get_or_create_work(
                    conn, title,
                    authors=item.get('authors'),
                    year=item.get('year'),
                )
                insert_mention(
                    conn,
                    episode_id=episode.get('id', ''),
                    mentioned_work_id=work_id,
                    mention_type=item.get('mention_type', 'citation'),
                    significance=item.get('significance', 'minor'),
                    extraction_method='llm',
                    confidence=0.6,
                )
                stored += 1
            except Exception:
                pass

        conn.close()
        if stored:
            log(f"   Stored {stored} discourse mentions")

    except ImportError:
        log("   literature_pipeline not available, skipping mention storage")
    except Exception as e:
        log(f"   Mention storage error: {e}")


def store_podcast_quotes(episode, quotes, excerpts, keywords):
    """Store extracted quotes and excerpts in the shared quotes DB."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from literature_pipeline.db import get_connection as get_lit_conn, init_db as init_lit_db
        from literature_pipeline.db import insert_quote, quote_exists

        init_lit_db()
        conn = get_lit_conn()
        stored = 0

        for q in quotes:
            text = q.get('text', '').strip()
            if not text:
                continue
            speaker = q.get('speaker', 'Unknown')
            if not quote_exists(conn, text, speaker):
                insert_quote(
                    conn,
                    text=text,
                    author=speaker,
                    source_title=f"{episode.get('podcast_name', '')}: {episode.get('title', '')}",
                    language='en',
                    entry_type='quote',
                    quote_type=q.get('quote_type', 'core_concept'),
                    topics=keywords,
                    context=episode.get('title', ''),
                    found_via='podcast',
                    episode_id=episode.get('id', ''),
                )
                stored += 1

        for ex in excerpts:
            content = ex.get('content', '').strip()
            if not content:
                continue
            if not quote_exists(conn, content):
                insert_quote(
                    conn,
                    text=content,
                    author=episode.get('podcast_name', ''),
                    source_title=episode.get('title', ''),
                    language='en',
                    entry_type='excerpt',
                    quote_type='core_concept',
                    topics=keywords,
                    context=ex.get('concept', ''),
                    found_via='podcast',
                    episode_id=episode.get('id', ''),
                )
                stored += 1

        conn.close()
        if stored:
            log(f"   Stored {stored} quotes/excerpts")

    except ImportError:
        log("   literature_pipeline not available, skipping quote storage")
    except Exception as e:
        log(f"   Quote storage error: {e}")


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def generate_episode_id(url):
    return hashlib.md5(url.encode()).hexdigest()


def format_duration(seconds):
    if not seconds:
        return "unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m"


def save_episode_markdown(episode, transcript, summary, keywords, output_dir):
    """Save episode as a research-ready markdown file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_title = re.sub(r'[^\w\s-]', '', episode['title'])[:60].strip()
    safe_title = re.sub(r'\s+', '-', safe_title).lower()
    date_prefix = ''
    if episode.get('pub_date'):
        date_prefix = episode['pub_date'][:10] + '_'

    filename = f"{date_prefix}{safe_title}.md"
    filepath = output_dir / filename

    keyword_str = ', '.join(keywords) if keywords else ''

    content = f"""---
title: "{episode['title']}"
podcast: {episode['podcast_name']}
date: {episode.get('pub_date', 'unknown')}
duration: {format_duration(episode.get('duration_seconds'))}
category: {episode.get('category', '')}
keywords: [{keyword_str}]
audio_url: {episode.get('audio_url', '')}
url: {episode.get('url', '')}
---

# {episode['title']}

**Podcast:** {episode['podcast_name']}
**Date:** {episode.get('pub_date', 'unknown')}
**Duration:** {format_duration(episode.get('duration_seconds'))}

## Summary

{summary or 'No summary available.'}

## Keywords

{', '.join(keywords) if keywords else 'None extracted.'}

## Transcript

{transcript or 'No transcript available.'}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(filepath)


def process_podcast(podcast, config, scan_only=False, transcribe_only=False):
    """Process a single podcast: scan feed, download, transcribe, summarize."""
    settings = config.get('settings', {})
    max_age = settings.get('max_age_days', 14)
    max_episodes = settings.get('max_episodes_per_feed', 3)
    output_base = Path(REPO_ROOT) / settings.get('output_dir', 'research/podcasts')
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age)

    name = podcast['name']
    feed_url = podcast['feed_url']
    category = podcast.get('category', '')

    stats = {'found': 0, 'new': 0, 'downloaded': 0, 'transcribed': 0, 'summarized': 0}

    if not transcribe_only:
        log(f"\n🎙️  {name}")
        episodes, error = parse_podcast_feed(feed_url)
        if error:
            log(f"   Feed error: {error}")
            return stats

        # Filter by age
        recent = []
        for ep in episodes:
            if ep.get('pub_date_dt'):
                pub_dt = ep['pub_date_dt']
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                if pub_dt >= cutoff:
                    recent.append(ep)
            else:
                recent.append(ep)  # Include episodes without dates

        stats['found'] = len(recent)
        log(f"   {len(recent)} recent episodes (last {max_age} days)")

        # Limit per feed
        recent = recent[:max_episodes]

        conn = get_connection()
        try:
            for ep in recent:
                if episode_exists(ep['url']):
                    continue

                stats['new'] += 1
                episode_id = generate_episode_id(ep['url'])

                conn.execute('''
                    INSERT OR IGNORE INTO episodes
                    (id, podcast_name, title, url, audio_url, pub_date,
                     duration_seconds, description, category, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
                ''', (
                    episode_id, name, ep['title'], ep['url'],
                    ep['audio_url'], ep.get('pub_date'),
                    ep.get('duration_seconds'), ep.get('description', ''),
                    category,
                ))
                conn.commit()
                log(f"   New: {ep['title'][:60]}")
        finally:
            conn.close()

    if scan_only:
        return stats

    # Download and transcribe new/downloaded episodes
    conn = get_connection()
    try:
        if transcribe_only:
            rows = conn.execute(
                "SELECT * FROM episodes WHERE podcast_name = ? AND status = 'downloaded'",
                (name,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM episodes WHERE podcast_name = ? AND status IN ('new', 'downloaded')",
                (name,)
            ).fetchall()
    finally:
        conn.close()

    for row in rows:
        episode = dict(row)
        episode_id = episode['id']

        # Date-based output directory
        pub_date = episode.get('pub_date', '')
        month_dir = pub_date[:7] if pub_date else datetime.now().strftime('%Y-%m')
        ep_output_dir = output_base / month_dir

        # Download
        if episode['status'] == 'new' and episode.get('audio_url'):
            safe_name = re.sub(r'[^\w\s-]', '', episode['title'])[:50].strip()
            safe_name = re.sub(r'\s+', '-', safe_name).lower()
            audio_ext = '.mp3'
            audio_filename = f"{pub_date[:10]}_{safe_name}{audio_ext}" if pub_date else f"{safe_name}{audio_ext}"
            audio_path = ep_output_dir / 'audio' / audio_filename

            if download_audio(episode['audio_url'], audio_path):
                stats['downloaded'] += 1
                conn = get_connection()
                try:
                    conn.execute(
                        "UPDATE episodes SET status = 'downloaded', audio_path = ?, updated_at = datetime('now') WHERE id = ?",
                        (str(audio_path), episode_id)
                    )
                    conn.commit()
                finally:
                    conn.close()
                episode['audio_path'] = str(audio_path)
                episode['status'] = 'downloaded'

        # Transcribe
        if episode['status'] == 'downloaded' and episode.get('audio_path'):
            audio_p = Path(episode['audio_path'])
            transcript_path = ep_output_dir / (audio_p.stem + '.md')

            transcript = transcribe_episode(audio_p, transcript_path, config)
            if transcript:
                stats['transcribed'] += 1
                word_count = len(transcript.split())

                # Summarize
                summary, keywords, quotes_data, excerpts_data = None, None, [], []
                persons_data, works_data = [], []
                if settings.get('summarize', True):
                    summary, keywords, quotes_data, excerpts_data, persons_data, works_data = summarize_transcript(transcript, episode['title'], config)
                    if summary:
                        stats['summarized'] += 1
                    # Store quotes/excerpts in shared DB
                    if quotes_data or excerpts_data:
                        store_podcast_quotes(episode, quotes_data, excerpts_data, keywords or [])
                    # Store discourse mentions
                    if persons_data or works_data:
                        store_podcast_mentions(episode, persons_data, works_data)

                # Save research markdown
                md_path = save_episode_markdown(
                    episode, transcript, summary, keywords or [], ep_output_dir
                )

                conn = get_connection()
                try:
                    conn.execute('''
                        UPDATE episodes SET
                            status = 'complete',
                            transcript_path = ?,
                            summary = ?,
                            keywords = ?,
                            word_count = ?,
                            updated_at = datetime('now')
                        WHERE id = ?
                    ''', (
                        md_path,
                        summary,
                        json.dumps(keywords) if keywords else None,
                        word_count,
                        episode_id,
                    ))
                    conn.commit()
                finally:
                    conn.close()

                # Clean up audio to save disk space
                if audio_p.exists():
                    audio_p.unlink()
                    log(f"   Cleaned up audio: {audio_p.name}")

    return stats


def main():
    parser = argparse.ArgumentParser(description='Podcast Scanner & Transcription Pipeline')
    parser.add_argument('--scan-only', action='store_true', help='Only scan for new episodes')
    parser.add_argument('--transcribe-only', action='store_true', help='Only transcribe downloaded episodes')
    parser.add_argument('--podcast', type=str, help='Process a single podcast by name')
    args = parser.parse_args()

    log("=" * 70)
    log("🎙️  Podcast Scanner & Transcription Pipeline")
    log("=" * 70)

    config = load_config()
    init_db()

    podcasts = config.get('podcasts', [])
    if args.podcast:
        podcasts = [p for p in podcasts if p['name'].lower() == args.podcast.lower()]
        if not podcasts:
            log(f"Podcast not found: {args.podcast}")
            return

    log(f"📋 {len(podcasts)} podcasts configured")

    totals = {'found': 0, 'new': 0, 'downloaded': 0, 'transcribed': 0, 'summarized': 0}

    for podcast in podcasts:
        stats = process_podcast(
            podcast, config,
            scan_only=args.scan_only,
            transcribe_only=args.transcribe_only,
        )
        for k in totals:
            totals[k] += stats.get(k, 0)
        time.sleep(REQUEST_DELAY)

    # Update state
    state = load_state()
    state['last_run'] = datetime.now().isoformat()
    state['last_stats'] = totals
    save_state(state)

    log("\n" + "=" * 70)
    log("📊 PODCAST SCAN SUMMARY")
    log("=" * 70)
    log(f"Episodes found:      {totals['found']}")
    log(f"New episodes:        {totals['new']}")
    log(f"Downloaded:          {totals['downloaded']}")
    log(f"Transcribed:         {totals['transcribed']}")
    log(f"Summarized:          {totals['summarized']}")

    # DB stats
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT status, COUNT(*) FROM episodes GROUP BY status'
        ).fetchall()
        if rows:
            log("\nDatabase status:")
            for status, count in rows:
                log(f"  {status}: {count}")
    finally:
        conn.close()

    log(f"\n✅ Done! Log: {LOG_FILE}")


if __name__ == '__main__':
    main()
