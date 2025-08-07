#!/usr/bin/env python3
"""
Simulateur de caméra/DVR - Envoie des pings périodiques vers le serveur de monitoring
"""
import requests
import time
import json
import random
from datetime import datetime

class SimulateurCamera:
    def __init__(self, serveur_monitoring, ma_ip, equipement_id, nom_equipement="Camera Simulée"):
        """
        Initialise le simulateur de caméra
        
        Args:
            serveur_monitoring: URL du serveur (ex: http://192.168.1.10:5000)
            ma_ip: IP de cette machine qui simule la caméra (ex: 192.168.1.100)
            equipement_id: ID de l'équipement dans la base du serveur
            nom_equipement: Nom pour l'affichage
        """
        self.serveur_url = f"{serveur_monitoring}/api/ping"
        self.ma_ip = ma_ip
        self.equipement_id = equipement_id
        self.nom = nom_equipement
        self.actif = True
        
        print(f"🔧 Simulateur initialisé:")
        print(f"   Nom: {self.nom}")
        print(f"   IP simulée: {self.ma_ip}")
        print(f"   Serveur: {serveur_monitoring}")
        print(f"   Équipement ID: {self.equipement_id}")
    
    def envoyer_ping(self):
        """Envoie un ping vers le serveur de monitoring"""
        try:
            # Temps de réponse simulé (comme une vraie caméra)
            response_time = round(random.uniform(20.0, 80.0), 1)
            
            # Données à envoyer (format attendu par votre API)
            data = {
                "ip": self.ma_ip,
                "equipement_id": self.equipement_id,
                "response_time": response_time,
                "message": f"Ping depuis {self.nom} - Simulation PC"
            }
            
            print(f"📡 {datetime.now().strftime('%H:%M:%S')} - Envoi ping...")
            
            # Envoyer la requête POST
            response = requests.post(
                self.serveur_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Succès ({response_time}ms) - Statut: {result.get('equipement', {}).get('statut', 'Inconnu')}")
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Impossible de contacter le serveur {self.serveur_url}")
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout - serveur trop lent")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    def demarrer_simulation(self, intervalle_secondes=60):
        """
        Démarre la simulation en boucle infinie
        
        Args:
            intervalle_secondes: Délai entre chaque ping (défaut: 60s comme une vraie caméra)
        """
        print(f"\n🚀 Démarrage de la simulation (ping toutes les {intervalle_secondes}s)")
        print("   Appuyez sur Ctrl+C pour arrêter")
        print("-" * 60)
        
        try:
            # Premier ping immédiat
            self.envoyer_ping()
            
            # Boucle principale
            while self.actif:
                time.sleep(intervalle_secondes)
                self.envoyer_ping()
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Simulation arrêtée par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur fatale: {e}")

def main():
    """Interface de configuration"""
    print("🎭 Simulateur de Caméra/DVR pour Monitoring")
    print("=" * 50)
    
    # Configuration par défaut
    serveur_defaut = "http://localhost:5000"
    ip_defaut = "192.168.1.100"
    id_defaut = 1
    
    print("\n📋 Configuration:")
    serveur = input(f"URL du serveur monitoring [{serveur_defaut}]: ").strip() or serveur_defaut
    ip_camera = input(f"IP de cette machine (caméra simulée) [{ip_defaut}]: ").strip() or ip_defaut
    
    try:
        equipement_id = int(input(f"ID de l'équipement [{id_defaut}]: ").strip() or id_defaut)
    except ValueError:
        equipement_id = id_defaut
    
    nom = input("Nom de la caméra [Camera Test]: ").strip() or "Camera Test"
    
    try:
        intervalle = int(input("Intervalle entre pings (secondes) [60]: ").strip() or 60)
    except ValueError:
        intervalle = 60
    
    # Test de connexion initial
    print(f"\n🔍 Test de connexion vers {serveur}...")
    try:
        response = requests.get(f"{serveur.rstrip('/api/ping')}", timeout=5)
        print("   ✅ Serveur accessible")
    except Exception as e:
        print(f"   ⚠️ Attention: {e}")
        continuer = input("Continuer quand même ? (o/N): ").strip().lower()
        if continuer not in ['o', 'oui', 'y', 'yes']:
            return
    
    # Créer et démarrer le simulateur
    simulateur = SimulateurCamera(serveur, ip_camera, equipement_id, nom)
    simulateur.demarrer_simulation(intervalle)

if __name__ == "__main__":
    main()
