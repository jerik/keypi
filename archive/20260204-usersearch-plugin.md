# Neues Keypirinha Plugin: Nutzersuche

Über die Confluence API oder Jira API will ich nach Nutzer suchen. Im Plugin werden dann die Nutzer als Einträge aufgelistet die mit dem pattern gefunden werden. 
Wenn ich einen Eintrag ausgewählt und [Enter] drücke soll die Standard Action ausgeführt werden. 

Das Plugin soll mit us aufgerufen werden kann jedoch umkonfiguriert werden. In der Configuration wird der API_KEY etc hinterlegt, als auch die baseurl für jira oder confluence

Es soll 2 Actions geben: 
1. URL zum Benutzer aufrufen. Die URL sollte aus der Ergebnisliste kommen 
2. Teams Chat aufrufen (Standard action). Dafür wird die E-Mail-Adresse des Nutzer genutzt.

Bevor du mit der implementierung anfängst, erstelle einen Plan in dieser Datei und dokumentieren diesen. Wenn der Plan für mich passt gebe ich dir das OK für die Umsetzung. 

Lass uns zu beginn einen technischen durchstich machen mit welchem verfahren die usersuche funktioniert. 

## Python Codeauszug mit dem ich den Teams Chat vie e-mail-adresse starten kann. 

    def _call_teams(self, user_email): 
        command = f'cmd /K start sip:{user_email}'
        DETACHED_PROCESS = 0x00000008
        subprocess.call(command, creationflags=DETACHED_PROCESS)

## Entwicklungshinweise
Orientiere dich an den Plugins keypi_jqe und keypi_cqe, als auch an den KEYPIRINHA-LEARNINGS.md

## Bisher recherchierte Informationen 
-*-*-*- Auszug Recherche Start
Gute Frage – **„alle Nutzer / Nutzer suchen“ ist in Atlassian Cloud leider je nach Produkt und API unterschiedlich gelöst**. Ich trenne das sauber nach **Jira Cloud**, **Confluence Cloud** 

***

## 1️⃣ Jira Cloud – Nutzer programmatisch auflisten / suchen ✅

### ✅ Offizielle REST‑APIs (empfohlen)

#### 🔹 Alle Nutzer (paginiert)

```http
GET /rest/api/3/users
```

oder (häufiger genutzt):

```http
GET /rest/api/3/users/search
```

*   Gibt **alle bekannten Nutzer der Site** zurück (aktive + ggf. inaktive)
*   **Pagination zwingend notwendig**
*   Kein `total`‑Feld → du iterierst, bis weniger als `maxResults` zurückkommen [\[community....assian.com\]](https://community.atlassian.com/forums/Jira-questions/Trying-to-get-list-of-all-users-through-rest/qaq-p/2927323)

**Beispiel (Pagination‑Logik):**

```http
GET /rest/api/3/users/search?startAt=0&maxResults=1000
GET /rest/api/3/users/search?startAt=1000&maxResults=1000
```

➡️ Abbruch, wenn `< maxResults` Nutzer geliefert werden [\[community....assian.com\]](https://community.atlassian.com/forums/Jira-questions/Trying-to-get-list-of-all-users-through-rest/qaq-p/2927323)

***

### 🔹 Nutzer gezielt suchen

```http
GET /rest/api/3/user/search?query=Max
```

Sucht in:

*   Display Name
*   E‑Mail (abhängig von Privacy)
*   Account‑ID

📌 **Limit:** Die User‑Search‑APIs liefern **max. 1000 Nutzer**, danach musst du selbst filtern oder Organisation‑APIs nutzen [\[developer....assian.com\]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-user-search/)

***

### 🔹 Produktzugriff / Rollen prüfen (Jira)

```http
GET /rest/api/3/user?accountId=XXX&expand=applicationRoles
```

→ Damit erkennst du:

*   Hat der Nutzer Jira Software?
*   Jira Service Management?
*   Ist er billable?

✅ **Das gibt es NUR in Jira**, nicht in Confluence [\[developer....assian.com\]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-users/)

***

## 2️⃣ Confluence Cloud – Nutzer auflisten ⚠️ eingeschränkt

### ❌ **Wichtig**

*   **CQL (`/search?cql=type=user`) ist für User‑Suchen DEPRECATED**
*   Es gibt **keine API**, die zuverlässig *alle Confluence‑Nutzer mit Produktzugriff* zurückliefert [\[developer....assian.com\]](https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/)

***

### ✅ Was geht in Confluence Cloud?

#### 🔹 Nutzer **suchen**, nicht vollständig listen

```http
GET /wiki/rest/api/search/user?query=Max
```

*   Für Picker / Autocomplete gedacht
*   **Nicht vollständig**
*   Keine Garantie auf „alle Nutzer“

***

#### 🔹 Nutzer über Gruppen ableiten (Workaround)

```http
GET /wiki/rest/api/group
GET /wiki/rest/api/group/member?groupName=confluence-users
```

⚠️ Nachteile:

*   Gruppenname **nicht standardisiert**
*   Kein sicheres Signal für **billable access**
*   Atlassian selbst empfiehlt das **nicht** mehr [\[community....assian.com\]](https://community.developer.atlassian.com/t/is-there-a-confluence-cloud-rest-api-equivalent-to-jira-s-user-applicationroles-apis/98838)

***

-*-*-*- Auszug Recherche Ende


## Entwicklung
- [] Beachte die Git und Branch richtlinien
- [] Das Feature soll gut getestet sein
- [] Commite regelmässig
- [] Aktualisieren deinen Fortschritt
- [] Aktualisiere am Ende die dokumentation, README.md, documentation.md, KEYPIRINHA-LEARNING.md
- [] Nutze eine Versionnummer für das neue Plugin

## Fortschritt

