# Session Review: Theorie & Kritik Quellenhygiene, Teil 3

Date: 2026-06-16

## Lagebild
The theory-and-critique chronology had the densest source-hygiene debt in the repository. In this slice I removed the remaining explicit `Wikipedia` labels from the later critical-theory, postcolonial, and labor/economy sections.

## Befunde
- The file now has zero explicit `Wikipedia` matches.
- The cleaned sections now read with only the remaining named sources and institutional/author references.
- The root chronology and the `research/` mirror must stay identical.

## Arbeitsplan
1. Remove the remaining explicit Wikipedia labels from the later theory sections.
2. Mirror the edits into `research/`.
3. Validate formatting and parity.
4. Measure the remaining source-hygiene surface.
5. Commit and push the completed pass.

## Umgesetzte Aenderungen
- `ki-chronologie-06-theorie-kritik.md`
- `research/ki-chronologie/ki-chronologie-06-theorie-kritik.md`

Changed source lines:
- Hugging Face, DAIR, AI Now Institute
- St. Martin's Press, Crown, MIT Press, Stanford University Press
- Yale University Press, Oxford University Press, Basic Books
- Duke University Press, Princeton University Press, Harvard University Press, Routledge, Pantheon
- Grove Press, Monthly Review Press, Vintage
- University of Minnesota Press, NYU Press, University of Michigan Press
- Polity Press, W.W. Norton, Tarcher/Putnam, Verso Books, Houghton Mifflin

## Validierung
- `git diff --check`
- `diff -q` between root and `research/` copies of the theory file
- `rg -n "Wikipedia"` returned `0` matches in the theory file

## Naechste Schritte
- Commit the completed theory hygiene pass.
- Push the commit to `origin/master`.
- Move on to the next file only if another major source-hygiene target remains.
