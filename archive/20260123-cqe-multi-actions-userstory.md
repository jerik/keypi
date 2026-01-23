# Userstory

Als Nutzer möchte ich folgede verbesserungen haben, 
	1. bei der ergebnisliste des confluence-query-plugin soll der Space und das letzte aktualisierungsdatum genannte werden, damit ich das ergebnis besser einordnen kann
	2. Einträge aus der Ergebnisliste soll mehrere Actions bekommen. Neben dem aufrufen von Der Webseite, möchte ich die URL kopieren können und die Seite im bearbeiten modus aufrufen können, um die Ergebnisse besesr in meinem Workflow nutzen zu könenn.

## Akzeptanzkriterien 
- Als User möchte in in der Ergebnisliste pro Eintrag die Inforamtionen zum Space, Typ und das Aktualsierungsdatum sehen.
- Als User möchte ich mehrere Actions zu einem Eintrag habe. 
	- Wähle ich einen Eintrag aus und drücke Enter, wird die URL des Eintrages im Browser aufgerufen
	- Wähle ich einen Eintrag aus und drücke Tabulator, werden mir in Keypirinha die möglichen Actions angezeigt. Das sind:  
		- Open page (standard actions)
		- Copy page URL - Die URL Der Seite wird in die Zwischenablege kopiert
		- Open page in editmode - Die Seite wird im Editmodus im Browser geöffnet


## Details zu 2. Einträge sollen mehr Actions bekommen
- Die Standard-Action ist, das die URL der Confluence Seite im Browser aufgrufen wird. Diese Action soll ausgeführt werden, wenn man den Eintrag in Keypirinha selektiert und Enter drückt
- Selektiert man den Eintrag in Keypirinha und drückt Tabulator, werden die möglichen Actions angezeigt. Das sind:
	- Aufruf der URL im Browser (Standard-Action)
	- Kopieren der URL in die Zwischenablage
	- Aufrufen der Confluence-Seite im Bearbeiten Modus


Wenn man die Normal URL der Confluence Seite aufruf gelangt man in den Ansicht Modus
<confluence-baseurl>/wiki/spaces/FOO/pages/687210497/foobar-seite.html

wechselt man in den bearbeiten modus der Conflunce-Seite sieht die URL folgendermassen aus: 
<confluence-baseurl>/wiki/spaces/FOO/pages/edit-v2/687210497

Informationen zu keypirinha documentation

- doku extending keyprinha: https://keypirinha.com/api.html
- doku zu create_action: https://keypirinha.com/api/plugin.html - doku zu create_action
- repo zu einem simplen keypirinha plugin was actions benutzt: https://github.com/TimberToe/keypirinha-todo-markdown/blob/master/src/todo-markdown.py
- Liste von anderen keypirinha plugins repos: https://github.com/topics/keypirinha-plugin

## Details zu 1: Space und Aktualisierungsdatum auslesen
Space ist im JSON unter folgenden Attributen zu finden. (Siehe weiter unten ein Auszug des JSON)
 'space': '/rest/api/space/FOO'},
 'displayUrl': '/spaces/FOO'},

In der Ergebnisliste soll dann FOO als Space angezeigt werden

Das Aktualisierungsdatum ist in folgenden Attribut zu finden  (Siehe weiter unte ein Auszug des JSON)
 'lastModified': '2026-01-21T14:27:02.000Z',

Das datum soll in der Ergebnisliste als ISO-Date angezeigt werden,  hier im Beipsiel 2026-01-21

Im Endergebnis sieht ein Eintrag in Keypirinha folgendermassen aus

	Titel 
	Space | Type | Actualisierungsdatum

Beispiel:

	Foobar is nice
	Space: FOO | Type: page | LastMod: 2026-01-21

### Beispielauszug des Ergebnis JSON der API-Antwort
[{
'content': {
'id': '690258032',
 'type': 'page',
 'status': 'current',
 'title': 'Roadmap Consent-Fachkonzepte 2026 / 2027',
 'title': 'Foobar is nic',
 'childTypes': {
},
 'macroRenderedOutput': {
},
 'restrictions': {
},
 '_expandable': {
'container': '',
 'metadata': '',
 'extensions': '',
 'operations': '',
 'children': '',
 'history': '/rest/api/content/690258032/history',
 'ancestors': '',
 'body': '',
 'version': '',
 'descendants': '',
 'space': '/rest/api/space/FOO'},
 '_links': {
'webui': '/spaces/FOO/pages/690258032/Foobar+is+nice',
 'self': 'https://foo.atlassian.net/wiki/rest/api/content/690258032',
 'tinyui': '/x/cIAkKQ'}},
 'title': 'Foobar is nice',
 'excerpt': 'Foobar, wie man es in der Entwicklung einsetzt und woher es kommt. Kurzer geschichtlicher Einblick und Fun-facts',
 'url': '/spaces/FOO/pages/690258032/Foobar+is+nice',
 'resultGlobalContainer': {
'title': 'Dev und Mehr',
 'displayUrl': '/spaces/FOO'},
 'breadcrumbs': [],
 'entityType': 'content',
 'iconCssClass': 'aui-icon content-type-page',
 'lastModified': '2026-01-21T14:27:02.000Z',
 'friendlyLastModified': 'gestern um 15:27',
 'score': 0.0}, 
 {
'content': {
'id': '690257967',
 'type': 'page',
 'status': 'current',
 ...
 }]
 

