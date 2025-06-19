"""
GUST Bot Practical Database Optimization
Focused on actual performance improvements for the GUST Discord bot
"""

import time
import logging
from functools import wraps
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)

class SimpleQueryCache:
    """Lightweight caching for frequently accessed data"""
    
    def __init__(self, max_size=500, ttl=300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.Lock()
    
    def get(self, key):
        """Get cached result if still valid"""
        with self.lock:
            if key in self.cache:
                if time.time() - self.access_times[key] < self.ttl:
                    return self.cache[key]
                else:
                    # Expired
                    del self.cache[key]
                    del self.access_times[key]
            return None
    
    def set(self, key, value):
        """Cache a result"""
        with self.lock:
            # Simple eviction - remove oldest if at capacity
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()

class GustDbOptimizer:
    """Practical database optimization for GUST Bot operations"""
    
    def __init__(self):
        self.user_cache = SimpleQueryCache(max_size=200, ttl=300)  # 5 minutes
        self.query_times = []
        self.cache_hits = 0
        self.cache_misses = 0
    
    def cached_get_user(self, storage, user_id, server_id=None):
        """Get user with simple caching - most common operation"""
        cache_key = f"user_{user_id}_{server_id}" if server_id else f"user_{user_id}"
        
        # Try cache first
        cached = self.user_cache.get(cache_key)
        if cached is not None:
            self.cache_hits += 1
            return cached
        
        # Get from storage
        self.cache_misses += 1
        start_time = time.time()
        
        try:
            if hasattr(storage, 'find_one'):
                # MongoDB-style
                query = {"userId": user_id}
                if server_id:
                    query["serverId"] = server_id
                result = storage.find_one(query)
            elif isinstance(storage, dict):
                # In-memory dict-style
                result = storage.get(user_id)
            else:
                # Other storage types
                result = None
            
            query_time = time.time() - start_time
            self.query_times.append(query_time)
            
            # Cache successful results
            if result:
                self.user_cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Database error in cached_get_user: {e}")
            return None
    
    def cached_get_user_balance(self, storage, user_id, server_id=None):
        """Get user balance with caching - very common operation"""
        cache_key = f"balance_{user_id}_{server_id}" if server_id else f"balance_{user_id}"
        
        cached = self.user_cache.get(cache_key)
        if cached is not None:
            self.cache_hits += 1
            return cached
        
        self.cache_misses += 1
        user = self.cached_get_user(storage, user_id, server_id)
        
        if user:
            balance = user.get('balance', 0) if isinstance(user, dict) else getattr(user, 'balance', 0)
            self.user_cache.set(cache_key, balance)
            return balance
        
        return 0
    
    def invalidate_user_cache(self, user_id, server_id=None):
        """Clear cache when user data changes"""
        cache_keys = [
            f"user_{user_id}_{server_id}" if server_id else f"user_{user_id}",
            f"balance_{user_id}_{server_id}" if server_id else f"balance_{user_id}"
        ]
        
        with self.user_cache.lock:
            for key in cache_keys:
                self.user_cache.cache.pop(key, None)
                self.user_cache.access_times.pop(key, None)
    
    def get_stats(self):
        """Get simple performance statistics"""
        total_queries = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_queries * 100) if total_queries > 0 else 0
        avg_query_time = sum(self.query_times) / len(self.query_times) if self.query_times else 0
        
        return {
            'cache_hit_rate': f"{hit_rate:.1f}%",
            'total_queries': total_queries,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'avg_query_time': f"{avg_query_time:.4f}s",
            'slow_queries': len([t for t in self.query_times if t > 0.1])
        }

# Global optimizer instance
gust_optimizer = GustDbOptimizer()

def db_performance_monitor(operation_name):
    """Simple decorator to monitor database operation performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log slow operations only
                if execution_time > 0.05:  # 50ms threshold
                    logger.info(f"Slow DB operation {operation_name}: {execution_time:.3f}s")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"DB operation {operation_name} failed after {execution_time:.3f}s: {e}")
                raise
        return wrapper
    return decorator

# Practical helper functions for GUST Bot
def get_user_with_cache(storage, user_id, server_id=None):
    """Get user profile with caching - replaces direct storage calls"""
    return gust_optimizer.cached_get_user(storage, user_id, server_id)

def get_user_balance_cached(storage, user_id, server_id=None):
    """Get user balance with caching - for economy operations"""
    return gust_optimizer.cached_get_user_balance(storage, user_id, server_id)

def update_user_balance(storage, user_id, new_balance, server_id=None):
    """Update user balance and invalidate cache"""
    try:
        # Update in storage
        if hasattr(storage, 'update_one'):
            # MongoDB-style
            query = {"userId": user_id}
            if server_id:
                query["serverId"] = server_id
            result = storage.update_one(query, {"$set": {"balance": new_balance}})
            success = result.modified_count > 0
        elif isinstance(storage, dict):
            # In-memory dict-style
            if server_id:
                if user_id not in storage:
                    storage[user_id] = {}
                storage[user_id]['balance'] = new_balance
            else:
                storage[user_id] = new_balance
            success = True
        else:
            success = False
        
        # Invalidate cache on successful update
        if success:
            gust_optimizer.invalidate_user_cache(user_id, server_id)
        
        return success
    except Exception as e:
        logger.error(f"Failed to update user balance: {e}")
        return False

def get_performance_report():
    """Get database performance report"""
    return gust_optimizer.get_stats()
