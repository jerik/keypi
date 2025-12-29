# KeyPi - Jira Query Explorer

**Version:** 1.2.0

---

## 📖 Übersicht

KeyPi-JQE ist ein Keypirinha-Plugin zum Abfragen von Jira Cloud mittels JQL.

**Funktionen:**
- JQL-Queries aus Keypirinha ausführen
- Ergebnisse als filterbare Liste
- JQL Shortcuts für häufige Queries
- Tickets im Browser öffnen

---

## 🚀 Installation

### Voraussetzungen
- Keypirinha (https://keypirinha.com)
- Jira Cloud Account
- Atlassian API Token (https://id.atlassian.com/manage-profile/security/api-tokens)

### Manuelle Installation
1. Kopiere `keypi_jqe/` nach:
   - **Standard:** `%APPDATA%\Keypirinha\InstalledPackages\`
   - **Portable:** `<Keypirinha>\portable\Profile\InstalledPackages\`

---

## ⚙️ Konfiguration

Erstelle: `%APPDATA%\Keypirinha\User\keypi_jqe.ini` (bzw. Portable-Pfad)

```ini
[main]
jira_url = https://deine-firma.atlassian.net
atlassian_email = deine@email.com
atlassian_api_key = dein-api-token
```

Keypirinha neu starten: `Ctrl + Alt + R`

---

## 💻 Verwendung

### Basis-Workflow

1. Tippe: `jqe` → `Tab`
2. JQL eingeben: `assignee = currentUser()`
3. `Enter` drücken → Query wird ausgeführt
4. Ergebnisse erscheinen

### Filter-Modus

Nach Ausführung der JQL-Query kannst du die Ergebnisse filtern:

1. JQL eingeben: `assignee = currentUser()` → `Enter`
2. Ergebnisse werden angezeigt (z.B. 50 Tickets)
3. Weiteren Text eingeben: `bug` → filtert Ergebnisse lokal
4. Ticket auswählen → `Enter` → öffnet im Browser

**Vorteile:**
- Keine zusätzlichen API-Calls beim Filtern
- Schnelles Durchsuchen großer Ergebnislisten
- Filter durchsucht: Ticket-ID, Summary, Status

### JQL Shortcuts

Spare Zeit mit wiederverwendbaren Shortcuts für häufige Queries!

**Shortcuts definieren** in `keypi_jqe.ini`:

```ini
[jql_shortcuts]
me = assignee = currentUser()
open = status = "Open"
mytask = assignee = currentUser() AND status = "Open"
```

**Shortcuts verwenden:**

1. **Alle Shortcuts anzeigen**:
   - Tippe: `jqe` → `#` → Liste aller Shortcuts erscheint

2. **Shortcut filtern**:
   - Tippe: `jqe` → `#me` → Zeigt Shortcuts mit "me" im Namen

3. **Shortcut ausführen**:
   - Wähle Shortcut → `Enter` → Query wird ausgeführt

4. **Config bearbeiten**:
   - Tippe: `jqe` → `#edit` → `Enter` → Config-Datei wird geöffnet

**Vorteile:**
- 🚀 Spare Zeit bei häufigen Queries
- 🎯 Keine komplexe JQL-Syntax merken
- ✏️ Einfach zu editieren und teilen
- 🔄 Shortcuts sind case-insensitive (#Me = #me)

### Konfiguration

Das Keyword ist konfigurierbar in `keypi_jqe.ini`:

```ini
[main]
keyword = jqe  # Ändere dies nach Belieben (z.B. "jira")
```

### JQL-Beispiele

```jql
assignee = currentUser()
project = MYPROJECT AND status = "Open"
filter = 12345
```

JQL-Doku: https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/

---

## 🔧 Troubleshooting

### "Configuration missing"
- Prüfe ob `keypi_jqe.ini` im User-Ordner existiert
- Alle drei Werte ausgefüllt?
- Keypirinha neugestartet?

### "Authentication failed"
- API Token korrekt?
- E-Mail korrekt?
- Jira-URL ohne `/` am Ende?

### Logs ansehen
Keypirinha-Konsole: `F2`

---

## 🔒 Sicherheit

- API Token niemals committen
- Token wie Passwort behandeln
- Token regelmäßig erneuern

---

## 📋 Limits

- Max. 50 Ergebnisse pro Query
- 10 Sekunden Timeout

---

## 🔄 Changelog

### Version 1.2.0 (2025-12-22)
- **Neu:** JQL Shortcuts für häufige Queries
- **Neu:** # Prefix für Shortcut-Zugriff (#me, #open, etc.)
- **Neu:** #edit öffnet Config-Datei zum Bearbeiten
- **Neu:** Liste aller Shortcuts mit # anzeigen
- **Feature:** Case-insensitive Shortcut-Matching
- **UX:** Direkte Ausführung ohne sichtbare JQL-Expansion

### Version 1.1.0 (2025-12-19)
- **Neu:** Two-Phase Filter Mode (JQL Input → Filter Results)
- **Neu:** Konfigurierbares Keyword (default: "jqe")
- **Verbesserung:** Keine API-Calls während JQL-Eingabe
- **Verbesserung:** Lokales Filtern von gecachten Ergebnissen
- **Performance:** ~90% weniger API-Calls

### Version 1.0.0 (2025-12-18)
- Initial Release (MVP)
- JQL-Queries ausführen
- Ergebnisse anzeigen
- Tickets im Browser öffnen

---

**Ende** | v1.2.0
