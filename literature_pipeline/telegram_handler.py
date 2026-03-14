#!/usr/bin/env python3
"""
Telegram PDF Handler for Literature Pipeline

Dieses Modul integriert die Literature Pipeline mit Telegram.
Es ermöglicht das Senden von PDFs via Telegram, die dann automatisch
verarbeitet und zusammengefasst werden.

Unterstützte Publikationstypen:
    - monograph: Einzelwerk/Buch (ein Autor, ein Werk)
    - edited_volume: Sammelband (Herausgeber, mehrere Artikel)
    - journal_article: Zeitschriftenartikel (Journal, Issue, Pages)
    - web_article: Wissenschaftlicher Online-Artikel / Preprint

Workflow:
    1. PDF wird via Telegram empfangen
    2. Publikationstyp wird erkannt (aus Filename oder LLM)
    3. PDF wird typ-spezifisch in inbox/{type}/ gespeichert
    4. Pipeline wird gestartet mit Typ-spezifischer Verarbeitung
    5. Zusammenfassung wird generiert
    6. Ergebnis wird zurück an Telegram gesendet

Usage (internal):
    Wird automatisch von OpenClau aufgerufen wenn PDF via Telegram empfangen wird.
    Nicht für manuelle Ausführung gedacht.

Archive:
    PDFs werden nach Verarbeitung nach archive/{type}/ verschoben (für späteres RAG)
"""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Pipeline-Module importieren
from .db import get_connection, init_db, get_source_by_id
from .utils import setup_logging, logger


# Konstanten für Verzeichnisstruktur
PIPELINE_DIR = Path(__file__).parent
INBOX_DIR = PIPELINE_DIR / "inbox"
ARCHIVE_DIR = PIPELINE_DIR / "archive"
DB_PATH = PIPELINE_DIR / "literature.db"

# Publikationstypen
PUB_TYPES = ["monograph", "edited_volume", "journal_article", "web_article"]


def ensure_directories():
    """Stellt sicher, dass alle benötigten Verzeichnisse existieren (nach Typ)."""
    for pub_type in PUB_TYPES:
        (INBOX_DIR / pub_type).mkdir(parents=True, exist_ok=True)
        (ARCHIVE_DIR / pub_type).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Verzeichnisse geprüft für Typen: {', '.join(PUB_TYPES)}")


def detect_publication_type(filename: str, text_sample: str = None) -> str:
    """
    Erkennt den Publikationstyp aus Filename und/oder Text.
    
    Heuristiken:
        - "edited by", "hrsg.", "eds." -> edited_volume
        - "journal", "vol.", "issue", "pp." -> journal_article
        - "arxiv", "preprint", "doi.org" -> web_article
        - sonst -> monograph (Default)
    
    Args:
        filename: Original-Dateiname
        text_sample: Erste 2000 Zeichen des Texts (optional)
        
    Returns:
        str: Ein aus PUB_TYPES
    """
    filename_lower = filename.lower()
    text_lower = (text_sample or "").lower()
    combined = filename_lower + " " + text_lower
    
    # Heuristiken für edited_volume
    if any(marker in combined for marker in ["edited by", "hrsg.", "(eds)", "(ed.)", "sammelband", "beiträge"]):
        return "edited_volume"
    
    # Heuristiken für journal_article
    if any(marker in combined for marker in ["journal", "vol.", "issue", "pp.", "pages", "zeitschrift"]):
        return "journal_article"
    
    # Heuristiken für web_article / preprint
    if any(marker in combined for marker in ["arxiv", "preprint", "doi.org", "ssrn", "researchgate", "working paper"]):
        return "web_article"
    
    # Default: monograph
    return "monograph"


def save_pdf_from_telegram(pdf_data: bytes, filename: str, pub_type: str = None) -> tuple:
    """
    Speichert ein PDF aus Telegram in den typ-spezifischen inbox-Ordner.
    
    Args:
        pdf_data: Binäre PDF-Daten
        filename: Original-Dateiname
        pub_type: Publikationstyp (optional, wird sonst erkannt)
        
    Returns:
        tuple: (Path zum gespeicherten PDF, erkannter Typ)
    """
    # Timestamp hinzufügen um Kollisionen zu vermeiden
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Typ erkennen falls nicht angegeben
    if not pub_type:
        pub_type = detect_publication_type(filename)
    
    safe_filename = f"{timestamp}_{filename}"
    pdf_path = INBOX_DIR / pub_type / safe_filename
    pdf_path.write_bytes(pdf_data)
    
    logger.info(f"PDF gespeichert [{pub_type}]: {pdf_path} ({len(pdf_data)} bytes)")
    return pdf_path, pub_type


