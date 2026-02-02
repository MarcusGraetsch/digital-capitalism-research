# Backup and Recovery

This directory contains scripts for disaster recovery.

## Files

- **backup.sh** - Creates backups of workspace and configs
- **restore.sh** - Restores environment on fresh VPS
- **SECRETS.md** - Documents API keys and sensitive config

## Usage

### Creating Backups

```bash
# Manual backup
cd /root/.openclaw/workspace
./scripts/backup.sh

# Backups stored in: /root/backups/
```

### Restoring After VPS Failure

```bash
# On fresh VPS
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/digital-capitalism-research/master/scripts/restore.sh
chmod +x restore.sh
sudo ./restore.sh
```

Or manually:

```bash
# 1. Install dependencies
apt-get update && apt-get install -y git nodejs npm python3 ffmpeg

# 2. Install OpenClaw
npm install -g openclaw

# 3. Clone repository
git clone https://github.com/YOUR_USERNAME/digital-capitalism-research.git /root/.openclaw/workspace

# 4. Restore API keys (see SECRETS.md)
```

## What's Backed Up

- Workspace files (excluding .git, node_modules)
- OpenClaw configuration
- System manifest (installed packages, versions)

## What's NOT Backed Up (Must Restore Manually)

- API keys (see SECRETS.md)
- GitHub SSH keys (if using SSH auth)
- System-level configurations

## Cloud Storage Integration (Optional)

For off-server backup storage, see CLOUD_STORAGE.md for setup instructions.
