echo. OFF
rem copy database 
copy C:\Users\e17\AppData\Local\Google\Chrome\USERDA~1\Default\History C:\Users\e17\AppData\Local\Google\Chrome\USERDA~1\Default\History.mybackup

rem create csv header 
echo title,url,last_visit_time > c:\users\e17\documents\chrome-history.csv
sqlite3 -header -csv C:\Users\e17\AppData\Local\Google\Chrome\USERDA~1\Default\History.mybackup "select title,url,last_visit_time from urls;" >> c:\users\e17\documents\chrome-history.csv
