#!/usr/bin/env python3
"""Discourse Mapping CLI — browse persons, works, mentions, and citation networks.

Usage:
    python -m literature_pipeline.discourse persons list [--role X] [--field X]
    python -m literature_pipeline.discourse persons show ID
    python -m literature_pipeline.discourse persons merge ID1 ID2
    python -m literature_pipeline.discourse works list [--type X] [--year X]
    python -m literature_pipeline.discourse works show ID
    python -m literature_pipeline.discourse mentions list [--person X] [--work X] [--type X]
    python -m literature_pipeline.discourse mentions stats
    python -m literature_pipeline.discourse network person ID
    python -m literature_pipeline.discourse seed-persons
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .db import (
    get_connection, init_db, get_or_create_person, get_or_create_work,
    get_person_mentions, get_work_mentions, get_discourse_network,
    find_duplicate_persons, merge_persons, _normalize_person_name,
    _generate_aliases,
)

# ---------------------------------------------------------------------------
# Seed person data: key authors from academic_config.json + major thinkers
# in the digital capitalism / Marxist political economy discourse
# ---------------------------------------------------------------------------

SEED_PERSONS = [
    # From academic_config.json
    {"name": "Pasquinelli, Matteo", "role": "scholar", "fields": ["ai", "labor_theory"], "openalex": "A5085389494"},
    {"name": "Srnicek, Nick", "role": "scholar", "fields": ["platform_capitalism"], "openalex": "A5091178311"},
    {"name": "Zuboff, Shoshana", "role": "scholar", "fields": ["surveillance_capitalism"], "openalex": "A5073480907"},
    {"name": "Gray, Mary L.", "role": "scholar", "fields": ["digital_labor", "ghost_work"], "openalex": "A5055422172"},
    {"name": "Suri, Siddharth", "role": "scholar", "fields": ["ghost_work", "crowdsourcing"], "openalex": "A5051257652"},
    {"name": "Cohen, Julie E.", "role": "scholar", "fields": ["platform_governance", "information_law"], "openalex": "A5087973237"},
    # Key digital capitalism scholars
    {"name": "Morozov, Evgeny", "role": "scholar", "fields": ["techno_critique", "political_economy"]},
    {"name": "Fuchs, Christian", "role": "scholar", "fields": ["digital_labor", "media_theory"]},
    {"name": "Staab, Philipp", "role": "scholar", "fields": ["digital_capitalism", "platform_economy"]},
    {"name": "Couldry, Nick", "role": "scholar", "fields": ["data_colonialism", "media_theory"]},
    {"name": "Mejias, Ulises A.", "role": "scholar", "fields": ["data_colonialism"]},
    {"name": "Mazzucato, Mariana", "role": "scholar", "fields": ["innovation_policy", "political_economy"]},
    {"name": "Piketty, Thomas", "role": "scholar", "fields": ["inequality", "political_economy"]},
    {"name": "Harvey, David", "role": "scholar", "fields": ["marxist_geography", "political_economy"]},
    {"name": "Fraser, Nancy", "role": "scholar", "fields": ["critical_theory", "capitalism"]},
    {"name": "Streeck, Wolfgang", "role": "scholar", "fields": ["political_economy", "capitalism"]},
    {"name": "Varoufakis, Yanis", "role": "scholar", "fields": ["techno_feudalism", "political_economy"]},
    {"name": "Durand, Cedric", "role": "scholar", "fields": ["techno_feudalism", "political_economy"]},
    {"name": "Vercellone, Carlo", "role": "scholar", "fields": ["cognitive_capitalism"]},
    {"name": "Scholz, Trebor", "role": "scholar", "fields": ["platform_cooperativism", "digital_labor"]},
    {"name": "Irani, Lilly", "role": "scholar", "fields": ["digital_labor", "ghost_work"]},
    {"name": "Rosenblat, Alex", "role": "scholar", "fields": ["gig_economy", "algorithmic_management"]},
    {"name": "Woodcock, Jamie", "role": "scholar", "fields": ["gig_economy", "labor"]},
    {"name": "Graham, Mark", "role": "scholar", "fields": ["digital_labor", "gig_economy"]},
    {"name": "Terranova, Tiziana", "role": "scholar", "fields": ["digital_labor", "network_culture"]},
    {"name": "Dyer-Witheford, Nick", "role": "scholar", "fields": ["cyber_proletariat", "marxism"]},
    {"name": "Sadowski, Jathan", "role": "scholar", "fields": ["data_commodification", "platform_economy"]},
    {"name": "Doctorow, Cory", "role": "activist", "fields": ["enshittification", "digital_rights"]},
    {"name": "O'Neil, Cathy", "role": "scholar", "fields": ["algorithmic_discrimination"]},
    {"name": "Noble, Safiya Umoja", "role": "scholar", "fields": ["algorithmic_discrimination"]},
    {"name": "Benjamin, Ruha", "role": "scholar", "fields": ["race_technology"]},
    {"name": "Eubanks, Virginia", "role": "scholar", "fields": ["digital_poverty", "automation"]},
    {"name": "Crawford, Kate", "role": "scholar", "fields": ["ai_politics", "data_extraction"]},
    {"name": "Coyle, Diane", "role": "scholar", "fields": ["digital_economy", "gdp"]},
    {"name": "Moulier-Boutang, Yann", "role": "scholar", "fields": ["cognitive_capitalism"]},
    # Classic political economy
    {"name": "Marx, Karl", "role": "scholar", "fields": ["political_economy", "capitalism"], "birth_year": 1818, "death_year": 1883},
    {"name": "Polanyi, Karl", "role": "scholar", "fields": ["political_economy"], "birth_year": 1886, "death_year": 1964},
    {"name": "Schumpeter, Joseph", "role": "scholar", "fields": ["political_economy", "innovation"], "birth_year": 1883, "death_year": 1950},
    # Frankfurt School / Critical Theory
    {"name": "Adorno, Theodor W.", "role": "scholar", "fields": ["critical_theory", "culture_industry"], "birth_year": 1903, "death_year": 1969},
    {"name": "Horkheimer, Max", "role": "scholar", "fields": ["critical_theory"], "birth_year": 1895, "death_year": 1973},
    {"name": "Habermas, Jurgen", "role": "scholar", "fields": ["critical_theory", "public_sphere"]},
    {"name": "Marcuse, Herbert", "role": "scholar", "fields": ["critical_theory"], "birth_year": 1898, "death_year": 1979},
    # Italian autonomism
    {"name": "Negri, Antonio", "role": "scholar", "fields": ["autonomism", "empire"]},
    {"name": "Hardt, Michael", "role": "scholar", "fields": ["autonomism", "empire"]},
    {"name": "Lazzarato, Maurizio", "role": "scholar", "fields": ["immaterial_labor", "debt"]},
    # Tech industry figures
    {"name": "Bezos, Jeff", "role": "executive", "fields": ["platform_economy"]},
    {"name": "Zuckerberg, Mark", "role": "executive", "fields": ["platform_economy", "surveillance"]},
    {"name": "Musk, Elon", "role": "executive", "fields": ["platform_economy", "ai"]},
    {"name": "Altman, Sam", "role": "executive", "fields": ["ai"]},
]


def cmd_backfill(args):
    """Backfill discourse tables from existing pipeline data.

    Mines existing DB tables (zero LLM cost):
    - sources.authors → person entries
    - extracted_references → works + persons
    - citations → mention records
    - knowledge_items (critiques) → person mentions
    """
    conn = init_db()
    created_persons = 0
    created_works = 0
    created_mentions = 0

    # 1. Create persons from sources.authors
    print("Phase 1: Creating persons from source authors...")
    sources = conn.execute("SELECT id, authors, title, year FROM sources").fetchall()
    for source in sources:
        authors_raw = source["authors"]
        if not authors_raw:
            continue
        try:
            authors = json.loads(authors_raw) if isinstance(authors_raw, str) else authors_raw
        except (json.JSONDecodeError, TypeError):
            authors = [authors_raw] if authors_raw else []

        for author_name in authors:
            if not author_name or not author_name.strip():
                continue
            existing = conn.execute(
                "SELECT id FROM persons WHERE sort_name = ?",
                (_normalize_person_name(author_name),),
            ).fetchone()
            if not existing:
                get_or_create_person(conn, author_name, fetch_metrics=False)
                created_persons += 1

    print(f"  Created {created_persons} persons from source authors")

    # 2. Create works + persons from extracted_references
    print("Phase 2: Creating works from extracted references...")
    refs = conn.execute(
        "SELECT * FROM extracted_references WHERE parsed_title IS NOT NULL"
    ).fetchall()
    for ref in refs:
        title = ref["parsed_title"]
        if not title or not title.strip():
            continue

        ref_authors_raw = ref["parsed_authors"]
        try:
            ref_authors = json.loads(ref_authors_raw) if isinstance(ref_authors_raw, str) else ref_authors_raw
        except (json.JSONDecodeError, TypeError):
            ref_authors = [ref_authors_raw] if ref_authors_raw else []

        work_id = get_or_create_work(
            conn, title,
            authors=ref_authors or None,
            year=ref["parsed_year"],
            fetch_metrics=False,
        )
        created_works += 1

    print(f"  Created/resolved {created_works} works from extracted references")

    # 3. Create mentions from citations table
    print("Phase 3: Creating mentions from citation edges...")
    citations = conn.execute(
        """SELECT c.*, s.authors, s.title as cited_title
           FROM citations c
           JOIN sources s ON s.id = c.cited_source_id"""
    ).fetchall()
    for cit in citations:
        # Create a mention for the cited source's authors
        authors_raw = cit["authors"]
        try:
            authors = json.loads(authors_raw) if isinstance(authors_raw, str) else authors_raw
        except (json.JSONDecodeError, TypeError):
            authors = [authors_raw] if authors_raw else []

        # Also create/link the cited work
        cited_title = cit["cited_title"]
        if cited_title:
            work_id = get_or_create_work(
                conn, cited_title,
                authors=authors or None,
                source_id=cit["cited_source_id"],
                fetch_metrics=False,
            )

            # Check if mention already exists
            existing = conn.execute(
                """SELECT id FROM mentions
                   WHERE source_id = ? AND mentioned_work_id = ?""",
                (cit["citing_source_id"], work_id),
            ).fetchone()
            if not existing:
                mention_type = cit["citation_type"] or "citation"
                # Map old citation types to new mention types
                type_map = {"supports": "agreement", "critiques": "critique",
                            "extends": "extension", "mentions": "citation"}
                mention_type = type_map.get(mention_type, mention_type)

                from .db import insert_mention
                insert_mention(
                    conn,
                    source_id=cit["citing_source_id"],
                    mentioned_work_id=work_id,
                    mention_type=mention_type,
                    context_text=cit["context"],
                    page_or_timestamp=cit["page"],
                    extraction_method="backfill",
                    confidence=0.6,
                )
                created_mentions += 1

        # Create person mentions for cited authors
        for author_name in (authors or []):
            if not author_name or not author_name.strip():
                continue
            person_id = get_or_create_person(conn, author_name, fetch_metrics=False)
            existing = conn.execute(
                """SELECT id FROM mentions
                   WHERE source_id = ? AND mentioned_person_id = ?""",
                (cit["citing_source_id"], person_id),
            ).fetchone()
            if not existing:
                insert_mention(
                    conn,
                    source_id=cit["citing_source_id"],
                    mentioned_person_id=person_id,
                    mention_type="citation",
                    extraction_method="backfill",
                    confidence=0.5,
                )
                created_mentions += 1

    print(f"  Created {created_mentions} mentions from citations")

    # 4. Create person mentions from knowledge_items critiques
    print("Phase 4: Creating mentions from critique knowledge items...")
    critique_mentions = 0
    critiques = conn.execute(
        "SELECT * FROM knowledge_items WHERE item_type = 'critique' AND target_author IS NOT NULL"
    ).fetchall()
    for crit in critiques:
        target = crit["target_author"].strip()
        if not target:
            continue
        person_id = get_or_create_person(conn, target, fetch_metrics=False)
        existing = conn.execute(
            """SELECT id FROM mentions
               WHERE source_id = ? AND mentioned_person_id = ? AND mention_type = 'critique'""",
            (crit["source_id"], person_id),
        ).fetchone()
        if not existing:
            insert_mention(
                conn,
                source_id=crit["source_id"],
                mentioned_person_id=person_id,
                mention_type="critique",
                context_text=crit["content"],
                page_or_timestamp=crit["page_range"],
                extraction_method="backfill",
                confidence=0.7,
            )
            critique_mentions += 1

    print(f"  Created {critique_mentions} mentions from critiques")

    # 5. Link existing sources to works table
    print("Phase 5: Linking sources to works...")
    linked = 0
    for source in sources:
        if not source["title"]:
            continue
        authors_raw = source["authors"]
        try:
            authors = json.loads(authors_raw) if isinstance(authors_raw, str) else authors_raw
        except (json.JSONDecodeError, TypeError):
            authors = [authors_raw] if authors_raw else []

        work_id = get_or_create_work(
            conn, source["title"],
            authors=authors or None,
            year=source["year"],
            source_id=source["id"],
            fetch_metrics=False,
        )
        linked += 1

    print(f"  Linked {linked} sources to works")

    # Summary
    final_persons = conn.execute("SELECT COUNT(*) FROM persons WHERE merged_into_id IS NULL").fetchone()[0]
    final_works = conn.execute("SELECT COUNT(*) FROM works WHERE merged_into_id IS NULL").fetchone()[0]
    final_mentions = conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]

    conn.close()

    print(f"\nBackfill complete!")
    print(f"  Persons:  {final_persons}")
    print(f"  Works:    {final_works}")
    print(f"  Mentions: {final_mentions}")
    print(f"\nRun 'python -m literature_pipeline.discourse fetch-metrics' to pull citation data.")


def cmd_fetch_metrics(args):
    """Fetch citation metrics from OpenAlex / Semantic Scholar."""
    from .fetch_metrics import update_all_persons, update_all_works

    conn = init_db()
    print("Fetching citation metrics from OpenAlex / Semantic Scholar...")
    print("(This may take a few minutes due to API rate limits)\n")

    if not args.works_only:
        print("=== Persons ===")
        update_all_persons(conn, force=args.full, dry_run=args.dry_run)

    if not args.persons_only:
        print("\n=== Works ===")
        update_all_works(conn, force=args.full, dry_run=args.dry_run)

    # Summary
    p_with = conn.execute(
        "SELECT COUNT(*) FROM persons WHERE cited_by_count IS NOT NULL AND merged_into_id IS NULL"
    ).fetchone()[0]
    p_total = conn.execute(
        "SELECT COUNT(*) FROM persons WHERE merged_into_id IS NULL"
    ).fetchone()[0]
    w_with = conn.execute(
        "SELECT COUNT(*) FROM works WHERE cited_by_count IS NOT NULL AND merged_into_id IS NULL"
    ).fetchone()[0]
    w_total = conn.execute(
        "SELECT COUNT(*) FROM works WHERE merged_into_id IS NULL"
    ).fetchone()[0]

    print(f"\nMetrics coverage: {p_with}/{p_total} persons, {w_with}/{w_total} works")

    # Show top cited persons
    if p_with > 0:
        print("\nTop 10 most-cited persons:")
        for row in conn.execute(
            """SELECT display_name, cited_by_count, h_index, metrics_source
               FROM persons
               WHERE cited_by_count IS NOT NULL AND merged_into_id IS NULL
               ORDER BY cited_by_count DESC LIMIT 10"""
        ):
            print(f"  {row['display_name']:<35} cited={row['cited_by_count']:>8}  h={row['h_index'] or '?':>4}  [{row['metrics_source']}]")

    conn.close()


def cmd_seed_persons(args):
    """Populate seed person list."""
    conn = init_db()
    created = 0
    skipped = 0

    for entry in SEED_PERSONS:
        name = entry["name"]
        existing = conn.execute(
            "SELECT id FROM persons WHERE sort_name = ?",
            (_normalize_person_name(name),),
        ).fetchone()

        if existing:
            skipped += 1
            continue

        person_id = get_or_create_person(
            conn, name,
            role=entry.get("role"),
            fields=entry.get("fields"),
            is_seed=1,
            birth_year=entry.get("birth_year"),
            death_year=entry.get("death_year"),
            fetch_metrics=False,  # batch-fetch later via fetch-metrics
        )

        # Store OpenAlex ID if present
        if entry.get("openalex"):
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO person_external_ids
                       (person_id, id_type, external_id, created_at)
                       VALUES (?, 'openalex', ?, ?)""",
                    (person_id, entry["openalex"], datetime.now().isoformat()),
                )
                conn.commit()
            except Exception:
                pass

        created += 1

    conn.close()
    print(f"Seed persons: {created} created, {skipped} already existed")
    print(f"Total: {created + skipped} seed persons")


