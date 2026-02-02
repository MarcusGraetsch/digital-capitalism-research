# SECRETS.md - API Keys and Sensitive Configuration
# 
# ⚠️  WARNING: This file contains sensitive information!
# Store securely (1Password, encrypted USB, etc.)
# Do NOT commit this file to Git (already in .gitignore)

## Critical API Keys

### Brave Search API
- **Purpose:** Web search functionality
- **Key format:** BSAM... (base64-like)
- **Where used:** web_search tool
- **How to restore:** 
  1. Get new key at: https://api.search.brave.com/app/keys
  2. Add to OpenClaw: `openclaw agents add main --env BRAVE_API_KEY=<key>`
  3. Or set: `export BRAVE_API_KEY=<key>`

### Telegram Bot Token
- **Purpose:** Telegram channel integration
- **Key format:** 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
- **Where used:** Telegram messaging
- **How to restore:**
  1. Get token from @BotFather
  2. Add to OpenClaw config: `telegram.token`

## OpenClaw Configuration

### File Location
- Main config: `/root/.openclaw/openclaw.json`
- Backup: Check `/root/backups/openclaw-config-*.json`

### Critical Config Sections
```json
{
  "channels": {
    "telegram": {
      "token": "***REDACTED***",
      "enabled": true
    }
  },
  "tools": {
    "web_search": {
      "provider": "brave",
      "apiKey": "***REDACTED***"
    }
  }
}
```

## Other Credentials

### SSH Keys (if used)
- Location: `~/.ssh/`
- Backup separately if needed

### Git Credentials
- HTTPS: Stored in git credential helper
- SSH: ~/.ssh/id_rsa (or ed25519)

## Disaster Recovery Checklist

If VPS dies, you need:

1. ✅ Git repository on GitHub (code is safe)
2. ✅ This SECRETS.md file (keys documented)
3. ✅ OpenClaw config backup (optional, can rebuild)
4. ⚠️  API keys (must regenerate or restore from backup)

## Recovery Steps

1. Spin up new VPS
2. Run: `scripts/restore.sh`
3. Reconfigure API keys using this document
4. Test: Send Telegram message, run web search
5. Resume work

## Backup Verification

Last verified: ___________

- [ ] Git push successful
- [ ] Scripts/backup.sh runs without errors
- [ ] Secrets documented in this file
- [ ] OpenClaw config backed up to /root/backups/
