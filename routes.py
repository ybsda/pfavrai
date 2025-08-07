import random
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import current_user
from sqlalchemy import desc

from app import app, db
from models import Camera, CameraAlert, SystemHealth
from replit_auth import require_login, make_replit_blueprint

# Register Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page for logged out users, dashboard for logged in users"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard with system overview"""
    user = current_user
    
    # Get user's cameras
    cameras = Camera.query.filter_by(created_by=user.id).all()
    
    # Get recent alerts
    camera_ids = [c.id for c in cameras]
    recent_alerts = []
    if camera_ids:
        recent_alerts = CameraAlert.query.filter(
            CameraAlert.camera_id.in_(camera_ids)
        ).order_by(desc(CameraAlert.created_at)).limit(10).all()
    
    # Calculate stats
    total_cameras = len(cameras)
    online_cameras = len([c for c in cameras if c.status == 'online'])
    offline_cameras = len([c for c in cameras if c.status == 'offline'])
    error_cameras = len([c for c in cameras if c.status == 'error'])
    
    # Mock system health data
    system_health = [
        {'metric': 'CPU Usage', 'value': f"{random.randint(15, 85)}%", 'status': 'normal'},
        {'metric': 'Memory Usage', 'value': f"{random.randint(40, 75)}%", 'status': 'normal'},
        {'metric': 'Disk Usage', 'value': f"{random.randint(25, 60)}%", 'status': 'normal'},
        {'metric': 'Network Traffic', 'value': f"{random.randint(10, 50)} Mbps", 'status': 'normal'},
    ]
    
    return render_template('dashboard.html', 
                         user=user,
                         cameras=cameras,
                         recent_alerts=recent_alerts,
                         total_cameras=total_cameras,
                         online_cameras=online_cameras,
                         offline_cameras=offline_cameras,
                         error_cameras=error_cameras,
                         system_health=system_health)

@app.route('/cameras')
@require_login
def cameras():
    """Camera management page"""
    user = current_user
    user_cameras = Camera.query.filter_by(created_by=user.id).all()
    
    return render_template('cameras.html', user=user, cameras=user_cameras)

@app.route('/cameras/add', methods=['GET', 'POST'])
@require_login
def add_camera():
    """Add new camera"""
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        ip_address = request.form.get('ip_address')
        port = request.form.get('port', 554, type=int)
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not name or not location:
            flash('Camera name and location are required', 'error')
            return redirect(url_for('cameras'))
        
        # Create new camera
        camera = Camera(
            name=name,
            location=location,
            ip_address=ip_address,
            port=port,
            username=username,
            password=password,
            created_by=current_user.id,
            status=random.choice(['online', 'offline'])  # Mock status
        )
        
        # Mock last_seen for online cameras
        if camera.status == 'online':
            camera.last_seen = datetime.now()
        
        db.session.add(camera)
        db.session.commit()
        
        flash(f'Camera "{name}" added successfully', 'success')
        return redirect(url_for('cameras'))
    
    return redirect(url_for('cameras'))

@app.route('/cameras/<int:camera_id>')
@require_login
def camera_detail(camera_id):
    """Camera detail page"""
    camera = Camera.query.filter_by(id=camera_id, created_by=current_user.id).first()
    if not camera:
        flash('Camera not found', 'error')
        return redirect(url_for('cameras'))
    
    # Get camera alerts
    alerts = CameraAlert.query.filter_by(camera_id=camera.id).order_by(
        desc(CameraAlert.created_at)
    ).limit(20).all()
    
    return render_template('camera_detail.html', camera=camera, alerts=alerts)

@app.route('/cameras/<int:camera_id>/delete', methods=['POST'])
@require_login
def delete_camera(camera_id):
    """Delete camera"""
    camera = Camera.query.filter_by(id=camera_id, created_by=current_user.id).first()
    if not camera:
        flash('Camera not found', 'error')
        return redirect(url_for('cameras'))
    
    # Delete associated alerts
    CameraAlert.query.filter_by(camera_id=camera.id).delete()
    
    # Delete camera
    db.session.delete(camera)
    db.session.commit()
    
    flash(f'Camera "{camera.name}" deleted successfully', 'success')
    return redirect(url_for('cameras'))

@app.route('/cameras/<int:camera_id>/toggle', methods=['POST'])
@require_login
def toggle_camera(camera_id):
    """Toggle camera status"""
    camera = Camera.query.filter_by(id=camera_id, created_by=current_user.id).first()
    if not camera:
        flash('Camera not found', 'error')
        return redirect(url_for('cameras'))
    
    # Toggle status
    if camera.status == 'online':
        camera.status = 'offline'
        camera.last_seen = None
    else:
        camera.status = 'online'
        camera.last_seen = datetime.now()
    
    db.session.commit()
    flash(f'Camera "{camera.name}" is now {camera.status}', 'info')
    return redirect(url_for('cameras'))

@app.route('/settings')
@require_login
def settings():
    """Settings page"""
    return render_template('settings.html', user=current_user)

@app.route('/api/camera-status')
@require_login
def camera_status_api():
    """API endpoint for real-time camera status updates"""
    user_cameras = Camera.query.filter_by(created_by=current_user.id).all()
    
    camera_data = []
    for camera in user_cameras:
        # Simulate random status changes for demo
        if random.random() < 0.1:  # 10% chance of status change
            new_status = random.choice(['online', 'offline', 'error'])
            if new_status != camera.status:
                camera.status = new_status
                if new_status == 'online':
                    camera.last_seen = datetime.now()
                elif new_status == 'offline':
                    camera.last_seen = None
                db.session.commit()
        
        camera_data.append({
            'id': camera.id,
            'name': camera.name,
            'status': camera.status,
            'last_seen': camera.last_seen.isoformat() if camera.last_seen else None
        })
    
    return jsonify(camera_data)

@app.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@require_login
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    alert = CameraAlert.query.join(Camera).filter(
        CameraAlert.id == alert_id,
        Camera.created_by == current_user.id
    ).first()
    
    if not alert:
        flash('Alert not found', 'error')
        return redirect(url_for('dashboard'))
    
    alert.acknowledged = True
    alert.acknowledged_at = datetime.now()
    db.session.commit()
    
    flash('Alert acknowledged', 'success')
    return redirect(request.referrer or url_for('dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('403.html', error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('403.html', error_message="Internal server error"), 500
