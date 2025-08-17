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
            nouveau_client = Client()
            nouveau_client.nom = nom_entreprise
            nouveau_client.email = email
            nouveau_client.adresse = adresse
            nouveau_client.telephone = telephone
            
            db.session.add(nouveau_client)
            db.session.flush()  # Pour obtenir l'ID du client
            
            # Créer l'utilisateur lié au client
            nouveau_user = User()
            nouveau_user.nom_utilisateur = nom_utilisateur
            nouveau_user.email = email
            nouveau_user.nom_complet = nom_complet
            nouveau_user.role = 'client'
            nouveau_user.statut = 'en_attente'
            nouveau_user.client_id = nouveau_client.id
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
        # Statistiques globales ou filtrées par client selon le rôle
        if current_user.role == 'admin':
            total_clients = Client.query.filter_by(actif=True).count()
            total_equipements = Equipement.query.filter_by(actif=True).count()
            equipements = Equipement.query.filter_by(actif=True).all()
            clients = Client.query.filter_by(actif=True).all()
        else:
            # Pour les clients, afficher seulement leurs données
            total_clients = 1 if current_user.client_id else 0
            total_equipements = Equipement.query.filter_by(client_id=current_user.client_id, actif=True).count()
            equipements = Equipement.query.filter_by(client_id=current_user.client_id, actif=True).all()
            clients = [current_user.client] if current_user.client else []
        
        # Compter les équipements en ligne et hors ligne
        equipements_en_ligne = 0
        equipements_hors_ligne = 0
        
        for eq in equipements:
            if eq.est_en_ligne:
                equipements_en_ligne += 1
            else:
                equipements_hors_ligne += 1
        
        # Alertes non lues (filtrées par client si nécessaire)
        if current_user.role == 'admin':
            alertes_non_lues = Alerte.query.filter_by(lue=False).count()
            dernieres_alertes = Alerte.query.order_by(Alerte.timestamp.desc()).limit(10).all()
        else:
            # Pour les clients, ne montrer que leurs alertes
            alertes_non_lues = db.session.query(Alerte).join(Equipement).filter(
                Equipement.client_id == current_user.client_id,
                Alerte.lue == False
            ).count()
            dernieres_alertes = db.session.query(Alerte).join(Equipement).filter(
                Equipement.client_id == current_user.client_id
            ).order_by(Alerte.timestamp.desc()).limit(10).all()
        
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
    """Page de gestion des clients (admin seulement)"""
    if current_user.role != 'admin':
        flash('Accès refusé : réservé aux administrateurs.', 'error')
        return redirect(url_for('dashboard'))
    
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
        if current_user.role == 'admin':
            equipements_list = Equipement.query.filter_by(actif=True).all()
            clients_list = Client.query.filter_by(actif=True).all()
        else:
            # Pour les clients, afficher seulement leurs équipements
            equipements_list = Equipement.query.filter_by(client_id=current_user.client_id, actif=True).all()
            clients_list = [current_user.client] if current_user.client else []
        
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
        
        if current_user.role == 'admin':
            historique_query = HistoriquePing.query.order_by(HistoriquePing.timestamp.desc())
        else:
            # Pour les clients, filtrer par leurs équipements
            historique_query = db.session.query(HistoriquePing).join(Equipement).filter(
                Equipement.client_id == current_user.client_id
            ).order_by(HistoriquePing.timestamp.desc())
        
        # Fallback pour SQLAlchemy avec pagination manuelle
        from sqlalchemy import func
        total = historique_query.count()
        historique_items = historique_query.offset((page - 1) * per_page).limit(per_page).all()
        
        class MockPagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
        
        historique_pagine = MockPagination(historique_items, page, per_page, total)
        
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
        if current_user.role == 'admin':
            alertes_list = Alerte.query.order_by(Alerte.timestamp.desc()).all()
        else:
            # Pour les clients, filtrer par leurs équipements
            alertes_list = db.session.query(Alerte).join(Equipement).filter(
                Equipement.client_id == current_user.client_id
            ).order_by(Alerte.timestamp.desc()).all()
        
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
            "message": "Ping reçu",
            "equipement_id": equipement.id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du ping: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

