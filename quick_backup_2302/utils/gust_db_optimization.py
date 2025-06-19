"""
GUST Bot Practical Database Optimization
Focused on actual performance improvements for the GUST Discord bot
Updated with missing functions for Step 7 validation compliance
"""

import time
import logging
from functools import wraps
from typing import Dict, Any, Optional, Union
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
        self.server_cache = SimpleQueryCache(max_size=100, ttl=600)  # 10 minutes
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
    
    def cached_get_server_data(self, storage, server_id):
        """Get server data with caching"""
        cache_key = f"server_{server_id}"
        
        cached = self.server_cache.get(cache_key)
        if cached is not None:
            self.cache_hits += 1
            return cached
        
        self.cache_misses += 1
        start_time = time.time()
        
        try:
            if hasattr(storage, 'find_one'):
                # MongoDB-style
                result = storage.find_one({"serverId": server_id})
            elif isinstance(storage, dict):
                # In-memory dict-style
                result = storage.get(server_id)
            else:
                result = None
            
            query_time = time.time() - start_time
            self.query_times.append(query_time)
            
            # Cache result
            if result:
                self.server_cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Database error in cached_get_server_data: {e}")
            return None
    
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
    
    def invalidate_server_cache(self, server_id):
        """Clear server cache when server data changes"""
        cache_key = f"server_{server_id}"
        
        with self.server_cache.lock:
            self.server_cache.cache.pop(cache_key, None)
            self.server_cache.access_times.pop(cache_key, None)
    
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

def get_server_data_cached(storage, server_id):
    """Get server data with caching"""
    return gust_optimizer.cached_get_server_data(storage, server_id)

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

def adjust_server_balance(storage, server_id: str, adjustment: Union[int, float], operation_type: str = "adjustment") -> bool:
    """
    Adjust server balance by a specified amount - MISSING FUNCTION ADDED
    
    Args:
        storage: Database storage instance
        server_id: Server identifier
        adjustment: Amount to adjust (positive or negative)
        operation_type: Type of operation for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get current server data
        server_data = get_server_data_cached(storage, server_id)
        
        if server_data is None:
            # Create new server entry if it doesn't exist
            server_data = {
                "serverId": server_id,
                "balance": 0,
                "total_transactions": 0,
                "last_updated": time.time()
            }
        
        # Calculate new balance
        current_balance = server_data.get('balance', 0)
        new_balance = current_balance + adjustment
        
        # Ensure balance doesn't go negative (if desired)
        if new_balance < 0:
            logger.warning(f"Server {server_id} balance would go negative: {new_balance}")
            new_balance = 0
        
        # Update in storage
        if hasattr(storage, 'update_one'):
            # MongoDB-style
            result = storage.update_one(
                {"serverId": server_id},
                {
                    "$set": {
                        "balance": new_balance,
                        "last_updated": time.time()
                    },
                    "$inc": {"total_transactions": 1}
                },
                upsert=True
            )
            success = result.acknowledged
        elif isinstance(storage, dict):
            # In-memory dict-style
            storage[server_id] = {
                "serverId": server_id,
                "balance": new_balance,
                "total_transactions": server_data.get('total_transactions', 0) + 1,
                "last_updated": time.time()
            }
            success = True
        else:
            success = False
        
        # Invalidate cache on successful update
        if success:
            gust_optimizer.invalidate_server_cache(server_id)
            logger.info(f"Server {server_id} balance adjusted by {adjustment} ({operation_type}). New balance: {new_balance}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to adjust server balance for {server_id}: {e}")
        return False

def get_server_balance(storage, server_id: str) -> Union[int, float]:
    """
    Get server balance with caching
    
    Args:
        storage: Database storage instance
        server_id: Server identifier
    
    Returns:
        Union[int, float]: Server balance (0 if not found)
    """
    try:
        server_data = get_server_data_cached(storage, server_id)
        if server_data:
            return server_data.get('balance', 0)
        return 0
    except Exception as e:
        logger.error(f"Failed to get server balance for {server_id}: {e}")
        return 0

def transfer_between_servers(storage, from_server_id: str, to_server_id: str, amount: Union[int, float]) -> bool:
    """
    Transfer balance between servers
    
    Args:
        storage: Database storage instance
        from_server_id: Source server ID
        to_server_id: Destination server ID
        amount: Amount to transfer
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if amount <= 0:
            logger.error("Transfer amount must be positive")
            return False
        
        # Check source server balance
        source_balance = get_server_balance(storage, from_server_id)
        if source_balance < amount:
            logger.error(f"Insufficient balance in server {from_server_id}: {source_balance} < {amount}")
            return False
        
        # Perform transfer
        debit_success = adjust_server_balance(storage, from_server_id, -amount, "transfer_out")
        if debit_success:
            credit_success = adjust_server_balance(storage, to_server_id, amount, "transfer_in")
            if credit_success:
                logger.info(f"Successfully transferred {amount} from {from_server_id} to {to_server_id}")
                return True
            else:
                # Rollback debit if credit failed
                adjust_server_balance(storage, from_server_id, amount, "transfer_rollback")
                logger.error(f"Transfer failed: could not credit {to_server_id}")
                return False
        else:
            logger.error(f"Transfer failed: could not debit {from_server_id}")
            return False
            
    except Exception as e:
        logger.error(f"Transfer failed between {from_server_id} and {to_server_id}: {e}")
        return False

