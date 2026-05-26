#!/bin/bash
# blogwatcher-digital-research.sh
# RSS-Feed Scanning für Digital Capitalism Research
# Wird täglich per Cron ausgeführt
#
# Feed-Liste:
# - Jacobin              — Linke Politik, USA
# - Rest of World        — Tech im Globalen Süden
# - Logic Magazine       — Tech-Kritik
# - AI Now Institute     — KI & Gesellschaft
# - Netzpolitik          — Digitalpolitik DE
# - Real Life Mag        — Kultur & Tech
# - LabourNet Germany    — Arbeitskämpfe DE
# - Nd                   — Sozialistische Zeitung DE

export PATH="$PATH:/root/go/bin"

RESEARCH_DIR="/root/.openclaw/workspace/projects/digital-research"
DIGEST_DIR="$RESEARCH_DIR/data/blogwatcher-digests"

cd "$RESEARCH_DIR" || exit 1

# Feeds scannen
echo "🔍 Scanne RSS-Feeds..."
blogwatcher scan

# Neue Artikel holen
ARTICLES=$(blogwatcher articles --unread 2>/dev/null)

if [ -n "$ARTICLES" ]; then
    TIMESTAMP=$(date +%Y-%m-%d)
    DIGEST_FILE="$DIGEST_DIR/digest-${TIMESTAMP}.md"
    mkdir -p "$DIGEST_DIR"
    
    cat > "$DIGEST_FILE" << EOF
# RSS Digest - ${TIMESTAMP}

## Neue Artikel

$ARTICLES

---
*Generiert via blogwatcher*
EOF
    
    echo "✅ Digest gespeichert: $DIGEST_FILE"
    echo "📰 Neue Artikel gefunden"
else
    echo "📭 Keine neuen Artikel"
fi