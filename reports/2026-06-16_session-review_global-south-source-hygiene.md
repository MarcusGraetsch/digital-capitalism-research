# Session Review: Quellenhygiene fuer Global South und Asien

Date: 2026-06-16

## Lagebild
The newest Global-South entries were already in place, but several of the fresh anchors still pointed at Wikipedia. I replaced those with official or origin-source references where that could be done without weakening the statement.

## Befunde
- Deep Learning Indaba is better anchored through its official mission page than through Wikipedia.
- Sarvam AI is now backed by Sarvam's own site and the open-sourcing announcement that states the models were trained in India on IndiaAI Mission compute.
- Bhashini remains partially sourced through a secondary article, but the official Bhashini portal is now included as the primary reference point.
- The `research/` mirror must remain identical to the root chronology file.

## Arbeitsplan
1. Replace secondary references with official/origin sources where possible.
2. Mirror the updated references into `research/`.
3. Validate formatting and parity.
4. Commit and push the source pass.

## Umgesetzte Aenderungen
- `ki-chronologie-43-global-south.md`
- `research/ki-chronologie/ki-chronologie-43-global-south.md`

Changed references:
- Deep Learning Indaba -> official website
- Bhashini -> official portal
- Sarvam AI -> official site and open-sourcing announcement

## Validierung
- `git diff --check`
- `diff -q` between root and `research/` copies of the Global-South file
- `git status --short --branch`

## Naechste Schritte
- Commit the source-hygiene pass.
- Push the commit to `origin/master`.
- Continue with the next thematic gap only if another concrete leverage point remains.
