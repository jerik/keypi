# KeyPi - Jira Query Explorer

**Version:** 1.0.0

---

## 📖 Übersicht

KeyPi-JQE ist ein Keypirinha-Plugin zum Abfragen von Jira Cloud mittels JQL.

**Funktionen:**
- JQL-Queries aus Keypirinha ausführen
- Ergebnisse als filterbare Liste
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

1. Tippe: `jqe` → `Tab`
2. JQL eingeben: `assignee = currentUser()`
3. `Enter` drücken
4. Ticket auswählen → `Enter` → öffnet im Browser

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

### Version 1.0.0 (2025-12-18)
- Initial Release (MVP)
- JQL-Queries ausführen
- Ergebnisse anzeigen
- Tickets im Browser öffnen

---

**Ende** | v1.0.0
