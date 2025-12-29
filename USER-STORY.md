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
