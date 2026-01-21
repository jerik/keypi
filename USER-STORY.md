# Beschreibung
Als User möchte ich das confluence mittels cfl (confluence query language) via keypirinha nutzen können. 
Als User möchte ich das Kommando ff in keypirinha eingeben und dann in den query-mmodus gelangen. Dort kann ich dann die query eingeben. 
Wenn ich im query-modus die Taste enter drücke soll, die query ausgeführt werden. 
Als ergebnis sehe ich in keypirinha die ergebnisliste. Diese enthält im Minimum den Titel der Confluence Seite.
Die Ergebnisse kann ich durch eingabe weitere Buchstaben in keypirinha entsprechend filtern. 
Wenn ich einen Eintrag ausgewählt habe und Enter drücke, öffnet sich diese Confluence Seite im Browser. 

Es können die gleichen Settings wie beim jira-querey-plugin in diesem repository genutzt werden. Also API-key und URL. 

Das confluence-query-plugin verhält sich ähnlich wie das jira-query-plugin: 
- plugin mit keyword aufrufen
- im query-modus die query eintippen
- mit Enter die query ausführen
- das Ergebnis ist über keypirinha filterbar
- wird ein Eintrag ausgewählt wird dieser im Browser geöffnet.

## Akzeptanzkriterien 
- Der User kann das Confluence-query-plugin in Keypirinha mit 'dd' aufrufen
- Nach aufruf möchte ich die query in cfl eingeben können
- Mit Enter wird die cfl ausgeführt
- Sofern ein Ergebnis vorhandne ist, wird das angezeigt, ansonste eine Fehlermeldung, das nichts zurückgeliefert wurde
- Das Ergebnis ist über Keypirinha filterbar, durch weitere Eingaben in Keypirinha.
- Wählt der Nutzer einen Eintrag aus, wird der Eintrag im Browser geöffnet.
- Es sollen die gleichen SEttings wie bei jira-query-plugin genutzt werden

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

