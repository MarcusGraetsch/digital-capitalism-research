# Session Review: Medizin-Quellenhygiene fuer Wysa und Woebot

Date: 2026-06-16

## Lagebild
The medicine chronology still had two therapy entries and matching references pointing at Wikipedia. I replaced those with the official product sites so the block now points at the primary source layer for the current mental-health tools.

## Befunde
- Wysa now points directly to its official site in the therapy section and the references block.
- Woebot now points directly to Woebot Health's official site in the therapy section and the references block.
- The root chronology and the `research/` mirror must stay identical.
- One older 2001 Wikipedia line remains in place because it is a historical anchor rather than a product entry.

## Arbeitsplan
1. Replace the two therapy references with official sites.
2. Mirror the edits into `research/`.
3. Validate formatting and parity.
4. Commit and push the source pass.

## Umgesetzte Aenderungen
- `ki-chronologie-38-medizin.md`
- `research/ki-chronologie/ki-chronologie-38-medizin.md`

Changed references:
- Wysa -> `wysa.com`
- Woebot -> `woebothealth.com`

## Validierung
- `git diff --check`
- `diff -q` between root and `research/` copies of the medicine file
- `sed` spot-check of the therapy and references sections

## Naechste Schritte
- Commit the medicine source-hygiene pass.
- Push the commit to `origin/master`.
- Continue with the next thematic file only if another clearly grounded source-hygiene target remains.
