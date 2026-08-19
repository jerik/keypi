# Plugin filelookup optimieren und erweitern
Ich habe ein Plugin, siehe keypi_filelookup womit eine Textdatei geparst wird. In der Textdatei siehe keypi_filelookup/winevent.log, sind die login/logout events gespeichert. Daraus lese ich, wann ich mit meiner Arbeit angefangen habe. 


Aktuell mein der Workflow so aus: 

    1. keypi launchbox starten 
    2. keyword 'fl' eingeben
    3. Es werden die Zeiten angezeigt, samt Datum 

    Beispielsweise Mi 09:04

Dann weiss ich das ich am Mittwoch um 09:04 angefangen habe. 

Was ich dann im Kopf mache ist: 
    a) Ich rufe die Launchbox mit keywordk 'fl' um 17:09 Uhr auf
    b) Ich rechne 17-9 = 8h die ich gearbeitet habe. Ich runde die Zahlen meistens auf 15 Minuten einheiten. 
    c) ich ziehe meine Mittagspause ab 8h - 1h = 7h 
    d) ich habe 7h gearbeitet. Das nutze ich um es in den Stundennachweis einzutragen


# Aufgabe
1) Bitte review das plugin und optimiere es. 

2) Meine Workflow möchte ich nun optimieren. 

    1. keypi launchbox starten (um 17:09)
    2. keyword 'fl' eingeben
    3. Es werden die Zeiten angezeigt, samt Datum, (bspw. 09:04)
    4. ich wähle ein Datum aus (via Tab)
    5. Es werden mit Optionen angezeigt: 
            8h ohne Pause
            7h mit 1h Pause
            6,5h mit 1,5h Pause
    6. Ich wähle einen Eintrag aus, bspw. 7h mit 1h Pause
            Dann wird in die Datei ~/Documents/logs/Journal.log folgender Eintrag angehängt:

                # Mi 2026-08-19 1709:44
                @arbeitsstunden am 2026-08-19: 7h 


Lies dir die Dateien development-best-practise.md, documentation.md und KEYPIRINHA-LEARNINGS.md durch

Sofern rückfragen sind, kläre diese mit mir im Dialog. 
Erstelle ein Konzept und ein Plan wie das vorhaben umgesetzt werden kann. 
Die Dokumentation (KEYPIRINHA-LEARNINGS.md, README.md, development-best-practice.md, documentation.md) muss nach der erstellung auf dem aktuellsten Stand sein. 
Wenn ich Konzept und Plan freigegeben haben, kannst du mit der Umsetzung anfangen.

# Entwicklungshinweise
- beachte die git richtlinien
- Orientiere dich bei der Entwicklung an den vorhanden plugins. Falls noch nicht vorhanden lege eine development-best-practise.md wo die wichtigsten Inforamtionen drinstehen, sodass das llm nicht immer den ganze code durchlesen muss um das zu verstehen
- Erstelle Testfälle.
- Push in git erfolgt erst wenn testfälle alle grün sind. Das übernimmst du selbsttändig. 

---

# Konzept & Plan (Claude, 2026-08-19)

## Entscheidungen aus dem Dialog

| Frage | Entscheidung |
|-------|--------------|
| Mehrere Sessions pro Tag | **Kein Tagesaggregat.** Jedes `gestartet`-Event bleibt ein eigener Eintrag in der Liste (wie bisher) |
| Endzeit | **Automatisch**: heute/offene Session → aktuelle Uhrzeit, vergangene Session → zugehöriges `beendet`-Event |
| Rundung | **Differenz runden**: `Ende - Start` roh rechnen, dann auf 15 Minuten kaufmännisch runden (17:09 - 09:04 = 8h 05m → 8h 00m) |
| Pausen | **Konfigurierbar** in der INI, Default `0, 60, 90` Minuten |
| Paket | **Umbenennung** `keypi_filelookup` → `keypi_worklog`, Keyword bleibt `fl` |

## Teil 1 — Review des bestehenden Plugins

Gefundene Probleme in `keypi_filelookup/file_lookup.py`:

**Korrektheit**
1. `getday()` nutzt `date.today().year` → Einträge vom Vorjahr (Log enthält Mai–Aug ohne Jahr) bekommen das falsche Jahr und damit den falschen Wochentag.
2. `locale.setlocale(locale.LC_TIME, "de_DE")` wird global gesetzt → wirkt prozessweit auf alle anderen Keypirinha-Plugins und wirft `locale.Error`, wenn das Locale auf dem System nicht existiert.
3. `round_quater(minute)` fehlt `self`, ist nie aufgerufen und die Grenzen sind falsch (Minute 37 fällt in den `else`-Zweig → 0 statt 45).
4. `until_now()` ist kaputt: `ts.replace(hour=7, minute=minute)` mit `minute` als String → `TypeError`; Ergebnis wird verworfen.
5. `_get_filecontent()` wirft `UnboundLocalError`, sobald `[files]` nicht **genau einen** Eintrag hat; fehlende/nicht lesbare Datei wird nicht abgefangen.
6. Feste Spalten-Slices (`monthday[9:15]`, `[16:]`) plus `split('Information')` → bricht, sobald sich die Spaltenbreite des Logs ändert.
7. Nur die ersten 30 Zeilen werden gelesen (hart kodiert, nicht konfigurierbar).

