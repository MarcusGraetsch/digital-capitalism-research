#!/usr/bin/env python3
"""Pipeline orchestrator: runs all steps in sequence.

Usage:
    python -m literature_pipeline.run_pipeline                       # Full pipeline
    python -m literature_pipeline.run_pipeline --dry-run             # Preview steps
    python -m literature_pipeline.run_pipeline --from extract_text   # Resume from step
    python -m literature_pipeline.run_pipeline --steps ingest,extract_text  # Specific steps
    python -m literature_pipeline.run_pipeline --stats               # Show DB stats
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from .db import init_db, stats
from .utils import setup_logging, logger, PIPELINE_DIR


STEPS = [
    {
        "name": "ingest",
        "module": "literature_pipeline.ingest",
        "description": "Register source metadata",
    },
    {
        "name": "extract_text",
        "module": "literature_pipeline.extract_text",
        "description": "Extract text from PDFs/ePubs",
    },
    {
        "name": "extract_refs",
        "module": "literature_pipeline.extract_refs",
        "description": "Extract bibliographic references",
    },
    {
        "name": "extract_knowledge",
        "module": "literature_pipeline.extract_knowledge",
        "description": "LLM knowledge extraction",
    },
    {
        "name": "build_graph",
        "module": "literature_pipeline.build_graph",
        "description": "Build citation graph",
    },
    {
        "name": "export_bib",
        "module": "literature_pipeline.export_bib",
        "description": "Sync bibliography.bib",
    },
    {
        "name": "generate_embeddings",
        "module": "literature_pipeline.generate_embeddings",
        "description": "Generate RAG embeddings",
    },
]


def run_step(step, dry_run=False, extra_args=None):
    """Run a single pipeline step as a subprocess."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Step: {step['name']} - {step['description']}")
    logger.info(f"{'='*60}")

    if dry_run:
        logger.info(f"  [DRY RUN] Would run: python -m {step['module']}")
        return True

    cmd = [sys.executable, "-m", step["module"]]
    if extra_args:
        cmd.extend(extra_args)

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
            cwd=str(PIPELINE_DIR.parent),
        )

        duration = time.time() - start

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                logger.info(f"  {line}")

        if result.returncode != 0:
            logger.warning(f"  Step {step['name']} exited with code {result.returncode}")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-10:]:
                    logger.warning(f"  STDERR: {line}")
            return False

        logger.info(f"  Completed in {duration:.1f}s")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"  Step {step['name']} timed out (1h limit)")
        return False
    except Exception as e:
        logger.error(f"  Step {step['name']} failed: {e}")
        return False


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Literature pipeline orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Preview steps without running")
    parser.add_argument("--from", dest="from_step", help="Resume from this step")
    parser.add_argument("--steps", help="Comma-separated list of specific steps to run")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--limit", type=int, help="Limit sources per step")
    args = parser.parse_args()

    conn = init_db()

    if args.stats:
        s = stats(conn)
        print("\nLiterature Pipeline Statistics")
        print("=" * 40)
        for k, v in s.items():
            print(f"  {k}: {v}")
        conn.close()
        return

    conn.close()

    # Determine which steps to run
    if args.steps:
        step_names = [s.strip() for s in args.steps.split(",")]
        steps_to_run = [s for s in STEPS if s["name"] in step_names]
    elif args.from_step:
        found = False
        steps_to_run = []
        for s in STEPS:
            if s["name"] == args.from_step:
                found = True
            if found:
                steps_to_run.append(s)
        if not found:
            logger.error(f"Unknown step: {args.from_step}")
            logger.info(f"Available: {', '.join(s['name'] for s in STEPS)}")
            return
    else:
        steps_to_run = STEPS

    logger.info(f"\nLiterature Pipeline - {datetime.now().isoformat()}")
    logger.info(f"Steps to run: {', '.join(s['name'] for s in steps_to_run)}")
    if args.dry_run:
        logger.info("[DRY RUN MODE]")

    start_time = time.time()
    results = {}

    for step in steps_to_run:
        extra_args = []
        if args.limit and step["name"] != "build_graph":
            extra_args = ["--limit", str(args.limit)]

        success = run_step(step, dry_run=args.dry_run, extra_args=extra_args)
        results[step["name"]] = success

        if not success and not args.dry_run:
            logger.warning(f"Step {step['name']} had issues, continuing...")

    duration = time.time() - start_time

    logger.info(f"\n{'='*60}")
    logger.info("PIPELINE SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Duration: {duration:.1f}s ({duration/60:.1f}m)")
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        logger.info(f"  {name}: {status}")

    # Print final DB stats
    if not args.dry_run:
        conn = init_db()
        s = stats(conn)
        logger.info(f"\nDatabase: {s['total_sources']} sources, "
                     f"{s['total_references']} refs, "
                     f"{s['total_citations']} citations, "
                     f"{s['total_knowledge_items']} knowledge items, "
                     f"{s['total_concepts']} concepts")
        conn.close()

    logger.info("\nPipeline complete.")


if __name__ == "__main__":
    main()
