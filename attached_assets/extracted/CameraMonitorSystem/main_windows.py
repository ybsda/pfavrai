#!/usr/bin/env python3
"""
Point d'entrée principal pour Windows - Système de monitoring de caméras
Utilise SQLite par défaut au lieu de PostgreSQL
"""
import os
import sys
import logging

# Configuration pour Windows
def setup_windows_environment():
    """Configure l'environnement pour Windows avec SQLite"""
    print("🪟 Configuration Windows détectée")
    
    # Variables d'environnement par défaut
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:///monitoring_local.db'
        print("📁 Base de données: SQLite local (monitoring_local.db)")
    
    if not os.environ.get('SESSION_SECRET'):
        os.environ['SESSION_SECRET'] = 'dev-secret-key-change-in-production'
        print("🔑 Clé de session: Mode développement")
    
    print()

# Configuration initiale
setup_windows_environment()

# Import de l'application après configuration
try:
    from app import app, db
    import routes  # Importer les routes
    import models  # Importer les modèles
    
    # Initialiser la base de données
    with app.app_context():
        db.create_all()
        print("✅ Base de données initialisée")
    
    print("🚀 Démarrage du serveur...")
    print("   URL: http://localhost:5000")
    print("   Admin: admin / admin123")
    print("   Arrêt: Ctrl+C")
    print()
    
    # Démarrer le serveur Flask
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000, debug=True)
        
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("🔧 Solutions possibles:")
    print("   1. Installez Flask: pip install flask flask-sqlalchemy")
    print("   2. Activez l'environnement virtuel: env\\Scripts\\activate")
    print("   3. Vérifiez que tous les fichiers sont présents")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)