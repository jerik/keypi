# features history im plugin usersearch

Im Plugin usersearch sollen die User die ich aufgerufen habe, egal ob webseite oder teamschat gespeichert werden, sodass sich darauf zugreifen kann. Ähnlich wie beim jqe und cfe history features. Orientiere dich daran

- Generell wird jede person die ich per action aufrufe historisiert. 
- Wenn ich die Person mehrmals aufrufe, wird nur ein Eintrag historisiert. Dabei soll für die spätere Verwendung alles notwendige gespeichert werden um die actions die es zu diesem Eintrag gibt, später auch wieder auszuführen
- Auf die History habe ich sofort nach dem activieren des plugins in der launchbox zugriff

## Bisheriger Ablauf
- lanchbox öffnen -> box ist offen
- us + [tab] eingeben -> usersearch plugin ist aktiviert
- Name eingeben + [Enter] -> Suche wird ausgelöst und Ergebnisliste wird angezeigt
- Filterung der Ergebnisse + Auswahl eines Eintrages + [Enter] -> Default action wird ausgeführt; 
### Alternative Möglichkeit
- Auswahl eines Eintrages + [Tab] -> Action Einträge werden angezeigt aus denen ich auswählen kann
	- Auswahl einer Action + [Enter] -> Action wird ausgeführt

## Neuer Ablauf mit history Feature
### Use case 1
- lanchbox öffnen -> box ist offen
- us + [tab] eingeben -> usersearch plugin ist aktiviert
- Name eingeben 
- Die History-Einträge werden angezeigt und nach dem namen gefiltert
- Auswahl eines History-Eintrages + [Enter] -> Default action wird ausgeführt
### Alternative Möglichkeit
- Auswahl eines History-Eintrages + [Tab] -> Action Einträge werden angezeigt aus denen ich auswählen kann
	- Auswahl einer Action + [Enter] -> Action wird ausgeführt
### Alternative Möglichkeit
- Unter Name kann kein History-Eintrag gefunden werden + [Enter] -> Suche wird ausgelöst und Ergebnisliste wird angezeigt
- Filterung der Ergebnisse + Auswahl eines Eintrages + [Enter] -> Default action wird ausgeführt & Eintrag wird in der History gespeichert
### Alternative Möglichkeit
- Unter Name kann kein History-Eintrag gefunden werden + [Enter] -> Suche wird ausgelöst und Ergebnisliste wird angezeigt
- Auswahl eines Eintrages + [Tab] -> Action Einträge werden angezeigt aus denen ich auswählen kann
	- Auswahl einer Action + [Enter] -> Action wird ausgeführt & Eintrag wird in der History gespeichert

# nach der erfolgreichen entwicklung
Aktualisiere alle dokumentationen, insbesondere die readme.md, dort fehlt die Information zum usersearch plugin
