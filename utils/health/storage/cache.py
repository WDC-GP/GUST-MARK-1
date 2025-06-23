"""
Intelligent Caching System for GUST-MARK-1 Server Health Storage System
========================================================================
✅ ENHANCED: High-performance caching with LRU eviction and TTL management
✅ OPTIMIZED: Multiple cache layers for different data types and access patterns
✅ INTELLIGENT: Adaptive TTL, cache warming, and invalidation strategies
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from collections import OrderedDict, defaultdict
import logging
import hashlib

logger = logging.getLogger(__name__)

class LRUCache:
    """
    ✅ OPTIMIZED: LRU Cache implementation with TTL support and thread safety
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """Initialize LRU cache with size limit and TTL"""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.ttl_values = {}
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with LRU update and TTL check"""
        with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            # Check TTL
            if self._is_expired(key):
                self._remove(key)
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        with self._lock:
            current_time = time.time()
            
            if key in self.cache:
                # Update existing
                self.cache[key] = value
                self.cache.move_to_end(key)
            else:
                # Add new
                self.cache[key] = value
                
                # Evict if necessary
                if len(self.cache) > self.max_size:
                    oldest = next(iter(self.cache))
                    self._remove(oldest)
                    self.evictions += 1
            
            # Set TTL
            self.timestamps[key] = current_time
            self.ttl_values[key] = ttl or self.default_ttl
    
    def invalidate(self, key: str) -> bool:
        """Remove specific key from cache"""
        with self._lock:
            if key in self.cache:
                self._remove(key)
                return True
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Remove all keys matching pattern"""
        with self._lock:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._remove(key)
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()
            self.ttl_values.clear()
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        with self._lock:
            expired_keys = [k for k in self.cache.keys() if self._is_expired(k)]
            for key in expired_keys:
                self._remove(key)
            return len(expired_keys)
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        
        age = time.time() - self.timestamps[key]
        ttl = self.ttl_values.get(key, self.default_ttl)
        return age > ttl
    
    def _remove(self, key: str) -> None:
        """Remove key from all cache structures"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        self.ttl_values.pop(key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_rate_percent': round(hit_rate, 2)
            }

class CacheManager:
    """
    ✅ ENHANCED: Multi-layered cache manager with intelligent caching strategies
    ✅ OPTIMIZED: Separate caches for different data types with optimal TTL values
    ✅ INTELLIGENT: Adaptive cache warming and invalidation patterns
    """
    
    def __init__(self):
        """Initialize multi-layered cache system"""
        # ✅ OPTIMIZED: Different cache layers for different data types
        self.health_cache = LRUCache(max_size=200, default_ttl=30)     # Health data (30s)
        self.command_cache = LRUCache(max_size=100, default_ttl=60)    # Commands (1min)
        self.trend_cache = LRUCache(max_size=50, default_ttl=120)      # Trends (2min)
        self.comprehensive_cache = LRUCache(max_size=50, default_ttl=30)  # Comprehensive (30s)
        self.metadata_cache = LRUCache(max_size=100, default_ttl=300)  # Metadata (5min)
        
        # ✅ NEW: Cache warming and preloading
        self.warm_cache_enabled = True
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        # ✅ ENHANCED: Cache statistics and monitoring
        self.cache_stats = {
            'total_hits': 0,
            'total_misses': 0,
            'cache_warming_hits': 0,
            'invalidations': 0,
            'cleanup_cycles': 0
        }
        
        # ✅ INTELLIGENT: Access pattern tracking
        self.access_patterns = defaultdict(int)
        self.popular_keys = set()
        
        logger.info("[Cache Manager] ✅ Initialized multi-layered cache system")
    
    # ===== HEALTH DATA CACHING =====
    
    def get_health_data(self, key: str) -> Optional[Any]:
        """Get health data from cache with pattern tracking"""
        try:
            result = self.health_cache.get(key)
            self._track_access(key, result is not None)
            return result
        except Exception as e:
            logger.error(f"[Cache Manager] Error getting health data for {key}: {e}")
            return None
    
    def set_health_data(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set health data in cache with intelligent TTL"""
        try:
            # ✅ INTELLIGENT: Adaptive TTL based on data type
            if ttl is None:
                ttl = self._calculate_adaptive_ttl(key, 'health')
            
            self.health_cache.set(key, value, ttl)
            self._mark_as_popular(key)
            logger.debug(f"[Cache Manager] ✅ Cached health data for {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"[Cache Manager] Error setting health data for {key}: {e}")
    
    def invalidate_health_cache(self, server_id: str) -> int:
        """Invalidate all health-related cache entries for a server"""
        try:
            pattern = f"health_{server_id}"
            invalidated = self.health_cache.invalidate_pattern(pattern)
            self.cache_stats['invalidations'] += invalidated
            
            if invalidated > 0:
                logger.debug(f"[Cache Manager] ✅ Invalidated {invalidated} health cache entries for {server_id}")
            
            return invalidated
        except Exception as e:
            logger.error(f"[Cache Manager] Error invalidating health cache for {server_id}: {e}")
            return 0
    
    # ===== COMMAND DATA CACHING =====
    
    def get_command_data(self, key: str) -> Optional[Any]:
        """Get command data from cache"""
        try:
            result = self.command_cache.get(key)
            self._track_access(key, result is not None)
            return result
        except Exception as e:
            logger.error(f"[Cache Manager] Error getting command data for {key}: {e}")
            return None
    
    def set_command_data(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set command data in cache"""
        try:
            if ttl is None:
                ttl = self._calculate_adaptive_ttl(key, 'command')
            
            self.command_cache.set(key, value, ttl)
            logger.debug(f"[Cache Manager] ✅ Cached command data for {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"[Cache Manager] Error setting command data for {key}: {e}")
    
    def invalidate_command_cache(self, server_id: str) -> int:
        """Invalidate command cache entries for a server"""
        try:
            pattern = f"commands_{server_id}"
            invalidated = self.command_cache.invalidate_pattern(pattern)
            self.cache_stats['invalidations'] += invalidated
            
            if invalidated > 0:
                logger.debug(f"[Cache Manager] ✅ Invalidated {invalidated} command cache entries for {server_id}")
            
            return invalidated
        except Exception as e:
            logger.error(f"[Cache Manager] Error invalidating command cache for {server_id}: {e}")
            return 0
    
    # ===== TREND DATA CACHING =====
    
    def get_trend_data(self, key: str) -> Optional[Any]:
        """Get trend data from cache"""
        try:
            result = self.trend_cache.get(key)
            self._track_access(key, result is not None)
            return result
        except Exception as e:
            logger.error(f"[Cache Manager] Error getting trend data for {key}: {e}")
            return None
    
    def set_trend_data(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set trend data in cache with longer TTL"""
        try:
            if ttl is None:
                ttl = self._calculate_adaptive_ttl(key, 'trend', default=120)
            
            self.trend_cache.set(key, value, ttl)
            logger.debug(f"[Cache Manager] ✅ Cached trend data for {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"[Cache Manager] Error setting trend data for {key}: {e}")
    
    def invalidate_trend_cache(self, server_id: str) -> int:
        """Invalidate trend cache entries for a server"""
        try:
            pattern = f"trends_{server_id}"
            invalidated = self.trend_cache.invalidate_pattern(pattern)
            self.cache_stats['invalidations'] += invalidated
            
            if invalidated > 0:
                logger.debug(f"[Cache Manager] ✅ Invalidated {invalidated} trend cache entries for {server_id}")
            
            return invalidated
        except Exception as e:
            logger.error(f"[Cache Manager] Error invalidating trend cache for {server_id}: {e}")
            return 0
    
    # ===== COMPREHENSIVE DATA CACHING =====
    
    def get_comprehensive_data(self, key: str) -> Optional[Any]:
        """Get comprehensive data from cache"""
        try:
            result = self.comprehensive_cache.get(key)
            self._track_access(key, result is not None)
            
            # ✅ INTELLIGENT: Trigger cache warming for popular keys
            if result is None and key in self.popular_keys:
                self._maybe_warm_cache(key)
            
            return result
        except Exception as e:
            logger.error(f"[Cache Manager] Error getting comprehensive data for {key}: {e}")
            return None
    
    def set_comprehensive_data(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set comprehensive data in cache"""
        try:
            if ttl is None:
                ttl = self._calculate_adaptive_ttl(key, 'comprehensive')
            
            self.comprehensive_cache.set(key, value, ttl)
            self._mark_as_popular(key)
            logger.debug(f"[Cache Manager] ✅ Cached comprehensive data for {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"[Cache Manager] Error setting comprehensive data for {key}: {e}")
    
    def invalidate_comprehensive_cache(self, server_id: str) -> int:
        """Invalidate comprehensive cache entries for a server"""
        try:
            pattern = f"comprehensive_{server_id}"
            invalidated = self.comprehensive_cache.invalidate_pattern(pattern)
            self.cache_stats['invalidations'] += invalidated
            
            if invalidated > 0:
                logger.debug(f"[Cache Manager] ✅ Invalidated {invalidated} comprehensive cache entries for {server_id}")
            
            return invalidated
        except Exception as e:
            logger.error(f"[Cache Manager] Error invalidating comprehensive cache for {server_id}: {e}")
            return 0
    
    # ===== METADATA CACHING =====
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """Get metadata from cache"""
        try:
            result = self.metadata_cache.get(key)
            self._track_access(key, result is not None)
            return result
        except Exception as e:
            logger.error(f"[Cache Manager] Error getting metadata for {key}: {e}")
            return None
    
    def set_metadata(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set metadata in cache with long TTL"""
        try:
            if ttl is None:
                ttl = 300  # 5 minutes for metadata
            
            self.metadata_cache.set(key, value, ttl)
            logger.debug(f"[Cache Manager] ✅ Cached metadata for {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"[Cache Manager] Error setting metadata for {key}: {e}")
    
    # ===== INTELLIGENT CACHING FEATURES =====
    
    def _calculate_adaptive_ttl(self, key: str, data_type: str, default: int = 30) -> int:
        """✅ INTELLIGENT: Calculate adaptive TTL based on access patterns"""
        try:
            # Base TTL values
            base_ttls = {
                'health': 30,      # Health data changes frequently
                'command': 60,     # Commands change less frequently
                'trend': 120,      # Trends are expensive to calculate
                'comprehensive': 30,  # Comprehensive data changes frequently
                'metadata': 300    # Metadata rarely changes
            }
            
            base_ttl = base_ttls.get(data_type, default)
            
            # ✅ ADAPTIVE: Increase TTL for popular keys (cache longer)
            if key in self.popular_keys:
                return min(base_ttl * 2, 300)  # Max 5 minutes
            
            # ✅ ADAPTIVE: Decrease TTL for rarely accessed keys
            access_count = self.access_patterns.get(key, 0)
            if access_count < 2:
                return max(base_ttl // 2, 10)  # Min 10 seconds
            
            return base_ttl
            
        except Exception as e:
            logger.error(f"[Cache Manager] Error calculating adaptive TTL: {e}")
            return default
    
    def _track_access(self, key: str, was_hit: bool) -> None:
        """Track cache access patterns for intelligence"""
        try:
            self.access_patterns[key] += 1
            
            if was_hit:
                self.cache_stats['total_hits'] += 1
            else:
                self.cache_stats['total_misses'] += 1
            
            # ✅ INTELLIGENT: Mark frequently accessed keys as popular
            if self.access_patterns[key] >= 5:
                self.popular_keys.add(key)
                
        except Exception as e:
            logger.error(f"[Cache Manager] Error tracking access for {key}: {e}")
    
    def _mark_as_popular(self, key: str) -> None:
        """Mark a key as popular for better caching"""
        try:
            self.popular_keys.add(key)
            self.access_patterns[key] += 1
        except Exception as e:
            logger.error(f"[Cache Manager] Error marking {key} as popular: {e}")
    
    def _maybe_warm_cache(self, key: str) -> None:
        """✅ INTELLIGENT: Trigger cache warming for popular missed keys"""
        try:
            if not self.warm_cache_enabled:
                return
            
            # This would trigger a background refresh of the data
            # Implementation depends on the calling system
            logger.debug(f"[Cache Manager] 🔥 Cache warming triggered for popular key: {key}")
            self.cache_stats['cache_warming_hits'] += 1
            
        except Exception as e:
            logger.error(f"[Cache Manager] Error warming cache for {key}: {e}")
    
    # ===== CACHE VALIDATION AND MAINTENANCE =====
    
    def is_valid(self, key: str, cache_type: str = 'health') -> bool:
        """✅ PRESERVED: Check if cache entry is valid (backward compatibility)"""
        try:
            cache_map = {
                'health': self.health_cache,
                'command': self.command_cache,
                'trend': self.trend_cache,
                'comprehensive': self.comprehensive_cache,
                'metadata': self.metadata_cache
            }
            
            cache = cache_map.get(cache_type, self.health_cache)
            result = cache.get(key)
            return result is not None
            
        except Exception as e:
            logger.error(f"[Cache Manager] Error checking cache validity for {key}: {e}")
            return False
    
    def cleanup_expired_entries(self) -> Dict[str, int]:
        """Clean up expired entries from all caches"""
        try:
            cleanup_stats = {}
            
            cleanup_stats['health'] = self.health_cache.cleanup_expired()
            cleanup_stats['command'] = self.command_cache.cleanup_expired()
            cleanup_stats['trend'] = self.trend_cache.cleanup_expired()
            cleanup_stats['comprehensive'] = self.comprehensive_cache.cleanup_expired()
            cleanup_stats['metadata'] = self.metadata_cache.cleanup_expired()
            
            total_cleaned = sum(cleanup_stats.values())
            if total_cleaned > 0:
                logger.info(f"[Cache Manager] ✅ Cleaned up {total_cleaned} expired entries")
            
            self.cache_stats['cleanup_cycles'] += 1
            self.last_cleanup = time.time()
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"[Cache Manager] Error during cleanup: {e}")
            return {'error': str(e)}
    
    def force_cleanup_all(self) -> Dict[str, Any]:
        """Force cleanup of all caches"""
        try:
            cleanup_stats = self.cleanup_expired_entries()
            
            # Also clean up access patterns for unused keys
            active_keys = set()
            for cache in [self.health_cache, self.command_cache, self.trend_cache, 
                         self.comprehensive_cache, self.metadata_cache]:
                active_keys.update(cache.cache.keys())
            
            # Remove access patterns for non-existent keys
            pattern_keys_to_remove = [k for k in self.access_patterns.keys() if k not in active_keys]
            for key in pattern_keys_to_remove:
                del self.access_patterns[key]
            
            # Update popular keys
            self.popular_keys = {k for k in self.popular_keys if k in active_keys}
            
            cleanup_stats['patterns_cleaned'] = len(pattern_keys_to_remove)
            cleanup_stats['popular_keys_updated'] = len(self.popular_keys)
            
            logger.info(f"[Cache Manager] ✅ Force cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"[Cache Manager] Error during force cleanup: {e}")
            return {'error': str(e)}
    
    def invalidate_all_server_caches(self, server_id: str) -> Dict[str, int]:
        """Invalidate all cache entries for a specific server"""
        try:
            invalidation_stats = {}
            
            invalidation_stats['health'] = self.invalidate_health_cache(server_id)
            invalidation_stats['command'] = self.invalidate_command_cache(server_id)
            invalidation_stats['trend'] = self.invalidate_trend_cache(server_id)
            invalidation_stats['comprehensive'] = self.invalidate_comprehensive_cache(server_id)
            
            total_invalidated = sum(invalidation_stats.values())
            if total_invalidated > 0:
                logger.info(f"[Cache Manager] ✅ Invalidated {total_invalidated} cache entries for {server_id}")
            
            return invalidation_stats
            
        except Exception as e:
            logger.error(f"[Cache Manager] Error invalidating server caches for {server_id}: {e}")
            return {'error': str(e)}
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            stats = {
                'cache_layers': {
                    'health': self.health_cache.get_stats(),
                    'command': self.command_cache.get_stats(),
                    'trend': self.trend_cache.get_stats(),
                    'comprehensive': self.comprehensive_cache.get_stats(),
                    'metadata': self.metadata_cache.get_stats()
                },
                'global_stats': self.cache_stats.copy(),
                'intelligence': {
                    'popular_keys_count': len(self.popular_keys),
                    'tracked_patterns': len(self.access_patterns),
                    'cache_warming_enabled': self.warm_cache_enabled
                },
                'maintenance': {
                    'last_cleanup': self.last_cleanup,
                    'cleanup_interval': self.cleanup_interval
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Calculate overall hit rate
            total_hits = sum(layer['hits'] for layer in stats['cache_layers'].values())
            total_misses = sum(layer['misses'] for layer in stats['cache_layers'].values())
            total_requests = total_hits + total_misses
            
            if total_requests > 0:
                stats['overall_hit_rate_percent'] = round((total_hits / total_requests) * 100, 2)
            else:
                stats['overall_hit_rate_percent'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"[Cache Manager] Error getting comprehensive stats: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform cache system health check"""
        try:
            start_time = time.time()
            
            # Test basic operations on each cache
            test_key = f"health_check_{int(time.time())}"
            test_value = {'test': True, 'timestamp': datetime.utcnow().isoformat()}
            
            # Test each cache layer
            cache_health = {}
            for name, cache in [
                ('health', self.health_cache),
                ('command', self.command_cache),
                ('trend', self.trend_cache),
                ('comprehensive', self.comprehensive_cache),
                ('metadata', self.metadata_cache)
            ]:
                try:
                    # Test set and get
                    cache.set(test_key, test_value, ttl=5)
                    retrieved = cache.get(test_key)
                    cache.invalidate(test_key)
                    
                    cache_health[name] = {
                        'status': 'healthy' if retrieved is not None else 'unhealthy',
                        'size': len(cache.cache)
                    }
                except Exception as e:
                    cache_health[name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Overall health determination
            unhealthy_caches = [name for name, health in cache_health.items() 
                              if health['status'] != 'healthy']
            
            overall_status = 'healthy' if not unhealthy_caches else 'degraded'
            
            return {
                'status': overall_status,
                'response_time_ms': round(response_time, 2),
                'cache_layers': cache_health,
                'unhealthy_caches': unhealthy_caches,
                'overall_hit_rate': self.get_comprehensive_stats().get('overall_hit_rate_percent', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
