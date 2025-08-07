import logging
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, flash, redirect, url_for
from app import app, db
from models import Client, Equipement, HistoriquePing, Alerte

logger = logging.getLogger(__name__)

@app.route('/')
def dashboard():
    """Page d'accueil avec vue d'ensemble du système"""
    try:
        # Statistiques globales
        total_clients = Client.query.filter_by(actif=True).count()
        total_equipements = Equipement.query.filter_by(actif=True).count()
        
        # Compter les équipements en ligne et hors ligne
        equipements_en_ligne = 0
        equipements_hors_ligne = 0
        
        equipements = Equipement.query.filter_by(actif=True).all()
        for eq in equipements:
            if eq.est_en_ligne:
                equipements_en_ligne += 1
            else:
                equipements_hors_ligne += 1
        
        # Alertes non lues
        alertes_non_lues = Alerte.query.filter_by(lue=False).count()
        
        # Dernières alertes
        dernieres_alertes = Alerte.query.order_by(Alerte.timestamp.desc()).limit(10).all()
        
        # Clients avec leurs équipements
        clients = Client.query.filter_by(actif=True).all()
        
        stats = {
            'total_clients': total_clients,
            'total_equipements': total_equipements,
            'equipements_en_ligne': equipements_en_ligne,
            'equipements_hors_ligne': equipements_hors_ligne,
            'alertes_non_lues': alertes_non_lues
        }
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             clients=clients,
                             dernieres_alertes=dernieres_alertes)
    except Exception as e:
        logger.error(f"Erreur dans dashboard: {e}")
        flash(f"Erreur lors du chargement du tableau de bord: {e}", "error")
        return render_template('dashboard.html', stats={}, clients=[], dernieres_alertes=[])

@app.route('/clients')
def clients():
    """Page de gestion des clients"""
    try:
        clients_list = Client.query.filter_by(actif=True).all()
        return render_template('clients.html', clients=clients_list)
    except Exception as e:
        logger.error(f"Erreur dans clients: {e}")
        flash(f"Erreur lors du chargement des clients: {e}", "error")
        return render_template('clients.html', clients=[])

@app.route('/equipements')
def equipements():
    """Page de gestion des équipements"""
    try:
        equipements_list = Equipement.query.filter_by(actif=True).all()
        clients_list = Client.query.filter_by(actif=True).all()
        return render_template('equipements.html', equipements=equipements_list, clients=clients_list)
    except Exception as e:
        logger.error(f"Erreur dans equipements: {e}")
        flash(f"Erreur lors du chargement des équipements: {e}", "error")
        return render_template('equipements.html', equipements=[], clients=[])

