# Instructions

Es sollen plugins für den app-launcher https://keypirinha.com/index.html in python geschrieben werden 
Das Plugin soll JQL Code in der Jira Cloud anfragen und die Ergebnisse als Liste von Jiras zurückgegeben. Diese Liste ist dann in Keypirinha filterbar.
Wählt man einen Eintrag aus, wird die URL im Browser aufgerufen. 

Der Ablauf soll in keypirinha folgendermassen sein: 
1. Keypirinha aufrunfe -> die Eingabbox wird angezeigt
2. keyword "jqe" eingeben + tabulator drücken -> jqe ist ausgewählt
3. die JQL eingeben, bspw: assignee = currentUser() + Enter drücken -> die Anfrage wird an Jira Cloud gesendet -> Die Liste der Tickets erscheint
4. Durch weitere Eingaben in der Eingabebox wird die Liste gefiltert
5. Wenn ein Listeneintrag ausgewählt wird + Enter gedrückt -> URL des Jira-Tickets wird in Browser aufgerufen

Aus dem Request in 3 sollen folgende Sachen bei den Jira-Tickets abgefragt werden: 
- TicketID
- Summary 
- Status 
- Priorität
- Creator
- Assigne
- CreatedDate

In der Liste der Tickets hat ein Eintrag folgendes format: 
    TicketID: [Status] Summary

Das Plugin soll konfigurierbar sein. In der Konfiguration soll der Atlassian_api_key gespeichert werden

Die Installation des Plugins soll via https://github.com/ueffel/Keypirinha-PackageControl funktionieren

Dokumentation Keypirinha 
* Architektur: https://keypirinha.com/architecture.html
* Packages Structur: https://keypirinha.com/packages.html
* Extending Keyprinha: https://keypirinha.com/api.html

Beispiele für Keyprinha Plugins findest du hier: 
* https://keypirinha.com/contributions.html

Dokumentation zu Jira Cloud
* https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#about


# Erweiterungen für später, wenn wir eine laufende ersten Version (MVP) des Plugins haben 
- In der Konfiguration können keywords für jql abgelegt werden. Bspw. me: assignee = currentUser(). Dann kann man mit jql -> tab -> me -> enter das jql
assignee = currentUser() ausführen
- History Feature, die letzten 10 aufrufen kann man mit dem keyword "hist" anzeigen lassen. Wählt man eines der Einträge aus, wird dieses jql ausgeführt

