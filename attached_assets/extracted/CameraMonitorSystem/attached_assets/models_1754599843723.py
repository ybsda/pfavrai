from datetime import datetime, timedelta
from app import db
from sqlalchemy import func

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.Text)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)
    
    # Relation avec les équipements
    equipements = db.relationship('Equipement', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Client {self.nom}>'
    
    @property
    def nb_equipements_total(self):
        return db.session.query(Equipement).filter_by(client_id=self.id, actif=True).count()
    
    @property
    def nb_equipements_en_ligne(self):
        equipements = db.session.query(Equipement).filter_by(client_id=self.id, actif=True).all()
        return len([eq for eq in equipements if eq.est_en_ligne])
    
    @property
    def nb_equipements_hors_ligne(self):
        equipements = db.session.query(Equipement).filter_by(client_id=self.id, actif=True).all()
        return len([eq for eq in equipements if not eq.est_en_ligne])

class Equipement(db.Model):
    __tablename__ = 'equipements'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    type_equipement = db.Column(db.String(50), nullable=False)  # DVR, Camera, etc.
    adresse_ip = db.Column(db.String(45), nullable=False)
    port = db.Column(db.Integer, default=80)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    dernier_ping = db.Column(db.DateTime)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)
    
    # Relation avec l'historique des pings
    historique_pings = db.relationship('HistoriquePing', backref='equipement', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Equipement {self.nom} - {self.adresse_ip}>'
    
    @property
    def est_en_ligne(self):
        """Vérifie si l'équipement est considéré comme en ligne (ping < 2 minutes)"""
        if not self.dernier_ping:
            return False
        
        timeout = datetime.utcnow() - timedelta(minutes=2)
        return self.dernier_ping > timeout
    
    @property
    def statut_texte(self):
        return "En ligne" if self.est_en_ligne else "Hors ligne"
    
    @property
    def duree_depuis_dernier_ping(self):
        """Retourne la durée depuis le dernier ping en format lisible"""
        if not self.dernier_ping:
            return "Jamais"
        
        delta = datetime.utcnow() - self.dernier_ping
        
        if delta.days > 0:
            return f"{delta.days} jour(s)"
        elif delta.seconds > 3600:
            heures = delta.seconds // 3600
            return f"{heures} heure(s)"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute(s)"
        else:
            return "< 1 minute"

class HistoriquePing(db.Model):
    __tablename__ = 'historique_pings'
    
    id = db.Column(db.Integer, primary_key=True)
    equipement_id = db.Column(db.Integer, db.ForeignKey('equipements.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), nullable=False)  # 'success', 'timeout', 'error'
    reponse_ms = db.Column(db.Integer)  # Temps de réponse en millisecondes
    message = db.Column(db.Text)
    
    def __repr__(self):
        return f'<HistoriquePing {self.equipement_id} - {self.statut} - {self.timestamp}>'

class Alerte(db.Model):
    __tablename__ = 'alertes'
    
    id = db.Column(db.Integer, primary_key=True)
    equipement_id = db.Column(db.Integer, db.ForeignKey('equipements.id'), nullable=False)
    type_alerte = db.Column(db.String(50), nullable=False)  # 'hors_ligne', 'retour_en_ligne'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    lue = db.Column(db.Boolean, default=False)
    
    # Relation avec l'équipement
    equipement = db.relationship('Equipement', backref='alertes')
    
    def __repr__(self):
        return f'<Alerte {self.type_alerte} - {self.equipement_id}>'
