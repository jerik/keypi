# Plugin filelookup optimieren und erweitern
Ich habe ein Plugin, siehe keypi_filelookup womit eine Textdatei geparst wird. In der Textdatei siehe keypi_filelookup/winevent.log, sind die login/logout events gespeichert. Daraus lese ich, wann ich mit meiner Arbeit angefangen habe. 


Aktuell mein der Workflow so aus: 

    1. keypi launchbox starten 
    2. keyword 'fl' eingeben
    3. Es werden die Zeiten angezeigt, samt Datum 

    Beispielsweise Mi 09:04

Dann weiss ich das ich am Mittwoch um 09:04 angefangen habe. 

Was ich dann im Kopf mache ist: 
    a) Ich rufe die Launchbox mit keywordk 'fl' um 17:09 Uhr auf
    b) Ich rechne 17-9 = 8h die ich gearbeitet habe. Ich runde die Zahlen meistens auf 15 Minuten einheiten. 
    c) ich ziehe meine Mittagspause ab 8h - 1h = 7h 
    d) ich habe 7h gearbeitet. Das nutze ich um es in den Stundennachweis einzutragen


# Aufgabe
1) Bitte review das plugin und optimiere es. 

2) Meine Workflow möchte ich nun optimieren. 

    1. keypi launchbox starten (um 17:09)
    2. keyword 'fl' eingeben
    3. Es werden die Zeiten angezeigt, samt Datum, (bspw. 09:04)
    4. ich wähle ein Datum aus (via Tab)
    5. Es werden mit Optionen angezeigt: 
            8h ohne Pause
            7h mit 1h Pause
            6,5h mit 1,5h Pause
    6. Ich wähle einen Eintrag aus, bspw. 7h mit 1h Pause
            Dann wird in die Datei ~/Documents/logs/Journal.log folgender Eintrag angehängt:

                # Mi 2026-08-19 1709:44
                @arbeitsstunden am 2026-08-19: 7h 


Lies dir die Dateien development-best-practise.md, documentation.md und KEYPIRINHA-LEARNINGS.md durch

Sofern rückfragen sind, kläre diese mit mir im Dialog. 
Erstelle ein Konzept und ein Plan wie das vorhaben umgesetzt werden kann. 
Die Dokumentation (KEYPIRINHA-LEARNINGS.md, README.md, development-best-practice.md, documentation.md) muss nach der erstellung auf dem aktuellsten Stand sein. 
Wenn ich Konzept und Plan freigegeben haben, kannst du mit der Umsetzung anfangen.

# Entwicklungshinweise
- beachte die git richtlinien
- Orientiere dich bei der Entwicklung an den vorhanden plugins. Falls noch nicht vorhanden lege eine development-best-practise.md wo die wichtigsten Inforamtionen drinstehen, sodass das llm nicht immer den ganze code durchlesen muss um das zu verstehen
- Erstelle Testfälle.
- Push in git erfolgt erst wenn testfälle alle grün sind. Das übernimmst du selbsttändig. 