def run_pipeline_on_pdf(pdf_path: Path, pub_type: str) -> dict:
    """
    Führt die Literature Pipeline auf einem PDF aus.
    
    Args:
        pdf_path: Path zum PDF
        pub_type: Publikationstyp (monograph/edited_volume/journal_article/web_article)
        
    Returns:
        Dict mit Pipeline-Ergebnissen
    """
    logger.info(f"Starte Pipeline für: {pdf_path.name} [Typ: {pub_type}]")
    
    # Typ-spezifische Konfiguration
    type_config = {
        "monograph": {"extract_refs": True, "extract_knowledge": True, "note_template": "monograph"},
        "edited_volume": {"extract_refs": True, "extract_knowledge": True, "note_template": "edited_volume"},
        "journal_article": {"extract_refs": True, "extract_knowledge": True, "note_template": "article"},
        "web_article": {"extract_refs": False, "extract_knowledge": True, "note_template": "web_article"},
    }.get(pub_type, {})
    
    # Schritt 1: Ingest (Metadaten erfassen)
    logger.info("Schritt 1/4: Ingest...")
    result = subprocess.run([
        sys.executable, "-m", "literature_pipeline.ingest",
        "--file", str(pdf_path),
        "--title", pdf_path.stem,
        "--type", pub_type,  # Typ an Pipeline übergeben
    ], capture_output=True, text=True, cwd=PIPELINE_DIR.parent)
    
    if result.returncode != 0:
        logger.error(f"Ingest fehlgeschlagen: {result.stderr}")
        raise RuntimeError(f"Ingest fehlgeschlagen: {result.stderr}")
    
    # Source ID aus Output extrahieren oder aus DB holen
    source_id = get_latest_source_id()
    logger.info(f"Source ID: {source_id}")
    
    # Schritt 2: Text extrahieren
    logger.info("Schritt 2/4: Text extrahieren...")
    subprocess.run([
        sys.executable, "-m", "literature_pipeline.extract_text",
        "--source-id", str(source_id)
    ], check=True, cwd=PIPELINE_DIR.parent)
    
    # Schritt 3: Referenzen extrahieren (optional je nach Typ)
    if type_config.get("extract_refs", True):
        logger.info("Schritt 3/4: Referenzen extrahieren...")
        subprocess.run([
            sys.executable, "-m", "literature_pipeline.extract_refs",
            "--source-id", str(source_id)
        ], check=True, cwd=PIPELINE_DIR.parent)
    else:
        logger.info("Schritt 3/4: Referenzen übersprungen (web_article)")
    
    # Schritt 4: Knowledge Extraction (LLM)
    logger.info("Schritt 4/4: Knowledge Extraction...")
    subprocess.run([
        sys.executable, "-m", "literature_pipeline.extract_knowledge",
        "--source-id", str(source_id)
    ], check=True, cwd=PIPELINE_DIR.parent)
    
    logger.info("Pipeline abgeschlossen")
    return {"source_id": source_id, "pdf_path": pdf_path, "pub_type": pub_type}
    logger.info("Schritt 2/4: Text extrahieren...")
    subprocess.run([
        sys.executable, "-m", "literature_pipeline.extract_text",
        "--source-id", str(source_id)
    ], check=True, cwd=PIPELINE_DIR.parent)
    
    # Schritt 3: Referenzen extrahieren
    logger.info("Schritt 3/4: Referenzen extrahieren...")
    subprocess.run([
        sys.executable, "-m", "literature_pipeline.extract_refs",
        "--source-id", str(source_id)
    ], check=True, cwd=PIPELINE_DIR.parent)
    
    # Schritt 4: Knowledge Extraction (LLM)
    logger.info("Schritt 4/4: Knowledge Extraction...")
    subprocess.run([
        sys.executable, "-m", "literature_pipeline.extract_knowledge",
        "--source-id", str(source_id)
    ], check=True, cwd=PIPELINE_DIR.parent)
    
    logger.info("Pipeline abgeschlossen")
    return {"source_id": source_id, "pdf_path": pdf_path}


