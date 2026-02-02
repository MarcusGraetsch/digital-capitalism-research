# Cloud Storage Backup Setup

This document explains how to set up automatic cloud storage backups for disaster recovery.

**Status:** Not configured — follow these steps when ready.

---

## Recommended: Backblaze B2

**Why:** Cheapest for backup use case (~$6/TB/month), free egress up to 3x stored amount.

### 1. Sign Up
- Go to: https://www.backblaze.com/b2/sign-up.html
- Create account (no credit card required to start)
- Create a bucket (e.g., `digital-capitalism-backups`)

### 2. Get Application Keys
- In B2 console: App Keys → Create Application Key
- Name: `backup-script`
- Capabilities: `listBuckets`, `readBuckets`, `writeBuckets`, `listFiles`, `readFiles`, `writeFiles`, `deleteFiles`
- Save: `keyID` and `applicationKey`

### 3. Install rclone
```bash
apt-get update && apt-get install -y rclone
```

### 4. Configure rclone
```bash
rclone config

# Choose:
# n) New remote
# name: b2
# Storage: Backblaze B2
# Account: (your keyID)
# Key: (your applicationKey)
# endpoint: (leave blank)
```

### 5. Test Upload
```bash
rclone copy /root/backups b2:digital-capitalism-backups/test/
rclone ls b2:digital-capitalism-backups/test/
```

### 6. Add to backup.sh
Edit `/root/.openclaw/workspace/scripts/backup.sh` and add at the end:

```bash
# Upload to Backblaze B2
echo "[5/5] Uploading to Backblaze B2..."
rclone copy $BACKUP_DIR b2:digital-capitalism-backups/
echo "    Uploaded to B2"
```

---

## Alternative: Wasabi

**Why:** Zero egress fees — good if you restore often.

### 1. Sign Up
- Go to: https://wasabi.com/cloud-storage-pricing/
- Create account
- Create bucket in EU (e.g., `digital-capitalism-backups`)

### 2. Get Keys
- Access Keys → Create New Key
- Save Access Key ID and Secret Key

### 3. Configure rclone
```bash
rclone config

# Choose:
# n) New remote
# name: wasabi
# Storage: S3
# Provider: Wasabi
# Access Key: (your key)
# Secret Key: (your secret)
# Region: eu-central-1
# Endpoint: s3.eu-central-1.wasabisys.com
```

### 4. Add to backup.sh
```bash
rclone copy $BACKUP_DIR wasabi:digital-capitalism-backups/
```

---

## Alternative: AWS S3 (Not Recommended for Cost)

Only if you already have AWS credits.

```bash
# Install AWS CLI
apt-get install -y awscli

# Configure
aws configure

# Add to backup.sh
aws s3 sync /root/backups s3://your-bucket/backups/
```

---

## Cost Estimation

| Provider | 1GB/Year | 10GB/Year | Egress Fees |
|----------|----------|-----------|-------------|
| Backblaze B2 | ~$0.07 | ~$0.72 | Free (3x stored/month) |
| Wasabi | ~$0.08 | ~$0.84 | Completely free |
| AWS S3 Standard | ~$2.76 | ~$27.60 | $0.09/GB |

Your current backup size: ~150KB
- **Annual cost: pennies** (effectively free)

---

## Security Notes

1. **Never commit API keys to Git** — use environment variables
2. **Restrict bucket access** — read/write only, no admin
3. **Enable versioning** (optional) — keeps old backup versions
4. **Test restore quarterly** — verify backups actually work

---

## Quick Reference

```bash
# Manual upload to B2
rclone copy /root/backups b2:digital-capitalism-backups/

# Manual upload to Wasabi
rclone copy /root/backups wasabi:digital-capitalism-backups/

# List remote files
rclone ls b2:digital-capitalism-backups/

# Download from B2
rclone copy b2:digital-capitalism-backups/workspace-2026-02-02.tar.gz /tmp/
```

---

*Document created: 2026-02-02*
*Status: Ready for setup when you have a cloud storage account*
