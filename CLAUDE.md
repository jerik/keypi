# KeyPi - Jira Query Explorer

Keypirinha-Plugin für direktes Abfragen von Jira Cloud mittels JQL (Jira Query Language) aus dem Keypirinha-Launcher.

---

## 📁 Projektstruktur

```
keypi/
├── CLAUDE.md                    # Diese Datei - Projektregeln & Standards
├── USER-STORY.md                # Aktuelle Feature-Arbeit (Dialog zwischen Erik & Claude)
├── BACKLOG.md                   # Feature-Ideen & Roadmap (Erik pflegt, Claude liest)
├── documentation.md             # Endnutzer-Dokumentation (Claude aktualisiert)
├── archive/                     # Abgeschlossene User Stories
│   └── YYYYMMDD-*.md           # Archivierte Spezifikationen
├── keypi_jqe/                   # Haupt-Plugin-Package
│   ├── __init__.py             # Plugin-Hauptklasse (erbt von keypirinha.plugin.Plugin)
│   ├── lib/                    # Interne Libraries
│   │   ├── __init__.py         # Package Marker
│   │   └── jira_client.py      # Jira API Client Wrapper
│   └── res/                    # Ressourcen & Konfiguration
│       ├── keypi_jqe.ini       # Benutzer-Konfigurationsdatei (Template)
│       ├── packages.json       # Package-Metadaten für Package Control
│       └── changelog/          # Versionshistorie
└── .gitignore                  # Git Ignore Rules
```

---

## 🔄 Entwicklungs-Workflow

### Neues Feature starten

1. **Erik** erstellt `USER-STORY.md` mit Feature-Beschreibung
2. **Erik + Claude** verfeinern `USER-STORY.md` im Dialog
   - Anforderungen klären
   - Technische Details festlegen
   - Offene Fragen beantworten
3. **Claude** liest:
   - `CLAUDE.md` (diese Datei) → Projektregeln
   - `USER-STORY.md` → Aktuelle Feature-Spec
   - `BACKLOG.md` → Kontext & Synergien
   - `KEYPIRINHA-LEARNINGS.md` → Best Practices & Lessons Learned
   - **Prüft Git Tags**: Checkt ob nach letztem Merge auf `main` ein Git Tag fehlt
     - Falls Tag fehlt: Erstellt Tag mit nächster Minor-Version (z.B. v1.1.0 → v1.2.0)
     - Tag-Format: `v{major}.{minor}.{patch}` (z.B. v1.2.0)
     - Regel: Mittlere Zahl (minor) wird +1 erhöht pro Feature-Release
4. **Claude** implementiert Feature
   - Aktualisiert Checkboxen in `USER-STORY.md` während Arbeit
   - Hält sich an Code-Standards
   - Führt DoD durch (siehe unten)
5. **Erik + Claude** besprechen Ergebnis
   - Testing
   - Bugfixing
   - Nachbesserungen
6. **Claude** aktualisiert `documentation.md` mit neuen Features
7. **Erik** verschiebt `USER-STORY.md` → `archive/YYYYMMDD-done-user-story.md`
8. **Nächstes Feature:** Erik erstellt neue `USER-STORY.md`

### Feature-Backlog

- **BACKLOG.md** enthält zukünftige Feature-Ideen (Erik pflegt)
- **Claude liest BACKLOG.md IMMER mit**, um Implikationen & Synergien zu erkennen
- Bei Diskussionen: Synergien aus Backlog aktiv ansprechen

---

## 🎯 Definition of Done (DoD)

**WICHTIG:** Vor jedem Commit müssen folgende Checks durchgeführt werden:

```bash
# 1. Code-Style prüfen
ruff check .

# 2. Code-Formatierung prüfen
ruff format --check .

# 3. Tests ausführen (falls vorhanden)
pytest

# Wenn Checks fehlschlagen: Iteriere bis alle grün sind!
```

### Abschluss-Checklist

