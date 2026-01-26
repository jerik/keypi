# User Story: CQE Shortcuts
Beschreibung
Ich benötige cqe shortcuts, damit ich häufig genutze cqe nicht immer neu eintippen muss, sondern diese über einen shortcut aufrufen kann. Die shortcuts sollen in der config datei konfiguriet, die ich dann aufrufen und editieren kann. Vom Verhalten orientiere dich bitte an den jqe shortcuts implementierung
Für die config-datei wäre ein Vorschlag [cqe_shortcuts] 
* myco = title ~ konzept and creator = currentUser()
* mytodo = title ~ todo and creator = currentUser() 

In keypirinha möchte ich nach dem keyword 'cqe' die shortcuts aufrufen können. Die jql shortcuts werde mit einem Prefix # aufgerufen. Das würde dann so aussehen [cqe| #myco ] oder [cqe| #mytodo] 

Wenn ich nur '#' eingebe soll die liste der cqe_shortcuts angezeigt werden. Analog zu den jqe_shortcuts
[cqe|# ] |
   #myco 
   title ~ konzept and creator = currentUser()
   ---
   #mytodo 
   title ~ todo and creator = currentUser()

Aus diesen Einträgen kann ich einen auswählen und ausführen.

Optional: wenn ich als jql_shortcut '#edit' eingebe soll die die configdatei im standard editor aufgerufen werden, damit ich die cqe_shortcuts bearbeiten kann. Analog zu der jqe implementierung

Akzeptanzkriterien
Als User möchte ich cqe_shortcuts verwalten können, damit ich weiss welche shortcuts ich definiert habe
Als User möchte ich die definierten shortcuts im plugin aufrufen können. Die shortcuts beginnen mit #, gefolgt von dem shortcut namen, bspw. #myco
Als User möchte ich die shortscust im cqe mode aufrufen können
Als User möchte ich dass der hinter dem shortcut hinterlegte cfl query im weiteren Prozess genutzt wird, d.h. die cfl wird ausgeführt und in keypirinha sehe ich die Ergebnisliste wie bisher auch
Als User möchte ich, dass bei der Eingabe von #, mir alle definierten Shortcuts aufgelistet werden. Aus diesen Shortcuts kann ich einen auswählen.
Als User möchte ich bei der eingabe von #edit, das die datei mit den shortcuts im standard-editor geöffnet werden, damit ich diese editieren kann.
Abnahme
Das Feature ist soweit abgenommen und funktionstüchtig. Akzeptanzkriterium 5, funktioniert nicht 100% aber das ist vertretbar.
