"""
GUST Bot Enhanced - Systems Package
==================================
Game systems and event management for GUST Bot

This package contains all game-related systems including:
- KOTH (King of the Hill) events system - vanilla Rust compatible
- Future systems can be added here (tournaments, raids, etc.)

All systems are designed to work with vanilla Rust servers without
requiring any plugins or modifications.
"""

import logging

# Import core systems
from .koth import VanillaKothSystem

# Package exports
__all__ = [
    'VanillaKothSystem',
    'get_systems_status',
    'get_available_systems',
    'SystemsManager'
]

# Package metadata
__version__ = "1.0.0"
__author__ = "GUST Bot Enhanced"
__description__ = "Game systems and event management for vanilla Rust servers"

# Set up logging for systems package
logger = logging.getLogger(__name__)

class SystemsManager:
    """
    Central manager for all game systems
    
    This class provides a unified interface for managing all game systems
    including KOTH events and any future systems that get added.
    """
    
    def __init__(self, gust_bot):
        """
        Initialize the systems manager
        
        Args:
            gust_bot: Reference to the main GUST bot instance
        """
        self.gust_bot = gust_bot
        self.systems = {}
        
        # Initialize available systems
        self._initialize_systems()
        
        logger.info("🎮 Systems Manager initialized")
    
    def _initialize_systems(self):
        """Initialize all available game systems"""
        try:
            # Initialize KOTH system
            self.systems['koth'] = VanillaKothSystem(self.gust_bot)
            logger.info("✅ KOTH system initialized")
            
            # Future systems can be added here
            # self.systems['tournaments'] = TournamentSystem(self.gust_bot)
            # self.systems['raids'] = RaidSystem(self.gust_bot)
            
        except Exception as e:
            logger.error(f"❌ Error initializing systems: {e}")
    
    def get_system(self, system_name):
        """
        Get a specific game system
        
        Args:
            system_name (str): Name of the system ('koth', etc.)
            
        Returns:
            System instance or None if not found
        """
        return self.systems.get(system_name)
    
    def get_koth_system(self):
        """
        Get the KOTH system instance
        
        Returns:
            VanillaKothSystem: The KOTH system instance
        """
        return self.systems.get('koth')
    
    def get_all_systems(self):
        """
        Get all initialized systems
        
        Returns:
            dict: Dictionary of all system instances
        """
        return self.systems.copy()
    
    def get_system_status(self, system_name):
        """
        Get status of a specific system
        
        Args:
            system_name (str): Name of the system
            
        Returns:
            dict: System status information
        """
        system = self.systems.get(system_name)
        if not system:
            return {
                'name': system_name,
                'available': False,
                'status': 'not_found'
            }
        
        if system_name == 'koth':
            return {
                'name': 'koth',
                'available': True,
                'status': 'operational',
                'active_events': len(system.get_active_events()),
                'vanilla_compatible': True,
                'features': [
                    'vanilla_rust_compatible',
                    'multiple_arenas',
                    'countdown_system',
                    'automatic_rewards',
                    'real_time_announcements'
                ]
            }
        
        return {
            'name': system_name,
            'available': True,
            'status': 'operational'
        }
    
    def get_all_system_status(self):
        """
        Get status of all systems
        
        Returns:
            dict: Status of all systems
        """
        return {
            name: self.get_system_status(name) 
            for name in self.systems.keys()
        }

def get_systems_status():
    """
    Get overview status of the systems package
    
    Returns:
        dict: Package status information
    """
    return {
        'package': 'systems',
        'version': __version__,
        'description': __description__,
        'available_systems': get_available_systems(),
        'total_systems': len(__all__) - 2,  # Exclude utility functions
        'koth_system': 'available',
        'vanilla_compatible': True,
        'features': {
            'koth_events': True,
            'vanilla_rust_support': True,
            'multi_arena_support': True,
            'countdown_system': True,
            'automatic_rewards': True,
            'real_time_announcements': True
        }
    }

def get_available_systems():
    """
    Get list of available game systems
    
    Returns:
        list: List of available system names
    """
    return [
        {
            'name': 'koth',
            'class': 'VanillaKothSystem',
            'description': 'King of the Hill events system',
            'compatible': 'vanilla_rust',
            'status': 'stable'
        }
        # Future systems would be added here
    ]

def create_systems_manager(gust_bot):
    """
    Factory function to create a systems manager instance
    
    Args:
        gust_bot: Reference to the main GUST bot instance
        
    Returns:
        SystemsManager: Configured systems manager
    """
    return SystemsManager(gust_bot)

# Convenience aliases for backward compatibility
def create_koth_system(gust_bot):
    """
    Create a KOTH system instance directly
    
    Args:
        gust_bot: Reference to the main GUST bot instance
        
    Returns:
        VanillaKothSystem: KOTH system instance
    """
    return VanillaKothSystem(gust_bot)

# System registry for dynamic system discovery
SYSTEM_REGISTRY = {
    'koth': {
        'class': VanillaKothSystem,
        'name': 'King of the Hill Events',
        'description': 'Vanilla Rust compatible KOTH event system',
        'version': '2.0.0',
        'compatible_servers': ['vanilla_rust'],
        'required_permissions': ['console_access'],
        'features': [
            'multi_arena_support',
            'countdown_announcements', 
            'automatic_rewards',
            'real_time_monitoring',
            'admin_controls'
        ]
    }
    # Future systems would be registered here
}

def get_system_registry():
    """
    Get the complete system registry
    
    Returns:
        dict: Complete system registry with all available systems
    """
    return SYSTEM_REGISTRY.copy()

def register_system(name, system_info):
    """
    Register a new system in the registry
    
    Args:
        name (str): System name
        system_info (dict): System information and metadata
    """
    SYSTEM_REGISTRY[name] = system_info
    logger.info(f"📝 Registered new system: {name}")

# Package initialization
logger.info("🎮 Systems package loaded successfully")
logger.info(f"📋 Available systems: {[s['name'] for s in get_available_systems()]}")