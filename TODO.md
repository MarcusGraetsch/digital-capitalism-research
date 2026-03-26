# TODO.md — Agent Environment & Skills

**Scope:** Rook agent setup, skills development, disaster recovery
**Last Updated:** 2026-02-25

---

## 🔴 HIGH PRIORITY — Repository Setup

### rook-agent Repo (Disaster Recovery)
- [x] **Create GitHub repo:** `MarcusGraetsch/rook-agent` ✅ DONE
  - Contents: SOUL.md, USER.md, AGENTS.md, TOOLS.md, HEARTBEAT.md, MEMORY.md
  - Skills: Custom skills (not the installed ones from /usr/lib/node_modules/)
  - NO credentials, NO .env files
  - Local clone: `/mnt/d/Develop/myWebsite/rook-agent`

- [x] **Document recovery process** ✅ DONE (in rook-agent README.md)
  - How to restore agent after VPS crash?
  - Dependencies: Which skills need reinstall?

---

## 🟡 MEDIUM PRIORITY — News & Research Infrastructure

### RSS Feed Optimization
- [x] **Complete RSS restructure with priority weighting** ✅ DONE (v2.0, 39 feeds)
- [x] **Add Fefes Blog** ✅ DONE (high priority, DE tech-politics)
- [x] **Evaluate additional German sources:** ✅ DONE
  - [x] Kuketz-Blog — added to RSS config (medium priority, active feed)
  - [x] chaos.social #digitalisierung — added to RSS config (low priority, 21 items, active)
  - [x] chaos.social #plattformkapitalismus — skipped (0 items, tag too niche)
  - [x] chaos.social #ueberwachung — skipped (12 items over 2 years, too low volume)
  - [x] techpolitik.social — skipped (instance dead, ECONNREFUSED)
  - [x] Nitter — skipped (project archived since 2024, no public instances)

### Newsletter Monitoring (High-Quality Sources)
- [x] **Set up newsletter aggregation workflow** ✅ DONE (native RSS, no RSS-Bridge needed)
  - **Tech/Labor intersections:**
    - [x] Platformer (Casey Newton) — added, high priority
    - [x] Big Technology (Alex Kantrowitz) — added, high priority
    - [x] Garbage Day (Ryan Broderick) — skipped (feed stale since Jan 2024)
  - **US Labor:**
    - [x] Luke O'Neil (Welcome to Hell World) — added, medium priority
    - [x] Discourse Blog — added, low priority
  - **Climate + Tech:**
    - [x] Heated (Emily Atkin) — added, medium priority
  - **EU/Germany:**
    - [x] Netzpolitik-Newsletter — already covered by netzpolitik.org/feed/
    - [x] Algorithm Watch Newsletter — already covered by algorithmwatch.org/en/feed/
    - [x] Digitale Gesellschaft DE — added, medium priority
  - **Finance/Economics:**
    - [x] Matt Stoller (BIG) — added, high priority
    - [x] Naked Capitalism — already in config (high priority)

### Podcast Transcription Pipeline
- [x] **Set up automated podcast transcription workflow** ✅ DONE
  - Target podcasts (all feeds verified active):
    - [x] Trashfuture (Podbean feed)
    - [x] Tech Won't Save Us (Megaphone feed)
    - [x] Upstream (Libsyn feed)
    - [x] It Could Happen Here (Omny feed)
    - [x] The Dig (Blubrry feed)
  - Workflow implemented in `research/scan_podcasts.py`:
    - [x] RSS monitoring for new episodes
    - [x] Direct MP3 download from enclosures
    - [x] OpenAI Whisper API transcription (with chunking for large files)
    - [x] Claude summarization + keyword extraction
    - [x] Archive to `research/podcasts/YYYY-MM/` with frontmatter
  - Config: `research/podcast_config.json`
  - Run: `python3 research/scan_podcasts.py` (or `--scan-only`, `--transcribe-only`, `--podcast "name"`)

### Academic Alerting System
- [x] **Set up proactive academic paper monitoring** ✅ DONE (OpenAlex API)
  - Platform: OpenAlex API (free, no auth, 100k req/day)
    - Chose over Semantic Scholar (better coverage, no auth needed)
    - Google Scholar has no native RSS export
  - Tracked authors (OpenAlex IDs resolved):
    - [x] Matteo Pasquinelli (A5085389494)
    - [x] Nick Srnicek (A5091178311)
    - [x] Shoshana Zuboff (A5073480907)
    - [x] Mary L. Gray (A5055422172)
    - [x] Siddharth Suri (A5051257652)
    - [x] Julie E. Cohen (A5087973237)
  - Keyword searches: platform capitalism, gig economy, algorithmic management,
    surveillance capitalism, digital labor, data extraction, platform cooperativism
  - Config: `research/academic_config.json`
  - Run: `python3 research/scan_academic.py` (or `--authors-only`, `--keywords-only`, `--digest-only`, `--stats`)
  - Output: `academic_papers.db` + monthly digest in `news/YYYY-MM-academic-digest.md`

### Email Link Aggregation
- [x] **Set up email scanning for forwarded article links** ✅ DONE (already implemented in scan_v5.py)
  - **Three Gmail accounts active** (Gmail API, OAuth2):
    - [x] **AI-relevant:** aichitchatter@critical-theory.digital
    - [x] **New Work/Tech:** newworkculture.twentyone@critical-theory.digital
    - [x] **Big Tech Power:** b1gt3ch.5n5lysis@critical-theory.digital
  - Implementation: Gmail API (option C) via `research/scan_v5.py`
  - Workflow fully implemented:
    - [x] Parse emails for URLs + newsletter detection
    - [x] Fetch article content (requests + BeautifulSoup)
    - [x] Categorize by account (aigen / newwork / bigtech)
    - [x] Deduplicate against articles.db
    - [x] Feeds into weekly pipeline (clean → label → summarize → digest)

### Academic Alerting — Author Expansion
- [ ] **Expand tracked authors beyond contemporary platform capitalism scholars**
  - [ ] **Recurring citation authors**: Authors frequently cited across the literature pipeline
    sources (extract from `knowledge_items` / `extracted_references` in literature.db).
    These are often central to specific debates and should be monitored.
  - [ ] **Cybernetics / systems theory pioneers**: Norbert Wiener, Heinz von Foerster,
    Stafford Beer, Gregory Bateson — foundational for understanding computation and control
  - [ ] **German critical theory / philosophy**: Frankfurt School (Adorno, Horkheimer, Habermas),
    Marx/Engels, Rosa Luxemburg, Wolfgang Fritz Haug (Argument), Robert Kurz (Krisis/Exit),
    and contemporary German-language scholars on technology and capitalism
  - [ ] **Classical political economy**: Authors relevant to bourgeois society, capitalism,
    and technology debates (value theory, labor process, machinery)
  - [ ] **Automated discovery**: Consider a pipeline step that extracts frequently-cited
    authors from literature.db and auto-suggests additions to academic_config.json

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
