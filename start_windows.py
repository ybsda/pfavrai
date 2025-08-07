#!/usr/bin/env python3
"""
Script de démarrage simplifié pour Windows
Lance le système sans configuration complexe
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """Vérifier si Python est disponible"""
    try:
        result = subprocess.run([sys.executable, '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✓ Python détecté: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("❌ Python non trouvé dans le PATH")
        return False

def install_requirements():
    """Installer les dépendances si nécessaires"""
    requirements = [
        'flask', 'flask-sqlalchemy', 'flask-login', 'werkzeug',
        'sendgrid', 'apscheduler', 'requests'
    ]
    
    print("Vérification des dépendances...")
    missing = []
    
    for package in requirements:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Installation des packages manquants: {', '.join(missing)}")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing, 
                         check=True)
            print("✓ Dépendances installées")
        except subprocess.CalledProcessError:
            print("❌ Erreur lors de l'installation des dépendances")
            return False
    else:
        print("✓ Toutes les dépendances sont présentes")
    
    return True

def setup_environment():
    """Configurer l'environnement"""
    # Variables d'environnement par défaut
    os.environ.setdefault('SESSION_SECRET', 'dev-secret-key-windows')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///monitoring_local.db')
    os.environ.setdefault('FLASK_ENV', 'development')
    
    print("✓ Variables d'environnement configurées")

def main():
    """Point d'entrée principal"""
    print("=" * 50)
    print("  SYSTÈME DE MONITORING CAMÉRAS - Windows")
    print("=" * 50)
    print()
    
    # Vérifications préliminaires
    if not check_python():
        input("Appuyez sur Entrée pour quitter...")
        sys.exit(1)
    
    if not install_requirements():
        input("Appuyez sur Entrée pour quitter...")
        sys.exit(1)
    
    setup_environment()
    
    try:
        # Importer et lancer l'application
        print("\nDémarrage du serveur...")
        print("🌐 URL: http://localhost:5000")
        print("👤 Admin: admin / admin123")
        print("\nAppuyez sur Ctrl+C pour arrêter")
        print("=" * 50)
        
        from app import app
        app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
        
    except KeyboardInterrupt:
        print("\n\n✅ Serveur arrêté")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        input("Appuyez sur Entrée pour quitter...")

if __name__ == '__main__':
    main()