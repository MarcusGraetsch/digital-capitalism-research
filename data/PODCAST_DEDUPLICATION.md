# Podcast Pipeline - Deduplication System

## Problem
Aktuell trackt `podcast_state.json` nur:
- "downloaded: 11" 
- Aber nicht WELCHE 11 Episoden

Beim nächsten Scan werden alle 11 erneut heruntergeladen!

## Lösung: Eindeutige Episode-ID

Jede Episode bekommt eine ID basierend auf:
- Podcast Name + Episode Titel + Publish Date
- Oder: RSS GUID (wenn vorhanden)
- Oder: Hash der Audio-URL

## Datenbank-Schema (vorgeschlagen)

```sql
CREATE TABLE episodes (
    id TEXT PRIMARY KEY,           -- Eindeutige ID (z.B. hash)
    podcast_name TEXT,             -- Podcast Name
    episode_title TEXT,            -- Episode Titel
    publish_date TEXT,             -- Veröffentlichungsdatum
    audio_url TEXT,                -- Audio URL
    
    -- Status Tracking
    status TEXT,                   -- 'new' | 'downloaded' | 'transcribed' | 'summarized' | 'error'
    
    -- Dateien
    audio_file TEXT,               -- Lokaler Pfad zur MP3
    transcript_file TEXT,          -- Pfad zur Transkription
    summary_file TEXT,             -- Pfad zur Zusammenfassung
    
    -- Metadaten
    duration_seconds INTEGER,      -- Länge in Sekunden
    file_size_mb REAL,             -- Dateigröße
    
    -- Tracking
    first_seen TEXT,               -- Wann erstmalig gefunden
    downloaded_at TEXT,            -- Wann heruntergeladen
    transcribed_at TEXT,           -- Wann transkribiert
    
    -- Inhalt (nach Verarbeitung)
    summary TEXT,                  -- Zusammenfassung
    keywords TEXT,                 -- Komma-getrennte Keywords
    concepts TEXT                  -- JSON Array der erkannten Konzepte
);

-- Indexe für schnelle Abfragen
CREATE INDEX idx_status ON episodes(status);
CREATE INDEX idx_podcast ON episodes(podcast_name);
CREATE INDEX idx_date ON episodes(publish_date);
```

## Workflow

### 1. Scan (RSS Feed)
```python
for episode in rss_feed:
    episode_id = hash(podcast_name + episode.title + episode.pub_date)
    
    # Prüfe ob bereits bekannt
    if db.exists(episode_id):
        continue  # Überspringen
    
    # Neue Episode
    db.insert({
        'id': episode_id,
        'status': 'new',
        'first_seen': now(),
        ...
    })
```

### 2. Download
```python
for episode in db.where(status='new'):
    download_audio(episode.audio_url)
    db.update(episode.id, {
        'status': 'downloaded',
        'audio_file': path,
        'downloaded_at': now()
    })
```

### 3. Transkription
```python
for episode in db.where(status='downloaded'):
    transcript = whisper.transcribe(episode.audio_file)
    db.update(episode.id, {
        'status': 'transcribed',
        'transcript_file': path,
        'transcribed_at': now()
    })
```

### 4. Summary
```python
for episode in db.where(status='transcribed'):
    summary = llm.summarize(episode.transcript_file)
    db.update(episode.id, {
        'status': 'summarized',
        'summary': summary.text,
        'keywords': summary.keywords,
        'concepts': summary.concepts
    })
```

## Vorteile

1. **Keine Duplikate** - Jede Episode nur einmal verarbeitet
2. **Resumable** - Bei Abbruch einfach neu starten
3. **Transparenz** - Genauer Status jeder Episode
4. **Skalierbar** - Einfache Abfragen: "Alle Episoden zu Venture Capital"

## Nächster Schritt

Soll ich:
- A) `scan_podcasts.py` erweitern mit Pro-Episode Tracking?
- B) Neue Datenbank anlegen mit korrektem Schema?
- C) Erst die 11 bereits geladenen Episoden manuell in DB eintragen?

Was bevorzugst du?