# ---------------------------------------------------------------------------
# Persons commands
# ---------------------------------------------------------------------------

def cmd_persons_list(args):
    """List persons with optional filters."""
    conn = init_db()
    conditions = ["merged_into_id IS NULL"]
    params = []

    if args.role:
        conditions.append("role = ?")
        params.append(args.role)
    if args.field:
        conditions.append("fields LIKE ?")
        params.append(f'%"{args.field}"%')

    where = " AND ".join(conditions)
    params.append(args.limit or 50)

    rows = conn.execute(
        f"""SELECT p.*, COUNT(m.id) as mention_count
            FROM persons p
            LEFT JOIN mentions m ON m.mentioned_person_id = p.id
            WHERE {where}
            GROUP BY p.id
            ORDER BY mention_count DESC, p.canonical_name
            LIMIT ?""",
        params,
    ).fetchall()
    conn.close()

    if not rows:
        print("No persons found.")
        return

    print(f"\n{'ID':>5}  {'Name':<35} {'Role':<12} {'Mentions':>8}  {'Seed':>4}")
    print("-" * 75)
    for r in rows:
        seed = "*" if r["is_seed"] else ""
        print(f"{r['id']:>5}  {r['canonical_name']:<35} {r['role'] or '':<12} {r['mention_count']:>8}  {seed:>4}")
    print()


