from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime,
                           default=datetime.now,
                           onupdate=datetime.now)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Camera model for monitoring system
class Camera(db.Model):
    __tablename__ = 'cameras'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    port = db.Column(db.Integer, default=554)  # Default RTSP port
    username = db.Column(db.String(50), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    stream_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='offline')  # online, offline, error
    last_seen = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String, db.ForeignKey(User.id), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship
    owner = db.relationship(User, backref='cameras')

# Camera alerts/notifications
class CameraAlert(db.Model):
    __tablename__ = 'camera_alerts'
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey(Camera.id), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # connection_lost, motion_detected, etc.
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='info')  # info, warning, error, critical
    acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    camera = db.relationship(Camera, backref='alerts')

# System health metrics
class SystemHealth(db.Model):
    __tablename__ = 'system_health'
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='normal')  # normal, warning, critical
    recorded_at = db.Column(db.DateTime, default=datetime.now)
