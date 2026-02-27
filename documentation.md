# KeyPi - Keypirinha Plugin Collection

**Jira Plugin Version:** 1.5.1
**Confluence Plugin Version:** 1.3.0
**User Search Plugin Version:** 1.1.0
**Mindbox Plugin Version:** 1.0.0
**PM-Buddy Plugin Version:** 1.0.0-dev

---

## 📖 Übersicht

KeyPi ist eine Sammlung von Keypirinha-Plugins für Produktivität und Atlassian Cloud-Produkte.

**Verfügbare Plugins:**
- **KeyPi-JQE**: Jira Query Explorer - Abfragen von Jira Cloud mittels JQL
- **KeyPi-CQE**: Confluence Query Explorer - Abfragen von Confluence Cloud mittels CQL
- **KeyPi-US**: User Search - Nutzersuche via Jira Cloud API
- **KeyPi-Mindbox**: Mindbox - Lokale .mb Dateien durchsuchen und öffnen
- **KeyPi-PMB**: PM-Buddy - Knowledge-Graph durchsuchen (Jira + Confluence, offline)

**Gemeinsame Funktionen:**
- Ergebnisse als filterbare Liste
- Direkte Browser-/Editor-Integration
- #edit Shortcut zum Bearbeiten der Konfiguration

---

# 🔧 Jira Query Explorer (JQE)

## Funktionen
- JQL-Queries aus Keypirinha ausführen
- Ergebnisse als filterbare Liste
- JQL Shortcuts für häufige Queries
- **Multi-Action Support**: Tab-Menü mit mehreren Aktionen
- Tickets im Browser öffnen oder URLs kopieren

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

### Multi-Action Support

Jeder Ticket-Eintrag bietet mehrere Aktionen:

**Standardaktion (Enter):**
- Ticket im Browser öffnen

**Action-Menü (Tab drücken):**
1. **Open ticket**: Ticket im Browser öffnen (Standard)
2. **Copy URL**: Ticket-URL in Zwischenablage kopieren

**Workflow:**
1. Query ausführen → Ergebnisse erscheinen
2. Ticket auswählen
3. **Tab** drücken → Action-Menü öffnet sich
4. Action auswählen (mit Pfeiltasten oder weiteres Tab)
5. **Enter** drücken → Action wird ausgeführt

**Vorteile:**
- 🚀 Schneller Zugriff auf häufige Aktionen
- 📋 URLs kopieren ohne Browser zu öffnen
- 🔄 Mehrere URLs nacheinander kopieren (kein Modus-Reset)

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

### Query History (Neu in v1.4.0, Virtual Query Mode in v1.5.0)

Greife schnell auf deine zuletzt ausgeführten Queries zu!

**History verwenden:**

1. **History anzeigen**:
   - Tippe: `jqe` → `#history` (oder `#his`) → Liste der letzten Queries erscheint

2. **History-Eintrag verwenden** (Virtual Query Mode ✨):
   - Wähle Query aus History → **Tab** → Query wird ausgeführt → Ergebnisse erscheinen direkt!
   - Du kannst die Ergebnisse dann filtern und ein Ticket auswählen
   - Alternativ: **Enter** → JQL-Suche im Browser öffnen

3. **History löschen**:
   - Tippe: `jqe` → `#history clear` → `Enter` → Alle Einträge gelöscht

**Virtual Query Mode (v1.5.0):**

Der neue Virtual Query Mode ermöglicht einen nahtlosen Workflow:
```
jqe → #history → Tab auf Eintrag → Ergebnisse erscheinen → Filtern → Ticket öffnen
```

Kein erneutes Eintippen der Query nötig!

**Konfiguration** in `keypi_jqe.ini`:

```ini
[main]
# Maximale Anzahl gespeicherter History-Einträge (Standard: 30)
history_max_entries = 30
```

**Vorteile:**
- 📜 Zuletzt verwendete Queries schnell wiederfinden
- ✨ Virtual Query Mode: Tab auf History → Ergebnisse direkt sehen
- 🔄 Duplikate werden automatisch nach oben verschoben
- 💾 Persistent über Keypirinha-Neustarts
- ⚙️ Konfigurierbare Anzahl der Einträge

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

