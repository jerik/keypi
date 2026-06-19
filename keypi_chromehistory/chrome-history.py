#!/usr/bin/env python
# coding: utf-8

# In[14]:


# use chrome history in keypirinha
# original history "C:\Users\e17\AppData\Local\Google\Chrome\User Data\Default\History" db will be copied to ~/documents/chrome-history.db
import pandas as pd
import sqlite3 as sql
import subprocess
cmd_preprocess = r'C:\Develop\bin\chrome-hist-prerocess.cmd'
browser_history_csv = r'c:\users\e17\documents\chrome-history.csv' # exported history db, from the preprocess
clean_db = r'c:\users\e17\documents\chrome-hist-clean.db'
export_csv = r'c:\users\e17\documents\delta-history.csv'
clean_csv = r'c:\users\e17\documents\clean-history.csv' # final file for keypirinha


# In[15]:


# prepare source
subprocess.call(cmd_preprocess)
df = pd.read_csv(browser_history_csv, encoding="utf-8")


# In[16]:


# focus only on the nvidia entries in the history
df_result = df[df['url'].str.contains('foo')]
# df_result


# In[17]:


# filter unessecary things 
# https://stackoverflow.com/a/39949288/1933185
# filter = df['Event Name'].str.contains(patternDel)
# df[~df.Subject.str.contains('|'.join(discard))]
# 2024-05-17: 
#   Geschweifte Klammern {} machen probleme, wenn möglich rausfiltern
discard_title = ["Suche", "nmeld", "ogin", "Home", "Vorgangsnavigator", 'Kontaktdaten', 'suc-', 'eitenverg', 'Seitenhistorie', 'Kommentar hin', 'Vorgang erstellen']
discard_url = ['editpage', 'broker', 'contextnavpagetreemode', 'MoveIssueUpdate', 'addDiagram', 'resumedraft', 'createpage', 'copypage', 'projektportal', 'create-content', 'diffpagesbyversion', 'edit-v2']
# whitelisting_url = ['display', 'login.action', 'resumedraft', 'copypage.action', 'tinyurl.action']
filter_title = df_result['title'].str.contains('|'.join(discard_title), na=False)
filter_url = df_result['url'].str.contains('|'.join(discard_url), na=False)
# print(filter_string)
df_filtered = df_result[~filter_title]
df_filtered = df_filtered[~filter_url]
df_filtered.to_csv(export_csv)
conn = sql.connect(clean_db)
# drop table if exists 
conn.execute('DROP TABLE IF EXISTS chrome_hist;')
df_filtered.to_sql('chrome_hist', conn)


# In[18]:


# not all entries are used, e.g. aroma is missing
# ggfs die anderen Lösungen ausprobieren: https://stackoverflow.com/q/15291506/1933185
query = '''
select ch.title, ch.url, ch.last_visit_time
from chrome_hist ch
inner join (
    select title, max(last_visit_time) youngest_visit
    from chrome_hist
    group by title
) chgrp
on chgrp.title = ch.title
where chgrp.youngest_visit = ch.last_visit_time
order by last_visit_time desc
'''

df = pd.read_sql(query, conn)
# csv without header and idx 
df.to_csv(clean_csv, sep=';', index=False, header=False)
conn.close()
# df

# cleanup 
import os
os.remove(browser_history_csv)
# os.remove(clean_db)
os.remove(export_csv)