# Routes d'administration (admin seulement)
@app.route('/admin/users')
@login_required
def admin_users():
    """Page d'administration des utilisateurs (admin seulement)"""
    if current_user.role != 'admin':
        flash('Accès refusé : réservé aux administrateurs.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        users_list = User.query.filter_by(actif=True).all()
        
        # Calculer les statistiques
        stats = {
            'total': len(users_list),
            'en_attente': len([u for u in users_list if u.statut == 'en_attente']),
            'approuves': len([u for u in users_list if u.statut == 'approuve']),
            'refuses': len([u for u in users_list if u.statut == 'refuse'])
        }
        
        return render_template('admin_users.html', users=users_list, stats=stats)
    except Exception as e:
        logger.error(f"Erreur dans admin_users: {e}")
        flash(f"Erreur lors du chargement des utilisateurs: {e}", "error")
        stats = {'total': 0, 'en_attente': 0, 'approuves': 0, 'refuses': 0}
        return render_template('admin_users.html', users=[], stats=stats)

@app.route('/admin/users/<int:user_id>/approve', methods=['POST'])
@login_required
def approve_user(user_id):
    """Approuver un utilisateur (admin seulement)"""
    if current_user.role != 'admin':
        flash('Accès refusé : réservé aux administrateurs.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('Utilisateur non trouvé.', 'error')
            return redirect(url_for('admin_users'))
        
        user.statut = 'approuve'
        db.session.commit()
        
        # Envoyer un email de confirmation
        if email_service:
            email_service.send_account_approval_notification(user.email, user.nom_complet or user.nom_utilisateur, approved=True)
        
        flash(f'Utilisateur {user.nom_utilisateur} approuvé avec succès.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'approbation de l'utilisateur {user_id}: {e}")
        flash('Erreur lors de l\'approbation de l\'utilisateur.', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/reject', methods=['POST'])
@login_required  
def reject_user(user_id):
    """Refuser un utilisateur (admin seulement)"""
    if current_user.role != 'admin':
        flash('Accès refusé : réservé aux administrateurs.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('Utilisateur non trouvé.', 'error')
            return redirect(url_for('admin_users'))
        
        user.statut = 'refuse'
        db.session.commit()
        
        # Envoyer un email de refus
        if email_service:
            email_service.send_account_approval_notification(user.email, user.nom_complet or user.nom_utilisateur, approved=False)
        
        flash(f'Utilisateur {user.nom_utilisateur} refusé.', 'info')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors du refus de l'utilisateur {user_id}: {e}")
        flash('Erreur lors du refus de l\'utilisateur.', 'error')
    
    return redirect(url_for('admin_users'))

# AJAX Routes pour les mises à jour en temps réel
@app.route('/api/stats')
@login_required
def api_stats():
    """API pour obtenir les statistiques en temps réel"""
    try:
        if current_user.role == 'admin':
            total_clients = Client.query.filter_by(actif=True).count()
            total_equipements = Equipement.query.filter_by(actif=True).count()
            equipements = Equipement.query.filter_by(actif=True).all()
        else:
            total_clients = 1 if current_user.client_id else 0
            total_equipements = Equipement.query.filter_by(client_id=current_user.client_id, actif=True).count()
            equipements = Equipement.query.filter_by(client_id=current_user.client_id, actif=True).all()
        
        equipements_en_ligne = len([eq for eq in equipements if eq.est_en_ligne])
        equipements_hors_ligne = len([eq for eq in equipements if not eq.est_en_ligne])
        
        if current_user.role == 'admin':
            alertes_non_lues = Alerte.query.filter_by(lue=False).count()
        else:
            alertes_non_lues = db.session.query(Alerte).join(Equipement).filter(
                Equipement.client_id == current_user.client_id,
                Alerte.lue == False
            ).count()
        
        return jsonify({
            'total_clients': total_clients,
            'total_equipements': total_equipements,
            'equipements_en_ligne': equipements_en_ligne,
            'equipements_hors_ligne': equipements_hors_ligne,
            'alertes_non_lues': alertes_non_lues
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_stats: {e}")
        return jsonify({'error': 'Erreur lors du chargement des statistiques'}), 500

@app.route('/api/equipements/status')
@login_required
def api_equipements_status():
    """API pour obtenir le statut des équipements en temps réel"""
    try:
        if current_user.role == 'admin':
            equipements = Equipement.query.filter_by(actif=True).all()
        else:
            equipements = Equipement.query.filter_by(client_id=current_user.client_id, actif=True).all()
        
        equipements_data = []
        for eq in equipements:
            equipements_data.append({
                'id': eq.id,
                'nom': eq.nom,
                'adresse_ip': eq.adresse_ip,
                'est_en_ligne': eq.est_en_ligne,
                'statut_texte': eq.statut_texte,
                'dernier_ping': eq.dernier_ping.isoformat() if eq.dernier_ping else None,
                'duree_depuis_dernier_ping': eq.duree_depuis_dernier_ping
            })
        
        return jsonify(equipements_data)
        
    except Exception as e:
        logger.error(f"Erreur dans api_equipements_status: {e}")
        return jsonify({'error': 'Erreur lors du chargement du statut des équipements'}), 500

# Routes pour la création et modification de clients et équipements
@app.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    """Ajouter un nouveau client (admin seulement)"""
    if current_user.role != 'admin':
        flash('Accès refusé : réservé aux administrateurs.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            nom = request.form.get('nom')
            email = request.form.get('email')
            adresse = request.form.get('adresse')
            telephone = request.form.get('telephone')
            
            if not nom or not email:
                flash('Le nom et l\'email sont obligatoires.', 'error')
                return render_template('clients.html')
            
            # Vérifier si l'email existe déjà
            if Client.query.filter_by(email=email, actif=True).first():
                flash('Cette adresse email est déjà utilisée par un autre client.', 'error')
                return render_template('clients.html')
            
            nouveau_client = Client()
            nouveau_client.nom = nom
            nouveau_client.email = email
            nouveau_client.adresse = adresse
            nouveau_client.telephone = telephone
            
            db.session.add(nouveau_client)
            db.session.commit()
            
            flash(f'Client "{nom}" ajouté avec succès.', 'success')
            logger.info(f'Nouveau client créé: {nom} par {current_user.nom_utilisateur}')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erreur lors de la création du client: {e}')
            flash('Une erreur est survenue lors de la création du client.', 'error')
    
    return redirect(url_for('clients'))

@app.route('/clients/<int:client_id>/edit', methods=['POST'])
@login_required
def edit_client(client_id):
    """Modifier un client (admin seulement)"""
    if current_user.role != 'admin':
        flash('Accès refusé : réservé aux administrateurs.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        client = Client.query.get(client_id)
        if not client:
            flash('Client non trouvé.', 'error')
            return redirect(url_for('clients'))
        
        client.nom = request.form.get('nom', client.nom)
        client.email = request.form.get('email', client.email)
        client.adresse = request.form.get('adresse', client.adresse)
        client.telephone = request.form.get('telephone', client.telephone)
        
        db.session.commit()
        flash(f'Client "{client.nom}" modifié avec succès.', 'success')
        logger.info(f'Client {client.nom} modifié par {current_user.nom_utilisateur}')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erreur lors de la modification du client {client_id}: {e}')
        flash('Une erreur est survenue lors de la modification du client.', 'error')
    
    return redirect(url_for('clients'))

@app.route('/clients/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    """Supprimer un client (admin seulement)"""
    if current_user.role != 'admin':
        flash('Accès refusé : réservé aux administrateurs.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        client = Client.query.get(client_id)
        if not client:
            flash('Client non trouvé.', 'error')
            return redirect(url_for('clients'))
        
        client.actif = False  # Suppression logique
        db.session.commit()
        flash(f'Client "{client.nom}" supprimé avec succès.', 'success')
        logger.info(f'Client {client.nom} supprimé par {current_user.nom_utilisateur}')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erreur lors de la suppression du client {client_id}: {e}')
        flash('Une erreur est survenue lors de la suppression du client.', 'error')
    
    return redirect(url_for('clients'))

@app.route('/equipements/add', methods=['GET', 'POST'])
@login_required
def add_equipement():
    """Ajouter un nouvel équipement"""
    if request.method == 'POST':
        try:
            nom = request.form.get('nom')
            type_equipement = request.form.get('type_equipement')
            adresse_ip = request.form.get('adresse_ip')
            port = request.form.get('port', 80, type=int)
            client_id = request.form.get('client_id', type=int)
            
            if not all([nom, type_equipement, adresse_ip]):
                flash('Le nom, type et adresse IP sont obligatoires.', 'error')
                return redirect(url_for('equipements'))
            
            # Vérifier les permissions
            if current_user.role == 'client':
                if client_id != current_user.client_id:
                    flash('Vous ne pouvez ajouter des équipements que pour votre client.', 'error')
                    return redirect(url_for('equipements'))
                client_id = current_user.client_id
            elif current_user.role == 'admin':
                if not client_id:
                    flash('Veuillez sélectionner un client.', 'error')
                    return redirect(url_for('equipements'))
            
            # Vérifier si l'IP existe déjà pour ce client
            if Equipement.query.filter_by(adresse_ip=adresse_ip, client_id=client_id, actif=True).first():
                flash('Cette adresse IP est déjà utilisée pour ce client.', 'error')
                return redirect(url_for('equipements'))
            
            nouvel_equipement = Equipement()
            nouvel_equipement.nom = nom
            nouvel_equipement.type_equipement = type_equipement
            nouvel_equipement.adresse_ip = adresse_ip
            nouvel_equipement.port = port
            nouvel_equipement.client_id = client_id
            
            db.session.add(nouvel_equipement)
            db.session.commit()
            
            flash(f'Équipement "{nom}" ajouté avec succès.', 'success')
            logger.info(f'Nouvel équipement créé: {nom} ({adresse_ip}) par {current_user.nom_utilisateur}')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erreur lors de la création de l\'équipement: {e}')
            flash('Une erreur est survenue lors de la création de l\'équipement.', 'error')
    
    return redirect(url_for('equipements'))

@app.route('/equipements/<int:equipement_id>/edit', methods=['POST'])
@login_required
def edit_equipement(equipement_id):
    """Modifier un équipement"""
    try:
        equipement = Equipement.query.get(equipement_id)
        if not equipement:
            flash('Équipement non trouvé.', 'error')
            return redirect(url_for('equipements'))
        
        # Vérifier les permissions
        if current_user.role == 'client' and equipement.client_id != current_user.client_id:
            flash('Vous ne pouvez modifier que vos propres équipements.', 'error')
            return redirect(url_for('equipements'))
        
        equipement.nom = request.form.get('nom', equipement.nom)
        equipement.type_equipement = request.form.get('type_equipement', equipement.type_equipement)
        equipement.adresse_ip = request.form.get('adresse_ip', equipement.adresse_ip)
        equipement.port = request.form.get('port', equipement.port, type=int)
        
        # Seuls les admins peuvent changer le client
        if current_user.role == 'admin':
            new_client_id = request.form.get('client_id', type=int)
            if new_client_id:
                equipement.client_id = new_client_id
        
        db.session.commit()
        flash(f'Équipement "{equipement.nom}" modifié avec succès.', 'success')
        logger.info(f'Équipement {equipement.nom} modifié par {current_user.nom_utilisateur}')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erreur lors de la modification de l\'équipement {equipement_id}: {e}')
        flash('Une erreur est survenue lors de la modification de l\'équipement.', 'error')
    
    return redirect(url_for('equipements'))

@app.route('/equipements/<int:equipement_id>/delete', methods=['POST'])
@login_required
def delete_equipement(equipement_id):
    """Supprimer un équipement"""
    try:
        equipement = Equipement.query.get(equipement_id)
        if not equipement:
            flash('Équipement non trouvé.', 'error')
            return redirect(url_for('equipements'))
        
        # Vérifier les permissions
        if current_user.role == 'client' and equipement.client_id != current_user.client_id:
            flash('Vous ne pouvez supprimer que vos propres équipements.', 'error')
            return redirect(url_for('equipements'))
        
        equipement.actif = False  # Suppression logique
        db.session.commit()
        flash(f'Équipement "{equipement.nom}" supprimé avec succès.', 'success')
        logger.info(f'Équipement {equipement.nom} supprimé par {current_user.nom_utilisateur}')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erreur lors de la suppression de l\'équipement {equipement_id}: {e}')
        flash('Une erreur est survenue lors de la suppression de l\'équipement.', 'error')
    
    return redirect(url_for('equipements'))