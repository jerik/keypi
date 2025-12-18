# KeyPi - Jira Query Explorer

## Installation & Konfiguration

### 1. Plugin installieren
Das Plugin ist bereits in Keypirinha installiert unter:
```
%APPDATA%\Keypirinha\InstalledPackages\keypi_jqe\
```

### 2. Konfiguration erstellen

**WICHTIG**: Die Konfiguration muss im **User-Verzeichnis** liegen, nicht im Plugin-Verzeichnis!

#### Option A: Konfigurationsdatei erstellen (empfohlen)
Erstelle die Datei:
```
%APPDATA%\Keypirinha\User\keypi_jqe.ini
```

Mit folgendem Inhalt:
```ini
[main]
jira_url = https://foo.atlassian.net
atlassian_email = foo.bar@foo.com
atlassian_api_key = dein-api-token
```

#### Option B: Via Windows Explorer
1. Drücke `Win + R`
2. Gib ein: `%APPDATA%\Keypirinha\User`
3. Erstelle neue Datei: `keypi_jqe.ini`
4. Füge die Konfiguration ein (siehe oben)
5. Speichern

### 3. Keypirinha neu starten
- Drücke `Ctrl + Alt + R` in Keypirinha

### 4. Plugin testen
1. Öffne Keypirinha
2. Tippe: `jqe`
3. Drücke: `Tab`
4. Gib JQL ein: `assignee = currentUser()`
5. Drücke: `Enter`

## Hinweis zur Konfiguration

Keypirinha lädt Konfigurationsdateien in dieser Reihenfolge:
1. **Default**: `InstalledPackages\keypi_jqe\res\keypi_jqe.ini` (nur als Template)
2. **User**: `User\keypi_jqe.ini` (wird vom Plugin gelesen)

Die Datei im Plugin-Ordner (`res/keypi_jqe.ini`) ist nur ein Template. Deine tatsächliche Konfiguration muss im `User\` Ordner liegen.

## Troubleshooting

### "Configuration missing" Fehler
- Stelle sicher, dass die Datei `%APPDATA%\Keypirinha\User\keypi_jqe.ini` existiert
- Überprüfe, dass alle drei Werte gefüllt sind (jira_url, atlassian_email, atlassian_api_key)
- Starte Keypirinha neu (`Ctrl + Alt + R`)

### API Token erstellen
1. Gehe zu: https://id.atlassian.com/manage-profile/security/api-tokens
2. Klicke "Create API token"
3. Kopiere den Token in die Konfiguration
