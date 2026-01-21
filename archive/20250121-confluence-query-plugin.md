# Beschreibung
Als User möchte ich Confluence mittels CQL (Confluence Query Language) via Keypirinha nutzen können.
Als User möchte ich das Kommando **`cqe`** (default, konfigurierbar) in Keypirinha eingeben und dann in den Query-Modus gelangen. Dort kann ich dann die Query eingeben.
Wenn ich im Query-Modus die Taste Enter drücke, soll die Query ausgeführt werden.
Als Ergebnis sehe ich in Keypirinha die Ergebnisliste. Diese enthält im Minimum den Titel der Confluence Seite.
Die Ergebnisse kann ich durch Eingabe weiterer Buchstaben in Keypirinha entsprechend filtern.
Wenn ich einen Eintrag ausgewählt habe und Enter drücke, öffnet sich diese Confluence Seite im Browser.

Es können die gleichen Settings wie beim Jira-Query-Plugin in diesem Repository genutzt werden. Also API-Key und URL.

Das Confluence-Query-Plugin verhält sich ähnlich wie das Jira-Query-Plugin:
- Plugin mit Keyword aufrufen
- Im Query-Modus die Query eintippen
- Mit Enter die Query ausführen
- Das Ergebnis ist über Keypirinha filterbar
- Wird ein Eintrag ausgewählt wird dieser im Browser geöffnet

## Akzeptanzkriterien
- Der User kann das Confluence-Query-Plugin in Keypirinha mit **`cqe`** (default) aufrufen
- Das Keyword ist in der INI-Datei konfigurierbar (analog zu JQE)
- Nach Aufruf möchte ich die Query in CQL eingeben können
- Mit Enter wird die CQL ausgeführt
- Sofern ein Ergebnis vorhanden ist, wird das angezeigt, ansonsten eine Fehlermeldung, dass nichts zurückgeliefert wurde
- Das Ergebnis ist über Keypirinha filterbar, durch weitere Eingaben in Keypirinha
- Wählt der Nutzer einen Eintrag aus, wird der Eintrag im Browser geöffnet
- Es sollen die gleichen Settings wie bei Jira-Query-Plugin genutzt werden (API-Key, URL)

## Technische Umsetzung

### Projektstruktur
```
keypi/
├── keypi_cqe/                   # Neues Confluence-Plugin-Package
│   ├── __init__.py             # Plugin-Hauptklasse
│   ├── lib/                    # Interne Libraries
│   │   ├── __init__.py         # Package Marker
│   │   └── confluence_client.py  # Confluence API Client Wrapper
│   └── res/                    # Ressourcen & Konfiguration
│       ├── keypi_cqe.ini       # Benutzer-Konfigurationsdatei (Template)
│       ├── packages.json       # Package-Metadaten
│       └── changelog/          # Versionshistorie
```

### API Integration
- **Endpoint**: Confluence Cloud REST API v1 - `/rest/api/content/search`
- **Query Parameter**: `cql=<query>`
- **Authentifizierung**: Basic Auth (Email + API Token) - gleich wie Jira
- **Relevante Felder**: `id`, `title`, `type`, `_links.webui` (für Browser-URL)

### Implementation Tasks
- [x] Create plugin structure (keypi_cqe/)
- [x] Implement confluence_client.py (API wrapper)
- [x] Implement plugin main class (inherit from keypirinha.plugin.Plugin)
- [x] Implement two-phase workflow (CQL input → Filter results)
- [x] Add configuration handling (keyword, credentials)
- [x] Implement error handling (auth, network, API errors)
- [x] Create INI template file
- [x] Add changelog entry
- [x] Update documentation.md
- [ ] Manual testing with real Confluence instance
- [x] Run DoD checks (ruff, tests)

# Hilfreiche Informationen
Hier sind die **offiziellen Links zur Confluence‑Cloud‑Dokumentation**, speziell für **API‑Queries mit der Confluence Query Language (CQL)** – also genau das, was du gesucht hast:

***

## 🔹 **1. Offizielle Atlassian‑Dokumentation zu CQL (Confluence Query Language)**

### **Advanced Searching using CQL (Cloud) – *DIE* Hauptdokumentation**

Dieser Link enthält:

*   Grundsyntax
*   Felder, Operatoren, Funktionen
*   Beispiele
*   REST‑API‑Abfragen mit `cql=`

📄 <https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/>    [\[developer....assian.com\]](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)

***

## 🔹 **2. Confluence Cloud REST API – *Search Endpoint (CQL via API)***

Dokumentation für API‑Abfragen mit CQL, inkl. Parametern (`limit`, `cursor`, `excerpt`, …), Beispiel‑Requests und Hinweise zu Einschränkungen:

📄 <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/>    [\[developer....assian.com\]](https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/)

***

## 🔹 **3. CQL Fields Reference (Alle verfügbaren Felder)**

Liste aller CQL‑Felder inkl.:

*   unterstützte Operatoren
*   Beispiele
*   Besonderheiten (z. B. `ancestor`, `label`, `created`, `creator`, …)

📄 <https://developer.atlassian.com/cloud/confluence/cql-fields/>    [\[developer....assian.com\]](https://developer.atlassian.com/cloud/confluence/cql-fields/)

***

## 🔹 **4. Community & Add‑On Infos – ergänzende CQL‑Guides (optional)**

### Adaptavist CQL Guide (sehr gute Erklärungen & Beispiele)

📄 <https://docs.adaptavist.com/sr4cc/latest/features/cql-script-jobs/cql-guide>    [\[docs.adaptavist.com\]](https://docs.adaptavist.com/sr4cc/latest/features/cql-script-jobs/cql-guide)

### Praecipio: CQL Guide (Erweiterte praktische Beispiele)

📄 <https://www.praecipio.com/resources/articlesarticles/confluence-query-language-cql-guide>    [\[praecipio.com\]](https://www.praecipio.com/resources/articlesarticles/confluence-query-language-cql-guide)

***

## 🔹 **5. CQL Search Macro Documentation (für UI‑Suche, nicht API)**

Kann hilfreich sein, wenn du CQL in Confluence‑Seiten einbetten möchtest:

📄 <https://streamline.atlassian.net/wiki/spaces/CQLSEARCH/overview>    [\[streamline...assian.net\]](https://streamline.atlassian.net/wiki/spaces/CQLSEARCH/overview)

***

Wenn du möchtest, kann ich dir auch:
✅ Beispiel‑Queries bauen (für API oder Cloud GUI)  
✅ CQL‑Snippets für deine DVAG‑Strukturen schreiben  
✅ dir eine fertige API‑Abfrage generieren (inkl. `curl`, Python, PowerShell)

Sag einfach Bescheid!

