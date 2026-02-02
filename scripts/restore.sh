#!/bin/bash
# restore.sh - Disaster recovery restore script
# Run this on a fresh VPS to rebuild the environment

set -e

BACKUP_DIR="/root/backups"
WORKSPACE="/root/.openclaw/workspace"

echo "=== Digital Capitalism Research Restore ==="
echo "This script will restore the research environment"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# 1. Update system
echo "[1/8] Updating system packages..."
apt-get update && apt-get upgrade -y

# 2. Install dependencies
echo "[2/8] Installing dependencies..."
apt-get install -y \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    ffmpeg \
    build-essential \
    software-properties-common

# 3. Install Node.js (LTS)
echo "[3/8] Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
fi
echo "    Node version: $(node --version)"

# 4. Install OpenClaw
echo "[4/8] Installing OpenClaw..."
npm install -g openclaw
echo "    OpenClaw version: $(openclaw --version)"

# 5. Clone repository
echo "[5/8] Cloning research repository..."
if [ -d "$WORKSPACE" ]; then
    echo "    WARNING: Workspace exists, backing up to $WORKSPACE.backup"
    mv $WORKSPACE $WORKSPACE.backup.$(date +%s)
fi

# Prompt for GitHub repo URL
read -p "Enter GitHub repository URL (e.g., https://github.com/username/repo.git): " REPO_URL
git clone $REPO_URL $WORKSPACE
cd $WORKSPACE

# 6. Restore OpenClaw config (if backup available)
echo "[6/8] Restoring OpenClaw configuration..."
if [ -f "$BACKUP_DIR/openclaw-config-*.json" ]; then
    LATEST_CONFIG=$(ls -t $BACKUP_DIR/openclaw-config-*.json | head -1)
    mkdir -p /root/.openclaw
    cp $LATEST_CONFIG /root/.openclaw/openclaw.json
    echo "    Restored: $LATEST_CONFIG"
else
    echo "    WARNING: No OpenClaw config backup found"
    echo "    You will need to reconfigure manually"
fi

# 7. Install Whisper (optional, for voice transcription)
echo "[7/8] Installing OpenAI Whisper (optional)..."
read -p "Install Whisper for voice transcription? (y/n): " INSTALL_WHISPER
if [ "$INSTALL_WHISPER" = "y" ]; then
    pip3 install openai-whisper
    echo "    Whisper installed"
else
    echo "    Skipping Whisper installation"
fi

# 8. Verify installation
echo "[8/8] Verifying installation..."
echo ""
echo "=== Verification ==="
echo "Node.js: $(node --version 2>/dev/null || echo 'NOT FOUND')"
echo "OpenClaw: $(openclaw --version 2>/dev/null || echo 'NOT FOUND')"
echo "Git: $(git --version 2>/dev/null || echo 'NOT FOUND')"
echo "Python3: $(python3 --version 2>/dev/null || echo 'NOT FOUND')"
echo "FFmpeg: $(ffmpeg -version 2>/dev/null | head -1 || echo 'NOT FOUND')"
echo ""
echo "Workspace location: $WORKSPACE"
echo "Git remote: $(cd $WORKSPACE && git remote -v 2>/dev/null | head -1 || echo 'Not configured')"
echo ""

# 9. Post-restore instructions
cat << 'EOF'
=== Post-Restore Steps ===

1. CONFIGURE OPENCLAW:
   - Edit /root/.openclaw/openclaw.json with your API keys
   - Or re-run: openclaw agents add <id>

2. RESTORE API KEYS:
   - Check SECRETS.md for list of keys to restore
   - Common keys: Brave Search API, Telegram bot token

3. VERIFY CRON JOBS:
   - Check: crontab -l
   - Re-add daily news scan if needed

4. TEST CONNECTIONS:
   - Test Telegram: send a message to your bot
   - Test web search: try a search query
   - Test browser: if installed

5. START WORKING:
   cd /root/.openclaw/workspace
   git status

=== Restore Complete ===
EOF