def cmd_persons_show(args):
    """Show full person profile."""
    conn = init_db()
    person = conn.execute("SELECT * FROM persons WHERE id = ?", (args.id,)).fetchone()
    if not person:
        print(f"Person {args.id} not found.")
        conn.close()
        return

    person = dict(person)
    print(f"\n{'='*60}")
    print(f"Person #{person['id']}: {person['display_name'] or person['canonical_name']}")
    print(f"{'='*60}")
    print(f"  Canonical: {person['canonical_name']}")
    print(f"  Sort name: {person['sort_name']}")
    if person.get("role"):
        print(f"  Role: {person['role']}")
    if person.get("affiliation"):
        print(f"  Affiliation: {person['affiliation']}")
    if person.get("fields"):
        fields = person["fields"]
        if isinstance(fields, str):
            try:
                fields = json.loads(fields)
            except (json.JSONDecodeError, TypeError):
                fields = [fields]
        print(f"  Fields: {', '.join(fields)}")
    if person.get("birth_year"):
        lifespan = str(person["birth_year"])
        if person.get("death_year"):
            lifespan += f"-{person['death_year']}"
        print(f"  Lifespan: {lifespan}")
    print(f"  Seed: {'Yes' if person.get('is_seed') else 'No'}")

    if person.get("cited_by_count") is not None:
        print(f"\n  Citation Metrics [{person.get('metrics_source', '?')}]:")
        print(f"    Citations:  {person['cited_by_count']:,}")
        if person.get("h_index") is not None:
            print(f"    h-index:    {person['h_index']}")
        if person.get("i10_index") is not None:
            print(f"    i10-index:  {person['i10_index']}")
        if person.get("works_count") is not None:
            print(f"    Works:      {person['works_count']:,}")
        if person.get("mean_citedness_2yr") is not None:
            print(f"    2yr mean:   {person['mean_citedness_2yr']:.2f}")
        if person.get("metrics_updated_at"):
            print(f"    Updated:    {person['metrics_updated_at'][:10]}")

    # Aliases
    aliases = conn.execute(
        "SELECT alias, alias_type FROM person_aliases WHERE person_id = ?",
        (args.id,),
    ).fetchall()
    if aliases:
        print(f"\n  Aliases:")
        for a in aliases:
            print(f"    - {a['alias']} ({a['alias_type']})")

    # External IDs
    ext_ids = conn.execute(
        "SELECT id_type, external_id FROM person_external_ids WHERE person_id = ?",
        (args.id,),
    ).fetchall()
    if ext_ids:
        print(f"\n  External IDs:")
        for e in ext_ids:
            print(f"    - {e['id_type']}: {e['external_id']}")

    # Works
    works = conn.execute(
        """SELECT w.* FROM works w
           JOIN work_authors wa ON wa.work_id = w.id
           WHERE wa.person_id = ? AND w.merged_into_id IS NULL
           ORDER BY w.year DESC""",
        (args.id,),
    ).fetchall()
    if works:
        print(f"\n  Works ({len(works)}):")
        for w in works:
            year = f" ({w['year']})" if w.get("year") else ""
            print(f"    [{w['id']}] {w['canonical_title']}{year}")

    # Mentions
    mentions = get_person_mentions(conn, args.id)
    if mentions:
        print(f"\n  Mentions ({len(mentions)}):")
        for m in mentions[:10]:
            m = dict(m)
            src = m.get("source_title") or m.get("article_id") or m.get("episode_id") or "?"
            print(f"    [{m['mention_type']}] {m['significance']} — {src[:50]}")
        if len(mentions) > 10:
            print(f"    ... and {len(mentions) - 10} more")

    conn.close()
    print()


