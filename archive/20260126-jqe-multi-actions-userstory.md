# User Story: JQE Multi-Actions

**Plugin:** Jira Query Explorer (JQE)
**Version:** 1.2.0 → 1.3.0
**Datum:** 2026-01-23

---

## 📋 User Story

Als Nutzer möchte ich folgende Verbesserungen im Jira Query Plugin haben:
- Die Einträge aus der Ergebnisliste sollen mehrere Actions bekommen
- Neben dem Aufrufen der Webseite möchte ich die URL kopieren können, um die Ergebnisse besser in meinem Workflow nutzen zu können

---

## ✅ Akzeptanzkriterien

### 1. Multi-Action Support für Ergebnisse
- [x] Als User möchte ich mehrere Actions zu einem Eintrag haben
- [x] Wähle ich einen Eintrag aus und drücke **Enter**, wird die URL des Eintrags im Browser aufgerufen (Standard-Action)
- [x] Wähle ich einen Eintrag aus und drücke **Tab**, werden mir in Keypirinha die möglichen Actions angezeigt

### 2. Verfügbare Actions
Die möglichen Actions sind:
- [x] **Open ticket** - Öffnet Jira-Ticket im Browser (Standard-Action bei Enter)
- [x] **Copy URL** - Kopiert Ticket-URL in die Zwischenablage

---

## 🔧 Implementierung

### Code-Änderungen (v1.3.0-dev.1)
- [x] Version auf v1.3.0-dev.1 gesetzt
- [x] Import json hinzugefügt
- [x] ACTION_OPEN und ACTION_COPY_URL Konstanten hinzugefügt
- [x] set_actions() in on_start() implementiert
- [x] data_bag von issue["key"] zu json.dumps(issue) geändert
- [x] on_execute() mit Action-Handling erweitert

### Status
✅ **Implementierung abgeschlossen**

Commit: `9843d8e` - feat: add multi-action support to JQE plugin

---

## 🧪 Testing

**Bereit für manuelle Tests in Keypirinha:**

1. **Standard-Action (Enter)**
   - [ ] JQL-Query ausführen
   - [ ] Ticket auswählen
   - [ ] Enter drücken
   - [ ] Erwartung: Ticket öffnet im Browser

2. **Action-Menü (Tab)**
   - [ ] Ticket auswählen
   - [ ] Tab drücken
   - [ ] Erwartung: 2 Actions erscheinen

3. **Copy URL Action**
   - [ ] Im Action-Menü "Copy URL" auswählen
   - [ ] Enter drücken
   - [ ] Erwartung: URL in Zwischenablage

---

## 📝 Nächste Schritte

Nach erfolgreichem Testing:
- [ ] Version auf v1.3.0 setzen (Final - ohne -dev)
- [ ] Dokumentation aktualisieren
- [ ] Commit und Push
- [ ] PR erstellen

---

**Status:** 🟡 Ready for Testing
