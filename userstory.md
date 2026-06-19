# User Story: Chrome History Plugin wiederherstellen und modernisieren

**Status:** In Arbeit  
**Branch:** `claude/exciting-franklin-c2ua11`  
**Ziel-Version:** `v1.0.0` (neues Plugin)

---

## Kontext

Erik hat ein bestehendes Keypirinha-Plugin für die Chrome-History. Seit dem Umzug auf einen neuen Rechner funktioniert es nicht mehr. Das Plugin soll modernisiert und wieder lauffähig gemacht werden.

**Keyword:** `ch`  
**Funktion:** Chrome-Browser-History in Keypirinha durchsuchen und URLs öffnen/kopieren

---

## Bisheriges Setup (alter Rechner)

### Preprocessing-Pipeline
1. **`chrome-hist-prerocess.cmd`** – Kopiert Chrome-DB und exportiert via externem `sqlite3.exe`-Tool zu CSV
2. **`chrome-history.py`** (Jupyter-Notebook-Stil) – Filtert CSV via `pandas`, dedupliziert, exportiert `clean-history.csv`
3. Windows Task Scheduler ruft das regelmäßig auf

### Keypirinha Plugin
- **`plugin-chrome-history.py`** – Liest `clean-history.csv`, zeigt Einträge in Keypirinha

### Bekannte Probleme des alten Setups
- Hardcodierte Pfade `c:\users\e17\...` → auf neuem Rechner kaputt
- Externe Abhängigkeit: `sqlite3.exe` CLI (nicht in Windows enthalten)
- `pandas` als Dependency (fragil, Versions-Konflikte möglich)
- Bug: Titel mit `{` crashen das Plugin (`.format()` auf Titel)
- Keine INI-Konfiguration – alles hardcodiert

---

## Geklärte Anforderungen

| Frage | Antwort |
|-------|---------|
| Username-Pfade | `%USERPROFILE%` dynamisch nutzen |
| URL-Filter | Konfigurierbar in INI (Firmen-Domain oder leer = alle) |
| Filter-Listen (discard_title/url) | Konfigurierbar in INI |
| CSV-Speicherort | `%USERPROFILE%\Documents\tmp\`, konfigurierbar in INI |
| Python-Tooling | `uv` für Preprocessing + Tests |

---

## Konzept: Neue Architektur

### Zwei Komponenten

```
Component 1: chrome-history-preprocess.py
  → Reines Python (sqlite3, shutil, csv, configparser – nur Stdlib)
  → Konfigurierbar via INI
  → Via `uv run` aufrufbar, Task Scheduler-fähig

Component 2: keypi_chromehistory/__init__.py  
  → Keypirinha Plugin
  → Liest CSV (Pfad aus INI)
  → Fixes: {} Bug, Error-Handling, konfigurierbare Optionen
```

### Neue Ordnerstruktur

```
keypi_chromehistory/
├── __init__.py                      # Plugin-Hauptklasse
├── lib/
│   └── __init__.py                  # Package Marker
├── res/
│   ├── keypi_chromehistory.ini      # Config-Template für Nutzer
│   └── changelog/
│       └── 1.0.0.md
├── chrome-history-preprocess.py     # Preprocessing (ersetzt CMD + altes py)
├── pyproject.toml                   # uv Projekt-Config + ruff + pytest
└── tests/
    ├── __init__.py
    └── test_preprocess.py           # Unit Tests für Filter-Logik
```

### INI-Konfiguration (Template)

```ini
[main]
keyword = ch
csv_path = %USERPROFILE%\Documents\tmp\chrome-history-clean.csv

[preprocess]
# Chrome History SQLite DB (automatisch mit %LOCALAPPDATA% aufgelöst)
chrome_db = %LOCALAPPDATA%\Google\Chrome\User Data\Default\History
output_csv = %USERPROFILE%\Documents\tmp\chrome-history-clean.csv
# URL-Filter: Nur URLs die dieses Muster enthalten (leer = alle)
url_filter =

[filter_out_titles]
# Titel-Muster die ausgeblendet werden (kommasepariert)
exclude = Login, Anmelden

