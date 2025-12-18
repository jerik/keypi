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
- `keypi_jqe/__init__.py`:
  - `on_suggest()`: Zwei-Phasen-Logik implementieren (JQL-Eingabe vs. Filter-Modus)
  - Neue Variable: `_current_mode` (JQL vs. FILTER)
  - Neue Variable: `_current_results` (Cache für gefilterte Anzeige)
  - `_execute_jql_query()`: Nur aufrufen wenn Enter in JQL-Modus

### Design-Entscheidungen

**Zwei-Phasen-Ansatz:**
1. **Phase 1: JQL-Eingabe-Modus**
   - User tippt JQL (z.B. "creator = currentUser()")
   - **KEINE API-Calls während Eingabe** (verhindert 400 Fehler)
   - Hint anzeigen: "Press Enter to execute query"
   - Enter → JQL senden + in Filter-Modus wechseln

2. **Phase 2: Filter-Modus**
   - Ergebnisse sind geladen und gecacht
   - User tippt (z.B. "ab") → filtert gecachte Ergebnisse
   - Kein neuer API-Call!
   - Enter → Ausgewähltes Ticket öffnen

**Alternativen:**
- [x] ~~Debouncing (500ms warten vor API-Call)?~~ → Nicht nötig mit Zwei-Phasen-Ansatz
- [x] ~~Tab statt Enter für Query-Ausführung?~~ → Enter ist intuitiver
- [x] Visuelles Feedback für Modus-Wechsel:
  - **JQL-Modus**: `jqe|` (normaler Modus)
  - **Filter-Modus**: `jqe filter|` (nach Enter auf JQL)

### Offene Fragen → Geklärt

- [x] **Wie zurück in JQL-Modus?**
  - **ESC**: Setzt alles zurück (von vorne anfangen) → OK
  - **Einen Schritt zurück** (Filter → JQL): Wäre nett, aber nicht notwendig
  - **Entscheidung**: ESC setzt zurück, ein Schritt zurück ist optional/nice-to-have

- [x] **Soll JQL in der Anzeige sichtbar bleiben?**
  - **Entscheidung**: NEIN, JQL nicht im Hintergrund sichtbar
  - Visuelles Feedback durch Prompt-Änderung:
    - `jqe|` → JQL-Modus
    - `jqe filter|` → Filter-Modus

- [x] **Timeout für gecachte Ergebnisse?**
  - **Entscheidung**: KEIN Cache-Timeout
  - Grund: Tickets ändern sich → Cache könnte Ergebnisse verfälschen
  - Ergebnisse bleiben nur für aktuelle Session gecacht

## 🧪 Testplan

### Manuelle Tests
- [ ] JQL eingeben → KEINE API-Calls (Logs prüfen)
- [ ] Enter drücken → Query wird ausgeführt (nur 1 API-Call)
- [ ] Ergebnisse erscheinen
- [ ] "ab" tippen → Liste filtert sich (kein neuer API-Call)
- [ ] Enter → Ausgewähltes Ticket öffnet im Browser
- [ ] Test mit leerer Query → Fehlermeldung
- [ ] Test mit ungültiger JQL → Fehlermeldung nach Enter
- [ ] Test mit 0 Ergebnissen → "No results" Meldung

## 📝 Notizen

**Aktuelles Problem:**
- Jeder Tastendruck sendet unfertige JQL → viele 400 Bad Request Fehler
- Enter führt erstes Ergebnis aus (statt Filter-Modus)
- Weitere Eingaben erweitern JQL (statt Ergebnisse zu filtern)

**Synergien mit BACKLOG.md:**
- Query Historie Feature könnte erfolgreiche Queries cachen
- JQL Shortcuts würden auch von diesem Zwei-Phasen-Ansatz profitieren

**Performance-Gewinn:**
- Drastisch weniger API-Calls (aktuell: >10 pro Query, künftig: 1 pro Query)
- Bessere Rate-Limiting-Compliance
- Schnelleres Filtern (lokal statt API)

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

**Letzte Aktualisierung:** 2025-12-19 (Design-Entscheidungen finalisiert)

---

## 💬 Dialog-Historie (Erkenntnisse)

**2025-12-19 - Problemanalyse:**
- Aktuell werden bei jedem Tastendruck API-Calls gemacht → viele Fehler
- User wünscht Zwei-Phasen-Modus: JQL-Eingabe + Filter-Modus
- Keypirinha-Live-Filtering funktioniert, aber Plugin interpretiert Eingaben als JQL-Erweiterung
- Lösung: State-Management in Plugin (JQL_MODE vs FILTER_MODE)

**2025-12-19 - Design-Entscheidungen getroffen:**
- ESC setzt komplett zurück (akzeptabel)
- Visuelles Feedback: `jqe|` (JQL) vs `jqe filter|` (Filter)
- Kein Cache-Timeout (Tickets ändern sich, Cache würde verfälschen)
- Ergebnisse nur für Session gecacht, nicht persistent
