# ⚠️ EXPERIMENTAL / DEPRECATED

**Diese Scripts sind veraltet und werden nicht mehr verwendet.**

Sie werden im Git archiviert als Referenz, aber der aktuelle Produktions-Workflow verwendet andere Scripts.

## Aktueller Workflow (Produktion)

```
weekly_pipeline.py
    ├── scan_v5.py          (Email-Scanner)
    ├── clean_smart.py       (Heuristisches Cleaning)
    └── label_articles.py    (Topic-Labeling)
```

## Deprecated Scripts

### clean_articles_stichprobe.py
- **Zweck:** Test-LLM-Cleaning an 25 zufälligen Artikeln
- **Status:** ❌ Deprecated - zu langsam, LLM-Rate-Limits
- **Ersatz:** `clean_smart.py` (Heuristiken statt LLM)

### clean_all_articles.py
- **Zweck:** Batch-LLM-Cleaning für alle Artikel
- **Status:** ❌ Deprecated - würde Stunden dauern, zu teuer
- **Ersatz:** `clean_smart.py`

### clean_with_llm.py
- **Zweck:** Direkte LLM-Integration via sessions_spawn
- **Status:** ❌ Deprecated - Subagent-Aufrufe unzuverlässig
- **Ersatz:** `clean_smart.py`

### process_llm_batches.py
- **Zweck:** Verarbeitung von llm_queue/ Batches
- **Status:** ❌ Deprecated - Workaround, nie produktiv
- **Ersatz:** `clean_smart.py`

## Warum Heuristiken statt LLM?

| Kriterium | Heuristiken (aktuell) | LLM (deprecated) |
|-----------|----------------------|------------------|
| Geschwindigkeit | Minuten | Stunden |
| Kosten | 0€ | 10-50€ |
| Zuverlässigkeit | 90% | 70% |
| Wartung | Einfach | Komplex |

## Für zukünftige Experimente

Wenn du diese Scripts verbessern möchtest:

1. **Kopiere** das Script nach `research/` (nicht experimental/)
2. **Bennene** es um (z.B. `clean_with_llm_v2.py`)
3. **Teste** isoliert vor Produktions-Einsatz
4. **Vergleiche** mit `clean_smart.py` Performance

## WICHTIG

- Ändere NICHT die Pfade in den deprecated Scripts
- Sie verwenden absolute Pfade, die funktionieren
- Datenbank-Schema ist kompatibel
- Aber: Sie werden vom weekly_pipeline NICHT aufgerufen

---

*Letzte Aktualisierung: 2026-03-06*