def cmd_persons_merge(args):
    """Merge two person records."""
    conn = init_db()
    p1 = conn.execute("SELECT * FROM persons WHERE id = ?", (args.id1,)).fetchone()
    p2 = conn.execute("SELECT * FROM persons WHERE id = ?", (args.id2,)).fetchone()

    if not p1 or not p2:
        print("One or both person IDs not found.")
        conn.close()
        return

    print(f"Merging: [{p2['id']}] {p2['canonical_name']} → [{p1['id']}] {p1['canonical_name']}")
    merge_persons(conn, args.id1, args.id2)
    conn.close()
    print("Merge complete.")


# ---------------------------------------------------------------------------
# Works commands
# ---------------------------------------------------------------------------

def cmd_works_list(args):
    """List works with optional filters."""
    conn = init_db()
    conditions = ["w.merged_into_id IS NULL"]
    params = []

    if args.type:
        conditions.append("w.work_type = ?")
        params.append(args.type)
    if args.year:
        conditions.append("w.year = ?")
        params.append(args.year)

    where = " AND ".join(conditions)
    params.append(args.limit or 50)

    rows = conn.execute(
        f"""SELECT w.*, COUNT(m.id) as mention_count,
               GROUP_CONCAT(p.display_name, '; ') as author_names
            FROM works w
            LEFT JOIN mentions m ON m.mentioned_work_id = w.id
            LEFT JOIN work_authors wa ON wa.work_id = w.id
            LEFT JOIN persons p ON p.id = wa.person_id
            WHERE {where}
            GROUP BY w.id
            ORDER BY mention_count DESC, w.year DESC
            LIMIT ?""",
        params,
    ).fetchall()
    conn.close()

    if not rows:
        print("No works found.")
        return

    print(f"\n{'ID':>5}  {'Title':<45} {'Year':>5} {'Mentions':>8}")
    print("-" * 70)
    for r in rows:
        title = r["canonical_title"][:43]
        year = str(r["year"]) if r.get("year") else ""
        print(f"{r['id']:>5}  {title:<45} {year:>5} {r['mention_count']:>8}")
    print()


