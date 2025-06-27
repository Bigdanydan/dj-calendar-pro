import os
import sys
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func, extract, text

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'dj-calendar-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, origins="*")
db = SQLAlchemy(app)

# Modèle pour les événements
class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Format YYYY-MM-DD
    start_time = db.Column(db.String(5), nullable=False)  # Format HH:MM
    end_time = db.Column(db.String(5), nullable=True)  # Format HH:MM
    venue_name = db.Column(db.String(200), nullable=False)
    venue_address = db.Column(db.Text, nullable=True)
    fee = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(3), nullable=False, default='EUR')
    status = db.Column(db.String(20), nullable=False, default='confirmed')
    event_type = db.Column(db.String(50), nullable=False, default='club')
    notes = db.Column(db.Text, nullable=True)
    
    # Notes techniques DJ
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

# Routes API
@app.route('/api/events', methods=['GET'])
def get_events():
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
        print(f"Erreur get_events: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/events', methods=['POST'])
def create_event():
    try:
        data = request.get_json()
        
        event = Event()
        event.title = data.get('title', '')
        event.date = data.get('date', '')
        event.start_time = data.get('startTime', '')
        event.end_time = data.get('endTime', '')
        event.venue_name = data.get('venueName', '')
        event.venue_address = data.get('venueAddress', '')
        event.fee = float(data.get('fee', 0))
        event.currency = data.get('currency', 'EUR')
        event.status = data.get('status', 'confirmed')
        event.event_type = data.get('type', 'club')
        event.notes = data.get('notes', '')
        
        # Notes techniques
        event.tech_equipment = data.get('techEquipment', '')
        event.tech_setup = data.get('techSetup', '')
        event.tech_playlist = data.get('techPlaylist', '')
        event.tech_setup_time = data.get('techSetupTime')
        event.tech_notes = data.get('techNotes', '')
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({'success': True, 'event': event.to_dict()})
    except Exception as e:
        print(f"Erreur create_event: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
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
        
        # Notes techniques
        event.tech_equipment = data.get('techEquipment', event.tech_equipment)
        event.tech_setup = data.get('techSetup', event.tech_setup)
        event.tech_playlist = data.get('techPlaylist', event.tech_playlist)
        event.tech_setup_time = data.get('techSetupTime', event.tech_setup_time)
        event.tech_notes = data.get('techNotes', event.tech_notes)
        
        db.session.commit()
        
        return jsonify({'success': True, 'event': event.to_dict()})
    except Exception as e:
        print(f"Erreur update_event: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Event deleted successfully'})
    except Exception as e:
        print(f"Erreur delete_event: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/events/stats', methods=['GET'])
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
        print(f"Erreur get_stats: {e}")
        return jsonify({
            'success': True,
            'stats': {
                'total_events': 0,
                'confirmed_events': 0,
                'pending_events': 0,
                'total_revenue': 0
            }
        })

@app.route('/api/events/analytics', methods=['GET'])
def get_analytics():
    try:
        # Revenus par type d'événement (version simplifiée)
        revenue_by_type = db.session.query(
            Event.event_type,
            func.sum(Event.fee).label('revenue'),
            func.count(Event.id).label('count')
        ).filter(Event.status == 'confirmed').group_by(Event.event_type).all()
        
        # Données mensuelles simplifiées
        monthly_revenue = []
        current_date = datetime.now()
        for i in range(6):  # 6 derniers mois
            month_date = current_date - timedelta(days=30*i)
            month_str = month_date.strftime('%Y-%m')
            
            # Compter les événements du mois
            month_events = Event.query.filter(
                Event.status == 'confirmed',
                Event.date.like(f"{month_str}%")
            ).all()
            
            month_revenue = sum(event.fee for event in month_events)
            monthly_revenue.append({
                'month': month_date.strftime('%b %Y'),
                'revenue': month_revenue
            })
        
        monthly_revenue.reverse()  # Ordre chronologique
        
        # Formatage des données par type
        type_data = []
        for item in revenue_by_type:
            type_data.append({
                'type': item.event_type,
                'revenue': float(item.revenue or 0),
                'count': item.count
            })
        
        return jsonify({
            'success': True,
            'analytics': {
                'monthly_revenue': monthly_revenue,
                'revenue_by_type': type_data
            }
        })
    except Exception as e:
        print(f"Erreur analytics: {e}")
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
    return {'status': 'healthy', 'message': 'DJ Calendar API is running'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("🎵 DJ Calendar PRO+ démarré !")
    print("📱 Accessible sur Render !")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
