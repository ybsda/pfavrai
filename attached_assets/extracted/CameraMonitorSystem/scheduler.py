import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app import db
from models import Equipement, Alerte
from email_service import email_service

logger = logging.getLogger(__name__)

def verifier_equipements_hors_ligne():
    """Vérifie périodiquement les équipements hors ligne et génère des alertes"""
    from app import app
    
    with app.app_context():
        try:
            # Définir le seuil de timeout (2 minutes)
            timeout = datetime.utcnow() - timedelta(minutes=2)
            
            # Trouver tous les équipements actifs
            equipements = Equipement.query.filter_by(actif=True).all()
            
            for equipement in equipements:
                # Vérifier si l'équipement était en ligne mais est maintenant hors ligne
                etait_en_ligne = True
                if equipement.dernier_ping is None or equipement.dernier_ping <= timeout:
                    etait_en_ligne = False
                
                # Vérifier s'il y a déjà une alerte récente pour cet équipement
                alerte_recente = Alerte.query.filter_by(
                    equipement_id=equipement.id,
                    type_alerte='hors_ligne'
                ).filter(
                    Alerte.timestamp > datetime.utcnow() - timedelta(hours=1)
                ).first()
                
                # Si l'équipement est hors ligne et qu'il n'y a pas d'alerte récente
                if not etait_en_ligne and not alerte_recente:
                    # Créer une nouvelle alerte
                    alerte = Alerte(
                        equipement_id=equipement.id,
                        type_alerte='hors_ligne',
                        message=f"L'équipement {equipement.nom} ({equipement.adresse_ip}) du client {equipement.client.nom} est hors ligne depuis plus de 2 minutes",
                        timestamp=datetime.utcnow()
                    )
                    
                    # Envoyer email d'alerte au client
                    if equipement.client.email:
                        email_service.send_equipment_offline_alert(
                            client_email=equipement.client.email,
                            client_name=equipement.client.nom,
                            equipment_name=equipement.nom,
                            equipment_type=equipement.type_equipement,
                            equipment_ip=equipement.adresse_ip
                        )
                        logger.info(f"Email d'alerte envoyé à {equipement.client.email} pour l'équipement {equipement.nom}")
                    
                    db.session.add(alerte)
                    logger.warning(f"Alerte générée: {equipement.nom} hors ligne")
            
            db.session.commit()
            logger.debug("Vérification des équipements hors ligne terminée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des équipements: {e}")
            db.session.rollback()

def nettoyer_historique():
    """Nettoie l'historique ancien pour éviter l'accumulation excessive de données"""
    from app import app
    
    with app.app_context():
        try:
            # Supprimer les entrées d'historique plus anciennes que 30 jours
            limite = datetime.utcnow() - timedelta(days=30)
            
            from models import HistoriquePing
            
            # Compter les entrées à supprimer
            nb_a_supprimer = HistoriquePing.query.filter(
                HistoriquePing.timestamp < limite
            ).count()
            
            if nb_a_supprimer > 0:
                # Supprimer les entrées anciennes
                HistoriquePing.query.filter(
                    HistoriquePing.timestamp < limite
                ).delete()
                
                db.session.commit()
                logger.info(f"Historique nettoyé: {nb_a_supprimer} entrées supprimées")
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de l'historique: {e}")
            db.session.rollback()

def nettoyer_alertes():
    """Nettoie les alertes anciennes déjà lues"""
    from app import app
    
    with app.app_context():
        try:
            # Supprimer les alertes lues plus anciennes que 7 jours
            limite = datetime.utcnow() - timedelta(days=7)
            
            nb_a_supprimer = Alerte.query.filter(
                Alerte.timestamp < limite,
                Alerte.lue == True
            ).count()
            
            if nb_a_supprimer > 0:
                Alerte.query.filter(
                    Alerte.timestamp < limite,
                    Alerte.lue == True
                ).delete()
                
                db.session.commit()
                logger.info(f"Alertes nettoyées: {nb_a_supprimer} alertes supprimées")
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des alertes: {e}")
            db.session.rollback()

def init_scheduler(app):
    """Initialise le planificateur de tâches"""
    try:
        scheduler = BackgroundScheduler()
        
        # Vérifier les équipements hors ligne toutes les minutes
        scheduler.add_job(
            func=verifier_equipements_hors_ligne,
            trigger=IntervalTrigger(minutes=1),
            id='verifier_equipements',
            name='Vérifier équipements hors ligne',
            replace_existing=True
        )
        
        # Nettoyer l'historique tous les jours à 2h du matin
        scheduler.add_job(
            func=nettoyer_historique,
            trigger='cron',
            hour=2,
            minute=0,
            id='nettoyer_historique',
            name='Nettoyer historique ancien',
            replace_existing=True
        )
        
        # Nettoyer les alertes tous les jours à 3h du matin
        scheduler.add_job(
            func=nettoyer_alertes,
            trigger='cron',
            hour=3,
            minute=0,
            id='nettoyer_alertes',
            name='Nettoyer alertes anciennes',
            replace_existing=True
        )
        
        # Démarrer le planificateur
        scheduler.start()
        
        logger.info("Planificateur de tâches initialisé avec succès")
        
        # Arrêter le planificateur proprement lors de l'arrêt de l'application
        import atexit
        atexit.register(lambda: scheduler.shutdown())
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du planificateur: {e}")
