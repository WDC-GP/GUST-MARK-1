"""
"""
"""
GUST Bot Enhanced - Event Management Routes
==========================================
Routes for KOTH and other event management
"""

# Standard library imports
from datetime import datetime
import logging

# Third-party imports
from flask import Blueprint, request, jsonify

# Local imports
from routes.auth import require_auth


# GUST database optimization imports
from utils.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor
)



logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__)

def init_events_routes(app, db, events_storage, vanilla_koth, console_output):
    """
    Initialize event routes with dependencies
    
    Args:
        app: Flask app instance
        db: Database connection (optional)
        events_storage: In-memory events storage
        vanilla_koth: KOTH system instance
        console_output: Console output deque
    """
    
    @events_bp.route('/api/events/koth/start', methods=['POST'])
    @require_auth
    def start_koth_event():
        """Start KOTH event - FIXED VERSION"""
        try:
            data = request.json
            
            # Enhanced event data with vanilla-compatible settings
            event_config = {
                'serverId': data.get('serverId'),
                'region': data.get('region', 'US'),
                'duration': data.get('duration', 30),  # Default 30 minutes
                'reward_item': data.get('reward_item', 'scrap'),
                'reward_amount': data.get('reward_amount', 1000),
                'arena_location': data.get('arena_location', 'Launch Site'),
                'give_supplies': data.get('give_supplies', True)
            }
            
            if not event_config['serverId']:
                return jsonify({'success': False, 'error': 'Server ID required'})
            
            # Validate reward amount
            if event_config['reward_amount'] <= 0:
                return jsonify({'success': False, 'error': 'Invalid reward amount'})
            
            # Validate duration
            if event_config['duration'] <= 0 or event_config['duration'] > 180:
                return jsonify({'success': False, 'error': 'Duration must be between 1 and 180 minutes'})
            
            # Use the fixed KOTH system
            result = vanilla_koth.start_koth_event_fixed(event_config)
            
            if result:
                # Add to console output
                console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"ðŸŽ¯ KOTH Event started on server {event_config['serverId']} at {event_config['arena_location']}",
                    'status': 'event',
                    'source': 'event_system',
                    'type': 'event'
                })
                
                logger.info(f"ðŸŽ¯ KOTH event started: Server {event_config['serverId']}, Duration {event_config['duration']}m, Location {event_config['arena_location']}")
            else:
                logger.error(f"âŒ Failed to start KOTH event for server {event_config['serverId']}")
            
            return jsonify({'success': result})
            
        except Exception as e:
            logger.error(f"âŒ Error starting KOTH event: {e}")
            return jsonify({'success': False, 'error': 'Failed to start event'}), 500
    
    @events_bp.route('/api/events/koth/stop', methods=['POST'])
    @require_auth
    def stop_koth_event():
        """Stop KOTH event"""
        try:
            data = request.json
            event_id = data.get('eventId')
            
            if not event_id:
                return jsonify({'success': False, 'error': 'Event ID required'})
            
            result = vanilla_koth.stop_event(event_id)
            
            if result:
                console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"ðŸ›‘ KOTH Event {event_id} stopped manually",
                    'status': 'event',
                    'source': 'event_system',
                    'type': 'event'
                })
                logger.info(f"ðŸ›‘ KOTH event stopped manually: {event_id}")
            
            return jsonify({'success': result})
            
        except Exception as e:
            logger.error(f"âŒ Error stopping KOTH event: {e}")
            return jsonify({'success': False, 'error': 'Failed to stop event'}), 500
    
    @events_bp.route('/api/events')
    @require_auth
    def get_events():
        """Get active events"""
        try:
            events = []
            
            if db:
                events = list(db.events.find({'status': 'active'}, {'_id': 0}))
            else:
                events = [e for e in events_storage if e.get('status') == 'active']
            
            # Add KOTH system events
            koth_events = vanilla_koth.get_active_events()
            for koth_event in koth_events:
                events.append({
                    'eventId': f"koth_{koth_event['server_id']}_{int(koth_event['start_time'].timestamp())}",
                    'type': 'koth',
                    'serverId': koth_event['server_id'],
                    'duration': koth_event['duration_minutes'],
                    'reward': f"{koth_event['reward_amount']} {koth_event['reward_item']}",
                    'status': 'active',
                    'startTime': koth_event['start_time'].isoformat(),
                    'arena_location': koth_event['arena_location'],
                    'phase': koth_event['phase']
                })
            
            logger.info(f"ðŸ“‹ Retrieved {len(events)} active events")
            return jsonify(events)
            
        except Exception as e:
            logger.error(f"âŒ Error retrieving events: {e}")
            return jsonify({'error': 'Failed to retrieve events'}), 500
    
    @events_bp.route('/api/events/<event_id>')
    @require_auth
    def get_event(event_id):
        """Get specific event details"""
        try:
            # Check KOTH events first
            koth_status = vanilla_koth.get_event_status(event_id)
            if koth_status:
                return jsonify(koth_status)
            
            # Check database/storage events
            if db:
                event = db.events.find_one({'eventId': event_id}, {'_id': 0})
            else:
                event = next((e for e in events_storage if e.get('eventId') == event_id), None)
            
            if not event:
                return jsonify({'error': 'Event not found'}), 404
            
            return jsonify(event)
            
        except Exception as e:
            logger.error(f"âŒ Error retrieving event {event_id}: {e}")
            return jsonify({'error': 'Failed to retrieve event'}), 500
    
    @events_bp.route('/api/events/server/<server_id>')
    @require_auth
    def get_events_for_server(server_id):
        """Get all events for a specific server"""
        try:
            events = []
            
            # Get KOTH events for server
            koth_events = vanilla_koth.get_events_for_server(server_id)
            for koth_event in koth_events:
                events.append({
                    'eventId': f"koth_{koth_event['server_id']}_{int(koth_event['start_time'].timestamp())}",
                    'type': 'koth',
                    'serverId': koth_event['server_id'],
                    'duration': koth_event['duration_minutes'],
                    'reward': f"{koth_event['reward_amount']} {koth_event['reward_item']}",
                    'status': 'active',
                    'startTime': koth_event['start_time'].isoformat(),
                    'arena_location': koth_event['arena_location'],
                    'phase': koth_event['phase']
                })
            
            # Get other events from database/storage
            if db:
                db_events = list(db.events.find({'serverId': server_id, 'status': 'active'}, {'_id': 0}))
                events.extend(db_events)
            else:
                storage_events = [e for e in events_storage 
                                if e.get('serverId') == server_id and e.get('status') == 'active']
                events.extend(storage_events)
            
            logger.info(f"ðŸ“‹ Retrieved {len(events)} events for server {server_id}")
            return jsonify(events)
            
        except Exception as e:
            logger.error(f"âŒ Error retrieving events for server {server_id}: {e}")
            return jsonify({'error': 'Failed to retrieve server events'}), 500
    
    @events_bp.route('/api/events/stats')
    @require_auth
    def get_event_stats():
        """Get event system statistics"""
        try:
            # Get KOTH statistics
            koth_stats = vanilla_koth.get_statistics()
            
            # Get other event statistics
            total_events = len(events_storage)
            if db:
                total_events = db.events.count_documents({})
                active_events = db.events.count_documents({'status': 'active'})
            else:
                active_events = len([e for e in events_storage if e.get('status') == 'active'])
            
            stats = {
                'total_events': total_events,
                'active_events': active_events + koth_stats['active_events'],
                'koth_events': koth_stats['active_events'],
                'koth_phases': koth_stats['phases'],
                'system_status': 'operational',
                'features': {
                    'koth_fixed': True,
                    'vanilla_compatible': True,
                    'multiple_arenas': True,
                    'auto_rewards': True
                }
            }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"âŒ Error getting event stats: {e}")
            return jsonify({'error': 'Failed to get event statistics'}), 500
    
    @events_bp.route('/api/events/arena-locations')
    @require_auth
    def get_arena_locations():
        """Get available arena locations for KOTH events"""
        from config import Config
        
        return jsonify({
            'locations': Config.ARENA_LOCATIONS,
            'count': len(Config.ARENA_LOCATIONS),
            'default': 'Launch Site'
        })
    
    @events_bp.route('/api/events/templates')
    @require_auth
    def get_event_templates():
        """Get event templates for quick setup"""
        templates = [
            {
                'name': 'Quick KOTH (30m)',
                'type': 'koth',
                'duration': 30,
                'reward_item': 'scrap',
                'reward_amount': 1000,
                'arena_location': 'Launch Site',
                'description': 'Standard 30-minute KOTH event'
            },
            {
                'name': 'Long KOTH (60m)',
                'type': 'koth',
                'duration': 60,
                'reward_item': 'scrap',
                'reward_amount': 2000,
                'arena_location': 'Military Base',
                'description': 'Extended 60-minute KOTH event'
            },
            {
                'name': 'Epic KOTH (90m)',
                'type': 'koth',
                'duration': 90,
                'reward_item': 'scrap',
                'reward_amount': 3000,
                'arena_location': 'Nuclear Missile Silo',
                'description': 'Epic 90-minute KOTH event'
            },
            {
                'name': 'Resources KOTH',
                'type': 'koth',
                'duration': 45,
                'reward_item': 'metal.fragments',
                'reward_amount': 5000,
                'arena_location': 'Mining Outpost',
                'description': 'Resource-focused KOTH event'
            }
        ]
        
        return jsonify(templates)
    
    return events_bp

