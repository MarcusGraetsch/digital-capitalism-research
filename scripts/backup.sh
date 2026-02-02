#!/bin/bash
# backup.sh - Disaster recovery backup script
# Run manually or via cron to create backups

set -e

DATE=$(date +%Y-%m-%d-%H%M)
BACKUP_DIR="/root/backups"
WORKSPACE="/root/.openclaw/workspace"

mkdir -p $BACKUP_DIR

echo "=== Digital Capitalism Research Backup ==="
echo "Date: $DATE"
echo ""

# 1. Ensure Git is up to date
echo "[1/4] Checking Git status..."
cd $WORKSPACE
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "Auto-backup before system backup: $DATE" || true
    echo "    Committed pending changes"
else
    echo "    No pending changes"
fi

# 2. Create workspace archive (excluding .git, node_modules)
echo "[2/4] Creating workspace archive..."
tar czf $BACKUP_DIR/workspace-$DATE.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.log' \
    -C $(dirname $WORKSPACE) \
    $(basename $WORKSPACE)
echo "    Created: workspace-$DATE.tar.gz"

# 3. Backup OpenClaw configuration
echo "[3/4] Backing up OpenClaw config..."
if [ -f /root/.openclaw/openclaw.json ]; then
    cp /root/.openclaw/openclaw.json $BACKUP_DIR/openclaw-config-$DATE.json
    echo "    Created: openclaw-config-$DATE.json"
else
    echo "    WARNING: openclaw.json not found"
fi

# 4. List installed packages/tools
echo "[4/4] Documenting system state..."
cat > $BACKUP_DIR/system-manifest-$DATE.txt << EOF
# System Manifest - $DATE
# Generated for disaster recovery

## Git Remote
$(cd $WORKSPACE && git remote -v 2>/dev/null || echo "No remote configured")

## OpenClaw Version
$(openclaw --version 2>/dev/null || echo "Unknown")

## Node Version
$(node --version 2>/dev/null || echo "Not installed")

## Python Version
$(python3 --version 2>/dev/null || echo "Not installed")

## Installed Packages (apt)
$(dpkg -l | grep -E 'ffmpeg|chromium|nodejs' 2>/dev/null || echo "Package list unavailable")

## Cron Jobs
$(crontab -l 2>/dev/null || echo "No crontab")

## Environment Variables (filtered)
$(env | grep -E 'BRAVE|API|KEY|TOKEN' 2>/dev/null | sed 's/=.*$/=***REDACTED***/' || echo "No API keys in env")
EOF
echo "    Created: system-manifest-$DATE.txt"

# Summary
echo ""
echo "=== Backup Complete ==="
echo "Location: $BACKUP_DIR"
echo "Files:"
ls -lh $BACKUP_DIR/*$DATE*
echo ""
echo "Next steps:"
echo "1. Copy these files to secure storage (S3, local machine, etc.)"
echo "2. Ensure Git remote is up to date: git push"
echo "3. Store SECRETS.md securely (contains API keys)"
