@echo off
echo Installation du Systeme de Monitoring des Cameras - Windows
echo =========================================================

echo Installation des dependances Python (versions compatibles)...
pip uninstall Flask Flask-SQLAlchemy Werkzeug SQLAlchemy -y
pip install SQLAlchemy==1.4.53
pip install Flask==2.3.3
pip install Flask-SQLAlchemy==3.0.5
pip install Werkzeug==2.3.7
pip install APScheduler==3.10.4
pip install email-validator==2.1.0

echo.
echo Configuration des variables d'environnement...
set DATABASE_URL=sqlite:///monitoring.db
set SESSION_SECRET=ma-cle-secrete-windows-123456

echo.
echo Suppression de l'ancienne base (pour eviter les conflits)...
if exist monitoring.db del monitoring.db

echo.
echo Demarrage de l'application...
echo L'application va se lancer sur http://localhost:5000
echo.
python main.py

pause