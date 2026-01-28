# User Story: JQE Query History

## Beschreibung

Als Benutzer möchte ich meine zuletzt ausgeführten JQL-Queries über `#history` abrufen können, um häufig genutzte Queries schnell wiederzuverwenden ohne sie erneut eintippen zu müssen.

---

## Akzeptanzkriterien

- [ ] History über `#history` aufrufbar
- [ ] Letzte Queries werden in einer Liste angezeigt (neueste zuerst)
- [ ] Query aus History auswählen und ausführen
- [ ] History wird persistent gespeichert (überlebt Keypirinha-Neustart)
- [ ] Anzahl der History-Einträge konfigurierbar (default: 30)
- [ ] Duplikate: Gleiche Query nur einmal (bei erneutem Aufruf nach oben verschieben)
- [ ] `#history clear` löscht die komplette History

---

## Technische Details

### Speicherung

**Entscheidung:** JSON-Datei im User-Verzeichnis

- **Pfad:** `%APPDATA%\Keypirinha\User\keypi_jqe_history.json`
- **Format:**
  ```json
  {
    "version": 1,
    "queries": [
      {"query": "assignee = currentUser()", "last_used": "2026-01-26T14:30:00"},
      {"query": "project = MYPROJ AND status = Open", "last_used": "2026-01-26T14:25:00"}
    ]
  }
  ```
- **Vorteile:**
  - Persistent über Neustarts
  - Einfach zu lesen/debuggen
  - Unabhängig von Plugin-Updates
  - Gleicher Ort wie Config-Datei

### Konfiguration

In `keypi_jqe.ini`:
```ini
[main]
# ... existing config ...

# Maximum number of history entries (default: 30)
history_max_entries = 30
```

### Duplikat-Handling

- Bei Ausführung einer Query:
  1. Prüfen ob Query bereits in History existiert
  2. Falls ja: Entfernen aus alter Position
  3. Query an erste Stelle (neueste) hinzufügen
  4. Falls History > max_entries: Älteste entfernen

### Integration in bestehendes `#`-Pattern

| Eingabe | Verhalten |
|---------|-----------|
| `jqe #` | Zeigt: #edit, #history, #history clear, alle Shortcuts |
| `jqe #history` | Zeigt History-Liste (neueste zuerst) |
| `jqe #history clear` | Löscht die komplette History |
| `jqe #his` | Prefix-Match auf "history" |

### Workflow

1. User tippt `jqe` → `#history`
2. Liste der letzten Queries erscheint
3. User wählt Query aus → Enter
4. Query wird ausgeführt (wie manuell eingegebene Query)

---

## Entschiedene Fragen

- [x] `#history clear` zum Löschen der History → **Ja**
- [x] History-Datei für manuelle Edits dokumentieren → **Nein**

---

## Nicht im Scope

- CQE History (separates Feature für später)
- Export/Import von History
- History-Suche/Filterung (Keypirinha filtert automatisch)

---

## Abhängigkeiten

- Bestehende Shortcuts-Implementierung (`#`-Pattern)
- JSON-Handling (Python stdlib)

---

## Testfälle

- [ ] History-Datei wird erstellt wenn nicht vorhanden
- [ ] Query wird zur History hinzugefügt nach Ausführung
- [ ] Duplikate werden nach oben verschoben (nicht doppelt)
- [ ] History wird auf max_entries begrenzt
- [ ] History überlebt Keypirinha-Neustart
- [ ] `#history` zeigt alle Einträge
- [ ] `#history clear` löscht alle Einträge
- [ ] Konfiguration `history_max_entries` wird respektiert
- [ ] Korrupte History-Datei wird graceful behandelt
