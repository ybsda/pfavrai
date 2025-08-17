@echo off
title Installation Complète - Système de Monitoring Caméras
echo ====================================================
echo    INSTALLATION COMPLETE MONITORING CAMERAS
echo ====================================================
echo.
echo Ce script va installer TOUT ce qui est nécessaire :
echo - Python 3.11
echo - Git
echo - Dépendances Python
echo - Configuration de la base de données
echo - Lancement de l'application
echo.
pause

:: Vérifier les privilèges administrateur
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERREUR: Ce script doit être exécuté en tant qu'administrateur !
    echo Clic droit sur le fichier et "Exécuter en tant qu'administrateur"
    pause
    exit /b 1
)

:: Créer le dossier de travail
set INSTALL_DIR=%USERPROFILE%\MonitoringCameras
echo Création du dossier d'installation : %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

:: 1. INSTALLATION DE PYTHON 3.11
echo.
echo ====================================================
echo   ÉTAPE 1/6 : Installation de Python 3.11
echo ====================================================
echo.

:: Vérifier si Python est déjà installé
python --version >nul 2>&1
if %errorLevel% EQU 0 (
    echo Python est déjà installé :
    python --version
) else (
    echo Téléchargement de Python 3.11...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-installer.exe'"
    
    echo Installation de Python 3.11...
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: Attendre la fin de l'installation
    timeout /t 30 /nobreak > nul
    
    :: Vérifier l'installation
    python --version >nul 2>&1
    if %errorLevel% NEQ 0 (
        echo ERREUR: L'installation de Python a échoué !
        pause
        exit /b 1
    )
    
    echo ✓ Python installé avec succès
    del python-installer.exe
)

:: 2. INSTALLATION DE GIT
echo.
echo ====================================================
echo   ÉTAPE 2/6 : Installation de Git
echo ====================================================
echo.

git --version >nul 2>&1
if %errorLevel% EQU 0 (
    echo Git est déjà installé :
    git --version
) else (
    echo Téléchargement de Git...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-scm/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe' -OutFile 'git-installer.exe'"
    
    echo Installation de Git...
    git-installer.exe /VERYSILENT /NORESTART
    
    :: Attendre la fin de l'installation
    timeout /t 20 /nobreak > nul
    
    echo ✓ Git installé avec succès
    del git-installer.exe
    
    :: Ajouter Git au PATH
    set PATH=%PATH%;C:\Program Files\Git\bin
)

:: 3. TÉLÉCHARGEMENT DU CODE SOURCE
echo.
echo ====================================================
echo   ÉTAPE 3/6 : Téléchargement du code source
echo ====================================================
echo.

if exist "camera-monitoring" (
    echo Mise à jour du code existant...
    cd camera-monitoring
    git pull
    cd ..
) else (
    echo Clonage du repository...
    echo ATTENTION: Remplacez cette URL par votre repository GitHub !
    echo git clone https://github.com/VOTRE-USERNAME/camera-monitoring.git
    echo.
    echo Pour l'instant, nous allons créer une structure locale...
    mkdir camera-monitoring
    cd camera-monitoring
    
    :: Copier les fichiers depuis le répertoire courant si ils existent
    if exist "..\*.py" copy "..\*.py" .
    if exist "..\templates" xcopy "..\templates" templates\ /E /I /Y
    if exist "..\static" xcopy "..\static" static\ /E /I /Y
    if exist "..\requirements.txt" copy "..\requirements.txt" .
    
    cd ..
)

cd camera-monitoring

:: 4. CRÉATION DE L'ENVIRONNEMENT VIRTUEL
echo.
echo ====================================================
echo   ÉTAPE 4/6 : Création de l'environnement virtuel
echo ====================================================
echo.

if exist "venv" (
    echo Environnement virtuel existant détecté
) else (
    echo Création de l'environnement virtuel Python...
    python -m venv venv
    if %errorLevel% NEQ 0 (
        echo ERREUR: Impossible de créer l'environnement virtuel !
        pause
        exit /b 1
    )
    echo ✓ Environnement virtuel créé
)

:: Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

:: 5. INSTALLATION DES DÉPENDANCES
echo.
echo ====================================================
echo   ÉTAPE 5/6 : Installation des dépendances
echo ====================================================
echo.

:: Créer requirements.txt si il n'existe pas
if not exist "requirements.txt" (
    echo Création du fichier requirements.txt...
    (
        echo Flask==2.3.3
        echo Flask-Login==0.6.3
        echo Flask-SQLAlchemy==3.0.5
        echo Werkzeug==2.3.7
        echo APScheduler==3.10.4
        echo requests==2.31.0
        echo python-dotenv==1.0.0
    ) > requirements.txt
)

echo Installation des dépendances Python...
pip install --upgrade pip
pip install -r requirements.txt

if %errorLevel% NEQ 0 (
    echo ERREUR: Installation des dépendances échouée !
    pause
    exit /b 1
)

echo ✓ Toutes les dépendances sont installées

:: 6. CONFIGURATION ET LANCEMENT
echo.
echo ====================================================
echo   ÉTAPE 6/6 : Configuration et lancement
echo ====================================================
echo.

:: Créer le fichier .env
if not exist ".env" (
    echo Création du fichier de configuration...
    (
        echo SESSION_SECRET=camera-monitoring-secret-key-2024
        echo DATABASE_URL=sqlite:///monitoring_local.db
        echo FLASK_ENV=development
        echo FLASK_DEBUG=1
    ) > .env
    echo ✓ Fichier de configuration créé
)

:: Créer un script de lancement simple
echo Création du script de lancement...
(
    echo @echo off
    echo cd /d "%INSTALL_DIR%\camera-monitoring"
    echo call venv\Scripts\activate.bat
    echo echo Lancement de l'application de monitoring...
    echo python app.py
    echo pause
) > lancer_monitoring.bat

echo.
echo ====================================================
echo   INSTALLATION TERMINÉE AVEC SUCCÈS !
echo ====================================================
echo.
echo L'application est installée dans : %INSTALL_DIR%\camera-monitoring
echo.
echo Pour lancer l'application :
echo 1. Double-cliquez sur "lancer_monitoring.bat"
echo 2. Ou lancez manuellement depuis le dossier
echo.
echo L'application sera accessible sur : http://localhost:5000
echo.
echo Utilisateur admin par défaut :
echo - Nom d'utilisateur : admin
echo - Mot de passe : admin
echo.

choice /C YN /M "Voulez-vous lancer l'application maintenant"
if errorlevel 2 goto end
if errorlevel 1 goto launch

:launch
echo.
echo Lancement de l'application...
call lancer_monitoring.bat

:end
echo.
echo Installation terminée !
pause