def cmd_works_show(args):
    """Show full work profile."""
    conn = init_db()
    work = conn.execute("SELECT * FROM works WHERE id = ?", (args.id,)).fetchone()
    if not work:
        print(f"Work {args.id} not found.")
        conn.close()
        return

    work = dict(work)
    print(f"\n{'='*60}")
    print(f"Work #{work['id']}: {work['canonical_title']}")
    print(f"{'='*60}")
    if work.get("year"):
        print(f"  Year: {work['year']}")
    if work.get("work_type"):
        print(f"  Type: {work['work_type']}")
    if work.get("publisher"):
        print(f"  Publisher: {work['publisher']}")
    if work.get("journal"):
        print(f"  Journal: {work['journal']}")

    # Authors
    authors = conn.execute(
        """SELECT p.*, wa.role, wa.position FROM persons p
           JOIN work_authors wa ON wa.person_id = p.id
           WHERE wa.work_id = ?
           ORDER BY wa.position""",
        (args.id,),
    ).fetchall()
    if authors:
        print(f"\n  Authors:")
        for a in authors:
            print(f"    [{a['id']}] {a['display_name'] or a['canonical_name']} ({a['role']})")

    # External IDs
    ext_ids = conn.execute(
        "SELECT id_type, external_id FROM work_external_ids WHERE work_id = ?",
        (args.id,),
    ).fetchall()
    if ext_ids:
        print(f"\n  External IDs:")
        for e in ext_ids:
            print(f"    - {e['id_type']}: {e['external_id']}")

    # Mentions
    mentions = get_work_mentions(conn, args.id)
    if mentions:
        print(f"\n  Mentioned in ({len(mentions)}):")
        for m in mentions[:10]:
            m = dict(m)
            src = m.get("source_title") or m.get("article_id") or m.get("episode_id") or "?"
            print(f"    [{m['mention_type']}] {m['significance']} — {src[:50]}")

    conn.close()
    print()