[filter_out_urls]
# URL-Muster die ausgeblendet werden (kommasepariert)  
exclude = editpage, createpage, edit-v2
```

### Preprocessing-Script: Was es tut

1. INI-Datei laden (Pfad als Argument oder Default)
2. `%ENV_VAR%` in Pfaden auflösen
3. Chrome DB kopieren (Chrome sperrt Original)
4. SQLite-Query: `SELECT title, url, last_visit_time FROM urls ORDER BY last_visit_time DESC`
5. URL-Filter anwenden (if configured)
6. Ausschlusslisten anwenden
7. Nach Titel deduplizieren (neuester Besuch gewinnt)
8. Als CSV nach `output_csv` exportieren (Trennzeichen: `;`)
9. Temp-Kopie der DB löschen

### Plugin: Wichtigste Fixes

- **`{}` Bug gefixt**: `target=f"ch_{index}"` statt `.format()` auf Titel
- **URL in `data_bag`**: sauber getrennt von `label` und `short_desc`
- **Pfad aus INI**: kein hardcodierter Pfad mehr
- **Fehler-Handling**: Wenn CSV nicht existiert → hilfreiche Meldung statt Crash

---

## Vorgehensplan

### Phase 0: Vorbereitung
- [x] User Story verfeinert (Anforderungen geklärt)
- [x] Git Tag für letztes Feature erstellt (v1.0.0 → PMB-State)
- [x] Branch ist `claude/exciting-franklin-c2ua11` ✓

### Phase 1: Projekt-Setup
- [x] `pyproject.toml` anlegen (uv, ruff, pytest)
- [x] Ordnerstruktur anlegen (`res/`, `tests/`)
- [x] `res/keypi_chromehistory.ini` Template erstellen

### Phase 2: Preprocessing Script
- [x] `chrome_history_preprocess.py` entwickeln
  - [x] INI lesen mit Pfad-Auflösung (`%ENV_VAR%` via `os.path.expandvars`)
  - [x] Chrome DB kopieren (shutil)
  - [x] SQLite Query ausführen
  - [x] URL-Filter anwenden
  - [x] Title/URL-Ausschlusslisten anwenden
  - [x] Deduplizierung (neuester Besuch pro Titel)
  - [x] CSV exportieren (`;`-Trennzeichen, keine Header)
  - [x] Temp-Dateien aufräumen
  - [x] CLI-Argumente: `--config` (Pfad zur INI)

### Phase 3: Unit Tests (Preprocessing)
- [x] `tests/test_preprocess.py` schreiben (25 Tests)
  - [x] Test: URL-Filter (match / kein match / leer = alle / case-insensitive)
  - [x] Test: Title-Ausschluss (mehrere Pattern, Whitespace, Case-insensitive)
  - [x] Test: URL-Ausschluss
  - [x] Test: Deduplizierung (neuester Eintrag gewinnt)
  - [x] Test: CSV Export (Datei, Delimiter, Roundtrip, Verzeichnis anlegen)
  - [x] Test: SQLite lesen (Anzahl, Sortierung, leere Titel)
- [x] `uv run pytest` → 25/25 grün

### Phase 4: Keypirinha Plugin
- [x] `__init__.py` entwickeln
  - [x] INI lesen (`keyword`, `csv_path`)
  - [x] `on_start()` – Actions registrieren
  - [x] `on_catalog()` – Keyword registrieren
  - [x] `on_suggest()` – CSV lesen, Items erstellen
  - [x] `on_execute()` – URL öffnen / in Clipboard
  - [x] `on_events()` – Config-Changes behandeln
  - [x] Bug-Fix: `target=f"ch_{idx}"` (kein `.format()`)
  - [x] Error-Handling: CSV fehlt / leer / nicht lesbar
  - [x] Keypirinha-Stub für Test-Kompatibilität

### Phase 5: DoD & Qualität
- [x] `uv run ruff check .` → keine Fehler
- [x] `uv run ruff format --check .` → keine Fehler
- [x] `uv run pytest` → 25/25 Tests grün
- [x] Debug-Logging entfernt (war nie drin)

### Phase 6: Dokumentation
- [x] `documentation.md` aktualisieren (Chrome History Plugin-Abschnitt)
- [x] `KEYPIRINHA-LEARNINGS.md` – neue Erkenntnisse hinzufügen
- [x] `res/changelog/1.0.0.md` erstellen
- [x] Task-Scheduler-Anleitung in `documentation.md`

### Phase 7: Commit & Push
- [ ] Version: `v1.0.0-dev.1` gesetzt ✓
- [ ] Commit + Push zu `claude/exciting-franklin-c2ua11`

---

## Offene Fragen / Notizen

- Welche Firmen-Domain soll als Default in `url_filter` stehen? (oder leer lassen als Default)
- Task-Scheduler: Nur dokumentieren oder auch ein Setup-Script erstellen?

---

## Definition of Done

- [ ] Plugin lädt in Keypirinha ohne Fehler
- [ ] `ch` → zeigt History-Einträge
- [ ] Fuzzy-Suche funktioniert
- [ ] URL öffnen (Enter) funktioniert
- [ ] URL kopieren (Tab → Aktion) funktioniert
- [ ] Konfiguration über INI-Datei möglich
- [ ] Preprocessing Script läuft via `uv run`
- [ ] Alle Tests grün
- [ ] ruff clean
- [ ] Dokumentation aktualisiert
