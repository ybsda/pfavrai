#!/usr/bin/env python3
"""
Script pour tester l'API de ping du système de monitoring
"""
import requests
import json
import time
from datetime import datetime

def test_ping_equipement():
    """Teste l'envoi d'un ping vers l'API"""
    
    # URL de votre serveur (ajustez selon votre configuration)
    base_url = "http://localhost:5000"
    ping_url = f"{base_url}/api/ping"
    
    print("🔄 Test de l'API de ping")
    print("=" * 40)
    
    # Données de test pour votre équipement DVR
    ping_data = {
        "ip": "192.144.11.1",
        "equipement_id": 1,  # ID de votre DVR dans la base
        "response_time": 45.5,
        "message": "DVR en ligne - Test manuel"
    }
    
    print(f"📡 Envoi du ping vers: {ping_url}")
    print(f"📊 Données: {json.dumps(ping_data, indent=2)}")
    
    try:
        # Envoyer la requête POST
        response = requests.post(
            ping_url,
            json=ping_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📈 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCÈS! Ping enregistré")
            print(f"📄 Réponse: {json.dumps(result, indent=2)}")
            
            # Vérifier le statut via l'API
            print("\n🔍 Vérification du statut...")
            status_url = f"{base_url}/api/equipements/statut"
            status_response = requests.get(status_url)
            
            if status_response.status_code == 200:
                equipements = status_response.json()
                for eq in equipements:
                    if eq.get('id') == 1:
                        statut = "🟢 EN LIGNE" if eq.get('est_en_ligne') else "🔴 HORS LIGNE"
                        print(f"   Équipement {eq.get('nom')}: {statut}")
                        if eq.get('dernier_ping'):
                            print(f"   Dernier ping: {eq.get('dernier_ping')}")
            
        else:
            print(f"❌ ERREUR: {response.status_code}")
            print(f"📄 Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERREUR: Impossible de se connecter au serveur")
        print("   Vérifiez que l'application est démarrée sur localhost:5000")
    except requests.exceptions.Timeout:
        print("❌ ERREUR: Timeout de la requête")
    except Exception as e:
        print(f"❌ ERREUR inattendue: {e}")

def test_multiple_pings():
    """Teste plusieurs pings consécutifs"""
    print("\n🔄 Test de pings multiples")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    ping_url = f"{base_url}/api/ping"
    
    # Simuler plusieurs équipements
    equipements_test = [
        {"ip": "192.144.11.1", "equipement_id": 1, "response_time": 45.5, "message": "DVR Principal OK"},
        {"ip": "192.168.1.101", "equipement_id": 2, "response_time": 32.1, "message": "Caméra Entrée OK"},
        {"ip": "192.168.1.102", "equipement_id": 3, "response_time": 28.9, "message": "Caméra Parking OK"},
    ]
    
    for i, data in enumerate(equipements_test, 1):
        print(f"\n📡 Ping {i}/3: {data['ip']}")
        
        try:
            response = requests.post(ping_url, json=data, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ Succès ({data['response_time']}ms)")
            else:
                print(f"   ❌ Échec: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Pause entre les pings
        time.sleep(1)

def test_avec_curl():
    """Affiche les commandes curl équivalentes"""
    print("\n🖥️  Commandes curl équivalentes")
    print("=" * 40)
    
    curl_cmd = '''curl -X POST http://localhost:5000/api/ping \\
  -H "Content-Type: application/json" \\
  -d '{
    "ip": "192.144.11.1",
    "equipement_id": 1,
    "response_time": 45.5,
    "message": "Test curl"
  }' '''
    
    print("Pour tester manuellement avec curl:")
    print(curl_cmd)
    
    # Version PowerShell
    ps_cmd = '''Invoke-RestMethod -Uri "http://localhost:5000/api/ping" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"ip":"192.144.11.1","equipement_id":1,"response_time":45.5,"message":"Test PowerShell"}'
'''
    
    print("\nPour tester avec PowerShell:")
    print(ps_cmd)

if __name__ == "__main__":
    print("🔧 Test de l'API de monitoring des caméras")
    print("=" * 50)
    
    # Test simple
    test_ping_equipement()
    
    # Test multiple (optionnel)
    response = input("\n❓ Voulez-vous tester plusieurs pings ? (o/n): ")
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        test_multiple_pings()
    
    # Afficher les alternatives
    test_avec_curl()
    
    print("\n✅ Tests terminés!")
    print("📱 Rafraîchissez votre page web pour voir les changements")
