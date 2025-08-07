@echo off
echo ===============================================
echo Installation Systeme de Monitoring de Cameras
echo ===============================================
echo.

echo 1. Verification de Python...
python --version
if %errorlevel% neq 0 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    echo Installez Python depuis https://python.org
    pause
    exit /b 1
)

echo.
echo 2. Creation de l'environnement virtuel...
if exist "env" (
    echo Environnement virtuel existant trouve
) else (
    python -m venv env
    echo Environnement virtuel cree
)

echo.
echo 3. Activation de l'environnement virtuel...
call env\Scripts\activate

echo.
echo 4. Installation des dependances...
pip install flask flask-sqlalchemy werkzeug requests apscheduler sendgrid

echo.
echo 5. Configuration de la base de données SQLite locale...
if not exist "monitoring_local.db" (
    echo Creation de la base de donnees locale...
    python -c "
import sqlite3
conn = sqlite3.connect('monitoring_local.db')
conn.close()
print('Base de donnees SQLite creee: monitoring_local.db')
"
)

echo.
echo 6. Configuration des variables d'environnement...
set DATABASE_URL=sqlite:///monitoring_local.db
set SESSION_SECRET=dev-secret-key-change-in-production

echo.
echo 7. Initialisation de l'utilisateur admin...
python init_admin_user.py

echo.
echo ===============================================
echo Installation terminee avec succes!
echo ===============================================
echo.
echo Pour lancer l'application:
echo   1. cd %~dp0
echo   2. call env\Scripts\activate
echo   3. set DATABASE_URL=sqlite:///monitoring_local.db
echo   4. set SESSION_SECRET=dev-secret-key
echo   5. python main.py
echo.
echo Identifiants admin: admin / admin123
echo URL: http://localhost:5000
echo.
pause