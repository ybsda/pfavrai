@echo off
title Systeme de Monitoring de Cameras
color 0A

echo ===============================================
echo 🎯 SYSTEME DE MONITORING DE CAMERAS
echo ===============================================
echo.

echo ⚡ Demarrage rapide...
set DATABASE_URL=sqlite:///monitoring_local.db
set SESSION_SECRET=dev-secret-key-change-in-production

echo 📊 Configuration:
echo    Base de donnees: SQLite local
echo    Port: 5000
echo    Mode: Developpement
echo.

echo 🔑 Identifiants admin:
echo    Utilisateur: admin
echo    Mot de passe: admin123
echo.

echo 🚀 Lancement du serveur...
python main_windows.py

pause