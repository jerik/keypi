# KeyPi - Feature Backlog

**Letzte Aktualisierung:** 2025-12-20

---

## Features

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
## Minor Bugs
### leere jql und man drück Enter 
Erwartetes Verhalten: Es wird eine Fehlermeldung angezeigt, man ist weiterhin im jql mode
Aktuelles Verhalten: die Launchbox schliesst sich. 
Workaround: Man fängt von neuem an, launchbox starten und jj eingeben
Prio: gering

### Neu konfigurieren des Keywords
In der Konfiguration ist das Keyword von jqe auf jj gesetzt worden
Nach dem neuladen der configuration, kann das plugin mit jj aufgerufen werden 

Erwartetes Verhalten: Das alte keyword funktioniert nicht mehr
Aktuelles Verhalten: Das alte keyword funktioniert weiterhin und ruft das plugin auf
Workaround: den eintrag jqe manuell aus dem Katalog entfernen, mittels CTRL + DEL sofern es stört
Prio: sehr gering

---

## Weitere Ideen
### Status des Tickes und oder Type des Tickets mit einem farblichen Icon im Eintrag sichtbar machen 
Icon ST, T, ST, SR, B, ...
Farbe: Grau = offen, erfasst, Blau = in Arbeit, Grün = erledigt, abgschlossen. 
Die Farbe und das mapping zum status sollte konfigurierbar sein

### JQL selbst im Browser aufrufen
Das genutzte JQL soll auch aufgerufen werden können. Erste Ideen, via Shortcut oder eigenem Eintrag.

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

### Refactoring
Umbenennen des Repositories in keypirinha-jql
Entsprechend den classennamen etc anpassen

## Installierbar mittels PackageControll machen. 
https://github.com/ueffel/Keypirinha-PackageControl
Overview
The default repository is maintained by myself, it's called "ueffel's Package Repository". An overview of available packages can be viewed [here](https://ue.spdns.de/packagecontrol/).

Submit your own package
If you created your own package and want it to be available via PackageControl to other Keypirinha users you can submit it [here]/https://ue.spdns.de/packagecontrol/new_package). The preferred way of publishing is GitHub. Your package repository should have the ready-to-use .keypirinha-package file in the release section. The package repository looks for the newest release (not pre-release) that has such a file and exposes it.

## Know Bugs
### Bug Shortcut UX - Auswahl der Shortcuts aus den Liste der Shortcuts funktioniert nicht 
Die angezeigte Liste der Shortcuts funktioniert nicht 100%. 
a) Als User möchte ich, dass bei der Eingabe von #, mir alle definierten Shortcuts aufgelistet werden. --> erfolgreich
b) Aus diesen Shortcuts kann ich einen auswählen. --> fehlerhaft, auswahl mit den Pfeiltasten + Enter funktioniert nicht. Man muss den shortcut voll ausschreiben, dann funktioniert es.

---

**Legende:**
- ✅ Fertig
- 🚧 In Arbeit  
- 📝 Geplant
- 💭 Idee
