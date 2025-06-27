import os
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'dj-calendar-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)

# Modèle Event
class Event(db.Model):
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

# Routes
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
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
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
                tech_setup_time=data.get('techSetupTime'),
                tech_notes=data.get('techNotes', '')
            )
            
            db.session.add(event)
            db.session.commit()
            
            return jsonify({'success': True, 'event': event.to_dict()})
        except Exception as e:
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
            event.tech_setup_time = data.get('techSetupTime', event.tech_setup_time)
            event.tech_notes = data.get('techNotes', event.tech_notes)
            
            db.session.commit()
            return jsonify({'success': True, 'event': event.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'DELETE':
        try:
            event = Event.query.get_or_404(event_id)
            db.session.delete(event)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Event deleted'})
        except Exception as e:
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
        return jsonify({'success': True, 'stats': {'total_events': 0, 'confirmed_events': 0, 'pending_events': 0, 'total_revenue': 0}})

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
        return jsonify({'success': True, 'analytics': {'monthly_revenue': [], 'revenue_by_type': []}})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