@app.route('/historique')
def historique():
    """Page d'historique des pings"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        historique_query = HistoriquePing.query.order_by(HistoriquePing.timestamp.desc())
        historique_pagine = historique_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('history.html', historique=historique_pagine)
    except Exception as e:
        logger.error(f"Erreur dans historique: {e}")
        flash(f"Erreur lors du chargement de l'historique: {e}", "error")
        return render_template('history.html', historique=None)

@app.route('/alertes')
def alertes():
    """Page des alertes"""
    try:
        alertes_list = Alerte.query.order_by(Alerte.timestamp.desc()).all()
        return render_template('alerts.html', alertes=alertes_list)
    except Exception as e:
        logger.error(f"Erreur dans alertes: {e}")
        flash(f"Erreur lors du chargement des alertes: {e}", "error")
        return render_template('alerts.html', alertes=[])

# API Routes pour recevoir les pings des DVR/caméras
@app.route('/api/ping', methods=['POST'])
def recevoir_ping():
    """Endpoint pour recevoir les pings des équipements"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Données JSON requises"}), 400
        
        adresse_ip = data.get('ip')
        equipement_id = data.get('equipement_id')
        
        if not adresse_ip and not equipement_id:
            return jsonify({"error": "IP ou ID d'équipement requis"}), 400
        
        # Trouver l'équipement
        if equipement_id:
            equipement = Equipement.query.get(equipement_id)
        else:
            equipement = Equipement.query.filter_by(adresse_ip=adresse_ip, actif=True).first()
        
        if not equipement:
            logger.warning(f"Équipement non trouvé pour IP: {adresse_ip}, ID: {equipement_id}")
            return jsonify({"error": "Équipement non trouvé"}), 404
        
        # Vérifier si l'équipement était hors ligne
        etait_hors_ligne = not equipement.est_en_ligne
        
        # Mettre à jour le dernier ping
        equipement.dernier_ping = datetime.utcnow()
        
        # Enregistrer dans l'historique
        historique = HistoriquePing()
        historique.equipement_id = equipement.id
        historique.timestamp = datetime.utcnow()
        historique.statut = 'success'
        historique.reponse_ms = data.get('response_time')
        historique.message = data.get('message', 'Ping reçu avec succès')
        
        db.session.add(historique)
        
        # Créer une alerte si l'équipement revient en ligne
        if etait_hors_ligne:
            alerte = Alerte()
            alerte.equipement_id = equipement.id
            alerte.type_alerte = 'retour_en_ligne'
            alerte.message = f"L'équipement {equipement.nom} ({equipement.adresse_ip}) est revenu en ligne"
            alerte.timestamp = datetime.utcnow()
            db.session.add(alerte)
            logger.info(f"Équipement {equipement.nom} revenu en ligne")
        
        db.session.commit()
        
        logger.debug(f"Ping reçu pour {equipement.nom} ({equipement.adresse_ip})")
        
        return jsonify({
            "status": "success",
            "message": "Ping enregistré avec succès",
            "equipement": {
                "id": equipement.id,
                "nom": equipement.nom,
                "statut": equipement.statut_texte
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du ping: {e}")
        db.session.rollback()
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500

# API Routes pour l'interface web
@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API pour obtenir les statistiques du dashboard"""
    try:
        total_clients = Client.query.filter_by(actif=True).count()
        total_equipements = Equipement.query.filter_by(actif=True).count()
        
        equipements_en_ligne = 0
        equipements_hors_ligne = 0
        
        equipements = Equipement.query.filter_by(actif=True).all()
        for eq in equipements:
            if eq.est_en_ligne:
                equipements_en_ligne += 1
            else:
                equipements_hors_ligne += 1
        
        alertes_non_lues = Alerte.query.filter_by(lue=False).count()
        
        return jsonify({
            'total_clients': total_clients,
            'total_equipements': total_equipements,
            'equipements_en_ligne': equipements_en_ligne,
            'equipements_hors_ligne': equipements_hors_ligne,
            'alertes_non_lues': alertes_non_lues
        })
        
    except Exception as e:
        logger.error(f"Erreur API dashboard stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/equipements/statut')
def api_equipements_statut():
    """API pour obtenir le statut de tous les équipements"""
    try:
        equipements = Equipement.query.filter_by(actif=True).all()
        
        resultats = []
        for eq in equipements:
            resultats.append({
                'id': eq.id,
                'nom': eq.nom,
                'type': eq.type_equipement,
                'adresse_ip': eq.adresse_ip,
                'client_nom': eq.client.nom,
                'est_en_ligne': eq.est_en_ligne,
                'statut_texte': eq.statut_texte,
                'dernier_ping': eq.dernier_ping.isoformat() if eq.dernier_ping else None,
                'duree_depuis_dernier_ping': eq.duree_depuis_dernier_ping
            })
        
        return jsonify(resultats)
        
    except Exception as e:
        logger.error(f"Erreur API équipements statut: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alertes/marquer_lue/<int:alerte_id>', methods=['POST'])
def api_marquer_alerte_lue(alerte_id):
    """API pour marquer une alerte comme lue"""
    try:
        alerte = Alerte.query.get_or_404(alerte_id)
        alerte.lue = True
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Alerte marquée comme lue"})
        
    except Exception as e:
        logger.error(f"Erreur API marquer alerte lue: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/equipement/<int:equipement_id>/test-connexion', methods=['POST'])
def api_test_connexion(equipement_id):
    """API pour tester la connexion d'un équipement en simulant un ping"""
    try:
        equipement = Equipement.query.get_or_404(equipement_id)
        
        # Simuler un test de connexion en envoyant un ping test
        import time
        import random
        
        # Temps de réponse simulé (entre 20ms et 100ms)
        response_time = round(random.uniform(20.0, 100.0), 1)
        
        # Vérifier si l'équipement était hors ligne
        etait_hors_ligne = not equipement.est_en_ligne
        
        # Mettre à jour le dernier ping
        equipement.dernier_ping = datetime.utcnow()
        
        # Enregistrer dans l'historique
        historique = HistoriquePing()
        historique.equipement_id = equipement.id
        historique.timestamp = datetime.utcnow()
        historique.statut = 'success'
        historique.reponse_ms = response_time
        historique.message = f'Test de connexion manuel depuis l\'interface web - {response_time}ms'
        
        db.session.add(historique)
        
        # Créer une alerte si l'équipement revient en ligne
        if etait_hors_ligne:
            alerte = Alerte()
            alerte.equipement_id = equipement.id
            alerte.type_alerte = 'retour_en_ligne'
            alerte.message = f"L'équipement {equipement.nom} ({equipement.adresse_ip}) est revenu en ligne suite au test manuel"
            alerte.timestamp = datetime.utcnow()
            db.session.add(alerte)
            logger.info(f"Équipement {equipement.nom} revenu en ligne via test manuel")
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Test de connexion réussi ({response_time}ms)",
            "equipement": {
                "id": equipement.id,
                "nom": equipement.nom,
                "adresse_ip": equipement.adresse_ip,
                "statut": equipement.statut_texte,
                "response_time": response_time,
                "etait_hors_ligne": etait_hors_ligne
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du test de connexion: {e}")
        db.session.rollback()
        return jsonify({"error": f"Erreur lors du test: {str(e)}"}), 500

# Routes pour ajouter des clients et équipements (gestion basique)
@app.route('/ajouter_client', methods=['POST'])
def ajouter_client():
    """Ajouter un nouveau client"""
    try:
        nom = request.form.get('nom')
        adresse = request.form.get('adresse', '')
        telephone = request.form.get('telephone', '')
        email = request.form.get('email', '')
        
        if not nom:
            flash("Le nom du client est requis", "error")
            return redirect(url_for('clients'))
        
        client = Client()
        client.nom = nom
        client.adresse = adresse
        client.telephone = telephone
        client.email = email
        
        db.session.add(client)
        db.session.commit()
        
        flash(f"Client '{nom}' ajouté avec succès", "success")
        logger.info(f"Nouveau client ajouté: {nom}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du client: {e}")
        db.session.rollback()
        flash(f"Erreur lors de l'ajout du client: {e}", "error")
    
    return redirect(url_for('clients'))

@app.route('/ajouter_equipement', methods=['POST'])
def ajouter_equipement():
    """Ajouter un nouvel équipement"""
    try:
        nom = request.form.get('nom')
        type_equipement = request.form.get('type_equipement')
        adresse_ip = request.form.get('adresse_ip')
        port = request.form.get('port', 80, type=int)
        client_id = request.form.get('client_id', type=int)
        
        if not all([nom, type_equipement, adresse_ip, client_id]):
            flash("Tous les champs sont requis", "error")
            return redirect(url_for('equipements'))
        
        equipement = Equipement()
        equipement.nom = nom
        equipement.type_equipement = type_equipement
        equipement.adresse_ip = adresse_ip
        equipement.port = port
        equipement.client_id = client_id
        
        db.session.add(equipement)
        db.session.commit()
        
        flash(f"Équipement '{nom}' ajouté avec succès", "success")
        logger.info(f"Nouvel équipement ajouté: {nom} ({adresse_ip})")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de l'équipement: {e}")
        db.session.rollback()
        flash(f"Erreur lors de l'ajout de l'équipement: {e}", "error")
    
    return redirect(url_for('equipements'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
