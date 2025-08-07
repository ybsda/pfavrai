@echo off
title Système de Monitoring Caméras
echo ====================================================
echo       SYSTEME DE MONITORING CAMERAS
echo ====================================================
echo.

:: Vérifier si l'environnement virtuel existe
if not exist "venv" (
    echo ERREUR: Environnement virtuel non trouvé !
    echo Veuillez d'abord exécuter install_windows.bat
    pause
    exit /b 1
)

:: Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

:: Charger les variables d'environnement depuis .env
if exist ".env" (
    echo Chargement de la configuration...
    for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
        set "%%A=%%B"
    )
)

:: Définir les variables par défaut si elles n'existent pas
if not defined SESSION_SECRET set SESSION_SECRET=dev-secret-key-change-in-production
if not defined DATABASE_URL set DATABASE_URL=sqlite:///monitoring_local.db

echo.
echo Configuration:
echo ✓ Variables d'environnement chargées
echo ✓ Base de données: %DATABASE_URL%
echo.

:: Lancer l'application
echo ====================================================
echo   DÉMARRAGE DU SERVEUR...
echo ====================================================
echo.
echo L'application sera accessible sur: http://localhost:5000
echo.
echo Utilisateur admin par défaut:
echo   - Nom d'utilisateur: admin
echo   - Mot de passe: admin123
echo.
echo Appuyez sur Ctrl+C pour arrêter le serveur
echo.
echo ====================================================

:: Lancer avec Python direct (plus simple pour Windows)
python main.py

:: Si erreur, afficher message et attendre
if %errorlevel% neq 0 (
    echo.
    echo ====================================================
    echo   ERREUR LORS DU DÉMARRAGE !
    echo ====================================================
    echo.
    echo Vérifications possibles:
    echo 1. Python est-il installé ? python --version
    echo 2. Les dépendances sont-elles installées ? pip list
    echo 3. Le port 5000 est-il libre ?
    echo.
    pause
)