Am Ende jeder Feature-Implementierung:
- [ ] Alle Checkboxen in `USER-STORY.md` abgehakt
- [ ] DoD durchgeführt (ruff, pytest)
- [ ] `documentation.md` aktualisiert
- [ ] Changelog in `keypi_jqe/res/changelog/` aktualisiert
- [ ] `KEYPIRINHA-LEARNINGS.md` mit neuen Erkenntnissen aktualisiert
- [ ] Manuelle Tests durchgeführt
- [ ] Kurze Zusammenfassung erstellt (was geändert, wie getestet)

---

## 💻 Tech Stack

- **Framework**: Keypirinha Plugin API
- **Sprache**: Python 3
- **API**: Jira Cloud REST API v3
- **Authentifizierung**: Atlassian API Keys (Basic Auth)
- **Konfiguration**: INI-Format
- **Distribution**: Keypirinha Package Control (GitHub)
- **Testing**: pytest (optional)
- **Linting**: ruff

---

## 📝 Code-Standards

### Python-Konventionen
- **PEP 8** Style Guide strikt befolgen
- Code und Kommentare im Quellcode **nur in Englisch**
- Git-Commits **nur in Englisch**
- Type Hints wo sinnvoll verwenden
- Docstrings für alle öffentlichen Methoden

### Keypirinha-Spezifisch
- Plugin-Klasse **muss** von `keypirinha.plugin.Plugin` erben
- Pflicht-Methoden implementieren:
  - `on_catalog()` - Catalog Items registrieren
  - `on_suggest()` - User Input verarbeiten
  - `on_execute()` - Aktionen ausführen
  - `on_events()` - Config-Changes behandeln
- **NIEMALS** UI blockieren - Async/Non-blocking für API-Calls
- `kp.shell_execute()` für Browser-URLs nutzen
- Keypirinha übernimmt Live-Filtering - nur Daten bereitstellen

### Error Handling
- Umfassendes Error Handling für API-Requests
- Benutzerfreundliche Fehlermeldungen in Keypirinha anzeigen
- Logging für Debugging implementieren (`self.info()`, `self.warn()`, `self.err()`)
- Network Errors abfangen (Timeout, Offline)
- Rate Limiting behandeln (429 Fehler)
- Auth-Fehler klar kommunizieren (401/403)

### API-Kommunikation
- **NUR** über `lib/jira_client.py`, **NICHT** direkt in Plugin-Klasse
- JQL-Syntax validieren vor API-Request
- Timeouts für API-Requests setzen (aktuell: 10 Sekunden)
- Custom Exceptions nutzen (`JiraAuthError`, `JiraAPIError`, `JiraNetworkError`)

---

## 🎨 Projektspezifische Regeln

### Plugin-Verhalten
- **Keyword**: Plugin reagiert auf `jqe` in Keypirinha
- **Ergebnis-Format**: `TICKET-ID: [Status] Summary`
- **Datenfelder**: TicketID, Summary, Status, Priority, Creator, Assignee, CreatedDate
- **Filtern**: Keypirinha macht Live-Filtering - Plugin liefert nur Daten