**Sicherheit / Verhalten**
8. Die Aktionen `Open bookmark` / `Copy bookmark` bauen `cmd /K start {short_desc}` — übergeben wird die *Beschreibung* (`"Aug 19 #34 gestartet"`), nicht ein Pfad. Sinnfrei und zugleich Shell-Injection über Dateiinhalt.
9. `subprocess.call()` blockiert den UI-Thread (verstösst gegen die Projektregel „NIEMALS UI blockieren").
10. `_get_filecontent()` wird in `on_suggest()` **vor** der `items_chain`-Prüfung aufgerufen → Datei-I/O bei jedem Tastendruck, auch ausserhalb des Plugins.

**Struktur / Standards**
11. Kein Package-Layout (`file_lookup.py` statt `__init__.py`, kein `lib/`, kein `res/`), INI-Template liegt im Paket-Root.
12. Kein `VERSION`, kein Versions-Log in `on_start()`, kein `#edit`-Shortcut — anders als alle anderen Plugins.
13. Klassenname `file_lookup` verstösst gegen PEP 8; toter Code (`OLD_get_filecontent`, `_bookmarks`, `_directories`, `_file`), ungenutzte Imports (`fileinput`, `re`, `kpnet`), Klassen- statt Instanzattribute für Zustand (`_box`).
14. `winevent.log` (echte, persönliche Logdaten) lag im Paketverzeichnis und war versioniert → jetzt in `.gitignore`, aus der Versionierung entfernt; Tests bekommen ein eigenes, anonymisiertes Fixture.

→ Das Plugin wird nicht gepatcht, sondern als `keypi_worklog` neu aufgebaut; alle Punkte oben sind damit erledigt.

## Teil 2 — Zielarchitektur

```
keypi_worklog/
├── __init__.py               # WorkLog(kp.Plugin) — nur Keypirinha-UI, keine Fachlogik
├── lib/
│   ├── __init__.py
│   └── worklog.py            # reine Fachlogik, KEINE keypirinha-Imports → direkt testbar
└── res/
    ├── keypi_worklog.ini     # Config-Template
    └── changelog/1.0.0.md
tests/
├── fixtures/winevent_sample.log  # anonymisiertes Beispiel-Log (echtes winevent.log ist gitignored)
└── test_worklog.py           # importiert lib/worklog.py per importlib (kein Copy-Paste mehr)
```

`lib/worklog.py` (reine Funktionen, keine Seiteneffekte ausser Datei-I/O beim Journal):

| Funktion | Zweck |
|----------|-------|
| `parse_events(text, start_marker, stop_marker)` | Log → Liste von Events (Monat, Tag, Zeit, Typ) per Regex, ohne feste Spalten |
| `resolve_years(events, today)` | Jahr ergänzen: Log ist absteigend sortiert; steigt `(Monat, Tag)` gegenüber dem vorigen Eintrag, wird das Jahr dekrementiert → Jahreswechsel korrekt |
| `build_sessions(events, now, max_entries)` | Jedes `gestartet` bekommt das nächste spätere `beendet`; ohne Partner = offene Session → Ende `now` |
| `round_minutes(minutes, step=15)` | Kaufmännische Rundung der **Differenz** |
| `format_hours(minutes)` | `480 → "8h"`, `390 → "6,5h"`, `435 → "7,25h"` (deutsches Dezimalkomma) |
| `format_duration(minutes)` | `485 → "8h 05m"` für die Anzeige der Rohzeit |
| `build_break_options(minutes, breaks)` | Liste `[{break, net_minutes, label}]`, negative Ergebnisse entfallen |
| `render_journal_entry(dt, date, hours, header_tpl, entry_tpl)` | Journal-Text bauen |
| `append_journal_entry(path, text)` | Anhängen, Verzeichnis anlegen, Leerzeile davor wenn nötig |
| `journal_contains_date(path, date, entry_tpl)` | Duplikat-Erkennung für den Hinweis „bereits erfasst" |

Wochentage (`Mo`–`So`) und Monatsnamen (`Jan`–`Dez` deutsch **und** englisch) über eigene Tabellen — **kein** `locale`.

## Teil 3 — Zielworkflow

**Schritt 1 — `fl` + Tab**
Liste der letzten Starts, neueste zuerst:
```
Mi 09:04    2026-08-19 · KW 34 · läuft · bisher 8h 05m
Di 08:10    2026-08-18 · KW 34 · bis 17:28 · 9h 18m
Mo 09:14    2026-08-17 · KW 34 · bis 16:41 · 7h 27m
```

**Schritt 2 — Tab auf einen Eintrag**
(`args_hint=ACCEPTED`, `hit_hint=KEEPALL`, `loop_on_suggest=True`, keine `set_actions()` auf dieser Kategorie)
```
8h              ohne Pause      · 09:04–17:09 → gerundet 8h 00m
7h              1h Pause        · 8h 00m - 1h
6,5h            1,5h Pause      · 8h 00m - 1,5h
```

**Schritt 3 — Enter**
Anhängen an `~/Documents/logs/Journal.log`:
```
# Mi 2026-08-19 17:09:44
@arbeitsstunden am 2026-08-19: 7h
```
Zweite Aktion im Tab-Menü: „Copy to clipboard" (Eintrag statt Datei-Schreibzugriff).

**Shortcuts:** `#edit` (INI öffnen), `#journal` (Journal.log öffnen), `#source` (winevent.log öffnen).

## Teil 4 — Konfiguration (`res/keypi_worklog.ini`)

```ini
[main]
keyword = fl
winevent_log =
journal_file =
break_options = 0, 60, 90
rounding_minutes = 15
max_entries = 30
event_start_marker = gestartet
event_stop_marker = beendet
journal_header = # {weekday} {date} {time}
journal_entry = @arbeitsstunden am {date}: {hours}
```

Fallback `journal_file`: `<Dokumente>\logs\Journal.log` über `kpu.shell_known_folder_path()`.

## Teil 5 — Testfälle (`tests/test_worklog.py`)

- Parsing: gültige Zeilen, Rauschzeilen, leere Datei, unbekannter Monatsname
- Jahreslogik: Jahreswechsel Dez→Jan, Log ohne Jahresangabe, Schaltjahr 29.02.
- Session-Bildung: Start ohne Ende (offen), Start/Ende über Mitternacht, mehrere Sessions pro Tag, `max_entries`
- Rundung: 8h 05m → 8h 00m, 8h 08m → 8h 15m, exakte Viertelstunde, 0 Minuten, negative Differenz
- Formatierung: `8h`, `6,5h`, `7,25h`, `0h`
- Pausen-Optionen: Default 0/60/90, Pause > Arbeitszeit, konfigurierte Liste, fehlerhafte INI-Werte
- Journal: Format exakt wie User Story, Anhängen an bestehende Datei, Anlegen bei fehlender Datei, Verzeichnis anlegen, Duplikat-Erkennung
- Config-Parsing: `break_options` mit Leerzeichen/ungültigen Werten

## Teil 6 — Umsetzungsschritte

1. `keypi_worklog/` mit `lib/worklog.py` anlegen (Fachlogik + Tests zuerst)
2. `tests/test_worklog.py` + Fixture, bis grün
3. `keypi_worklog/__init__.py` (Plugin-Klasse nach Mindbox-/PMB-Muster), `res/keypi_worklog.ini`, `res/changelog/1.0.0.md`
4. `keypi_filelookup/` entfernen (echtes `winevent.log` bleibt lokal, ist gitignored)
5. Doku: `README.md`, `documentation.md`, `KEYPIRINHA-LEARNINGS.md`, `development-best-practice.md`
6. DoD: `ruff check .`, `ruff format --check .`, `pytest` — erst dann Push auf `claude/keypi-userstory-review-4an7tw`

## Geklärte Punkte

- **Zeitstempel im Journal:** `# Mi 2026-08-19 1709:44` ist **kein** Tippfehler, sondern das gewünschte Format. Die Uhrzeit wird als `%H%M:%S` ausgegeben (Stunde und Minute ohne Trenner, danach die Sekunden). Default-Template: `journal_header = # {weekday} {date} {time}`, `{time}` = `1709:44`. Über die INI änderbar.
- **Git Tags:** Der letzte Commit auf `main` war ohne Tag. Es wird `v1.6.0` auf den aktuellen `main`-Stand gesetzt (höchste dokumentierte Version ist JQE v1.5.0 → nächste Minor-Version).

- **Persönliche Daten:** `winevent.log` und `Journal.log` sind in `.gitignore` aufgenommen und aus der Versionierung entfernt. Die Tests arbeiten mit `tests/fixtures/winevent_sample.log` (anonymisiertes Beispiel, gleiche Struktur).
