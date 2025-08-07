#!/usr/bin/env python3
"""
Script d'initialisation pour créer l'utilisateur administrateur par défaut
"""
import sys
from app import app, db
from models import User

def create_admin_user():
    """Créer l'utilisateur admin par défaut si il n'existe pas"""
    with app.app_context():
        try:
            # Vérifier si un admin existe déjà
            admin_user = User.query.filter_by(nom_utilisateur='admin').first()
            
            if admin_user:
                print("✅ Utilisateur admin existant trouvé")
                print(f"   Nom d'utilisateur: {admin_user.nom_utilisateur}")
                print(f"   Email: {admin_user.email}")
                print(f"   Rôle: {admin_user.role}")
                print(f"   Statut: {admin_user.statut}")
                return
            
            # Créer l'utilisateur admin
            admin = User(
                nom_utilisateur='admin',
                email='admin@camerasystem.local',
                nom_complet='Administrateur Système',
                role='admin',
                statut='approuve'
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Utilisateur administrateur créé avec succès !")
            print("   Nom d'utilisateur: admin")
            print("   Mot de passe: admin123")
            print("   Email: admin@camerasystem.local")
            print("   Rôle: admin")
            print()
            print("⚠️  IMPORTANT: Changez le mot de passe par défaut après la première connexion !")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'utilisateur admin: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    create_admin_user()