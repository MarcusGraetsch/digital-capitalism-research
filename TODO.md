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
