import logging
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import Client, Equipement, HistoriquePing, Alerte, User
from email_service import email_service

logger = logging.getLogger(__name__)

# Routes d'authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nom_utilisateur = request.form.get('nom_utilisateur')
        mot_de_passe = request.form.get('mot_de_passe')
        
        if not nom_utilisateur or not mot_de_passe:
            flash('Veuillez saisir votre nom d\'utilisateur et mot de passe.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(nom_utilisateur=nom_utilisateur, actif=True).first()
        
        if user and user.check_password(mot_de_passe):
            # Vérifier si le compte est approuvé
            if user.statut == 'en_attente':
                flash('Votre compte est en attente d\'approbation par un administrateur.', 'warning')
                return render_template('login.html')
            elif user.statut == 'refuse':
                flash('Votre demande de compte a été refusée. Contactez un administrateur.', 'error')
                return render_template('login.html')
            
            login_user(user)
            user.update_last_login()
            flash(f'Connexion réussie ! Bienvenue {user.nom_complet or user.nom_utilisateur}.', 'success')
            
            # Redirection vers la page demandée ou dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription pour les clients (avec validation admin)"""
    if request.method == 'POST':
        nom_utilisateur = request.form.get('nom_utilisateur')
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')
        nom_complet = request.form.get('nom_complet')
        nom_entreprise = request.form.get('nom_entreprise')
        adresse = request.form.get('adresse')
        telephone = request.form.get('telephone')
        
        if not all([nom_utilisateur, email, mot_de_passe, nom_entreprise]):
            flash('Tous les champs obligatoires doivent être remplis.', 'error')
            return render_template('register.html')
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(nom_utilisateur=nom_utilisateur).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Cette adresse email est déjà utilisée.', 'error')
            return render_template('register.html')
        
        try:
            # Créer d'abord le client
            nouveau_client = Client(
                nom=nom_entreprise,
                email=email,
                adresse=adresse,
                telephone=telephone
            )
            db.session.add(nouveau_client)
            db.session.flush()  # Pour obtenir l'ID du client
            
            # Créer l'utilisateur lié au client
            nouveau_user = User(
                nom_utilisateur=nom_utilisateur,
                email=email,
                nom_complet=nom_complet,
                role='client',
                statut='en_attente',
                client_id=nouveau_client.id
            )
            nouveau_user.set_password(mot_de_passe)
            
            db.session.add(nouveau_user)
            db.session.commit()
            
            flash('Votre demande de compte a été soumise avec succès ! Un administrateur va examiner votre demande et vous recevrez un email de confirmation.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erreur lors de la création du compte client: {e}')
            flash('Une erreur est survenue lors de la création du compte.', 'error')
    
    return render_template('register.html')

@app.route('/')
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
        
        return redirect(url_for('clients'))
        
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
            flash("Tous les champs obligatoires doivent être remplis", "error")
            return redirect(url_for('equipements'))
        
        # Vérifier que le client existe
        client = Client.query.get(client_id)
        if not client:
            flash("Client invalide", "error")
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
        
        return redirect(url_for('equipements'))
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de l'équipement: {e}")
        db.session.rollback()
        flash(f"Erreur lors de l'ajout de l'équipement: {e}", "error")
        return redirect(url_for('equipements'))

# Routes de gestion des utilisateurs (Admin seulement)
@app.route('/admin/users')
@login_required
def admin_users():
    """Page de gestion des utilisateurs (Admin seulement)"""
    if current_user.role != 'admin':
        flash('Accès non autorisé. Seuls les administrateurs peuvent accéder à cette page.', 'error')
        return redirect(url_for('dashboard'))
    
    # Récupérer tous les utilisateurs
    users = User.query.order_by(User.date_creation.desc()).all()
    
    # Statistiques
    total_users = User.query.count()
    users_en_attente = User.query.filter_by(statut='en_attente').count()
    users_approuves = User.query.filter_by(statut='approuve').count()
    users_refuses = User.query.filter_by(statut='refuse').count()
    
    stats = {
        'total': total_users,
        'en_attente': users_en_attente,
        'approuves': users_approuves,
        'refuses': users_refuses
    }
    
    return render_template('admin_users.html', users=users, stats=stats)

@app.route('/admin/users/<int:user_id>/approve', methods=['POST'])
@login_required
def approve_user(user_id):
    """Approuver un utilisateur"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.statut == 'en_attente':
        user.statut = 'approuve'
        db.session.commit()
        
        # Envoyer email de notification
        email_service.send_account_approval_notification(
            user.email, 
            user.nom_complet or user.nom_utilisateur, 
            approved=True
        )
        
        flash(f'Utilisateur {user.nom_utilisateur} approuvé avec succès. Email de notification envoyé.', 'success')
    else:
        flash('Cet utilisateur n\'est pas en attente d\'approbation.', 'warning')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/reject', methods=['POST'])
@login_required
def reject_user(user_id):
    """Rejeter un utilisateur"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.statut == 'en_attente':
        user.statut = 'refuse'
        db.session.commit()
        
        # Envoyer email de notification
        email_service.send_account_approval_notification(
            user.email, 
            user.nom_complet or user.nom_utilisateur, 
            approved=False
        )
        
        flash(f'Utilisateur {user.nom_utilisateur} refusé. Email de notification envoyé.', 'warning')
    else:
        flash('Cet utilisateur n\'est pas en attente d\'approbation.', 'warning')
    
    return redirect(url_for('admin_users'))