def bulk_update_user_balances(storage, updates: Dict[str, Union[int, float]], server_id: Optional[str] = None) -> Dict[str, bool]:
    """
    Update multiple user balances efficiently
    
    Args:
        storage: Database storage instance
        updates: Dictionary of {user_id: new_balance}
        server_id: Optional server ID for scoped updates
    
    Returns:
        Dict[str, bool]: Results for each user update
    """
    results = {}
    
    try:
        for user_id, new_balance in updates.items():
            try:
                success = update_user_balance(storage, user_id, new_balance, server_id)
                results[user_id] = success
            except Exception as e:
                logger.error(f"Failed to update balance for user {user_id}: {e}")
                results[user_id] = False
        
        successful_updates = sum(1 for success in results.values() if success)
        logger.info(f"Bulk update completed: {successful_updates}/{len(updates)} successful")
        
        return results
        
    except Exception as e:
        logger.error(f"Bulk update failed: {e}")
        return {user_id: False for user_id in updates.keys()}

@db_performance_monitor("optimization_health_check")
def perform_optimization_health_check() -> Dict[str, Any]:
    """
    Perform a health check on the optimization system
    
    Returns:
        Dict[str, Any]: Health check results
    """
    try:
        stats = gust_optimizer.get_stats()
        
        # Determine health status
        hit_rate = float(stats['cache_hit_rate'].replace('%', ''))
        avg_query_time = float(stats['avg_query_time'].replace('s', ''))
        
        health_status = "healthy"
        warnings = []
        
        if hit_rate < 30:
            health_status = "warning"
            warnings.append("Low cache hit rate")
        
        if avg_query_time > 0.1:
            health_status = "warning"
            warnings.append("High average query time")
        
        if stats['slow_queries'] > 10:
            health_status = "warning"
            warnings.append("Many slow queries detected")
        
        return {
            "status": health_status,
            "warnings": warnings,
            "statistics": stats,
            "cache_size": len(gust_optimizer.user_cache.cache),
            "server_cache_size": len(gust_optimizer.server_cache.cache),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "warnings": [f"Health check failed: {str(e)}"],
            "timestamp": time.time()
        }

def get_performance_report():
    """Get database performance report"""
    return gust_optimizer.get_stats()

def clear_all_caches():
    """Clear all caches - use with caution"""
    try:
        with gust_optimizer.user_cache.lock:
            gust_optimizer.user_cache.cache.clear()
            gust_optimizer.user_cache.access_times.clear()
        
        with gust_optimizer.server_cache.lock:
            gust_optimizer.server_cache.cache.clear()
            gust_optimizer.server_cache.access_times.clear()
        
        logger.info("All caches cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to clear caches: {e}")
        return False

# Create a global performance monitor instance for external access
db_performance_monitor = gust_optimizer

# Export commonly used functions for easy importing
__all__ = [
    'gust_optimizer',
    'db_performance_monitor', 
    'get_user_with_cache',
    'get_user_balance_cached',
    'get_server_data_cached',
    'update_user_balance',
    'adjust_server_balance',  # MISSING FUNCTION NOW INCLUDED
    'get_server_balance',
    'transfer_between_servers',
    'bulk_update_user_balances',
    'perform_optimization_health_check',
    'get_performance_report',
    'clear_all_caches'
]
