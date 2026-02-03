# better cqe history feature

You are an expert Keypirinha plugin developer (Python) and you know the Keypirinha Plugin API.

Ziel
Erstelle mir für die cqe ein analoges feature wie bei jqe, siehe archive/20260128-jqe-query-history-userstory.md

Entwicklung
- [x] Beachte die Git richtlinien
- [x] Das Feature soll gut getestet sein
- [x] Commite regelmässig
- [x] Aktualisieren deinen Fortschritt
- [x] Aktualisiere am Ende die dokumentation, README.md, documentation.md, KEYPIRINHA-LEARNING.md

## Fortschritt

### Implementiert (v1.3.0-dev.1)
- [x] History storage (JSON file handling)
- [x] `#history` command to show recent CQL queries
- [x] `#history clear` command to clear all history
- [x] `history_max_entries` config option (default: 30)
- [x] Virtual Query Mode: Tab on history entry executes query directly
- [x] Duplicate handling (same query moves to top)
- [x] 32 unit tests for CQE history feature
- [x] DoD checks pass (ruff check, ruff format, pytest)
- [x] Documentation updated (documentation.md, KEYPIRINHA-LEARNINGS.md)
- [x] Changelog created (keypi_cqe/res/changelog/1.3.0.md)
