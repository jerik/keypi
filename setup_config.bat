@echo off
echo KeyPi - Jira Query Explorer - Konfiguration Setup
echo ===================================================
echo.

set USER_DIR=%APPDATA%\Keypirinha\User
set CONFIG_FILE=%USER_DIR%\keypi_jqe.ini

echo Erstelle Konfigurationsdatei in: %CONFIG_FILE%
echo.

REM Create User directory if it doesn't exist
if not exist "%USER_DIR%" (
    mkdir "%USER_DIR%"
)

REM Create config file
(
echo [main]
echo # Your Jira Cloud instance URL ^(e.g., https://your-domain.atlassian.net^)
echo # Do NOT include a trailing slash
echo jira_url =
echo.
echo # Your Atlassian account email address
echo atlassian_email =
echo.
echo # Your Atlassian API token
echo # Create one at: https://id.atlassian.com/manage-profile/security/api-tokens
echo atlassian_api_key =
echo.
echo.
echo # Future feature: JQL shortcuts ^(Phase 2^)
echo #[jql_shortcuts]
echo #me = assignee = currentUser^(^)
echo #open = status = "Open"
) > "%CONFIG_FILE%"

echo Konfigurationsdatei erstellt!
echo.
echo Naechste Schritte:
echo 1. Oeffne die Datei: %CONFIG_FILE%
echo 2. Fuege deine Jira-Credentials ein
echo 3. Speichern
echo 4. Keypirinha neu starten ^(Ctrl+Alt+R^)
echo.

REM Open the config file in default editor
start notepad "%CONFIG_FILE%"

pause
