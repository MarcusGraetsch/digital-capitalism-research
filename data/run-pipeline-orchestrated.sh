#!/usr/bin/env bash
# run-pipeline-orchestrated.sh
#
# Orchestrator-v2-style execution of the weekly research pipeline.
# Runs the two independent scan steps in parallel (T0), then sequential
# processing (T1 clean/label), then synthesis and digest (T2).
#
# Usage: ./run-pipeline-orchestrated.sh [--dry-run] [--skip-digest]
#
# Logs structured JSONL to: ./orchestrator-run.log

set -euo pipefail

RESEARCH_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$RESEARCH_DIR/orchestrator-run.log"
DRY_RUN=0
SKIP_DIGEST=0

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=1 ;;
    --skip-digest) SKIP_DIGEST=1 ;;
  esac
done

log() {
  local level="$1"; shift
  local msg="$*"
  local entry
  entry=$(printf '{"ts":"%s","level":"%s","msg":%s}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$(printf '%s' "$msg" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')")
  echo "$entry" | tee -a "$LOG_FILE"
}

run_step() {
  local tier="$1"
  local name="$2"
  shift 2
  local cmd=("$@")
  local start end duration exit_code=0

  log INFO "step_start tier=$tier name=$name"
  start=$(date +%s)

  if [[ $DRY_RUN -eq 1 ]]; then
    log INFO "step_skip (dry-run) name=$name"
    return 0
  fi

  "${cmd[@]}" >> "$LOG_FILE" 2>&1 || exit_code=$?
  end=$(date +%s)
  duration=$((end - start))

  if [[ $exit_code -eq 0 ]]; then
    log INFO "step_done name=$name duration=${duration}s"
  else
    log WARN "step_failed name=$name exit_code=$exit_code duration=${duration}s"
    # Non-fatal: pipeline continues even if a step fails
  fi
  return $exit_code
}

# ---------------------------------------------------------------------------
# Pipeline start
# ---------------------------------------------------------------------------
log INFO "pipeline_start dry_run=$DRY_RUN"
PIPELINE_START=$(date +%s)

# ---------------------------------------------------------------------------
# T0 — Parallel data ingestion (independent, no LLM)
# ---------------------------------------------------------------------------
log INFO "phase_start phase=T0-ingest"

EMAIL_SCAN_RC=0
RSS_SCAN_RC=0

if [[ $DRY_RUN -eq 0 ]]; then
  python3 "$RESEARCH_DIR/scan_v5.py" >> "$LOG_FILE" 2>&1 &
  PID_EMAIL=$!
  python3 "$RESEARCH_DIR/scan_rss.py" >> "$LOG_FILE" 2>&1 &
  PID_RSS=$!

  wait "$PID_EMAIL" || EMAIL_SCAN_RC=$?
  wait "$PID_RSS"   || RSS_SCAN_RC=$?
else
  log INFO "step_skip (dry-run) name=email_scan"
  log INFO "step_skip (dry-run) name=rss_scan"
fi

log INFO "phase_done phase=T0-ingest email_rc=$EMAIL_SCAN_RC rss_rc=$RSS_SCAN_RC"

# ---------------------------------------------------------------------------
# T1 — Sequential processing (light LLM: clean + label)
# ---------------------------------------------------------------------------
log INFO "phase_start phase=T1-process"

run_step T1 clean  python3 "$RESEARCH_DIR/clean_smart.py"  || true
run_step T1 label  python3 "$RESEARCH_DIR/label_articles.py" || true

log INFO "phase_done phase=T1-process"

# ---------------------------------------------------------------------------
# T2 — Synthesis (heavier: briefing + digest)
# ---------------------------------------------------------------------------
log INFO "phase_start phase=T2-synthesis"

WORKSPACE="$(dirname "$RESEARCH_DIR")"

run_step T2 weekly_briefing \
  python3 "$WORKSPACE/generate_weekly_briefing.py" || true

run_step T2 self_improvement \
  python3 "$WORKSPACE/skills/xiucheng-self-improving-agent/self_improving.py" --report || true

if [[ $SKIP_DIGEST -eq 0 ]]; then
  run_step T2 telegram_digest \
    python3 "$RESEARCH_DIR/weekly_telegram_digest.py" || true
fi

log INFO "phase_done phase=T2-synthesis"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
PIPELINE_END=$(date +%s)
TOTAL=$((PIPELINE_END - PIPELINE_START))
log INFO "pipeline_done total_seconds=$TOTAL"

echo "[research-pipeline] Completed in ${TOTAL}s. Log: $LOG_FILE" >&2