### Version 1.4.0 (2026-01-27)
- **Neu:** Query History - Zuletzt ausgeführte Queries mit `#history` oder `#his` abrufen
- **Neu:** History Actions: JQL kopieren (Default) oder im Browser öffnen
- **Neu:** `#history clear` zum Löschen der kompletten History
- **Feature:** Persistente History-Datei (überlebt Neustarts)
- **Feature:** Konfigurierbare Anzahl History-Einträge (default: 30)
- **Feature:** Duplikate werden automatisch nach oben verschoben
- **Test:** 24 Unit-Tests für History-Funktionalität

### Version 1.3.0 (2026-01-23)
- **Neu:** Multi-Action Support (Tab-Menü mit 2 Aktionen)
  - Open ticket (Standard-Aktion mit Enter)
  - Copy URL (Kopiert URL in Zwischenablage)
- **UX:** Konsistente Action-Muster wie andere Keypirinha-Plugins
- **Feature:** Copy URL resettet Modus nicht (mehrere URLs kopieren möglich)

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
- Ergebnisse als filterbare Liste mit erweiterten Infos (Space, Type, LastModified)
- **Multi-Action Support**: Tab-Menü mit mehreren Aktionen
- Seiten im Browser öffnen, URLs kopieren oder im Edit-Modus öffnen

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
   - Format: `Titel | Space: FOO | Type: page | LastMod: 2026-01-22`
3. Weiteren Text eingeben: `setup` → filtert Ergebnisse lokal
4. Seite auswählen → `Enter` → öffnet im Browser

**Vorteile:**
- Keine zusätzlichen API-Calls beim Filtern
- Schnelles Durchsuchen großer Ergebnislisten
- Filter durchsucht: Titel, Space, Type
- Zeigt wichtige Infos: Space, Type und letztes Änderungsdatum

### Multi-Action Support (Neu in v1.1.0)

Jeder Sucheintrag bietet mehrere Aktionen:

**Standardaktion (Enter):**
- Seite im Browser öffnen (Ansichtsmodus)

**Action-Menü (Tab drücken):**
1. **Open page**: Seite im Browser öffnen (Ansichtsmodus)
2. **Copy URL**: Seiten-URL in Zwischenablage kopieren
3. **Edit page**: Seite im Bearbeiten-Modus öffnen

**Workflow:**
1. Query ausführen → Ergebnisse erscheinen
2. Seite auswählen
3. **Tab** drücken → Action-Menü öffnet sich
4. Action auswählen (mit Pfeiltasten oder weiteres Tab)
5. **Enter** drücken → Action wird ausgeführt

**Vorteile:**
- 🚀 Schneller Zugriff auf häufige Aktionen
- 📋 URLs kopieren ohne Browser zu öffnen
- ✏️ Direkt in Bearbeiten-Modus springen

### CQL Shortcuts (Neu in v1.2.0)

Spare Zeit mit wiederverwendbaren Shortcuts für häufige Queries!

**Shortcuts definieren** in `keypi_cqe.ini`:

```ini
[cqe_shortcuts]
myco = title ~ konzept and creator = currentUser()
mytodo = title ~ todo and creator = currentUser()
recent = lastModified >= now("-7d") ORDER BY lastModified DESC
```

**Shortcuts verwenden:**

1. **Alle Shortcuts anzeigen**:
   - Tippe: `cqe` → `#` → Liste aller Shortcuts erscheint

2. **Shortcut filtern**:
   - Tippe: `cqe` → `#myco` → Zeigt Shortcuts mit "myco" im Namen

3. **Shortcut ausführen**:
   - Wähle Shortcut → `Enter` → Query wird ausgeführt

4. **Config bearbeiten**:
   - Tippe: `cqe` → `#edit` → `Enter` → Config-Datei wird geöffnet

