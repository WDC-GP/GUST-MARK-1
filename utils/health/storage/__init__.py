"""
Storage Package Initialization for GUST-MARK-1 Server Health Storage System
============================================================================
✅ NEW: Storage subdirectory within existing utils/health/ package
✅ PRESERVED: Backward compatibility through proper exports
✅ ENHANCED: Modular storage architecture with clean separation of concerns
"""

# Import storage classes from specialized modules
from .base import ServerHealthStorage
from .mongodb import MongoHealthStorage 
from .memory import MemoryHealthStorage
from .cache import CacheManager
from .models import HealthMetric, CommandExecution, HealthSnapshot, TrendData
from .queries import QueryBuilder, HealthQueryManager

# Export main storage interface for backward compatibility
__all__ = [
    'ServerHealthStorage',  # Main interface - maintains existing API
    'MongoHealthStorage',   # MongoDB-specific operations
    'MemoryHealthStorage',  # In-memory storage operations
    'CacheManager',         # Intelligent caching system
    'HealthMetric',         # Data model for health metrics
    'CommandExecution',     # Data model for command tracking
    'HealthSnapshot',       # Data model for snapshots
    'TrendData',            # Data model for trend analysis
    'QueryBuilder',         # Query optimization utilities
    'HealthQueryManager'    # Aggregated query management
]

# Version information
__version__ = '2.0.0'
__description__ = 'Optimized modular storage system for GUST-MARK-1 server health monitoring'

# Initialize storage subsystem logging
import logging
logger = logging.getLogger(__name__)
logger.info("[Storage Package] Initialized optimized storage modules")
