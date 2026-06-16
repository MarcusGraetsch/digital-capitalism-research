# Session Review: India-Quellenhygiene in der International-Chronologie

Date: 2026-06-16

## Lagebild
The international chronology still had several India-related entries sourced via Wikipedia. I tightened the IndiaAI mission entry and aligned the surrounding National Strategy / Responsible AI lines with official portal and NITI Aayog references.

## Befunde
- The IndiaAI Mission is better anchored through the official IndiaAI portal and the Impact Summit portal.
- The National Strategy for Artificial Intelligence and the Responsible AI lines now point to institutional sources instead of Wikipedia.
- The India strategy line in the Global South subsection inside the same file now also has an explicit source.
- The `research/` mirror must stay identical to the root chronology file.

## Arbeitsplan
1. Replace the most brittle India references with official portals.
2. Add sources to the previously unsourced India strategy line in the Global South subsection.
3. Mirror the edits into `research/`.
4. Validate formatting and parity.
5. Commit and push.

## Umgesetzte Aenderungen
- `ki-chronologie-22-international.md`
- `research/ki-chronologie/ki-chronologie-22-international.md`

Changed references:
- IndiaAI Mission / INDIAai Portal -> `indiaai.gov.in` and `impact.indiaai.gov.in`
- National Strategy for Artificial Intelligence -> `niti.gov.in` and `indiaai.gov.in`
- Principles for Responsible AI -> `niti.gov.in` and `indiaai.gov.in`
- Global South India strategy line -> explicit source added

## Validierung
- `git diff --check`
- `diff -q` between root and `research/` copies of the International file
- `sed` spot-check of the modified sections

## Naechste Schritte
- Commit the India source-hygiene pass.
- Push the commit to `origin/master`.
- Continue with the next thematic file only if another concrete source-hygiene leverage point remains.
