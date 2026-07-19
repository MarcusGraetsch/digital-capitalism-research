# Projektanweisungen: Digital Research

## Einordnung

- **Arbeitsmodus:** `research-knowledge`
- **Status dieser Einordnung:** vorläufig; beim ersten echten Projektreview anhand von README, Git-Remote und Builddateien verifizieren
- **Kanonischer Scope:** dieses Projektverzeichnis nach Auflösung mit `realpath`

## Zweck

Forschungs-, Wissens-, Planungs- oder Publikationsprojekt. Quellenprovenienz und Trennung von Befund, Interpretation und These erhalten.

## Verbindlicher Start

1. Globale `~/.openclaw/AGENTS.md` lesen.
2. Passenden Modus-Prompt unter `~/.openclaw/prompts/` lesen.
3. `realpath .`, Git-Root, Branch, Status und letzte Commits bestimmen.
4. README, CONTRIBUTING, Architektur-, Build- und Deploymentdateien lesen.
5. Vorhandenen projektlokalen `AGENT_CHANGELOG.md` und neueste relevante Reports lesen.
6. Schreibscope auf dieses Projekt begrenzen.

## Projektkonventionen ermitteln

Beim ersten Einsatz diese Datei konkretisieren um:

- tatsächlichen Projektzweck
- Sprache, Framework und Laufzeit
- Architektur und zentrale Einstiegspunkte
- Installations-, Test-, Build- und Startbefehle
- Deployment- und Rollbackverfahren
- geschützte Daten und Verzeichnisse
- Definition of Done

Erfinde fehlende Befehle nicht. Leite sie aus vorhandenen Dateien ab und teste sie.

## Dokumentation

Größere Ergebnisse speichern unter:

```text
docs/agent-reports/YYYY/
```

Substantielle Sessions in `AGENT_CHANGELOG.md` dokumentieren. Falls diese Dateien
noch fehlen, dürfen sie beim ersten größeren Auftrag angelegt werden.

## Git

Commit und Push dürfen ausschließlich dieses Repository betreffen. Fremde oder
bereits vorhandene Änderungen nicht überschreiben oder ungeprüft einbeziehen.