def get_latest_source_id() -> int:
    """Holt die zuletzt hinzugefügte Source ID aus der DB."""
    conn = get_connection()
    cursor = conn.execute("SELECT id FROM sources ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    raise RuntimeError("Keine Source in DB gefunden")


def generate_telegram_summary(source_id: int, pub_type: str) -> str:
    """
    Generiert eine Telegram-freundliche Zusammenfassung (typ-spezifisch).
    
    Format je nach Typ:
        Monograph: Titel + Autor + Verlag + Jahr + Key Findings
        Edited Volume: Titel + Herausgeber + Beiträge-Übersicht
        Journal Article: Titel + Autor + Journal + Issue + Pages + Abstract
        Web Article: Titel + Autor + URL/DOI + Abstract
        
    Args:
        source_id: ID in der Datenbank
        pub_type: Publikationstyp
    """
    conn = get_connection()
    
    # Source-Metadaten holen
    cursor = conn.execute(
        "SELECT title, authors, year, abstract, key_findings, publisher, journal, volume, issue, pages, url FROM sources WHERE id = ?",
        (source_id,)
    )
    source = cursor.fetchone()
    
    if not source:
        conn.close()
        return "❌ Fehler: Source nicht in Datenbank gefunden"
    
    title, authors, year, abstract, key_findings, publisher, journal, volume, issue, pages, url = source
    
    # Referenzen holen (max 3)
    cursor = conn.execute(
        "SELECT raw_ref, authors, title FROM refs WHERE source_id = ? LIMIT 3",
        (source_id,)
    )
    refs = cursor.fetchall()
    
    # BibTeX-Einträge holen (max 3)
    cursor = conn.execute(
        "SELECT bibtex_entry FROM refs WHERE source_id = ? AND bibtex_entry IS NOT NULL LIMIT 3",
        (source_id,)
    )
    bibtex_entries = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    # Telegram-Nachricht zusammenbauen (typ-spezifisch)
    lines = []
    
    # Header mit Typ-Emoji
    type_emoji = {
        "monograph": "📚",
        "edited_volume": "📖",
        "journal_article": "📄",
        "web_article": "🌐"
    }.get(pub_type, "📄")
    
    lines.append(f"{type_emoji} *{title}*")
    
    # Typ-spezifische Metadaten
    if pub_type == "monograph":
        lines.append(f"👤 {authors or 'Unbekannt'}")
        if publisher:
            lines.append(f"🏛 {publisher}")
        if year:
            lines.append(f"📅 {year}")
            
    elif pub_type == "edited_volume":
        lines.append(f"✏️ Herausgeber: {authors or 'Unbekannt'}")
        if year:
            lines.append(f"📅 {year}")
        lines.append("📑 Sammelband mit mehreren Beiträgen")
        
    elif pub_type == "journal_article":
        lines.append(f"👤 {authors or 'Unbekannt'}")
        journal_info = []
        if journal:
            journal_info.append(journal)
        if volume:
            journal_info.append(f"Vol. {volume}")
        if issue:
            journal_info.append(f"Issue {issue}")
        if pages:
            journal_info.append(f"pp. {pages}")
        if year:
            journal_info.append(str(year))
        if journal_info:
            lines.append(f"📰 {', '.join(journal_info)}")
            
    elif pub_type == "web_article":
        lines.append(f"👤 {authors or 'Unbekannt'}")
        if year:
            lines.append(f"📅 {year}")
        if url:
            lines.append(f"🔗 {url[:60]}...")
    
    lines.append("")
    
    # Zusammenfassung (für alle Typen)
    if key_findings:
        lines.append("📝 *Key Findings:*")
        lines.append(key_findings[:800] + "..." if len(key_findings) > 800 else key_findings)
    elif abstract:
        lines.append("📝 *Abstract:*")
        lines.append(abstract[:800] + "..." if len(abstract) > 800 else abstract)
    else:
        lines.append("📝 *Keine Zusammenfassung verfügbar*")
    
    lines.append("")
    
    # Beispiel-Referenzen (nur für Monograph und Edited Volume sinnvoll)
    if pub_type in ["monograph", "edited_volume"] and refs:
        lines.append("📚 *Beispiel-Referenzen:*")
        for i, (raw_ref, ref_authors, ref_title) in enumerate(refs, 1):
            ref_text = ref_title or raw_ref[:100]
            lines.append(f"{i}. {ref_text}")
        lines.append("")
    
    # BibTeX-Einträge
    if bibtex_entries:
        lines.append("📖 *BibTeX (erste 3):*")
        lines.append("```bibtex")
        for entry in bibtex_entries:
            lines.append(entry[:300] + "..." if len(entry) > 300 else entry)
            lines.append("")
        lines.append("```")
    
    return "\n".join(lines)


def archive_pdf(pdf_path: Path, source_id: int, pub_type: str) -> Path:
    """
    Archiviert das PDF für späteres RAG (typ-spezifisch).
    
    Args:
        pdf_path: Original-PDF-Path
        source_id: ID in der Datenbank
        pub_type: Publikationstyp
        
    Returns:
        Neuer Path im Archiv
    """
    # Neue Dateiname mit Source-ID und Typ für einfache Zuordnung
    new_name = f"{pub_type}_source_{source_id}_{pdf_path.name}"
    archive_path = ARCHIVE_DIR / pub_type / new_name
    
    shutil.move(str(pdf_path), str(archive_path))
    logger.info(f"PDF archiviert [{pub_type}]: {archive_path}")
    
    return archive_path


def process_pdf_from_telegram(pdf_data: bytes, filename: str, suggested_type: str = None) -> str:
    """
    Hauptfunktion: Verarbeitet ein PDF aus Telegram und gibt Summary zurück.
    
    Dies ist der Entry-Point der von OpenClau aufgerufen wird.
    
    Args:
        pdf_data: Binäre PDF-Daten aus Telegram
        filename: Original-Dateiname
        suggested_type: Optional vorgeschlagener Typ (monograph/edited_volume/journal_article/web_article)
        
    Returns:
        Telegram-formatierte Zusammenfassung
    """
    setup_logging()
    ensure_directories()
    init_db()
    
    try:
        # 1. PDF speichern und Typ erkennen
        pdf_path, pub_type = save_pdf_from_telegram(pdf_data, filename, suggested_type)
        
        # 2. Pipeline ausführen (typ-spezifisch)
        result = run_pipeline_on_pdf(pdf_path, pub_type)
        source_id = result["source_id"]
        
        # 3. Zusammenfassung generieren (typ-spezifisch)
        summary = generate_telegram_summary(source_id, pub_type)
        
        # 4. PDF archivieren (typ-spezifisch)
        archive_pdf(pdf_path, source_id, pub_type)
        
        # 5. Dashboard aktualisieren
        try:
            logger.info("Updating dashboard...")
            subprocess.run(
                ['python3', str(RESEARCH_DIR / '..' / 'update_dashboard.py')],
                check=True,
                timeout=30,
                cwd=RESEARCH_DIR
            )
            logger.info("Dashboard updated")
        except Exception as e:
            logger.warning(f"Dashboard update failed: {e}")
        
        # 6. Erfolgs-Indikator hinzufügen
        type_emoji = {
            "monograph": "📚",
            "edited_volume": "📖", 
            "journal_article": "📄",
            "web_article": "🌐"
        }.get(pub_type, "📄")
        
        summary = f"{type_emoji} *{pub_type.replace('_', ' ').title()}* verarbeitet\n\n{summary}"
        summary += f"\n\n💾 Archiviert: {pub_type}/source_{source_id}_..."
        
        return summary
        
    except Exception as e:
        logger.error(f"Fehler bei Verarbeitung: {e}")
        return f"❌ *Fehler bei Verarbeitung:*\n```\n{str(e)}\n```"


def main():
    """CLI-Entry-Point für manuelle Tests."""
    parser = argparse.ArgumentParser(
        description="Telegram Handler für Literature Pipeline"
    )
    parser.add_argument(
        "--test-file",
        type=Path,
        help="PDF-Datei für manuellen Test (nicht für Produktion)"
    )
    parser.add_argument(
        "--type",
        choices=PUB_TYPES,
        help=f"Publikationstyp ({', '.join(PUB_TYPES)}) - sonst automatische Erkennung"
    )
    
    args = parser.parse_args()
    
    if args.test_file:
        # Manueller Test-Modus
        setup_logging()
        pdf_data = args.test_file.read_bytes()
        result = process_pdf_from_telegram(pdf_data, args.test_file.name, args.type)
        print(result)
    else:
        parser.print_help()
        print("\nHinweis: Dieses Script wird normalerweise von OpenClau aufgerufen,")
        print("nicht manuell. Für manuelle Tests: --test-file path/to.pdf [--type monograph]")


if __name__ == "__main__":
    main()
