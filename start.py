#!/usr/bin/env python3
"""
Script de démarrage pour le système de monitoring de caméras
Usage: python start.py
"""
import os
import sys
import subprocess
from app import app

def main():
    """Démarrer l'application de monitoring de caméras"""
    print("🎯 Système de Monitoring de Caméras de Sécurité")
    print("=" * 50)
    print()
    
    # Vérifications de base
    print("🔍 Vérification de l'environnement...")
    
    # Vérifier la base de données
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"✅ Base de données configurée: PostgreSQL")
    else:
        print("❌ DATABASE_URL non configurée")
        sys.exit(1)
    
    # Vérifier SendGrid (optionnel)
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    if sendgrid_key:
        print("✅ SendGrid configuré - Emails d'alertes activés")
    else:
        print("⚠️  SendGrid non configuré - Emails d'alertes désactivés")
    
    print()
    print("🚀 Démarrage du serveur...")
    print("   URL: http://localhost:5000")
    print("   Admin: admin / admin123")
    print("   Arrêter avec Ctrl+C")
    print()
    
    try:
        # Démarrer Flask en mode développement
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Arrêt du serveur demandé")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()