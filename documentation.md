# KeyPi - Atlassian Query Explorer Plugins

**Jira Plugin Version:** 1.2.0
**Confluence Plugin Version:** 1.0.0

---

## 📖 Übersicht

KeyPi ist eine Sammlung von Keypirinha-Plugins für Atlassian Cloud-Produkte.

**Verfügbare Plugins:**
- **KeyPi-JQE**: Jira Query Explorer - Abfragen von Jira Cloud mittels JQL
- **KeyPi-CQE**: Confluence Query Explorer - Abfragen von Confluence Cloud mittels CQL

**Gemeinsame Funktionen:**
- Queries aus Keypirinha ausführen
- Ergebnisse als filterbare Liste
- Direkte Browser-Integration
- Geteilte Atlassian-Credentials

---

# 🔧 Jira Query Explorer (JQE)

## Funktionen
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

---

# 🌐 Confluence Query Explorer (CQE)

## Funktionen
- CQL-Queries aus Keypirinha ausführen
- Confluence-Seiten durchsuchen
- Ergebnisse als filterbare Liste
- Seiten im Browser öffnen

---

## 🚀 Installation (CQE)

### Voraussetzungen
- Keypirinha (https://keypirinha.com)
- Confluence Cloud Account
- Atlassian API Token (https://id.atlassian.com/manage-profile/security/api-tokens)

### Manuelle Installation
1. Kopiere `keypi_cqe/` nach:
   - **Standard:** `%APPDATA%\Keypirinha\InstalledPackages\`
   - **Portable:** `<Keypirinha>\portable\Profile\InstalledPackages\`

---

## ⚙️ Konfiguration (CQE)

Erstelle: `%APPDATA%\Keypirinha\User\keypi_cqe.ini` (bzw. Portable-Pfad)

```ini
[main]
confluence_url = https://deine-firma.atlassian.net
atlassian_email = deine@email.com
atlassian_api_key = dein-api-token
keyword = cqe
```

**Hinweis:** Du kannst dieselben Credentials wie beim Jira-Plugin verwenden!

Keypirinha neu starten: `Ctrl + Alt + R`

---

## 💻 Verwendung (CQE)

### Basis-Workflow

1. Tippe: `cqe` → `Tab`
2. CQL eingeben: `type=page AND space=MYSPACE`
3. `Enter` drücken → Query wird ausgeführt
4. Ergebnisse erscheinen

### Filter-Modus

Nach Ausführung der CQL-Query kannst du die Ergebnisse filtern:

1. CQL eingeben: `type=page AND space=DOC` → `Enter`
2. Ergebnisse werden angezeigt (z.B. 50 Seiten)
3. Weiteren Text eingeben: `setup` → filtert Ergebnisse lokal
4. Seite auswählen → `Enter` → öffnet im Browser

**Vorteile:**
- Keine zusätzlichen API-Calls beim Filtern
- Schnelles Durchsuchen großer Ergebnislisten
- Filter durchsucht: Titel, Space, Type

### Konfiguration

Das Keyword ist konfigurierbar in `keypi_cqe.ini`:

```ini
[main]
keyword = cqe  # Ändere dies nach Belieben (z.B. "conf")
```

### CQL-Beispiele

```cql
# Alle Seiten in einem Space
type=page AND space=MYSPACE

# Suche nach Titel
type=page AND title~"Setup"

# Aktuelle Seiten
type=page AND created >= "2025/01/01"

# Kombinierte Bedingungen
type=page AND space=DOC AND title~"API"
```

CQL-Doku: https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/

---

## 🔧 Troubleshooting (CQE)

### "Configuration missing"
- Prüfe ob `keypi_cqe.ini` im User-Ordner existiert
- Alle drei Werte ausgefüllt?
- Keypirinha neugestartet?

### "Authentication failed"
- API Token korrekt?
- E-Mail korrekt?
- Confluence-URL ohne `/` und ohne `/wiki` am Ende?

### Logs ansehen
Keypirinha-Konsole: `F2`

---

## 📋 Limits (CQE)

- Max. 50 Ergebnisse pro Query
- 10 Sekunden Timeout

---

## 🔄 Changelog (CQE)

### Version 1.0.0 (2025-01-21)
- **Initial Release:** Confluence Query Explorer
- **Neu:** CQL-Queries ausführen
- **Neu:** Two-Phase Filter Mode (CQL Input → Filter Results)
- **Neu:** Konfigurierbares Keyword (default: "cqe")
- **Feature:** Lokales Filtern von gecachten Ergebnissen
- **Feature:** Seiten im Browser öffnen
- **Integration:** Nutzt gleiche Atlassian-Credentials wie Jira-Plugin

---

**Ende** | JQE v1.2.0 | CQE v1.0.0