# ---------------------------------------------------------------------------
# Mentions commands
# ---------------------------------------------------------------------------

def cmd_mentions_list(args):
    """List mentions with optional filters."""
    conn = init_db()
    conditions = ["1=1"]
    params = []

    if args.person:
        conditions.append("m.mentioned_person_id = ?")
        params.append(args.person)
    if args.work:
        conditions.append("m.mentioned_work_id = ?")
        params.append(args.work)
    if args.type:
        conditions.append("m.mention_type = ?")
        params.append(args.type)

    where = " AND ".join(conditions)
    params.append(args.limit or 30)

    rows = conn.execute(
        f"""SELECT m.*,
               s.title as source_title,
               p.display_name as person_name,
               w.canonical_title as work_title
            FROM mentions m
            LEFT JOIN sources s ON s.id = m.source_id
            LEFT JOIN persons p ON p.id = m.mentioned_person_id
            LEFT JOIN works w ON w.id = m.mentioned_work_id
            WHERE {where}
            ORDER BY m.created_at DESC
            LIMIT ?""",
        params,
    ).fetchall()
    conn.close()

    if not rows:
        print("No mentions found.")
        return

    print(f"\n{'ID':>5}  {'Type':<12} {'Significance':<10} {'Person/Work':<30} {'Source':<25}")
    print("-" * 90)
    for r in rows:
        target = (r["person_name"] or r["work_title"] or "?")[:28]
        src = (r["source_title"] or r["article_id"] or r["episode_id"] or "?")[:23]
        print(f"{r['id']:>5}  {r['mention_type']:<12} {r['significance'] or '':<10} {target:<30} {src:<25}")
    print()


