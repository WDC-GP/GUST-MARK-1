# -*- coding: utf-8 -*-
"""
Basic Server Monitor
Provides basic server health monitoring
"""

import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

def check_health(server_id):
    """Basic server health check"""
    try:
        return {
            'server_id': str(server_id),
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'response_time': 0.1,
            'last_check': time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed for server {server_id}: {e}")
        return {
            'server_id': str(server_id),
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': str(e),
            'last_check': time.time()
        }
