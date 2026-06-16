# Session Review: Bildung-Quellenhygiene fuer Duolingo, Khanmigo und Squirrel AI

Date: 2026-06-16

## Lagebild
The education chronology still had several education-platform entries sourced through Wikipedia. I tightened the most relevant current AI education products by replacing those references with official sites and the Khan Academy / Khanmigo ecosystem pages.

## Befunde
- Duolingo entries now point to Duolingo's official site and blog instead of Wikipedia.
- Khanmigo entries now point to Khanmigo and Khan Academy official pages.
- Squirrel AI entries now point to the official Squirrel AI site.
- The root file and the `research/` mirror must stay identical.
- A few older historical or conceptual entries remain unsourced by design because they are background markers rather than product references.

## Arbeitsplan
1. Replace the current product-level education references with official sites.
2. Mirror the edits into `research/`.
3. Validate formatting and parity.
4. Commit and push the source pass.

## Umgesetzte Aenderungen
- `ki-chronologie-39-bildung.md`
- `research/ki-chronologie/ki-chronologie-39-bildung.md`

Changed references:
- Duolingo -> `duolingo.com` and `blog.duolingo.com`
- Khanmigo -> `khanmigo.ai` and `khanacademy.org`
- Squirrel AI -> `squirrelai.com`

## Validierung
- `git diff --check`
- `diff -q` between root and `research/` copies of the education file
- `sed` spot-check of the modified education sections

## Naechste Schritte
- Commit the education source-hygiene pass.
- Push the commit to `origin/master`.
- Continue with the next thematic file only if another concrete source-hygiene target remains.
