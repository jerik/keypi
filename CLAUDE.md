# KeyPi - Jira Query Explorer

Keypirinha-Plugin für direktes Abfragen von Jira Cloud mittels JQL (Jira Query Language) aus dem Keypirinha-Launcher.

## Tech Stack
- **Framework**: Keypirinha Plugin API
- **Sprache**: Python 3
- **API**: Jira Cloud REST API v3
- **Authentifizierung**: Atlassian API Keys
- **Konfiguration**: INI-Format
- **Distribution**: Keypirinha Package Control (GitHub)

## Projektstruktur
```
keypi/
├── keypi_jqe/              # Haupt-Plugin-Package
│   ├── __init__.py         # Plugin-Hauptklasse (erbt von keypirinha.plugin.Plugin)
│   ├── lib/                # Interne Libraries
│   │   └── jira_client.py  # Jira API Client Wrapper
│   └── res/                # Ressourcen & Konfiguration
│       ├── keypi_jqe.ini   # Benutzer-Konfigurationsdatei
│       ├── packages.json   # Package-Metadaten für Package Control
│       └── changelog/      # Versionshistorie
├── instructions.md         # Projekt-Requirements & MVP-Spezifikation
└── CLAUDE.md              # Diese Datei
```

## Entwicklung
```bash
# Plugin testen
# 1. Kopiere keypi_jqe/ nach %APPDATA%\Keypirinha\InstalledPackages\
# 2. Starte Keypirinha neu (Strg+Alt+R)
# 3. Teste mit Keyword "jqe"

# Installation für Endnutzer
# Via Keypirinha Package Control installieren

# Deployment
# 1. Push nach GitHub
# 2. Registrierung bei Keypirinha Package Control
# 3. Nutzer installieren via Package Control
```

## Code-Standards
- **PEP 8** Style Guide für Python-Code befolgen
- Plugin-Klasse muss von `keypirinha.plugin.Plugin` erben
- Pflicht-Methoden implementieren: `on_activate()`, `on_suggest()`, `on_execute()`
- Async/Non-blocking für API-Calls (UI nicht blockieren)
- Umfassendes Error Handling für API-Requests
- Logging für Debugging implementieren
- JQL-Syntax vor API-Request validieren

## Projektspezifische Regeln
- **Keyword**: Plugin reagiert auf "jqe" in Keypirinha
- **API-Kommunikation**: Nur über `lib/jira_client.py`, nicht direkt in Plugin-Klasse
- **Ergebnis-Format**: `TICKET-ID: [Status] Summary`
- **Datenfelder**: TicketID, Summary, Status, Priority, Creator, Assignee, CreatedDate
- **Konfiguration**: API-Key in `keypi_jqe.ini` speichern (nicht im Code)
- **Browser-Öffnung**: Nutze `kp.shell_execute()` für Ticket-URLs
- **Filtern**: Keypirinha übernimmt Live-Filtering - nur Daten bereitstellen

## MVP Features (Phase 1)
1. ✅ Keyword "jqe" aktiviert Plugin
2. ✅ User kann JQL-Query eingeben
3. ✅ Query an Jira Cloud API mit API-Key
4. ✅ Ergebnisse als Liste anzeigen
5. ✅ Alle relevanten Felder extrahieren (siehe oben)
6. ✅ Ticket im Browser öffnen bei Auswahl
7. ✅ API-Key in Config speichern

## Zukünftige Features (Phase 2)
- JQL-Shortcuts in Config (z.B. "me" → "assignee = currentUser()")
- Query-Historie (letzte 10 Queries)
- Schnellzugriff auf Historie mit "hist" Keyword

## Wichtige Hinweise
- **API-Keys**: Werden in `keypi_jqe.ini` gespeichert - Nutzer ist für Sicherheit verantwortlich
- **Konfigurationsdatei**: Nie mit Credentials in Git committen (`.gitignore` beachten)
- **Rate Limiting**: Jira Cloud API hat Rate Limits - graceful handling implementieren
- **Pagination**: API limitiert Ergebnisse - Pagination beachten
- **Timeouts**: API-Requests mit Timeout versehen (nicht unbegrenzt warten)
- **Error Messages**: Benutzerfreundliche Fehlermeldungen in Keypirinha anzeigen
- **Network Errors**: Offline-Szenario und Netzwerkfehler abfangen

## Häufige Fehler vermeiden
- **NICHT**: API-Keys im Code hardcoden oder unverschlüsselt commiten
- **NICHT**: UI während API-Calls blockieren (immer async)
- **NICHT**: Ohne Validierung JQL an API senden
- **NICHT**: 401/403 Fehler ignorieren (User muss API-Key konfigurieren)
- **NICHT**: `on_deactivate()` Cleanup vergessen
- **IMMER**: Von `keypirinha.plugin.Plugin` erben
- **IMMER**: Alle drei Methoden implementieren: `on_activate`, `on_suggest`, `on_execute`
- **IMMER**: Netzwerkfehler und Rate Limiting behandeln
- **IMMER**: Sinnvolle Defaults in Beispiel-Config bereitstellen
- **IMMER**: `.ini` Dateien mit Credentials in `.gitignore` eintragen

## Nützliche Ressourcen
- **Keypirinha Architektur**: https://keypiranha.com/architecture.html
- **Keypirinha Packages**: https://keypiranha.com/packages.html
- **Keypirinha API Docs**: https://keypiranha.com/api.html
- **Jira Cloud REST API v3**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/
- **Package Control**: https://github.com/ueffel/Keypirinha-PackageControl
- **Keypirinha Contributions**: https://keypiranha.com/contributions.html

## Beispiel-Konfiguration (keypi_jqe.ini)
```ini
[main]
# Dein Atlassian API Token (erstelle unter: https://id.atlassian.com/manage/api-tokens)
atlassian_api_key =

# Deine Jira Cloud URL (z.B. https://dein-domain.atlassian.net)
jira_url =

# Dein Atlassian Account Email
atlassian_email =

[jql_shortcuts]
# Optional: Shortcuts für häufige JQL-Queries (Phase 2)
# me = assignee = currentUser()
# open = status = "Open"
```

## Git Workflow
- **Development Branch**: `claude/create-claude-md-w4YYd`
- **Main Branch**: (wird noch festgelegt)
- Commits: Klare, beschreibende Commit-Messages
- Push mit: `git push -u origin claude/create-claude-md-w4YYd`
