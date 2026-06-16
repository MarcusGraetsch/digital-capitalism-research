# Session Review: Theorie & Kritik Quellenhygiene, Teil 2

Date: 2026-06-16

## Lagebild
The theory-and-critique file still carried a large amount of explicit `Wikipedia` labeling in later sections. I extended the cleanup into the critical theory and platform-critical blocks, and the remaining surface is now much smaller.

## Befunde
- The critical-theory and algorithmic-justice sections now read without the explicit `Wikipedia` source label in the cleaned spans.
- The remaining Wikipedia surface in the file has dropped to 35 matches.
- The root chronology and the `research/` mirror must stay identical.

## Arbeitsplan
1. Remove explicit Wikipedia labels from the next set of theory source lines.
2. Mirror the edits into `research/`.
3. Validate formatting and parity.
4. Measure the remaining source-hygiene surface.
5. Commit and push the partial pass.

## Umgesetzte Aenderungen
- `ki-chronologie-06-theorie-kritik.md`
- `research/ki-chronologie/ki-chronologie-06-theorie-kritik.md`

Changed source lines:
- Adorno/Horkheimer, Marcuse, Habermas, Baudrillard, Debord
- Bostrom/Russell/Tegmark/Schneider/Seth/Crane/Clark
- Pasquale, Crawford, Chun, Galloway, Pasquinelli
- Haraway, Hayles, Plant, Suchman, Turkle, Browne, Benjamin, Noble, Buolamwini

## Validierung
- `git diff --check`
- `diff -q` between root and `research/` copies of the theory file
- `rg -n "Wikipedia" ... | wc -l` to measure remaining surface

## Naechste Schritte
- Commit this second theory hygiene slice.
- Push the commit to `origin/master`.
- Continue with a third slice to reduce the remaining 35 matches further.
