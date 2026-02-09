# neues Plugin Mindbox
Mindbox-Dateien sind Textdateien in einem Ordner in denen ich Informationen für mich vorhalte. Die Textdateien werden über ein script-erstellt (update-mindbox.cmd)
Als Nutzer möchte ich mit dem Minbox-plugin besser mit den Minbox-Dateien arbeiten. 

# Akzeptanzkriterien 
- Wenn ich das Keyword 'mb' eingeben, zeigt das plugin alle verfügbaren Mindbox-Dateien an. Wenn ich weiter Tippe, werden die Einträge gefiltert. 
- Wenn ich einen Eintrag auswähle wird die Datei die im Eintrag hinterlegt ist, geöffnet.
- Wenn ich im plugin #edit eingebe wird die configurationsdatei aufgerufen
- In der Konfigurationsdatei soll
  - der Ordner angegeben werden, wo die Mindbox Dateien liegen
  - das plugin-keyword angegeben werden, default ist 'mb'

# Entwicklungshinweise
- beachte die git richtlinien
- Orientiere dich bei der Entwicklung an den vorhanden plugins. Falls noch nicht vorhanden lege eine development-best-practise.md wo die wichtigsten Inforamtionen drinstehen, sodass das llm nicht immer den ganze code durchlesen muss um das zu verstehen
- Erstelle Testfälle.
- Push in git erfolgt erst wenn testfälle alle grün sind. Das übernimmst du selbsttändig. 
