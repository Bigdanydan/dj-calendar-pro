import os
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'dj-calendar-secret-key-2025'

# Configuration PostgreSQL avec psycopg 3
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Render utilise postgres:// mais SQLAlchemy avec psycopg 3 veut postgresql+psycopg://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
    elif DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    logger.info("✅ Utilisation de PostgreSQL avec psycopg 3")
else:
    # Fallback vers SQLite pour le développement local
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar.db'
    logger.info("⚠️ Utilisation de SQLite (développement)")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)

# Modèle Event optimisé PostgreSQL + Mobile
class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=True)
    venue_name = db.Column(db.String(200), nullable=False)
    venue_address = db.Column(db.Text, nullable=True)
    fee = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='EUR')
    status = db.Column(db.String(20), default='confirmed')
    event_type = db.Column(db.String(50), default='club')
    notes = db.Column(db.Text, nullable=True)
    tech_equipment = db.Column(db.Text, nullable=True)
    tech_setup = db.Column(db.Text, nullable=True)
    tech_playlist = db.Column(db.Text, nullable=True)
    tech_setup_time = db.Column(db.Integer, nullable=True)
    tech_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date,
            'startTime': self.start_time,
            'endTime': self.end_time,
            'venueName': self.venue_name,
            'venueAddress': self.venue_address,
            'fee': self.fee,
            'currency': self.currency,
            'status': self.status,
            'type': self.event_type,
            'notes': self.notes,
            'techEquipment': self.tech_equipment,
            'techSetup': self.tech_setup,
            'techPlaylist': self.tech_playlist,
            'techSetupTime': self.tech_setup_time,
            'techNotes': self.tech_notes
        }

# Fonction utilitaire pour gérer les entiers
def safe_int(value):
    """Convertit une valeur en entier ou retourne None si vide/invalide"""
    if value is None or value == '' or value == 'null':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