### Konfiguration
- API-Key in `keypi_jqe.ini` speichern (**NICHT** im Code)
- Konfigurationsdatei liegt im User-Verzeichnis (`%APPDATA%\Keypirinha\User\`)
- Template mit leeren Werten im Plugin committen
- **NIEMALS** Credentials in Git committen

### API-Endpunkte
- **Current**: `/rest/api/3/search/jql` (nicht `/rest/api/3/search` - ist deprecated/410 Gone)
- Basic Auth: Email + API Token (nicht Passwort!)
- Max Results: 50 (konfigurierbar in `jira_client.py`)

---

## 🚨 Häufige Fehler vermeiden

### NICHT tun:
- ❌ API-Keys im Code hardcoden oder unverschlüsselt commiten
- ❌ UI während API-Calls blockieren
- ❌ Ohne Validierung JQL an API senden
- ❌ 401/403 Fehler ignorieren
- ❌ `on_deactivate()` Cleanup vergessen
- ❌ Direkt auf `main` committen/pushen
- ❌ Veraltete API-Endpunkte nutzen

### IMMER tun:
- ✅ Von `keypirinha.plugin.Plugin` erben
- ✅ Alle erforderlichen Methoden implementieren
- ✅ Netzwerkfehler und Rate Limiting behandeln
- ✅ Sinnvolle Defaults in Beispiel-Config bereitstellen
- ✅ `.ini` Dateien mit Credentials in `.gitignore` eintragen
- ✅ DoD durchführen vor jedem Commit
- ✅ In neuem Branch arbeiten (Format: `claude/*`)
- ✅ Code und Kommentare in Englisch

---

## 🔧 Entwicklung & Testing

### Plugin lokal testen

```bash
# 1. Kopiere Plugin-Ordner
cp -r keypi_jqe/ %APPDATA%\Keypirinha\InstalledPackages\

# 2. Erstelle User-Config
# Datei: %APPDATA%\Keypirinha\User\keypi_jqe.ini
# Inhalt: jira_url, atlassian_email, atlassian_api_key

# 3. Keypirinha neu starten
# Drücke: Ctrl + Alt + R

# 4. Plugin testen
# - Tippe: jqe
# - Tab drücken
# - JQL eingeben
# - Enter drücken
```

### DoD ausführen

```bash
# In keypi/ Verzeichnis:
ruff check .
ruff format --check .
pytest  # falls Tests vorhanden
```

### Installation für Endnutzer

- Via Keypirinha Package Control (geplant)
- Manuelle Installation (siehe `documentation.md`)

---

## 📦 Git Workflow

### Branch-Strategie
- **Main Branch**: `main` (geschützt)
- **Feature Branches**: `claude/<feature-name>-<session-id>`
- **NIEMALS** direkt auf `main` pushen
- Commits: Klare, beschreibende Messages (Englisch)
- Conventional Commits verwenden (feat:, fix:, docs:, chore:)

### Session-ID für Git Push (claude.ai/code)
**WICHTIG:** Bei Git Push Problemen (403 Error) - Session-ID wiederverwenden!

- **Problem**: claude.ai/code erlaubt nur Pushes mit authorisierten Session-IDs
- **Lösung**: Nutze Session-ID von einem existierenden Remote Branch
- **Beispiel**:
  ```bash
  # 1. Finde funktionierende Session-ID
  git branch -a | grep claude
  # Output: remotes/origin/claude/add-new-feature-4YXWQ

  # 2. Erstelle neuen Branch mit dieser Session-ID
  git checkout -b claude/jqe-multi-actions-4YXWQ  # Gleiche ID: 4YXWQ

  # 3. Push funktioniert jetzt!
  git push -u origin claude/jqe-multi-actions-4YXWQ
  ```
- **Merke**: Session-IDs wie `4YXWQ`, `5HZNQ` etc. sind nicht beliebig - nur autorisierte IDs funktionieren
- **Best Practice**: Schau in `git branch -a` nach existierenden Remote Branches und verwende deren Session-ID wieder

### Versioning & Git Tags
- **Semantic Versioning**: `v{major}.{minor}.{patch}` (z.B. v1.2.0)
- **Tag-Strategie**:
  - Jedes Feature-Release auf `main` bekommt einen Tag
  - Minor-Version wird +1 erhöht pro Feature (v1.1.0 → v1.2.0)
  - Tags werden automatisch von Claude erstellt (bei Beginn einer neuen User Story)
  - Beispiel: Nach Merge von Filter-Feature → `v1.1.0`
- **Tag-Erstellung**:
  ```bash
  # Claude prüft bei jeder neuen User Story:
  git tag --list  # Checkt existierende Tags
  # Falls Tag für letzten Merge fehlt:
  git tag -a v1.X.0 -m "Release v1.X.0: Feature Name"
  git push origin v1.X.0  # Push to remote
  ```
- **Zweck**: Nachvollziehbarkeit, welches Feature in welcher Version enthalten ist
- **GitHub Releases**: Tags erscheinen automatisch als Releases in GitHub

### Development Version Policy

**WICHTIG:** Bei jedem Commit während der Entwicklung muss die Versionsnummer hochgezählt werden!

#### Version-Format während Entwicklung
- **Dev-Versionen**: `v{major}.{minor}.{patch}-dev.{counter}`
- **Beispiel**: `v1.1.0-dev.1`, `v1.1.0-dev.2`, `v1.1.0-dev.3`, etc.
- **Counter**: Startet bei 1, wird bei jedem Commit +1 erhöht

#### Workflow
1. **Feature Start**: Version auf `v{major}.{minor}.{patch}-dev.1` setzen
   - Beispiel: `VERSION = "1.1.0-dev.1"`

2. **Während Entwicklung**: Bei **jedem Commit** Version hochzählen
   - Commit 1: `v1.1.0-dev.1`
   - Commit 2: `v1.1.0-dev.2`
   - Commit 3: `v1.1.0-dev.3`
   - etc.

3. **Feature fertig**: Bei finaler Dokumentation → Release-Version setzen
   - Beispiel: `VERSION = "1.1.0"` (ohne `-dev.X`)

#### Zweck
- **Debugging**: Im Keypirinha-Log sehen welche Version läuft
- **Nachvollziehbarkeit**: Jeder Commit hat eindeutige Version
- **Testen**: User kann sicher sein dass neue Version geladen wurde

#### Beispiel aus Log
```
ConfluenceQueryExplorer v1.1.0-dev.3 loaded  # Dev-Version
JiraQueryExplorer v1.2.0-dev.7 loaded        # Anderes Plugin, 7. Commit
```

#### Plugin-spezifische Dateien
- **JQE Plugin**: `keypi_jqe/__init__.py` → `VERSION = "..."`
- **CQE Plugin**: `keypi_cqe/__init__.py` → `VERSION = "..."`

**Regel:** Vergiss NIEMALS die Version bei Commits zu erhöhen - sonst wissen wir nicht welche Version läuft!

---

## 📚 Nützliche Ressourcen

### Keypirinha
- **Architektur**: https://keypirinha.com/architecture.html
- **Packages**: https://keypirinha.com/packages.html
- **API Docs**: https://keypirinha.com/api.html
- **Contributions**: https://keypirinha.com/contributions.html

### Jira Cloud
- **REST API v3**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/
- **JQL Dokumentation**: https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/

### Tools
- **Package Control**: https://github.com/ueffel/Keypirinha-PackageControl
- **Ruff**: https://docs.astral.sh/ruff/

---

## 💡 Wichtige Hinweise

### Sicherheit
- **API-Keys**: Nutzer ist für Sicherheit verantwortlich
- **Credentials**: Nie in Git committen
- **Berechtigungen**: Plugin nutzt User-Permissions

### Performance
- **Rate Limiting**: Jira Cloud API hat Limits - graceful handling
- **Pagination**: API limitiert Ergebnisse (aktuell max. 50)
- **Timeouts**: 10 Sekunden pro Request
- **Caching**: Aktuell kein Cache (könnte zukünftig implementiert werden)

### Compatibility
- **Keypirinha**: Windows-only (Keypirinha ist Windows-only)
- **Jira Cloud**: Nur Cloud, nicht Server/Data Center
- **Python**: Python 3 (Keypirinha nutzt embedded Python)

---

## 📞 Support & Kommunikation

### Bei Fragen während Implementierung
- BACKLOG.md konsultieren (Synergien?)
- Offene Fragen in USER-STORY.md dokumentieren
- Im Dialog mit Erik klären

### Bei technischen Problemen
- Keypirinha-Konsole prüfen (F2)
- Logs analysieren (`self.info()`, `self.warn()`, `self.err()`)
- DoD-Checks durchführen

---

**Version:** 2.0 (Workflow-Update)
**Letzte Aktualisierung:** 2025-12-18