def cmd_mentions_stats(args):
    """Show discourse statistics."""
    conn = init_db()

    total_persons = conn.execute("SELECT COUNT(*) FROM persons WHERE merged_into_id IS NULL").fetchone()[0]
    total_works = conn.execute("SELECT COUNT(*) FROM works WHERE merged_into_id IS NULL").fetchone()[0]
    total_mentions = conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
    total_aliases = conn.execute("SELECT COUNT(*) FROM person_aliases").fetchone()[0]

    print(f"\nDiscourse Database Statistics")
    print(f"{'='*40}")
    print(f"Persons:   {total_persons}")
    print(f"  Seed:    {conn.execute('SELECT COUNT(*) FROM persons WHERE is_seed = 1').fetchone()[0]}")
    print(f"  Aliases: {total_aliases}")
    print(f"Works:     {total_works}")
    print(f"Mentions:  {total_mentions}")

    if total_mentions > 0:
        print(f"\nBy mention type:")
        for row in conn.execute("SELECT mention_type, COUNT(*) FROM mentions GROUP BY mention_type ORDER BY COUNT(*) DESC"):
            print(f"  {row[0]}: {row[1]}")

        print(f"\nBy significance:")
        for row in conn.execute("SELECT significance, COUNT(*) FROM mentions GROUP BY significance ORDER BY COUNT(*) DESC"):
            print(f"  {row[0] or 'unset'}: {row[1]}")

        print(f"\nBy pipeline:")
        lit = conn.execute("SELECT COUNT(*) FROM mentions WHERE source_id IS NOT NULL").fetchone()[0]
        news = conn.execute("SELECT COUNT(*) FROM mentions WHERE article_id IS NOT NULL").fetchone()[0]
        pod = conn.execute("SELECT COUNT(*) FROM mentions WHERE episode_id IS NOT NULL").fetchone()[0]
        print(f"  Literature: {lit}")
        print(f"  News:       {news}")
        print(f"  Podcast:    {pod}")

        print(f"\nTop 10 most-mentioned persons:")
        for row in conn.execute(
            """SELECT p.display_name, COUNT(m.id) as cnt
               FROM mentions m
               JOIN persons p ON p.id = m.mentioned_person_id
               WHERE m.mentioned_person_id IS NOT NULL
               GROUP BY m.mentioned_person_id
               ORDER BY cnt DESC LIMIT 10"""
        ):
            print(f"  {row[0]}: {row[1]}")

        print(f"\nTop 10 most-mentioned works:")
        for row in conn.execute(
            """SELECT w.canonical_title, COUNT(m.id) as cnt
               FROM mentions m
               JOIN works w ON w.id = m.mentioned_work_id
               WHERE m.mentioned_work_id IS NOT NULL
               GROUP BY m.mentioned_work_id
               ORDER BY cnt DESC LIMIT 10"""
        ):
            print(f"  {row[0][:50]}: {row[1]}")

    conn.close()
    print()


# ---------------------------------------------------------------------------
# Network command
# ---------------------------------------------------------------------------

