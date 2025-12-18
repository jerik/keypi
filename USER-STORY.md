# User Story: Filerung in der Jira-Ergebnisliste

**Status:** 📝 In Planung
**Erstellt:** 2025-12-19

---

## 🎯 Beschreibung

Wenn ich als User in der launchbox die jql geschrieben habe, wird mir die Ergebnisliste angezeigt. Diese kann lang sein und diese möchte ich filtern. D.h. das JQL wird nicht mehr verändert, sondern durch weitere Eingaben kann ich in der bestehend Ergebnisliste filtern. Wenn ich die Buchstaben 'ab' eingebe, wird in der ergebnisliste nur noch die Einträge angezeigt die 'ab' besitzen.
Eine idee, wenn das jql abgeschlossen ist drückt man Enter. Anstatt das erste eregbnis auszuwählen, geht man in den Filtermodus und kann in der Ergebnisliste filtern. Wenn man dann Enter drückt wird das ausgewählte Eintrag ausgeführt. 

1. launchbox jqe aufrufen und query eingeben
[jqe| creator = currentUser()] 
| entry a|
| entry ab|
| entry c|
| entry abc|

2. In dern Filtermodus wechseln
[jqe| creator = currentUser()] + Enter
[jqe filter| ab]
| entry ab|
| entry abc|

3. Ausführen 
[jqe filter| ab]
| entry ab |
| entry abc | <-- Enter

URL des Entry abc wird aufgerufen


## Akzeptanzkriterien 

1. Als User möchte ich nach meiner Eingabe der jql diese mit Enter oder Tabulator oder ähnlich abschliessen, 
damit ich in eine Fitltermodus wechseln kann, um die Ergebnisliste durch weitere eingaben zu filtern. 

2. Als User möchte ich im Filtermodus weitere Eingaben tätigen, damit diese Ergebnis aus der jql anhand dieser Eingaben gefiltert werden,
damit die Ergebnisliste kürzer wird und ich schneller das von mir gesuchte Ticket finde.



## 🔧 Technische Details

### Betroffene Dateien
- `Datei 1`: Was wird geändert
- `Datei 2`: Was wird geändert

### Design-Entscheidungen
- [Wichtige technische Entscheidungen]

### Offene Fragen
- [ ] Frage 1?
- [ ] Frage 2?

## 🧪 Testplan

### Manuelle Tests
- [ ] Test 1
- [ ] Test 2

## 📝 Notizen

[Zusätzliche Notizen]

---

## 🎬 Umsetzung

### Implementation Checklist
- [ ] Feature implementiert
- [ ] Tests durchgeführt
- [ ] DoD: ruff check, ruff format
- [ ] documentation.md aktualisiert
- [ ] Changelog updated

### Dialog-Historie
[Diskussionen und Entscheidungen während der Entwicklung]

---

**Letzte Aktualisierung:** YYYY-MM-DD
