@echo off
echo ====================================================
echo   INSTALLATION DU SYSTEME DE MONITORING CAMERAS
echo ====================================================
echo.

:: Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Python n'est pas installé ou pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)

echo ✓ Python détecté
python --version

:: Créer un environnement virtuel si il n'existe pas
if not exist "venv" (
    echo.
    echo Création de l'environnement virtuel...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERREUR: Impossible de créer l'environnement virtuel
        pause
        exit /b 1
    )
    echo ✓ Environnement virtuel créé
)

:: Activer l'environnement virtuel
echo.
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement virtuel
    pause
    exit /b 1
)

:: Installer les dépendances
echo.
echo Installation des dépendances...
pip install --upgrade pip
pip install -r requirements_windows.txt

if %errorlevel% neq 0 (
    echo ERREUR: Erreur lors de l'installation des dépendances
    pause
    exit /b 1
)

echo ✓ Toutes les dépendances installées

:: Configuration de l'environnement
echo.
echo Configuration de l'environnement...
if not exist ".env" (
    echo SESSION_SECRET=votre-clé-secrète-très-sécurisée-changez-la > .env
    echo SENDGRID_API_KEY= >> .env
    echo FROM_EMAIL=no-reply@votre-domaine.com >> .env
    echo DATABASE_URL=sqlite:///monitoring_local.db >> .env
    echo ✓ Fichier .env créé
)

:: Créer la base de données et l'utilisateur admin
echo.
echo Initialisation de la base de données...
python init_admin_user.py
if %errorlevel% neq 0 (
    echo ATTENTION: Erreur lors de l'initialisation de l'admin
)

echo.
echo ====================================================
echo   INSTALLATION TERMINÉE AVEC SUCCÈS !
echo ====================================================
echo.
echo Pour lancer le système:
echo   1. Double-cliquez sur "launch_windows.bat"
echo   2. Ou utilisez: python main.py
echo.
echo Connexion admin par défaut:
echo   - Utilisateur: admin
echo   - Mot de passe: admin123
echo   - URL: http://localhost:5000
echo.
echo IMPORTANT: Changez le mot de passe admin après la première connexion !
echo.
pause