# Route pour initialiser la base de données
@app.route('/init-database')
def init_database():
    try:
        logger.info("🔧 Initialisation de la base de données PostgreSQL...")
        
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        # Vérifier que la table existe (compatible psycopg 3)
        result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = [row[0] for row in result]
        
        logger.info(f"✅ Tables créées: {tables}")
        
        return jsonify({
            'success': True, 
            'message': 'Base de données PostgreSQL initialisée avec psycopg 3',
            'tables': tables,
            'database_type': 'PostgreSQL + psycopg 3'
        })
    except Exception as e:
        logger.error(f"❌ Erreur initialisation: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        })

# Routes principales
@app.route('/api/events', methods=['GET', 'POST'])
def handle_events():
    if request.method == 'GET':
        try:
            search = request.args.get('search', '')
            event_type = request.args.get('type', '')
            status = request.args.get('status', '')
            
            query = Event.query
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (Event.title.like(search_term)) | 
                    (Event.venue_name.like(search_term))
                )
            
            if event_type:
                query = query.filter(Event.event_type == event_type)
            
            if status:
                query = query.filter(Event.status == status)
            
            events = query.order_by(Event.date.asc()).all()
            return jsonify({'success': True, 'events': [event.to_dict() for event in events]})
        except Exception as e:
            logger.error(f"Erreur GET events: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.info(f"Données reçues: {data}")
            
            # Gestion sécurisée des champs entiers
            tech_setup_time = safe_int(data.get('techSetupTime'))
            
            event = Event(
                title=data.get('title', ''),
                date=data.get('date', ''),
                start_time=data.get('startTime', ''),
                end_time=data.get('endTime', ''),
                venue_name=data.get('venueName', ''),
                venue_address=data.get('venueAddress', ''),
                fee=float(data.get('fee', 0)),
                currency=data.get('currency', 'EUR'),
                status=data.get('status', 'confirmed'),
                event_type=data.get('type', 'club'),
                notes=data.get('notes', ''),
                tech_equipment=data.get('techEquipment', ''),
                tech_setup=data.get('techSetup', ''),
                tech_playlist=data.get('techPlaylist', ''),
                tech_setup_time=tech_setup_time,  # Utilise la fonction safe_int
                tech_notes=data.get('techNotes', '')
            )
            
            db.session.add(event)
            db.session.commit()
            logger.info(f"✅ Événement créé: {event.id}")
            
            return jsonify({'success': True, 'event': event.to_dict()})
        except Exception as e:
            logger.error(f"❌ Erreur POST events: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/events/<int:event_id>', methods=['PUT', 'DELETE'])
def handle_event(event_id):
    if request.method == 'PUT':
        try:
            event = Event.query.get_or_404(event_id)
            data = request.get_json()
            
            event.title = data.get('title', event.title)
            event.date = data.get('date', event.date)
            event.start_time = data.get('startTime', event.start_time)
            event.end_time = data.get('endTime', event.end_time)
            event.venue_name = data.get('venueName', event.venue_name)
            event.venue_address = data.get('venueAddress', event.venue_address)
            event.fee = float(data.get('fee', event.fee))
            event.currency = data.get('currency', event.currency)
            event.status = data.get('status', event.status)
            event.event_type = data.get('type', event.event_type)
            event.notes = data.get('notes', event.notes)
            event.tech_equipment = data.get('techEquipment', event.tech_equipment)
            event.tech_setup = data.get('techSetup', event.tech_setup)
            event.tech_playlist = data.get('techPlaylist', event.tech_playlist)
            event.tech_setup_time = safe_int(data.get('techSetupTime', event.tech_setup_time))
            event.tech_notes = data.get('techNotes', event.tech_notes)
            
            db.session.commit()
            return jsonify({'success': True, 'event': event.to_dict()})
        except Exception as e:
            logger.error(f"Erreur PUT event: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    if request.method == 'DELETE':
        try:
            event = Event.query.get_or_404(event_id)
            db.session.delete(event)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Event deleted'})
        except Exception as e:
            logger.error(f"Erreur DELETE event: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/events/stats')
def get_stats():
    try:
        total_events = Event.query.count()
        confirmed_events = Event.query.filter_by(status='confirmed').count()
        pending_events = Event.query.filter_by(status='pending').count()
        confirmed_events_list = Event.query.filter_by(status='confirmed').all()
        total_revenue = sum(event.fee for event in confirmed_events_list)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_events': total_events,
                'confirmed_events': confirmed_events,
                'pending_events': pending_events,
                'total_revenue': total_revenue
            }
        })
    except Exception as e:
        logger.error(f"Erreur stats: {e}")
        return jsonify({
            'success': True, 
            'stats': {
                'total_events': 0, 
                'confirmed_events': 0, 
                'pending_events': 0, 
                'total_revenue': 0
            }
        })

@app.route('/api/events/analytics')
def get_analytics():
    try:
        return jsonify({
            'success': True,
            'analytics': {
                'monthly_revenue': [],
                'revenue_by_type': []
            }
        })
    except Exception as e:
        logger.error(f"Erreur analytics: {e}")
        return jsonify({
            'success': True, 
            'analytics': {
                'monthly_revenue': [], 
                'revenue_by_type': []
            }
        })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/health')
def health():
    db_type = "PostgreSQL + psycopg 3" if DATABASE_URL else "SQLite"
    return {
        'status': 'healthy', 
        'message': f'DJ Calendar API is running with {db_type}',
        'database': db_type
    }

if __name__ == '__main__':
    logger.info("🚀 Démarrage DJ Calendar PRO+ avec PostgreSQL + psycopg 3")
    
    with app.app_context():
        try:
            # Créer les tables automatiquement
            db.create_all()
            logger.info("✅ Tables PostgreSQL créées/vérifiées")
            
        except Exception as e:
            logger.error(f"❌ Erreur création tables: {e}")
    
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🎵 DJ Calendar PRO+ démarré sur le port {port}")
    app.run(host='0.0.0.0', port=port)
