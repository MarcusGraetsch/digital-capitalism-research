#!/bin/bash
# digital-research-daily.sh
# Integrierter Daily Research Workflow für Digital Capitalism Research
#
# Nutzung:
#   ./digital-research-daily.sh           # Normaler Lauf
#   ./digital-research-daily.sh --dry-run # Test ohne Ausführung
#
# Cron: Täglich 08:30 (Europe/Berlin)
#   30 8 * * * /root/.openclaw/workspace/projects/digital-research/scripts/digital-research-daily.sh

set -euo pipefail

# --- Konfiguration ---
export PATH="$PATH:/root/go/bin"
RESEARCH_DIR="/root/.openclaw/workspace/projects/digital-research"
DATA_DIR="$RESEARCH_DIR/data"
LOG_DIR="$DATA_DIR/logs"
BLOGWATCHER_STATE="$DATA_DIR/blogwatcher-state.json"

# Symlinks im workspace/research für Legacy-Skripte
mkdir -p /root/.openclaw/workspace/research
ln -sf "$DATA_DIR/articles.db" /root/.openclaw/workspace/research/ 2>/dev/null || true
ln -sf "$DATA_DIR/fulltext" /root/.openclaw/workspace/research/ 2>/dev/null || true
ln -sf "$DATA_DIR/digests" /root/.openclaw/workspace/research/ 2>/dev/null || true

# Logging
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily-$(date +%Y-%m-%d).log"

log() {
    echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"
}

DRY_RUN=0
for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=1 ;;
    esac
done

log "=========================================="
log "📚 Digital Research Daily — $(date +%Y-%m-%d)"
log "=========================================="

if [[ $DRY_RUN -eq 1 ]]; then
    log "⚠️  DRY RUN — Keine Änderungen"
fi

# --- PHASE 1: Blogwatcher RSS Scan ---
log "🔍 Phase 1: RSS-Feed Scan (blogwatcher)"
cd "$RESEARCH_DIR"

# Scanne RSS-Feeds
blogwatcher scan >> "$LOG_FILE" 2>&1 || true

# Neue Artikel zählen
UNREAD=$(blogwatcher articles 2>/dev/null | grep -c "^\s*\[" || echo "0")
log "📰 $UNREAD ungelesene RSS-Artikel"

# Speichere State für spätere Integration
cat > "$BLOGWATCHER_STATE" << EOF
{
  "last_scan": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "unread_count": $UNREAD,
  "feeds": [
    "AI Now Institute",
    "Jacobin", 
    "LabourNet Germany",
    "Netzpolitik",
    "Real Life Mag",
    "Rest of World"
  ]
}
EOF

# --- PHASE 2: Quick Database Stats ---
log "📊 Phase 2: Datenbank-Status"
if [[ -f "$DATA_DIR/articles.db" ]]; then
    ARTICLE_COUNT=$(sqlite3 "$DATA_DIR/articles.db" "SELECT COUNT(*) FROM articles;" 2>/dev/null || echo "N/A")
    log "   Artikel in DB: $ARTICLE_COUNT"
else
    log "   ⚠️  Keine Artikel-DB gefunden"
fi

# --- PHASE 3: Blogwatcher Digest für heute ---
log "📝 Phase 3: RSS-Digest erstellen"
DIGEST_DIR="$DATA_DIR/blogwatcher-digests"
mkdir -p "$DIGEST_DIR"

ARTICLES=$(blogwatcher articles 2>/dev/null)
if [[ -n "$ARTICLES" && "$ARTICLES" != *"No unread articles"* ]]; then
    TIMESTAMP=$(date +%Y-%m-%d)
    DIGEST_FILE="$DIGEST_DIR/digest-${TIMESTAMP}.md"
    
    cat > "$DIGEST_FILE" << EOF
# RSS-Digest — ${TIMESTAMP}

## Ungelesene Artikel

$ARTICLES

---
*Generiert: $(date +%Y-%m-%d\ %H:%M:%S) via blogwatcher*
EOF
    log "   ✅ Digest gespeichert: $DIGEST_FILE"
else
    log "   📭 Keine neuen Artikel für Digest"
fi

# --- PHASE 4: Integration in Research-DB ---
log "⚙️  Phase 4: Integration (optionale DB-Sync)"

# Die blogwatcher-Artikel könnten in die Haupt-DB importiert werden
# Aktuell: Nur als separate Digest-Dateien gespeichert
# Später: Import-Skript das blogwatcher-Artikel in articles.db überführt

# --- Abschluss ---
DURATION=$(($(date +%s) - $(date -d "$(head -2 "$LOG_FILE" | tail -1 | cut -d'[' -f2 | cut -d']' -f1)" +%s 2>/dev/null || echo 0)))
log "✅ Tages-Scan abgeschlossen"
log "=========================================="

# Cron-Next-Info für Status
echo ""
echo "Nächster Lauf: Morgen 08:30 Berlin"