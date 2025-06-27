import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func, extract

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'dj-calendar-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, origins="*")
db = SQLAlchemy(app)

# Modèle pour les événements (avec notes techniques)
class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    venue_name = db.Column(db.String(200), nullable=False)
    venue_address = db.Column(db.Text, nullable=True)
    fee = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(3), nullable=False, default='EUR')
    status = db.Column(db.String(20), nullable=False, default='confirmed')
    event_type = db.Column(db.String(50), nullable=False, default='club')
    notes = db.Column(db.Text, nullable=True)
    
    # Nouvelles colonnes pour les notes techniques DJ
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
            'date': self.date.isoformat() if self.date else None,
            'startTime': self.start_time.strftime('%H:%M') if self.start_time else None,
            'endTime': self.end_time.strftime('%H:%M') if self.end_time else None,
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
    search = request.args.get('search', '')
    event_type = request.args.get('type', '')
    status = request.args.get('status', '')
    
    query = Event.query
    
    if search:
        query = query.filter(
            (Event.title.contains(search)) | 
            (Event.venue_name.contains(search))
        )
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if status:
        query = query.filter(Event.status == status)
    
    events = query.order_by(Event.date.asc()).all()
    return jsonify({'success': True, 'events': [event.to_dict() for event in events]})

@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.get_json()
    
    event = Event()
    event.title = data.get('title')
    event.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    event.start_time = datetime.strptime(data.get('startTime'), '%H:%M').time()
    if data.get('endTime'):
        event.end_time = datetime.strptime(data.get('endTime'), '%H:%M').time()
    event.venue_name = data.get('venueName')
    event.venue_address = data.get('venueAddress')
    event.fee = float(data.get('fee', 0))
    event.currency = data.get('currency', 'EUR')
    event.status = data.get('status', 'confirmed')
    event.event_type = data.get('type', 'club')
    event.notes = data.get('notes')
    
    # Notes techniques
    event.tech_equipment = data.get('techEquipment')
    event.tech_setup = data.get('techSetup')
    event.tech_playlist = data.get('techPlaylist')
    event.tech_setup_time = data.get('techSetupTime')
    event.tech_notes = data.get('techNotes')
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'success': True, 'event': event.to_dict()})

@app.route('/api/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json()
    
    event.title = data.get('title')
    event.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    event.start_time = datetime.strptime(data.get('startTime'), '%H:%M').time()
    if data.get('endTime'):
        event.end_time = datetime.strptime(data.get('endTime'), '%H:%M').time()
    else:
        event.end_time = None
    event.venue_name = data.get('venueName')
    event.venue_address = data.get('venueAddress')
    event.fee = float(data.get('fee', 0))
    event.currency = data.get('currency', 'EUR')
    event.status = data.get('status', 'confirmed')
    event.event_type = data.get('type', 'club')
    event.notes = data.get('notes')
    
    # Notes techniques
    event.tech_equipment = data.get('techEquipment')
    event.tech_setup = data.get('techSetup')
    event.tech_playlist = data.get('techPlaylist')
    event.tech_setup_time = data.get('techSetupTime')
    event.tech_notes = data.get('techNotes')
    
    db.session.commit()
    
    return jsonify({'success': True, 'event': event.to_dict()})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Event deleted successfully'})

@app.route('/api/events/stats', methods=['GET'])
def get_stats():
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

@app.route('/api/events/analytics', methods=['GET'])
def get_analytics():
    try:
        # Revenus par mois (12 derniers mois)
        one_year_ago = datetime.now().date() - timedelta(days=365)
        
        monthly_revenue = db.session.query(
            extract('year', Event.date).label('year'),
            extract('month', Event.date).label('month'),
            func.sum(Event.fee).label('revenue')
        ).filter(
            Event.status == 'confirmed',
            Event.date >= one_year_ago
        ).group_by(
            extract('year', Event.date),
            extract('month', Event.date)
        ).order_by('year', 'month').all()
        
        # Revenus par type d'événement
        revenue_by_type = db.session.query(
            Event.event_type,
            func.sum(Event.fee).label('revenue'),
            func.count(Event.id).label('count')
        ).filter(Event.status == 'confirmed').group_by(Event.event_type).all()
        
        # Formatage des données
        monthly_data = []
        month_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 
                       'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        
        for item in monthly_revenue:
            monthly_data.append({
                'month': f"{month_names[int(item.month)-1]} {int(item.year)}",
                'revenue': float(item.revenue or 0)
            })
        
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
                'monthly_revenue': monthly_data,
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
    print("📱 Ouvre ton navigateur et va sur: http://localhost:5000" )
    app.run(host='0.0.0.0', port=5000, debug=True)
