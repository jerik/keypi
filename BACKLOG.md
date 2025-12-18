# KeyPi - Feature Backlog

**Letzte Aktualisierung:** 2025-12-18

---

## Phase 2 Features

### JQL Shortcuts
Nutzer können häufig verwendete JQL-Queries als Shortcuts in der Konfiguration speichern.

**Beispiel:**
```ini
[jql_shortcuts]
me = assignee = currentUser()
open = status = "Open"
```

---

### Query Historie
Die letzten 10 JQL-Queries werden gespeichert und können über "hist" Keyword abgerufen werden.

**Features:**
- Letzte 10 Queries persistent speichern
- Keyword "hist" zeigt Historie
- Historie kann gelöscht werden

---

## Weitere Ideen

### Pagination Support
Mehr als 50 Ergebnisse pro Query anzeigen.

### Custom Fields Support
Nutzer können konfigurieren, welche Felder angezeigt werden.

### Multi-Jira-Instanz Support
Mehrere Jira-Instanzen (Firma + Personal) unterstützen.

### Offline Cache
Letzte Ergebnisse cachen für offline Zugriff.

### Favoriten
Tickets als Favoriten markieren für schnellen Zugriff.

### Ticket-Aktionen
Status ändern, Kommentare hinzufügen direkt aus Keypirinha.

---

**Legende:**
- ✅ Fertig
- 🚧 In Arbeit  
- 📝 Geplant
- 💭 Idee
