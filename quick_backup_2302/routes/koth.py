"""
GUST Bot Enhanced - KOTH Event System
====================================
KOTH system that works with vanilla Rust servers
Uses only standard console commands available in all Rust servers
"""

# Standard library imports
from datetime import datetime
import logging
import threading
import time

# Utility imports
from utils.helpers import get_countdown_announcements

# Local imports
from config import Config




logger = logging.getLogger(__name__)

class VanillaKothSystem:
    """
    KOTH system that works with vanilla Rust servers
    Uses only standard console commands available in all Rust servers
    """
    
    def __init__(self, gust_bot):
        """
        Initialize KOTH system
        
        Args:
            gust_bot: Reference to main GUST bot instance
        """
        self.gust_bot = gust_bot
        self.active_events = {}
        
    def start_koth_event_fixed(self, event_data):
        """
        Start a KOTH event using only vanilla Rust commands
        
        Args:
            event_data (dict): Event configuration data
            
        Returns:
            bool: True if event started successfully
        """
        server_id = event_data['serverId']
        region = event_data.get('region', 'US')
        duration = event_data.get('duration', Config.KOTH_DEFAULT_DURATION)
        reward_item = event_data.get('reward_item', 'scrap')
        reward_amount = event_data.get('reward_amount', 1000)
        arena_location = event_data.get('arena_location', 'Launch Site')
        
        # Create event entry
        event_id = f"koth_{server_id}_{int(time.time())}"
        
        self.active_events[event_id] = {
            'server_id': server_id,
            'region': region,
            'start_time': datetime.now(),
            'duration_minutes': duration,
            'reward_item': reward_item,
            'reward_amount': reward_amount,
            'arena_location': arena_location,
            'phase': 'announcement',
            'winner': None
        }
        
        # Store in GUST bot's events list
        if hasattr(self.gust_bot, 'events'):
            self.gust_bot.events.append({
                'eventId': event_id,
                'type': 'koth',
                'serverId': server_id,
                'duration': duration,
                'reward': f"{reward_amount} {reward_item}",
                'status': 'active',
                'startTime': datetime.now().isoformat(),
                'arena_location': arena_location
            })
        
        # Start the event in a separate thread
        threading.Thread(target=self._run_koth_event_sequence, args=(event_id,), daemon=True).start()
        
        logger.info(f"ðŸŽ¯ KOTH event {event_id} started for server {server_id}")
        return True
    
    def _run_koth_event_sequence(self, event_id):
        """
        Run the complete KOTH event sequence
        
        Args:
            event_id (str): Event ID
        """
        event = self.active_events[event_id]
        
        try:
            logger.info(f"ðŸŽ¯ Starting KOTH event sequence: {event_id}")
            
            # Phase 1: Announcement and preparation (5 minutes)
            self._announcement_phase(event_id)
            
            # Phase 2: Active combat phase
            self._active_phase(event_id)
            
            # Phase 3: End event and rewards
            self._end_phase(event_id)
            
            logger.info(f"âœ… KOTH event completed successfully: {event_id}")
            
        except Exception as e:
            logger.error(f"âŒ Error in KOTH event {event_id}: {e}")
            self._emergency_end_event(event_id)
    
    def _announcement_phase(self, event_id):
        """
        Announcement phase - 5 minutes to prepare
        
        Args:
            event_id (str): Event ID
        """
        event = self.active_events[event_id]
        
        logger.info(f"ðŸ“¢ Starting announcement phase for {event_id}")
        
        # Initial announcement
        self._send_command(event, 
            f'global.say "<color=yellow><size=30>[KOTH EVENT]</size></color> '
            f'King of the Hill starting in 5 minutes at {event["arena_location"]}!"')
        
        time.sleep(2)
        
        self._send_command(event,
            f'global.say "<color=yellow>[KOTH]</color> Reward: {event["reward_amount"]} {event["reward_item"]} '
            f'for survivors!"')
        
        time.sleep(2)
        
        self._send_command(event,
            f'global.say "<color=yellow>[KOTH]</color> Duration: {event["duration_minutes"]} minutes. '
            f'Get to {event["arena_location"]} and prepare for battle!"')
        
        # Countdown announcements
        countdown_announcements = get_countdown_announcements()
        
        start_time = time.time()
        
        for delay, message in countdown_announcements:
            # Calculate when to send this announcement
            target_time = start_time + (Config.KOTH_PREPARATION_TIME - delay)
            
            # Wait until it's time
            current_time = time.time()
            if target_time > current_time:
                time.sleep(target_time - current_time)
            
            self._send_command(event,
                f'global.say "<color=red><size=25>[KOTH]</size></color> '
                f'Starting in {message}!"')
        
        event['phase'] = 'active'
        logger.info(f"âš”ï¸ Announcement phase completed for {event_id}")
    
    def _active_phase(self, event_id):
        """
        Active combat phase
        
        Args:
            event_id (str): Event ID
        """
        event = self.active_events[event_id]
        
        logger.info(f"âš”ï¸ Starting active phase for {event_id}")
        
        # Event starts
        self._send_command(event,
            f'global.say "<color=red><size=35>[KOTH EVENT STARTED!]</size></color> '
            f'Fight to be the last standing at {event["arena_location"]}!"')
        
        time.sleep(2)
        
        # Give basic combat supplies to all players
        self._send_command(event, 'global.say "<color=green>[KOTH]</color> Combat supplies distributed!"')
        
        supply_commands = [
            'giveall medical.bandage 5',
            'giveall ammo.pistol 60', 
            'giveall weapon.pistol.revolver 1'
        ]
        
        for cmd in supply_commands:
            self._send_command(event, cmd)
            time.sleep(1)
        
        # Monitor event duration
        duration_seconds = event['duration_minutes'] * 60
        elapsed = 0
        
        # Periodic announcements during event
        while elapsed < duration_seconds:
            time.sleep(30)  # Check every 30 seconds
            elapsed += 30
            
            remaining_minutes = (duration_seconds - elapsed) // 60
            remaining_seconds = (duration_seconds - elapsed) % 60
            
            # Announcement every 5 minutes
            if remaining_minutes > 0 and remaining_minutes % 5 == 0 and remaining_seconds == 0:
                self._send_command(event,
                    f'global.say "<color=yellow>[KOTH]</color> '
                    f'{remaining_minutes} minutes remaining! Stay alive at {event["arena_location"]}!"')
            
            # Final countdown
            elif remaining_minutes == 0 and remaining_seconds in [60, 30, 10, 5]:
                self._send_command(event,
                    f'global.say "<color=red>[KOTH]</color> '
                    f'{int(remaining_seconds)} seconds remaining!"')
        
        event['phase'] = 'finished'
        logger.info(f"ðŸ Active phase completed for {event_id}")
    
    def _end_phase(self, event_id):
        """
        End the event and determine winner
        
        Args:
            event_id (str): Event ID
        """
        event = self.active_events[event_id]
        
        logger.info(f"ðŸ† Starting end phase for {event_id}")
        
        self._send_command(event,
            f'global.say "<color=red><size=35>[KOTH EVENT ENDED!]</size></color> '
            f'Distributing rewards to survivors..."')
        
        time.sleep(3)
        
        # Give rewards to all players (in vanilla, we can't easily track location)
        reward_command = f'giveall {event["reward_item"]} {event["reward_amount"]}'
        self._send_command(event, reward_command)
        
        time.sleep(1)
        
        self._send_command(event,
            f'global.say "<color=gold><size=30>[KOTH REWARDS DISTRIBUTED!]</size></color> '
            f'All participants received {event["reward_amount"]} {event["reward_item"]}!"')
        
        # Clean up
        self._cleanup_event(event_id)
        logger.info(f"âœ… End phase completed for {event_id}")
    
    def _emergency_end_event(self, event_id):
        """
        Emergency cleanup if event fails
        
        Args:
            event_id (str): Event ID
        """
        logger.warning(f"ðŸš¨ Emergency ending event {event_id}")
        
        if event_id in self.active_events:
            event = self.active_events[event_id]
            self._send_command(event,
                'global.say "<color=red>[KOTH]</color> Event ended due to technical issues. Sorry!"')
            self._cleanup_event(event_id)
    
    def _cleanup_event(self, event_id):
        """
        Clean up event data
        
        Args:
            event_id (str): Event ID
        """
        if event_id in self.active_events:
            del self.active_events[event_id]
        
        # Remove from GUST bot events list
        if hasattr(self.gust_bot, 'events'):
            self.gust_bot.events = [e for e in self.gust_bot.events if e.get('eventId') != event_id]
        
        logger.info(f"ðŸ§¹ Cleaned up event {event_id}")
    
    def _send_command(self, event, command):
        """
        Send a command to the server
        
        Args:
            event (dict): Event data
            command (str): Console command to send
        """
        try:
            success = self.gust_bot.send_console_command_graphql(
                command, 
                event['server_id'], 
                event['region']
            )
            if not success:
                logger.warning(f"âŒ Failed to send command: {command}")
        except Exception as e:
            logger.error(f"âŒ Error sending command '{command}': {e}")
    
    def get_active_events(self):
        """
        Get list of active KOTH events
        
        Returns:
            list: List of active event data
        """
        return list(self.active_events.values())
    
    def stop_event(self, event_id):
        """
        Manually stop a KOTH event
        
        Args:
            event_id (str): Event ID to stop
            
        Returns:
            bool: True if event was stopped
        """
        if event_id in self.active_events:
            event = self.active_events[event_id]
            self._send_command(event,
                'global.say "<color=red>[KOTH]</color> Event manually stopped by administrator."')
            self._cleanup_event(event_id)
            logger.info(f"ðŸ›‘ Manually stopped event {event_id}")
            return True
        return False
    
    def get_event_status(self, event_id):
        """
        Get status of a specific event
        
        Args:
            event_id (str): Event ID
            
        Returns:
            dict or None: Event status data
        """
        if event_id in self.active_events:
            event = self.active_events[event_id].copy()
            # Add computed status
            event['elapsed_time'] = (datetime.now() - event['start_time']).total_seconds()
            event['is_active'] = event['phase'] in ['announcement', 'active']
            return event
        return None
    
    def get_events_for_server(self, server_id):
        """
        Get all active events for a specific server
        
        Args:
            server_id: Server ID
            
        Returns:
            list: List of events for the server
        """
        return [event for event in self.active_events.values() 
                if event['server_id'] == str(server_id)]
    
    def get_statistics(self):
        """
        Get KOTH system statistics
        
        Returns:
            dict: Statistics data
        """
        active_count = len(self.active_events)
        phases = {}
        
        for event in self.active_events.values():
            phase = event.get('phase', 'unknown')
            phases[phase] = phases.get(phase, 0) + 1
        
        return {
            "active_events": active_count,
            "phases": phases,
            "system_status": "operational",
            "vanilla_compatible": True
        }
