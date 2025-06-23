"""
GUST Bot Utils Package - Full Backwards Compatibility
====================================================
All imports work through both old and new paths.
"""

# Core utilities - primary imports
try:
    from .core.helpers import *
except ImportError as e:
    print(f"Warning: Could not import core helpers: {e}")

# Authentication
try:
    from .auth.auth_helpers import *
    from .auth.auth_decorators import *
    from .auth.credential_manager import *
    from .auth.token_manager import *
except ImportError as e:
    print(f"Warning: Could not import auth modules: {e}")

# Data processing
try:
    from .data.data_helpers import *
    from .data.validation_helpers import *
except ImportError as e:
    print(f"Warning: Could not import data modules: {e}")

# Console operations
try:
    from .console.console_helpers import *
except ImportError as e:
    print(f"Warning: Could not import console modules: {e}")

# Database operations
try:
    from .database.db_helpers import *
    from .database.user_helpers import *
    from .database.user_migration import *
    from .database.gust_db_optimization import *
except ImportError as e:
    print(f"Warning: Could not import database modules: {e}")

# Health monitoring
try:
    from .health import *
    from .health.server_monitor import *
    from .health.graphql_sensors import *
    from .health.server_health_storage import *
except ImportError as e:
    print(f"Warning: Could not import health modules: {e}")

# Core utilities for backwards compatibility
try:
    from .core.rate_limiter import *
    from .core.error_handlers import *
    from .core.common_imports import *
except ImportError as e:
    print(f"Warning: Could not import core utilities: {e}")

__version__ = "2.0.2"
__description__ = "GUST Bot utilities - full backwards compatibility"

import logging
logger = logging.getLogger(__name__)
logger.info("✅ GUST Utils v2.0.2 loaded with full backwards compatibility")