def cmd_network_person(args):
    """Show discourse network for a person."""
    conn = init_db()
    person = conn.execute("SELECT * FROM persons WHERE id = ?", (args.id,)).fetchone()
    if not person:
        print(f"Person {args.id} not found.")
        conn.close()
        return

    print(f"\nDiscourse Network: {person['display_name'] or person['canonical_name']}")
    print(f"{'='*60}")

    # All mentions of this person
    mentions = get_person_mentions(conn, args.id)
    print(f"\nTotal mentions: {len(mentions)}")

    if mentions:
        # Group by mention type
        by_type = {}
        for m in mentions:
            t = m["mention_type"]
            by_type.setdefault(t, []).append(m)

        for mtype, ms in sorted(by_type.items(), key=lambda x: -len(x[1])):
            print(f"\n  {mtype} ({len(ms)}):")
            for m in ms[:5]:
                m = dict(m)
                src = m.get("source_title") or m.get("article_id") or m.get("episode_id") or "?"
                sig = f"[{m.get('significance', '?')}]"
                print(f"    {sig:<10} {src[:50]}")
            if len(ms) > 5:
                print(f"    ... and {len(ms) - 5} more")

    # Co-mentioned persons (who appears in the same sources)
    co_mentioned = conn.execute(
        """SELECT p2.display_name, p2.id, COUNT(DISTINCT m1.source_id) as shared
           FROM mentions m1
           JOIN mentions m2 ON m2.source_id = m1.source_id AND m2.id != m1.id
           JOIN persons p2 ON p2.id = m2.mentioned_person_id
           WHERE m1.mentioned_person_id = ?
             AND m2.mentioned_person_id IS NOT NULL
             AND m1.source_id IS NOT NULL
           GROUP BY p2.id
           ORDER BY shared DESC
           LIMIT 10""",
        (args.id,),
    ).fetchall()

    if co_mentioned:
        print(f"\n  Co-mentioned persons:")
        for cm in co_mentioned:
            print(f"    [{cm['id']}] {cm['display_name']} (shared sources: {cm['shared']})")

    conn.close()
    print()


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Discourse Mapping CLI")
    sub = parser.add_subparsers(dest="command")

    # seed-persons
    sub.add_parser("seed-persons", help="Populate seed person list")

    # backfill
    sub.add_parser("backfill", help="Backfill discourse tables from existing pipeline data (zero LLM cost)")

    # fetch-metrics
    p_fm = sub.add_parser("fetch-metrics", help="Fetch citation metrics from OpenAlex / Semantic Scholar")
    p_fm.add_argument("--full", action="store_true", help="Force-refresh all, ignore staleness")
    p_fm.add_argument("--persons-only", action="store_true")
    p_fm.add_argument("--works-only", action="store_true")
    p_fm.add_argument("--dry-run", action="store_true", help="Preview without writing")

    # persons
    p_persons = sub.add_parser("persons", help="Person commands")
    persons_sub = p_persons.add_subparsers(dest="persons_cmd")

    p_plist = persons_sub.add_parser("list", help="List persons")
    p_plist.add_argument("--role", help="Filter by role")
    p_plist.add_argument("--field", help="Filter by field")
    p_plist.add_argument("--limit", type=int, default=50)

    p_pshow = persons_sub.add_parser("show", help="Show person profile")
    p_pshow.add_argument("id", type=int)

    p_pmerge = persons_sub.add_parser("merge", help="Merge two persons")
    p_pmerge.add_argument("id1", type=int, help="ID to keep")
    p_pmerge.add_argument("id2", type=int, help="ID to merge into id1")

    # works
    p_works = sub.add_parser("works", help="Work commands")
    works_sub = p_works.add_subparsers(dest="works_cmd")

    p_wlist = works_sub.add_parser("list", help="List works")
    p_wlist.add_argument("--type", help="Filter by work type")
    p_wlist.add_argument("--year", type=int, help="Filter by year")
    p_wlist.add_argument("--limit", type=int, default=50)

    p_wshow = works_sub.add_parser("show", help="Show work profile")
    p_wshow.add_argument("id", type=int)

    # mentions
    p_mentions = sub.add_parser("mentions", help="Mention commands")
    mentions_sub = p_mentions.add_subparsers(dest="mentions_cmd")

    p_mlist = mentions_sub.add_parser("list", help="List mentions")
    p_mlist.add_argument("--person", type=int, help="Filter by person ID")
    p_mlist.add_argument("--work", type=int, help="Filter by work ID")
    p_mlist.add_argument("--type", help="Filter by mention type")
    p_mlist.add_argument("--limit", type=int, default=30)

    mentions_sub.add_parser("stats", help="Discourse statistics")

    # network
    p_network = sub.add_parser("network", help="Network analysis")
    network_sub = p_network.add_subparsers(dest="network_cmd")

    p_nperson = network_sub.add_parser("person", help="Person discourse network")
    p_nperson.add_argument("id", type=int)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "seed-persons":
        cmd_seed_persons(args)
    elif args.command == "backfill":
        cmd_backfill(args)
    elif args.command == "fetch-metrics":
        cmd_fetch_metrics(args)
    elif args.command == "persons":
        if not hasattr(args, "persons_cmd") or not args.persons_cmd:
            p_persons.print_help()
        elif args.persons_cmd == "list":
            cmd_persons_list(args)
        elif args.persons_cmd == "show":
            cmd_persons_show(args)
        elif args.persons_cmd == "merge":
            cmd_persons_merge(args)
    elif args.command == "works":
        if not hasattr(args, "works_cmd") or not args.works_cmd:
            p_works.print_help()
        elif args.works_cmd == "list":
            cmd_works_list(args)
        elif args.works_cmd == "show":
            cmd_works_show(args)
    elif args.command == "mentions":
        if not hasattr(args, "mentions_cmd") or not args.mentions_cmd:
            p_mentions.print_help()
        elif args.mentions_cmd == "list":
            cmd_mentions_list(args)
        elif args.mentions_cmd == "stats":
            cmd_mentions_stats(args)
    elif args.command == "network":
        if not hasattr(args, "network_cmd") or not args.network_cmd:
            p_network.print_help()
        elif args.network_cmd == "person":
            cmd_network_person(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
