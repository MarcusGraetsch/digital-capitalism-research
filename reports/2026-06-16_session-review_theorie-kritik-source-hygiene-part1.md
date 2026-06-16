# Session Review: Theorie & Kritik Quellenhygiene, Teil 1

Date: 2026-06-16

## Lagebild
The theory-and-critique chronology contained the densest concentration of `Wikipedia` references in the whole set. I started a conservative cleanup pass that removes the explicit Wikipedia wording from the earliest philosophy and theory source lines, while keeping the broader structure intact.

## Befunde
- The first sections now read with cleaner source lines instead of `Wikipedia` labels.
- The pass is intentionally partial: the file still contains many later Wikipedia references and needs additional slices.
- The root chronology and the `research/` mirror must stay identical.

## Arbeitsplan
1. Remove explicit `Wikipedia` labels from the earliest theory source lines.
2. Mirror the edits into `research/`.
3. Validate formatting and parity.
4. Measure the remaining source-hygiene surface.
5. Commit and push the partial pass.

## Umgesetzte Aenderungen
- `ki-chronologie-06-theorie-kritik.md`
- `research/ki-chronologie/ki-chronologie-06-theorie-kritik.md`

Changed source lines:
- Plato, Aristotle, Descartes, Hobbes, La Mettrie, Leibniz
- Boole, Babbage, Ada Lovelace, Nietzsche, William James
- Wittgenstein, Heidegger, Ryle
- John Searle, Dreyfus

## Validierung
- `git diff --check`
- `diff -q` between root and `research/` copies of the theory file
- `rg -n "Wikipedia" ... | wc -l` to measure remaining surface

## Naechste Schritte
- Commit this first theory hygiene slice.
- Push the commit to `origin/master`.
- Continue with additional slices in the same file until the remaining Wikipedia surface is reduced further.
