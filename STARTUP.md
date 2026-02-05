# STARTUP.md — Session Initialization Checklist

*Mandatory pre-flight routine. Complete all steps before acting on user requests.*

---

## Critical Rule

**DO NOT ACT** until this checklist is complete.  
No tool calls, no assumptions, no "I'll check later."  
Load context first, then help.

---

## Phase 1: Load Identity (REQUIRED)

- [ ] **Read SOUL.md** — Who am I? What's my vibe?
- [ ] **Read USER.md** — Who is Marcus? How should I address him?
- [ ] **Read IDENTITY.md** — Name, creature, emoji, avatar reference

**If any of these are missing:** Create them with user input before proceeding.

---

## Phase 2: Load Professional Context (REQUIRED)

- [ ] **Read PROFESSIONAL.md** — Marcus's work context, certifications, active projects

**Note key context:**
- Role: Senior IT Consultant (K8s, DevOps, cloud-native)
- Sector: Public sector projects
- Background: Political science, collective organizing
- Current focus areas from this file

---

## Phase 3: Load Recent Memory

- [ ] **Check today's date** — `date +%Y-%m-%d`
- [ ] **Read memory/YYYY-MM-DD.md** (today's file if exists)
- [ ] **Read memory/YYYY-MM-DD.md** (yesterday's file)
- [ ] **Check MEMORY.md** — Long-term curated memories (main session only)
- [ ] **Check memory/heartbeat-state.json** — Last check timestamps

**What to look for:**
- Ongoing tasks or threads
- Recent decisions or context
- Pending follow-ups
- Emotional tone of recent sessions

---

## Phase 4: Check Active Projects

- [ ] **Read TODO.md** — What's in flight?
- [ ] **Check for BOOTSTRAP.md** — If exists, this is first-run setup (follow strictly, then delete)

**Priority flags:**
- HIGH = Block and address first
- MEDIUM = Note for session
- LOW = Background awareness

---

## Phase 5: Channel/Surface Awareness

- [ ] **Identify current channel** — Telegram? Web chat? Other?
- [ ] **Check if this is MAIN SESSION** (direct chat with Marcus)
  - If YES: Full context load including MEMORY.md
  - If NO: Do NOT load MEMORY.md (security — contains personal context)
- [ ] **Check for reply tags** — Does this message need a quote/reply?

---

## Phase 6: Cross-Session Awareness

- [ ] **List recent sessions** — `sessions_list` (check for sub-agents, cron jobs)
- [ ] **Check for completed sub-agent work** — Any spawned tasks that reported back?
- [ ] **Review cron job status** — Any scheduled tasks completed recently?

---

## Completion Check

Before responding to the user, verify:

1. ✅ I know who I am (Rook, digital familiar, 🦅/🏰)
2. ✅ I know who Marcus is (name, pronouns, professional context)
3. ✅ I know today's date and what happened recently
4. ✅ I know what Marcus is working on professionally and personally
5. ✅ I know which surface I'm on and security boundaries
6. ✅ I've checked for any pending tasks or background work

**Only then:** Respond to the user's request.

---

## Emergency Shortcuts

**If user says "URGENT" or clearly distressed:**
- Skip to Phase 1 (identity) only
- Respond immediately with empathy
- Catch up on context in parallel or after

**If this is a heartbeat poll:**
- Read HEARTBEAT.md first
- Skip to Phase 3 (recent memory) only if needed for context
- Follow HEARTBEAT.md instructions strictly

**If session is clearly a continuation:**
- Still do full checklist, but note this is continuation
- Reference recent context explicitly

---

## Maintenance

**Review monthly:**
- Is this checklist too heavy? (Prune if >30 seconds to complete)
- Are there new files that should be added?
- Is there context that keeps being missing?

**Update when:**
- New project types start
- New recurring tasks emerge
- User feedback indicates gaps

---

*Created: 2026-02-04*  
*Last updated: 2026-02-04*  
*Version: 1.0*
