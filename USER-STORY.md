# User-Story: jql shortcuts
## Beschreibung
Ich benötige jql shortcuts, damit ich häufig genutze jql nicht immer neu eintippen muss, sondern diese über einen shortcut aufrufen kann. Die shortcuts sollen in der config datei konfiguriet werden. 
Weswegen ich mir bei der config datei unsicher bin ist, die jql enthalten auch '='-Zeichen. Ziel ist es die jql shortcuts irgendwo abzulegen wo ich sie leicht editieren und verändern kann und das sie sauber von keypirinha verwendet werden kann. 

Für die config-datei wäre ein Vorschlag
[jql_shortcuts]
me = assignee = currentUser()
open = status = "Open"
mytask = assignee = currentUser() and status = open

In keypirinha möchte ich nach dem keyword 'jj' die shortcuts aufrufen können. Die jql shortcuts werde mit einem Prefix aufgerufen, bspw. # oder :. Das würde dann so aussehen 
[jj| #me ] oder [jj| :me]
[jj| #open] oder [jj| :open] 

Am liebsten wäre mit # als Prefix. 

Wenn ich nur '#' eingebe soll die liste der jql_shortcuts angezeigt werden. Bspw. 
[jj|#      ]
| #me - assignee = currentUser()|
| #open - status = "open"|
| #mytask - assignee = currentUser() and status = open|

Aus diesen Einträgen kann ich einen auswählen und ausführen. 

Optional: 
wenn ich als jql_shortcut '#config' eingebe soll die die configdatei im standard editor aufgerufen werden, damit ich die jql_shortcuts bearbeiten kann. 

## Akzeptanzkriterien 
1. Als User möchte ich jql_shortcuts verwalten können, damit ich weiss welche shortcuts ich definiert habe
2. Als User möchte ich die definierten shortcuts im plugin aufrufen können. Die shortcuts beginnen mit #, gefolgt von dem shortcut namen, bspw. #me
3. Als User möchte ich die shortscust im jql mode aufrufen können
4. Als User möchte ich dass der hinter dem shortcut hinterlegte jql query im weiteren Prozess genutzt wird, d.h. die jql wird ausgeführt und in keypirinha sehe ich die ergebnisliste wie bisher auch
5. Als User möchte ich, dass bei der Eingabe von #, mir alle definierten Shortcuts aufgelistet werden. Aus diesen Shortcuts kann ich einen auswählen. 
6. Optional: Als User möchte ich bei der eingabe von #edit, das die datei mit den shortcuts im standard-editor geöffnet werden, damit ich diese editieren kann. 

# Abnahme
Das Feature ist soweit abgenommen und funktionstüchtig. Akzeptanzkriterium 5, funktioniert nicht 100% aber das ist vertretbar.

5. a) Als User möchte ich, dass bei der Eingabe von #, mir alle definierten Shortcuts aufgelistet werden. --> erfolgreich
   b) Aus diesen Shortcuts kann ich einen auswählen. --> fehlerhaft, auswahl mit den Pfeiltasten + Enter funktioniert nicht. Man muss den shortcut voll ausschreiben, dann funktioniert es.

Das nehme ich mit auf ins Backlog.

---

## 🔧 Technische Details

### Betroffene Dateien
- `keypi_jqe/__init__.py`:
  - **Version**: v1.2.0-dev.7 (finale Version)
  - **Neue Konstanten**:
    - `ITEMCAT_SHORTCUT`: Neue Item-Kategorie für Shortcuts
  - **Neue Instanzvariablen**:
    - `_jql_shortcuts`: Dict {shortcut_name: jql_query} für Shortcuts
  - **Geänderte Methoden**:
    - `_load_config()`: Lädt [jql_shortcuts] Sektion aus INI-Datei
    - `on_suggest()`: Erkennt # Prefix und delegiert an `_handle_shortcut_input()`
    - `on_execute()`: Behandelt #edit und Shortcut-Auswahl
  - **Neue Methoden**:
    - `_handle_shortcut_input(user_input)`: Zentrale Shortcut-Logik

- `keypi_jqe/res/keypi_jqe.ini`:
  - **Neue Sektion**: `[jql_shortcuts]`
  - Shortcuts werden als `name = jql_query` definiert
  - Beispiel: `me = assignee = currentUser()`

### Design-Entscheidungen

**1. INI-Format trotz '=' in JQL:**
- INI-Parser von Keypirinha kann mehrere '=' pro Zeile verarbeiten
- Erstes '=' ist Key-Value-Trenner, Rest gehört zum Value
- Beispiel: `me = assignee = currentUser()` → Key: "me", Value: "assignee = currentUser()"
- **Funktioniert einwandfrei**, keine Probleme festgestellt

**2. # als Prefix (nicht :)**
- Entscheidung für # Prefix wie vom User gewünscht
- Klare visuelle Unterscheidung zu normaler JQL
- Konsistent mit #edit für Config-Editor

**3. Case-Insensitive Matching:**
- Alle Shortcuts werden in lowercase gespeichert: `key.lower()`
- User-Input wird ebenfalls lowercase: `shortcut_name = user_input[1:].lower()`
- Ermöglicht Eingabe von #ME, #Me, #me (alle matchen gleich)

**4. Auto-Expand bei Exact Match (v1.2.0-dev.7):**
- Wenn User exakt einen Shortcut eintippt (z.B. #me), wird direkt JQL angezeigt
- Verhindert unnötigen Zwischenschritt
- User sieht: `jqe: assignee = currentUser()` mit "Press Enter to execute"
- Enter → Query läuft direkt, Launchbox bleibt offen (durch `hit_hint=KEEPALL`)

**5. Unique Targets für Shortcuts:**
- **Problem entdeckt**: Keypirinha dedupliziert Items nach (category, target)
- Alle Shortcuts mit `target="execute_shortcut"` → nur 1 sichtbar!
- **Lösung**: Unique targets: `target=f"shortcut_{name}"`
- Dadurch werden alle Shortcuts korrekt angezeigt

### Keypirinha-Verhalten (Lessons Learned)

**1. on_execute() schließt IMMER Keypirinha:**
- `on_execute()` ist für finale Aktionen gedacht
- `set_suggestions()` in `on_execute()` verhindert NICHT das Schließen
- Items brauchen `hit_hint=KEEPALL` VOR on_execute(), nicht darin

**2. Tab funktioniert NUR in Step 1:**
- Nach Tab-Druck in Step 1 (jqe → Tab) wird `on_suggest()` aufgerufen
- In Step 2 (nach Enter auf Item) funktioniert Tab NICHT
- User-Feedback bestätigt: "Tab funktioniert nicht. Keine Reaktion, erst auf [Enter]"
- **Konsequenz**: Workflow muss Enter nutzen, nicht Tab

**3. Item-Deduplication:**
- Keypirinha zeigt Items nur einmal pro (category, target) Kombination
- Mehrere Items mit gleicher Kategorie UND gleichem Target → nur eins wird angezeigt
- **Fix**: Jeden Shortcut mit unique target versehen

**4. args_hint vs hit_hint:**
- `args_hint=REQUIRED`: Item erwartet weitere Eingabe (z.B. JQL-Query)
- `args_hint=ACCEPTED`: Item kann weitere Eingabe akzeptieren
- `args_hint=FORBIDDEN`: Item hat keine weitere Eingabe
- `hit_hint=KEEPALL`: Verhindert Schließen bei Enter
- `hit_hint=IGNORE`: Erlaubt Schließen bei Enter

**5. Match.ANY wichtig bei set_suggestions():**
- `self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)`
- `Match.ANY`: Keypirinha filtert NICHT selbst, alle Items werden angezeigt
- Ohne Match.ANY: Keypirinha würde eigenes Filtering anwenden

### Entwicklungs-Iterationen

**v1.2.0-dev.1 - Initiale Implementation:**
- Shortcuts in Config
- Basis-Matching und Anzeige
- #edit Funktionalität

**v1.2.0-dev.2 - FOLDERID Fix:**
- Problem: `kpu.FOLDERID` existiert nicht in Keypirinha
- Lösung: Relative Pfade mit `os.path.dirname(__file__)` und `../../User/keypi_jqe.ini`

**v1.2.0-dev.3 - Unique Targets:**
- Problem: Nur 2 von 5 Shortcuts sichtbar (Deduplication)
- Lösung: `target=f"shortcut_{name}"` für jeden Shortcut
- **Durchbruch**: Alle Shortcuts werden angezeigt

**v1.2.0-dev.4 - Tab-Versuch:**
- Versuch: Tab-Handler in on_suggest() für Shortcuts
- Ergebnis: Tab funktioniert nicht in Step 2 (User-Feedback)

**v1.2.0-dev.5 - on_execute() Handler:**
- Versuch: JQL in on_execute() anzeigen mit set_suggestions()
- Ergebnis: Keypirinha schließt trotzdem

**v1.2.0-dev.6 - args_hint=ACCEPTED:**
- Versuch: args_hint auf ACCEPTED ändern für Shortcuts
- Erwartung: Enter fügt zu items_chain hinzu statt on_execute()
- Ergebnis: on_execute() wird trotzdem aufgerufen

**v1.2.0-dev.7 - Auto-Expand (FINALE LÖSUNG):**
- **Ansatz**: Bei Exact Match (z.B. #me) direkt execute-Item zeigen
- execute-Item hat `args_hint=REQUIRED` und `hit_hint=KEEPALL`
- Enter → Query läuft, Launchbox bleibt offen ✅
- **Workflow**: `jqe → #me → ENTER → Query läuft`
- **Funktioniert perfekt** für Typing-Workflow

**Finale Optimierung - Logging reduziert:**
- Problem: Excessive Logging verlangsamt Keypirinha
- Lösung: Nur EXACT MATCH und Warnings loggen
- Alle Debug-Logs entfernt
- Performance-Verbesserung spürbar

### Bekannte Einschränkungen

**1. Arrow-Key-Selection funktioniert nicht:**
- Workflow: `jqe → # → Arrow Keys → #me auswählen → ENTER`
- **Problem**: Keypirinha schließt sich, Query läuft nicht
- **Grund**: Shortcut-Items haben `hit_hint=IGNORE`, damit sie auswählbar sind
- **Workaround**: Shortcut vollständig austippen (z.B. #me)
- **Kompromiss akzeptiert**: Typing-Workflow funktioniert perfekt

**2. Warum Arrow-Key-Fix nicht implementiert:**
- **Versuch**: `hit_hint=KEEPALL` für Shortcut-Items
- **Problem**: Dann zeigt Keypirinha KEINE JQL-Expansion mehr
- **Erklärung**: Items mit KEEPALL können nicht in items_chain aufgenommen werden
- **Trade-off**: Typing-Workflow vs Arrow-Selection
- **Entscheidung**: Typing-Workflow priorisiert (häufigerer Use-Case)

### Code-Highlights

**Shortcut-Matching-Logik:**
```python
def _handle_shortcut_input(self, user_input):
    shortcut_name = user_input[1:].lower()  # Remove # and lowercase

    # EXACT MATCH → Zeige JQL direkt
    if shortcut_name in self._jql_shortcuts:
        exact_match_jql = self._jql_shortcuts[shortcut_name]
        self.info(f"EXACT MATCH: #{shortcut_name} -> {exact_match_jql[:50]}...")
        # Create execute-Item (KEEPALL hält Launchbox offen)
        suggestions.append(self.create_item(
            category=self.ITEMCAT_QUERY,
            label=f"{self._keyword}: {exact_match_jql}",
            short_desc="Press Enter to execute query",
            target="execute_jql",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.KEEPALL,
            data_bag=exact_match_jql,
        ))
    else:
        # PREFIX MATCH → Zeige Shortcut-Liste
        for name, jql in sorted(self._jql_shortcuts.items()):
            if name.startswith(shortcut_name):
                suggestions.append(self.create_item(
                    category=self.ITEMCAT_SHORTCUT,
                    label=f"#{name}",
                    short_desc=jql,
                    target=f"shortcut_{name}",  # UNIQUE!
                    args_hint=kp.ItemArgsHint.ACCEPTED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    data_bag=jql,
                ))
```

**Config-Loading (INI mit mehreren '='):**
```python
def _load_config(self):
    self._jql_shortcuts = {}
    if settings.has_section("jql_shortcuts"):
        for key in settings.keys("jql_shortcuts"):
            jql_query = settings.get_stripped(key, section="jql_shortcuts", fallback="")
            if jql_query:
                self._jql_shortcuts[key.lower()] = jql_query  # Case-insensitive
        self.info(f"Loaded {len(self._jql_shortcuts)} JQL shortcuts")
```

---

## 💬 Dialog-Historie (Erkenntnisse)

**2025-12-28 - Initiale Analyse:**
- User wünscht JQL Shortcuts mit # Prefix
- Unsicherheit wegen '=' in JQL (würde INI-Format stören?)
- Entscheidung: INI-Format ausprobieren → **funktioniert perfekt**

**2025-12-28 - Erste Bugs:**
1. #edit öffnet nicht → FOLDERID existiert nicht
2. Nur 2 von 5 Shortcuts sichtbar → Deduplication-Problem
3. Keypirinha schließt bei Shortcut-Auswahl
4. State-Persistenz nach Restart

**2025-12-28 - Unique Target Durchbruch:**
- Analyse: Keypirinha dedupliziert nach (category, target)
- Alle Shortcuts hatten `target="execute_shortcut"` → nur 1 sichtbar
- Fix: `target=f"shortcut_{name}"` → **alle Shortcuts erscheinen**

**2025-12-28 - Tab/Enter Problematik:**
- User-Feedback: "Tab funktioniert nicht in Step 2. Nur Enter."
- Erkenntnisse aus filter-feature branch:
  - "Keypirinha schließt IMMER nach on_execute()"
  - set_suggestions() in on_execute() funktioniert NICHT
- Mehrere Versuche: Tab-Handler, args_hint=ACCEPTED, on_execute() suggestions
- **Alle gescheitert**

**2025-12-28 - Auto-Expand Lösung:**
- **Idee**: Bei Exact Match direkt JQL-execute-Item zeigen
- execute-Item hat KEEPALL → Launchbox bleibt offen
- **Workflow**: User tippt #me → sieht JQL → Enter → läuft
- **Funktioniert perfekt** für Typing-Workflow
- Arrow-Selection opfern für funktionierenden Typing-Workflow

**2025-12-29 - Performance-Optimierung:**
- User-Feedback: "Excessive Logging verlangsamt Keypirinha"
- Debug-Logs entfernt (24 Zeilen)
- Nur EXACT MATCH und Warnings behalten
- Spürbare Performance-Verbesserung

**Finale Erkenntnisse:**
- INI-Format mit mehreren '=' funktioniert einwandfrei
- Keypirinha's Item-Deduplication erfordert unique targets
- on_execute() ist finale Aktion, kein Zwischenschritt möglich
- hit_hint=KEEPALL muss VOR on_execute() gesetzt werden
- Tab funktioniert nur in Step 1, nicht in Step 2
- Trade-offs sind notwendig: Typing-Workflow vs Arrow-Selection

**Wichtig für zukünftige Features:**
- **Items brauchen unique targets** zur Vermeidung von Deduplication
- **Mehrstufige Workflows** erfordern items_chain-Handling in on_suggest()
- **on_execute() schließt immer** → finale Aktionen planen
- **Tab ist limitiert** → Enter als primäre Interaktion nutzen
- **Performance**: Excessive Logging vermeiden, nur notwendige Logs

---

**Letzte Aktualisierung:** 2025-12-29 