**Vorteile:**
- 🚀 Spare Zeit bei häufigen Queries
- 🎯 Keine komplexe CQL-Syntax merken
- ✏️ Einfach zu editieren und teilen
- 🔄 Shortcuts sind case-insensitive (#Myco = #myco)

### Query History (Neu in v1.3.0)

Greife schnell auf deine zuletzt ausgeführten Queries zu!

**History verwenden:**

1. **History anzeigen**:
   - Tippe: `cqe` → `#history` (oder `#his`) → Liste der letzten Queries erscheint

2. **History-Eintrag verwenden** (Virtual Query Mode ✨):
   - Wähle Query aus History → **Tab** → Query wird ausgeführt → Ergebnisse erscheinen direkt!
   - Du kannst die Ergebnisse dann filtern und eine Seite auswählen
   - Alternativ: **Enter** → CQL-Suche im Browser öffnen

3. **History löschen**:
   - Tippe: `cqe` → `#history clear` → `Enter` → Alle Einträge gelöscht

**Virtual Query Mode:**

Der Virtual Query Mode ermöglicht einen nahtlosen Workflow:
```
cqe → #history → Tab auf Eintrag → Ergebnisse erscheinen → Filtern → Seite öffnen
```

Kein erneutes Eintippen der Query nötig!

**Konfiguration** in `keypi_cqe.ini`:

```ini
[main]
# Maximale Anzahl gespeicherter History-Einträge (Standard: 30)
history_max_entries = 30
```

**Vorteile:**
- 📜 Zuletzt verwendete Queries schnell wiederfinden
- ✨ Virtual Query Mode: Tab auf History → Ergebnisse direkt sehen
- 🔄 Duplikate werden automatisch nach oben verschoben
- 💾 Persistent über Keypirinha-Neustarts
- ⚙️ Konfigurierbare Anzahl der Einträge

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

### Version 1.3.0 (2026-02-03)
- **Neu:** Query History - Zuletzt ausgeführte Queries mit `#history` oder `#his` abrufen
- **Neu:** Virtual Query Mode: Tab auf History-Eintrag → Ergebnisse direkt sehen
- **Neu:** `#history clear` zum Löschen der kompletten History
- **Feature:** Persistente History-Datei (überlebt Neustarts)
- **Feature:** Konfigurierbare Anzahl History-Einträge (default: 30)
- **Feature:** Duplikate werden automatisch nach oben verschoben
- **Test:** 32 Unit-Tests für History-Funktionalität

### Version 1.2.0 (2026-01-26)
- **Neu:** CQL Shortcuts für häufige Queries
- **Neu:** # Prefix für Shortcut-Zugriff (#myco, #mytodo, etc.)
- **Neu:** #edit öffnet Config-Datei zum Bearbeiten
- **Neu:** Liste aller Shortcuts mit # anzeigen
- **Feature:** Case-insensitive Shortcut-Matching
- **UX:** Direkte Ausführung ohne sichtbare CQL-Expansion

### Version 1.1.0 (2026-01-23)
- **Neu:** Multi-Action Support (Tab-Menü mit 3 Aktionen)
  - Open page (Standard-Aktion mit Enter)
  - Copy URL (Kopiert URL in Zwischenablage)
  - Edit page (Öffnet Seite im Bearbeiten-Modus)
- **Neu:** Erweiterte Ergebnis-Anzeige
  - Space-Name anzeigen
  - Content-Type anzeigen (page, blogpost, etc.)
  - LastModified-Datum anzeigen (YYYY-MM-DD)
- **Verbesserung:** API expand-Parameter für vollständige Space/Version-Daten
- **UX:** Konsistente Action-Muster wie andere Keypirinha-Plugins
- **Testing:** 15 Unit-Tests für API-Parsing und URL-Transformationen

### Version 1.0.0 (2025-01-21)
- **Initial Release:** Confluence Query Explorer
- **Neu:** CQL-Queries ausführen
- **Neu:** Two-Phase Filter Mode (CQL Input → Filter Results)
- **Neu:** Konfigurierbares Keyword (default: "cqe")
- **Feature:** Lokales Filtern von gecachten Ergebnissen
- **Feature:** Seiten im Browser öffnen
- **Integration:** Nutzt gleiche Atlassian-Credentials wie Jira-Plugin

---

---

# 👤 User Search (US)

## Funktionen
- Nutzersuche via Jira Cloud API
- Ergebnisse als filterbare Liste
- **Multi-Action Support**: Teams Chat oder Profil öffnen
- Integration mit MS Teams

---

## 🚀 Installation (US)

### Voraussetzungen
- Keypirinha (https://keypirinha.com)
- Jira Cloud Account
- Atlassian API Token (https://id.atlassian.com/manage-profile/security/api-tokens)

### Manuelle Installation
1. Kopiere `keypi_us/` nach:
   - **Standard:** `%APPDATA%\Keypirinha\InstalledPackages\`
   - **Portable:** `<Keypirinha>\portable\Profile\InstalledPackages\`

---

## ⚙️ Konfiguration (US)

Erstelle: `%APPDATA%\Keypirinha\User\keypi_us.ini` (bzw. Portable-Pfad)

```ini
[main]
keyword = us
jira_url = https://deine-firma.atlassian.net
atlassian_email = deine@email.com
atlassian_api_key = dein-api-token

# Maximale Anzahl gespeicherter History-Einträge (Standard: 30)
history_max_entries = 30
```

**Hinweis:** Du kannst dieselben Credentials wie beim Jira-Plugin verwenden!

Keypirinha neu starten: `Ctrl + Alt + R`

---

## 💻 Verwendung (US)

### Basis-Workflow

1. Tippe: `us` → `Tab`
2. Suchbegriff eingeben: `Max`
3. `Tab` drücken → Suche wird ausgeführt
4. Ergebnisse erscheinen:
   - Format: `Max Mustermann | max.mustermann@company.com`
5. Nutzer auswählen → `Enter` → Teams Chat öffnet sich

### Filter-Modus

Nach Ausführung der Suche kannst du die Ergebnisse filtern:

1. Suchbegriff eingeben: `schmidt` → `Tab`
2. Ergebnisse werden angezeigt (z.B. 30 Nutzer)
3. Weiteren Text eingeben: `anna` → filtert Ergebnisse lokal
4. Nutzer auswählen → `Enter` → Teams Chat öffnet sich

**Vorteile:**
- Keine zusätzlichen API-Calls beim Filtern
- Schnelles Durchsuchen großer Ergebnislisten
- Filter durchsucht: Name, E-Mail

### Multi-Action Support

Jeder Nutzer-Eintrag bietet mehrere Aktionen:

**Standardaktion (Enter):**
- Teams Chat öffnen (bei Nutzern mit E-Mail)
- Profil öffnen (bei Nutzern ohne E-Mail)

**Action-Menü (Tab drücken):**
1. **Open Profile**: Jira-Benutzerprofil im Browser öffnen
2. **Teams Chat**: MS Teams Chat öffnen (Standard)

**Bei Nutzern ohne E-Mail:**
- Teams Chat zeigt: "nicht möglich - keine E-Mail"
- Standard-Action öffnet Profil

**Workflow:**
1. Suche ausführen → Ergebnisse erscheinen
2. Nutzer auswählen
3. **Tab** drücken → Action-Menü öffnet sich
4. Action auswählen
5. **Enter** drücken → Action wird ausgeführt

**Vorteile:**
- 💬 Schneller Zugriff auf Teams Chat
- 👤 Direkt zum Jira-Profil springen
- 🔄 Tab+Enter für schnellen Profilzugriff

### User History (Neu in v1.1.0)

Greife schnell auf deine zuletzt verwendeten Nutzer zu!

**History verwenden:**

1. **History anzeigen**:
   - Tippe: `us` → `#history` → Tab → Liste der letzten Nutzer erscheint

2. **History filtern**:
   - Tippe: `us` → `max` → Gefilterte History-Einträge erscheinen mit `[History]` Prefix
   - Zusätzlich: `us: max` Option für API-Suche am Ende der Liste

3. **History-Eintrag verwenden**:
   - Wähle Nutzer aus History → **Enter** → Teams Chat öffnet sich (oder Profil bei fehlender E-Mail)
   - Wähle Nutzer aus History → **Tab** → Action-Menü erscheint

4. **History löschen**:
   - Tippe: `us` → `#history clear` → `Enter` → Alle Einträge gelöscht

**Workflow-Beispiel:**
```
us → max → [History] Max Mustermann erscheint → Enter → Teams Chat
```

**Features:**
- 📜 Zuletzt verwendete Nutzer schnell wiederfinden
- 🔍 History wird beim Tippen automatisch gefiltert
- 🔄 Duplikate werden nach oben verschoben (keine doppelten Einträge)
- 💾 Persistent über Keypirinha-Neustarts
- ⚙️ Konfigurierbare Anzahl der Einträge (default: 30)
- 🔗 API-Suche immer als Option verfügbar

### Config bearbeiten

Tippe: `us` → `#edit` → `Enter` → Config-Datei wird geöffnet

### Konfiguration

Das Keyword ist konfigurierbar in `keypi_us.ini`:

```ini
[main]
keyword = us  # Ändere dies nach Belieben (z.B. "user")
```

---

## 🔧 Troubleshooting (US)

### "Configuration missing"
- Prüfe ob `keypi_us.ini` im User-Ordner existiert
- Alle drei Werte ausgefüllt?
- Keypirinha neugestartet?

### "Authentication failed"
- API Token korrekt?
- E-Mail korrekt?
- Jira-URL ohne `/` am Ende?

### "Keine E-Mail verfügbar"
- Atlassian Privacy-Einstellungen des Nutzers
- Einige Nutzer haben E-Mail-Sichtbarkeit deaktiviert

### Logs ansehen
Keypirinha-Konsole: `F2`

---

## 📋 Limits (US)

- Max. 50 Ergebnisse pro Suche
- 10 Sekunden Timeout
- E-Mail-Verfügbarkeit abhängig von Nutzer-Einstellungen

---

## 🔄 Changelog (US)

### Version 1.1.0 (2026-02-05)
- **Neu:** User History - Zuletzt verwendete Nutzer mit `#history` abrufen
- **Neu:** Gefilterte History beim Tippen (z.B. `max` zeigt passende History-Einträge)
- **Neu:** `#history clear` zum Löschen der kompletten History
- **Feature:** Persistente History-Datei (überlebt Neustarts)
- **Feature:** Konfigurierbare Anzahl History-Einträge (default: 30)
- **Feature:** Duplikate werden automatisch nach oben verschoben
- **UX:** API-Suche Option immer verfügbar unter History-Einträgen

### Version 1.0.0 (2026-02-05)
- **Initial Release:** User Search Plugin
- **Neu:** Nutzersuche via Jira Cloud API
- **Neu:** Two-Phase Filter Mode (Suche → Filter Results)
- **Neu:** Multi-Action Support
  - Open Profile (Tab+Enter)
  - Teams Chat (Enter, Standard)
- **Neu:** #edit Shortcut zum Öffnen der Config
- **Feature:** Erkennung von Nutzern ohne E-Mail
- **Feature:** Teams Chat Integration via sip: Protokoll
- **Feature:** Konfigurierbares Keyword (default: "us")
- **Test:** 19 Unit-Tests für Filter und Parsing

---

---

---

# 📂 Mindbox (MB)

## Funktionen
- Lokale .mb Dateien aus einem konfigurierten Ordner durchsuchen
- Ergebnisse als filterbare Liste mit Dateiname und Änderungsdatum
- Dateien mit dem Standard-Editor öffnen

---

## 🚀 Installation (Mindbox)

### Voraussetzungen
- Keypirinha (https://keypirinha.com)
- Ein Ordner mit .mb Dateien

### Manuelle Installation
1. Kopiere `keypi_mindbox/` nach:
   - **Standard:** `%APPDATA%\Keypirinha\InstalledPackages\`
   - **Portable:** `<Keypirinha>\portable\Profile\InstalledPackages\`

---

## ⚙️ Konfiguration (Mindbox)

Erstelle: `%APPDATA%\Keypirinha\User\keypi_mindbox.ini` (bzw. Portable-Pfad)

```ini
[main]
mindbox_folder = C:\Users\DeinName\Documents\Mindbox
keyword = mb
```

Keypirinha neu starten: `Ctrl + Alt + R`

---

## 💻 Verwendung (Mindbox)

### Basis-Workflow

1. Tippe: `mb` → `Tab`
2. Alle .mb Dateien werden angezeigt
3. Weiter tippen → Liste wird gefiltert
4. Datei auswählen → `Enter` → Datei wird im Standard-Editor geöffnet

### Anzeige-Format

Jeder Eintrag zeigt:
- **Label:** Dateiname (ohne .mb Endung)
- **Beschreibung:** Änderungsdatum + vollständiger Dateiname

### Config bearbeiten

Tippe: `mb` → `#edit` → `Enter` → Config-Datei wird geöffnet

### Konfiguration

Das Keyword ist konfigurierbar in `keypi_mindbox.ini`:

```ini
[main]
keyword = mb  # Ändere dies nach Belieben (z.B. "mind")
mindbox_folder = C:\Pfad\zu\deinen\Mindbox-Dateien
```

---

## 🔧 Troubleshooting (Mindbox)

### "Configuration missing"
- Prüfe ob `keypi_mindbox.ini` im User-Ordner existiert
- `mindbox_folder` Pfad ausgefüllt?
- Keypirinha neugestartet?

### "No .mb files found"
- Prüfe ob der konfigurierte Ordner existiert
- Prüfe ob .mb Dateien im Ordner vorhanden sind
- Unterordner werden nicht durchsucht

### Logs ansehen
Keypirinha-Konsole: `F2`

---

## 🔄 Changelog (Mindbox)

### Version 1.0.0 (2026-02-09)
- **Initial Release:** Mindbox file browser plugin
- **Neu:** .mb Dateien aus konfiguriertem Ordner durchsuchen
- **Neu:** Filterbare Liste mit Dateiname + Änderungsdatum
- **Neu:** Dateien mit Standard-Editor öffnen
- **Neu:** #edit Shortcut zum Öffnen der Config
- **Feature:** Konfigurierbares Keyword (default: "mb")
- **Test:** 22 Unit-Tests für Folder-Scanning, Shortcuts und Config

---

---

---

# 🔍 PM-Buddy (PMB)

## Funktionen
- Jira-Tickets und Confluence-Seiten aus dem pm-buddy Knowledge-Graph durchsuchen
- Lokale PMM-Dateien (Markdown-Projektdateien) direkt anzeigen und aufklappen
- Direkter SQLite-Zugriff (kein pm-buddy-Package nötig)
- Ergebnisse als filterbare Liste mit Ranking (Epics vor Stories, häufig besuchte zuerst, PMM-Dateien zuerst)
- **Multi-Action Support**: Tab-Menü mit mehreren Aktionen
- Tickets/Seiten im Browser öffnen oder URLs kopieren
- Tab auf PMM-Datei: verknüpfte Jira-Tickets und Datumsfelder als Sub-Items

---

## 🚀 Installation (PMB)

### Voraussetzungen
- Keypirinha (https://keypirinha.com)
- pm-buddy installiert und mindestens einmal synchronisiert (`pm-buddy sync`)
- Optional: PMM-Ordner mit Markdown-Projektdateien (für PMM-Features)

### Manuelle Installation
1. Kopiere `keypi_pmb/` nach:
   - **Standard:** `%APPDATA%\Keypirinha\InstalledPackages\`
   - **Portable:** `<Keypirinha>\portable\Profile\InstalledPackages\`

---

## ⚙️ Konfiguration (PMB)

Erstelle: `%APPDATA%\Keypirinha\User\keypi_pmb.ini`

```ini
[main]
keyword = pmb
# Pfad zur pm-buddy Datenbank (Umgebungsvariablen werden aufgelöst)
db_path = %USERPROFILE%\.pm-buddy\pm-buddy.db
# Pfad zum PMM-Ordner mit Markdown-Projektdateien (optional)
# Leer lassen = PMM-Features deaktiviert
pmm_folder = %USERPROFILE%\OneDrive\pmm
```

- `db_path`: Unterstützt `%USERPROFILE%`, `%APPDATA%` und `~`
- `pmm_folder`: Leer = nur DB-Suche; gesetzt = PMM-Dateien erscheinen über DB-Ergebnissen

Keypirinha neu starten: `Ctrl + Alt + R`

---

## 💻 Verwendung (PMB)

### Basis-Workflow

1. Tippe: `pmb` → `Tab`
2. Suchbegriff eingeben: `steuer`
3. `Enter` drücken → Suche wird ausgeführt
4. Ergebnisse erscheinen (PMM-Dateien zuerst, dann DB-Ergebnisse)

### Filter-Modus

Nach Ausführung der Suche kannst du die Ergebnisse filtern:

1. Suchbegriff eingeben: `auth` → `Enter`
2. Ergebnisse werden angezeigt
3. Weiteren Text eingeben: `open` → filtert Ergebnisse lokal (nach Titel, Key, Status, Tags)
4. Eintrag auswählen → `Enter` → öffnet im Browser (DB) oder Editor (PMM)

**Vorteile:**
- Keine zusätzlichen Datenbankabfragen beim Filtern
- Schnelles Durchsuchen großer Ergebnislisten
- Filter durchsucht: Titel, Ticket-Key, Status, Assignee, Tags, alle Frontmatter-Felder

### Anzeige-Format

| Typ | Label | Beschreibung |
|-----|-------|-------------|
| PMM-Datei | `PMM: Foobar implementieren` | `FOO-2360 | INT-264 | Tags: foo, bar` |
| Jira | `KEY-123: [epic][Open] Steuererklaerung` | `Assignee: Max | Fix: 1.2.0 | Tags: steuer` |
| Confluence | `[STEU] Fachkonzept Steuern` | `Type: confluence_page | Modified: 2026-01-15` |

### PMM Drill-Down (Tab auf PMM-Datei)

Tab auf einer PMM-Datei öffnet Sub-Items für jeden verlinkten Jira-Ticket und jedes Datumsfeld:

```
[epic] FOO-2360: Umsetzung foobar [Open]    ← Jira-Ticket (Enter = im Browser öffnen)
[story] BAR-6852: Backend-Anbindung [Done]  ← Jira-Ticket
Fälligkeit: 2026-03-31                       ← Datum (Enter = in Clipboard kopieren)
```

- **Jira-Key-Felder**: Typ, Key, Summary (50 Zeichen), Status aus DB; Enter öffnet Jira im Browser
- **ISO-Datum-Felder** (`YYYY-MM-DD`): Enter kopiert Datum in Clipboard
- Ticket nicht in DB? → Fallback-URL aus `atlassian_url` (automatisch beim `pm-buddy sync` gespeichert)

### Multi-Action Support (DB-Ergebnisse)

**Standardaktion (Enter):**
- URL im Browser öffnen

**Action-Menü (Tab drücken):**
1. **Open**: URL im Browser öffnen (Standard)
2. **Copy URL**: URL in Zwischenablage kopieren

### Suchalgorithmus

Das Plugin verwendet den gleichen Algorithmus wie pm-buddy:
- **PMM-Dateien** stehen immer über DB-Ergebnissen
- **FTS5-Volltext** auf Titel und Ticket-Key (Präfix-Suche)
- **Tag-Suche** auf auto/manuelle Tags
- **Typ-Boost**: Initiativen (4×) > Epics (3×) > Confluence-Seiten (1.5×) > Stories/Bugs/Tasks (1×) > Subtasks (0.5×)
- **PMM-Boost**: Tickets in PMM-Dateien erwähnt → +10.0 Score-Bonus
- **Visit-Boost**: Häufig im Browser besuchte Einträge werden bevorzugt
- **Hidden-Filter**: Versteckte Einträge werden ausgeblendet

### Shortcuts

| Shortcut | Beschreibung |
|----------|-------------|
| `#edit` | Konfigurationsdatei öffnen |
| `#list` | Alle PMM-Dateien anzeigen (mit Live-Filter) |

### Config bearbeiten

Tippe: `pmb` → `#edit` → `Enter` → Config-Datei wird geöffnet

---

## 📄 PMM-Datei-Format

PMM-Dateien sind Markdown-Dateien mit YAML-Frontmatter:

```markdown
---
title: Foobar implementieren
initiative: INT-264
fachkonzept: FOO-2360
umsetzung: BAR-6852
tags: [foo, bar]
Fälligkeit: 2026-03-31
---

# Notizen...
```

**Konventionen:**
- Dateiname = Haupt-Ticket-Key (z.B. `FOO-2360.md`) — oder beliebiger Name
- `title` → Anzeige-Label im Plugin (`PMM: Foobar implementieren`)
- Felder mit Jira-Key-Wert → Drill-Down-Aktionen (Tab auf PMM-Ergebnis)
- Felder mit ISO-Datum-Wert (`YYYY-MM-DD`) → Clipboard-Aktion
- `tags: [...]` → suchbar und filterbar
- Zeilen mit `#` → ignoriert (Kommentare)
- Windows-Zeilenenden (CRLF) und Pfade mit Leerzeichen (OneDrive) unterstützt

---

## 🔧 Troubleshooting (PMB)

### "Configuration missing"
- Prüfe ob `keypi_pmb.ini` im User-Ordner existiert
- `db_path` ausgefüllt und Pfad korrekt?
- Keypirinha neugestartet?

### "No results found"
- pm-buddy noch nie synchronisiert? → `pm-buddy sync` ausführen
- Datenbankpfad korrekt? → `#edit` → prüfen

### PMM-Dateien erscheinen nicht
- `pmm_folder` in `keypi_pmb.ini` gesetzt?
- Pfad korrekt? Ordner vorhanden?
- Dateien haben `.md`-Endung?

### Logs ansehen
Keypirinha-Konsole: `F2`

---

## 📋 Limits (PMB)

- Max. 50 Ergebnisse pro Suche (DB)
- Nur Lese-Zugriff (kein Schreiben in die Datenbank)

---

## 🔄 Changelog (PMB)

### Version 1.0.0-dev (2026-02-27)
- **Neu:** PMM-Integration (lokale Markdown-Projektdateien)
  - PMM-Dateien erscheinen über DB-Ergebnissen
  - Tab auf PMM-Datei: Drill-Down mit verlinkten Jira-Tickets und Datumsfeldern
  - Jira-Sub-Items zeigen Typ, Summary (50 Zeichen), Status, Fix-Version
  - ISO-Datum-Felder: Enter kopiert Datum in Clipboard
  - Fallback-URL via `atlassian_url` aus DB-Settings (kein doppelter Config-Eintrag)
- **Neu:** `#list` Shortcut – alle PMM-Dateien anzeigen
- **Neu:** `pmm_folder` Config-Option (optional; leer = PMM deaktiviert)
- **Neu:** PMM-Boost im Suchalgorithmus (+10.0 für Tickets in PMM-Dateien)
- **Feature:** Flexible Dateinamen (nicht mehr auf KEY.md beschränkt)
- **Test:** Tests für PMM-Client, Drill-Down und pmb_client erweitert

### Version 1.0.0 (2026-02-19)
- **Initial Release:** PM-Buddy Knowledge-Graph Plugin
- **Neu:** Jira-Tickets und Confluence-Seiten durchsuchen
- **Neu:** Two-Phase Filter Mode (Suche → Filter Results)
- **Neu:** Multi-Action Support (Open, Copy URL)
- **Neu:** #edit Shortcut zum Öffnen der Config
- **Feature:** Typ-Boost Ranking (Epics/Initiativen bevorzugt)
- **Feature:** Chrome Visit-Boost Ranking
- **Feature:** Hidden-Nodes-Filter
- **Feature:** Konfigurierbares Keyword (default: "pmb")
- **Feature:** Umgebungsvariablen in db_path (z.B. %USERPROFILE%)
- **Test:** 24 Unit-Tests für Suche, Ranking und Formatierung

---

**Ende** | JQE v1.5.1 | CQE v1.3.0 | US v1.1.0 | MB v1.0.0 | PMB v1.0.0-dev
