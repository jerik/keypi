# Plugin Chromehistory wieder zum laufen bringen und optimieren. 
Ich habe ein Plugin womit ich in keypirinha die Chromehistory durchsuchen kann. Ich gebe das Keyword 'ch' ein und habe dann zugriff auf ausgewählte chrome history einträge. Der Prozess dafür funktioniert, seit dem Umstieg auf einen neuen Rechner nicht mehr. 
Du sollst das Plugin wieder zum laufen bringen und wenn möglich den Prozess optimieren. 

Untern dem Verzeichenis keyp_chromehistory/ findest du die whichtigsten Daten dafür. Hier kurz die erklärung wie das alte Setup funktionert hat. 

unter c:\Users\e17\bin liegen die Dateien 
chrome-hist-prerocess.cmd
chrome-history.py

Per Windows Aufgabenverwaltung wird chrome-history.py aufgerufen und nutzt chrome-hist-prerocess.cmd um die Datei c:\Users\e17\documents\chrome-history.csv zu erzeugen. 

Das Keypirinha Plugin C:\Develop\programs\Keypirinha\portable\Profile\Packages\chrome-history\chrome-history.py hat dann anhand der csv file die entsprechend Einträge generiert. Wegen der Namensgleichheit habe ich diese Plugin in keyp_chromehistory/plugin-chrome-history.py umbenannt. 

# Aufgabe
Bitte lies dir alle Dateien durch und entwickle ein Konzept mit dem wir das Plugin wieder zum laufen bringen. 
Sofern rückfragen sind, kläre diese mit mir im Dialog. 
Erstelle ein Konzept und ein Plan wie das vorhaben umgesetzt werden kann. 
Die Dokumentation (KEYPIRINHA-LEARNINGS.md, README.md, development-best-practice.md, documentation.md) muss nach der erstellung auf dem aktuellsten Stand sein. 
Wenn ich Konzept und Plan freigegeben haben, kannst du mit der Umsetzung anfangen.

# Entwicklungshinweise
- beachte die git richtlinien
- Orientiere dich bei der Entwicklung an den vorhanden plugins. Falls noch nicht vorhanden lege eine development-best-practise.md wo die wichtigsten Inforamtionen drinstehen, sodass das llm nicht immer den ganze code durchlesen muss um das zu verstehen
- Erstelle Testfälle.
- Push in git erfolgt erst wenn testfälle alle grün sind. Das übernimmst du selbsttändig. 
