# TODO.md — Agent Environment & Skills

**Scope:** Rook agent setup, skills development, disaster recovery
**Last Updated:** 2026-02-25

---

## 🔴 HIGH PRIORITY — Repository Setup

### rook-agent Repo (Disaster Recovery)
- [ ] **Create GitHub repo:** `MarcusGraetsch/rook-agent`
  - Contents: SOUL.md, USER.md, AGENTS.md, TOOLS.md, HEARTBEAT.md, MEMORY.md
  - Skills: Custom skills (not the installed ones from /usr/lib/node_modules/)
  - NO credentials, NO .env files

- [ ] **Document recovery process**
  - How to restore agent after VPS crash?
  - Dependencies: Which skills need reinstall?

---

## 🟡 MEDIUM PRIORITY — News & Research Infrastructure

### RSS Feed Optimization
- [x] **Complete RSS restructure with priority weighting** ✅ DONE (v2.0, 39 feeds)
- [x] **Add Fefes Blog** ✅ DONE (high priority, DE tech-politics)
- [ ] **Evaluate additional German sources:**
  - [ ] Kuketz-Blog (privacy/security focus) — medium priority
  - [ ] Mastodon feeds (specific instances: chaos.social, techpolitik.social) — optional
  - [ ] Nitter (Twitter/X proxy) for specific accounts — low priority, unstable

### Newsletter Monitoring (High-Quality Sources)
- [ ] **Set up newsletter aggregation workflow**
  - **Tech/Labor intersections:**
    - [ ] Platformer (Casey Newton) — Meta/Uber/Amazon insider
    - [ ] Big Technology (Alex Kantrowitz)
    - [ ] Garbage Day (Ryan Broderick) — internet culture + politics
  - **US Labor:**
    - [ ] Luke O'Neil (Welcome to Hell World) — service worker perspective
    - [ ] Discourse Blog ( labor + culture)
  - **Climate + Tech:**
    - [ ] Heated (Emily Atkin) — fossil fuel industry + big tech
  - **EU/Germany:**
    - [ ] Netzpolitik-Newsletter
    - [ ] Algorithm Watch Newsletter
    - [ ] Digitale Gesellschaft Newsletter
  - **Finance/Economics:**
    - [ ] Matt Stoller (BIG) — monopoly power
    - [ ] Naked Capitalism Links
  - **Implementation:** RSS-Bridge, Kill the Newsletter, or IMAP forwarding

### Podcast Transcription Pipeline
- [ ] **Set up automated podcast transcription workflow**
  - Target podcasts for platform capitalism research:
    - [ ] Trashfuture (UK tech + capitalism)
    - [ ] Tech Won't Save Us (Paris Marx)
    - [ ] Upstream (Doughnut Economics)
    - [ ] It Could Happen Here (labor organizing)
    - [ ] The Dig (Jacobin — deep interviews)
  - Workflow:
    - [ ] RSS monitoring for new episodes
    - [ ] Download audio (youtube-dl/yt-dlp for YT, direct for RSS)
    - [ ] Whisper transcription (openai-whisper skill)
    - [ ] Summarization + keyword extraction
    - [ ] Archive to research directory with metadata
  - Storage: `~/research/podcasts/YYYY-MM/`

### Academic Alerting System
- [ ] **Set up proactive academic paper monitoring**
  - Platforms:
    - [ ] Zotero Saved Searches → RSS ("platform capitalism", "gig economy", "algorithmic management")
    - [ ] Google Scholar Alerts → RSS forwarding
    - [ ] ResearchGate alerts for specific authors (Pasquinelli, Srnicek, Zuboff, etc.)
    - [ ] Semantic Scholar API (free, up to 100 req/min)
  - Key authors to track:
    - [ ] Matteo Pasquinelli (AI + labor theory)
    - [ ] Nick Srnicek (platform capitalism)
    - [ ] Shoshana Zuboff (surveillance capitalism)
    - [ ] Mary Gray & Siddharth Suri (ghost work)
    - [ ] Julie Cohen (platform governance)
  - Workflow:
    - [ ] Weekly digest of new papers
    - [ ] Priority flagging for highly relevant titles
    - [ ] Direct download to `~/research/papers/YYYY-MM/`

### Email Link Aggregation
- [ ] **Set up email scanning for forwarded article links**
  - **Three email addresses to monitor:**
    - [ ] **AI-relevant:** AI developments, ML research, automation news
    - [ ] **New Work/Tech:** Changes in work through technology, workplace transformation
    - [ ] **Big Tech Power:** Power structures, monopolies, platform governance
  - Implementation options:
    - **A) IMAP polling:** Direct mailbox access (requires credentials)
    - **B) Forwarding rules:** Auto-forward to dedicated processing address
    - **C) API integration:** Gmail/Outlook API with filtering
  - Workflow:
    - [ ] Parse incoming emails for URLs
    - [ ] Fetch article content (web fetch + readability)
    - [ ] Categorize by topic (AI / New Work / Big Tech)
    - [ ] Deduplicate against existing research
    - [ ] Add to daily digest or weekly review
  - Security: OAuth2 preferred, app passwords if necessary, store in `.env`

---

## 🟡 MEDIUM PRIORITY — Infrastructure & Automation

### Contabo VM Lifecycle Automation
- [ ] **Contabo API Integration for VM start/stop**
  - Docs: https://contabo.com/de/contabo-api/
  - Goal: Reduce costs by running VM only when needed (08:00-20:00 CET)
  - Options to implement:
    - **A) Automatic schedule:** GitHub Actions cron (7:55 startup, 20:00 shutdown)
    - **B) Manual on-demand:** Telegram buttons or web interface for immediate start/stop
  - Requirements:
    - Contabo API token (store in `.env` / GitHub secrets)
    - Instance ID of the VM
    - SSH key for graceful shutdown
  - Disaster Recovery benefit: API-based recovery if VM fails

---

## 🟡 MEDIUM PRIORITY — Skills

### Published Skills
- [x] **vps-openclaw-security-hardening → ClawHub** ✅ DONE (v1.0.6 published)

### Skill Workflows (Post-Recovery)
- [ ] **openai-whisper** — Document usage pattern
  - Extract audio → transcribe → archive
- [ ] **blogwatcher** — Set up monitoring feeds
  - Feeds: HRW, LabourNet, ETUI
- [ ] **obsidian-cli** — Sync workflow with vault
- [ ] **agent-memory-kit** — Daily log process established?

---

## 🟢 LOW PRIORITY — Future Skills

- [ ] **Browser automation workflow** — Research use cases
- [ ] **Credential manager integration** — Audit existing setup
- [ ] **Proactive agent** — Evaluate if still needed

---

## ✅ Recently Completed

- [x] Installed: openai-whisper, blogwatcher, obsidian-cli
- [x] Installed: agent-memory-kit (templates in place)
- [x] Created: vps-openclaw-security-hardening v1.0.5 → v1.0.6
- [x] Published: vps-openclaw-security-hardening on ClawHub
- [x] Created: local security repo at `/root/.openclaw/security-local/`

---

*Note: Krankschreibung ended 2026-02-17*
