"""
Query Optimization and Management for GUST-MARK-1 Server Health Storage System
===============================================================================
✅ ENHANCED: Optimized query builders and aggregation pipelines
✅ PRESERVED: All existing query patterns and result formats
✅ OPTIMIZED: Performance-focused query strategies with intelligent fallbacks
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from .models import HealthMetric, CommandExecution, HealthSnapshot, TrendData

logger = logging.getLogger(__name__)

class QueryBuilder:
    """
    ✅ OPTIMIZED: Advanced query builder with MongoDB aggregation and memory query support
    """
    
    def __init__(self):
        """Initialize query builder"""
        self.query_cache = {}
        self.performance_stats = {
            'queries_executed': 0,
            'total_execution_time': 0,
            'cached_queries': 0
        }
    
    def build_health_trends_query(self, server_id: str, hours: int = 6) -> Dict[str, Any]:
        """Build optimized MongoDB aggregation pipeline for health trends"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            # Stage 1: Match documents
            {
                "$match": {
                    "server_id": server_id,
                    "timestamp": {"$gte": cutoff_time}
                }
            },
            # Stage 2: Sort by timestamp
            {
                "$sort": {"timestamp": 1}
            },
            # Stage 3: Project only needed fields
            {
                "$project": {
                    "_id": 0,
                    "timestamp": 1,
                    "health_data.statistics.fps": 1,
                    "health_data.statistics.memory_usage": 1,
                    "health_data.statistics.cpu_usage": 1,
                    "health_data.statistics.player_count": 1,
                    "health_data.statistics.response_time": 1,
                    "health_percentage": 1,
                    "data_quality": 1
                }
            },
            # Stage 4: Limit results for performance
            {
                "$limit": 100
            }
        ]
        
        return {
            'type': 'aggregation',
            'pipeline': pipeline,
            'collection': 'server_health_snapshots'
        }
    
    def build_command_history_query(self, server_id: str, hours: int = 24, 
                                   command_type: Optional[str] = None) -> Dict[str, Any]:
        """Build optimized query for command history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Base query
        query = {
            "server_id": server_id,
            "timestamp": {"$gte": cutoff_time}
        }
        
        # Add command type filter if specified
        if command_type:
            query["command_type"] = command_type
        
        return {
            'type': 'find',
            'query': query,
            'sort': [("timestamp", DESCENDING)],
            'limit': 1000,
            'collection': 'server_health_commands'
        }
    
    def build_performance_summary_query(self, server_id: str, hours: int = 24) -> Dict[str, Any]:
        """Build aggregation query for performance summary"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            # Match recent documents
            {
                "$match": {
                    "server_id": server_id,
                    "timestamp": {"$gte": cutoff_time}
                }
            },
            # Group by metric type and calculate statistics
            {
                "$group": {
                    "_id": "$metric_type",
                    "avg_value": {"$avg": "$metric_value"},
                    "min_value": {"$min": "$metric_value"},
                    "max_value": {"$max": "$metric_value"},
                    "count": {"$sum": 1},
                    "latest_timestamp": {"$max": "$timestamp"}
                }
            },
            # Sort by metric type
            {
                "$sort": {"_id": 1}
            }
        ]
        
        return {
            'type': 'aggregation',
            'pipeline': pipeline,
            'collection': 'server_performance_metrics'
        }
    
    def build_server_summary_query(self, server_id: str) -> List[Dict[str, Any]]:
        """Build multiple queries for comprehensive server summary"""
        queries = []
        
        # Latest health snapshot
        queries.append({
            'name': 'latest_snapshot',
            'type': 'find',
            'query': {"server_id": server_id},
            'sort': [("timestamp", DESCENDING)],
            'limit': 1,
            'collection': 'server_health_snapshots'
        })
        
        # Recent command count
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        queries.append({
            'name': 'recent_commands',
            'type': 'count',
            'query': {
                "server_id": server_id,
                "timestamp": {"$gte": recent_cutoff}
            },
            'collection': 'server_health_commands'
        })
        
        # Health trend over last 6 hours
        queries.append({
            'name': 'health_trend',
            **self.build_health_trends_query(server_id, 6)
        })
        
        return queries
    
    def build_memory_filter_query(self, server_id: str, hours: int = 24) -> Dict[str, Any]:
        """Build query for in-memory storage filtering"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        return {
            'server_id': server_id,
            'time_cutoff': cutoff_str,
            'max_results': 1000
        }

class HealthQueryManager:
    """
    ✅ ENHANCED: Comprehensive query manager that coordinates MongoDB and memory storage
    ✅ OPTIMIZED: Intelligent query routing, caching, and fallback strategies
    ✅ PRESERVED: All existing query interfaces and result formats
    """
    
    def __init__(self, mongo_storage=None, memory_storage=None):
        """Initialize query manager with storage backends"""
        self.mongo_storage = mongo_storage
        self.memory_storage = memory_storage
        self.query_builder = QueryBuilder()
        
        # Performance tracking
        self.query_stats = {
            'mongodb_queries': 0,
            'memory_queries': 0,
            'combined_queries': 0,
            'fallback_queries': 0,
            'total_query_time': 0
        }
        
        logger.info("[Query Manager] ✅ Initialized with storage backends")
    
    # ===== HEALTH TRENDS QUERIES =====
    
    def get_health_trends(self, server_id: str, hours: int = 6) -> Dict[str, Any]:
        """
        ✅ OPTIMIZED: Get health trends with intelligent storage routing
        ✅ PRESERVED: Exact same return format as original system
        """
        start_time = time.time()
        
        try:
            logger.debug(f"[Query Manager] Getting health trends for {server_id} ({hours}h)")
            
            # Try MongoDB first (preferred for historical data)
            if self.mongo_storage:
                mongo_result = self._get_trends_from_mongodb(server_id, hours)
                if mongo_result.get('success'):
                    self._update_query_stats('mongodb_queries', start_time)
                    logger.debug(f"[Query Manager] ✅ MongoDB trends for {server_id}")
                    return mongo_result
            
            # Fallback to memory storage
            if self.memory_storage:
                memory_result = self._get_trends_from_memory(server_id, hours)
                if memory_result.get('success'):
                    self._update_query_stats('memory_queries', start_time)
                    logger.debug(f"[Query Manager] ✅ Memory trends for {server_id}")
                    return memory_result
            
            # No data available
            self._update_query_stats('fallback_queries', start_time)
            logger.warning(f"[Query Manager] No trend data available for {server_id}")
            return {'success': False, 'error': 'no_data_available'}
            
        except Exception as e:
            self._update_query_stats('fallback_queries', start_time)
            logger.error(f"[Query Manager] Error getting trends for {server_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_trends_from_mongodb(self, server_id: str, hours: int) -> Dict[str, Any]:
        """Get trends from MongoDB using optimized aggregation"""
        try:
            query_def = self.query_builder.build_health_trends_query(server_id, hours)
            result = self.mongo_storage.get_health_trends_aggregated(server_id, hours)
            
            if result.get('success'):
                return {
                    'success': True,
                    'charts': result['trends'],
                    'source': 'mongodb',
                    'data_points': result.get('count', 0)
                }
            else:
                return {'success': False, 'error': result.get('error', 'mongodb_query_failed')}
                
        except Exception as e:
            logger.error(f"[Query Manager] MongoDB trends error: {e}")
            return {'success': False, 'error': f'mongodb_error: {e}'}
    
    def _get_trends_from_memory(self, server_id: str, hours: int) -> Dict[str, Any]:
        """Get trends from memory storage"""
        try:
            result = self.memory_storage.get_health_trends_data(server_id, hours)
            
            if result.get('success'):
                return {
                    'success': True,
                    'charts': result['trends'],
                    'source': 'memory',
                    'data_points': result.get('count', 0)
                }
            else:
                return {'success': False, 'error': result.get('error', 'memory_query_failed')}
                
        except Exception as e:
            logger.error(f"[Query Manager] Memory trends error: {e}")
            return {'success': False, 'error': f'memory_error: {e}'}
    
    # ===== COMMAND HISTORY QUERIES =====
    
    def get_command_history(self, server_id: str, hours: int = 24, 
                           command_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        ✅ OPTIMIZED: Get command history with intelligent storage routing
        ✅ PRESERVED: Exact same return format as original system
        """
        start_time = time.time()
        
        try:
            logger.debug(f"[Query Manager] Getting command history for {server_id} ({hours}h, type: {command_type})")
            
            commands = []
            
            # Try MongoDB first
            if self.mongo_storage:
                mongo_commands = self._get_commands_from_mongodb(server_id, hours, command_type)
                if mongo_commands:
                    commands.extend(mongo_commands)
                    self._update_query_stats('mongodb_queries', start_time)
                    logger.debug(f"[Query Manager] ✅ Got {len(mongo_commands)} commands from MongoDB")
            
            # Supplement with memory storage if needed
            if self.memory_storage and len(commands) < 50:  # Fill gaps
                memory_commands = self._get_commands_from_memory(server_id, hours, command_type)
                if memory_commands:
                    # Merge and deduplicate
                    commands = self._merge_command_lists(commands, memory_commands)
                    self._update_query_stats('combined_queries', start_time)
                    logger.debug(f"[Query Manager] ✅ Combined with {len(memory_commands)} memory commands")
            
            # Sort by timestamp (most recent first)
            commands.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return commands[:1000]  # Limit results
            
        except Exception as e:
            self._update_query_stats('fallback_queries', start_time)
            logger.error(f"[Query Manager] Error getting command history for {server_id}: {e}")
            return []
    
    def _get_commands_from_mongodb(self, server_id: str, hours: int, 
                                  command_type: Optional[str]) -> List[Dict[str, Any]]:
        """Get commands from MongoDB"""
        try:
            if not self.mongo_storage:
                return []
            
            commands = self.mongo_storage.get_command_history(server_id, hours, command_type)
            return commands
            
        except Exception as e:
            logger.error(f"[Query Manager] MongoDB commands error: {e}")
            return []
    
    def _get_commands_from_memory(self, server_id: str, hours: int, 
                                 command_type: Optional[str]) -> List[Dict[str, Any]]:
        """Get commands from memory storage"""
        try:
            if not self.memory_storage:
                return []
            
            commands = self.memory_storage.get_command_history(server_id, hours, command_type)
            return commands
            
        except Exception as e:
            logger.error(f"[Query Manager] Memory commands error: {e}")
            return []
    
    def _merge_command_lists(self, mongo_commands: List[Dict], 
                            memory_commands: List[Dict]) -> List[Dict[str, Any]]:
        """Merge and deduplicate command lists"""
        try:
            # Create a set of MongoDB command IDs for deduplication
            mongo_ids = {cmd.get('command_id') for cmd in mongo_commands if cmd.get('command_id')}
            
            # Add memory commands that aren't in MongoDB
            merged = mongo_commands.copy()
            for cmd in memory_commands:
                if cmd.get('command_id') not in mongo_ids:
                    merged.append(cmd)
            
            return merged
            
        except Exception as e:
            logger.error(f"[Query Manager] Error merging command lists: {e}")
            return mongo_commands  # Return MongoDB commands as fallback
    
    # ===== LATEST HEALTH DATA QUERIES =====
    
    def get_latest_health_data(self, server_id: str) -> Dict[str, Any]:
        """
        ✅ OPTIMIZED: Get latest health data with intelligent storage routing
        ✅ PRESERVED: Compatible with existing health data format
        """
        start_time = time.time()
        
        try:
            logger.debug(f"[Query Manager] Getting latest health data for {server_id}")
            
            # Try memory first (faster for recent data)
            if self.memory_storage:
                memory_result = self._get_latest_from_memory(server_id)
                if memory_result.get('success'):
                    self._update_query_stats('memory_queries', start_time)
                    logger.debug(f"[Query Manager] ✅ Latest data from memory for {server_id}")
                    return memory_result
            
            # Fallback to MongoDB
            if self.mongo_storage:
                mongo_result = self._get_latest_from_mongodb(server_id)
                if mongo_result.get('success'):
                    self._update_query_stats('mongodb_queries', start_time)
                    logger.debug(f"[Query Manager] ✅ Latest data from MongoDB for {server_id}")
                    return mongo_result
            
            # No data available
            self._update_query_stats('fallback_queries', start_time)
            return {'success': False, 'error': 'no_latest_data'}
            
        except Exception as e:
            self._update_query_stats('fallback_queries', start_time)
            logger.error(f"[Query Manager] Error getting latest health data for {server_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_latest_from_memory(self, server_id: str) -> Dict[str, Any]:
        """Get latest health data from memory storage"""
        try:
            latest_snapshots = self.memory_storage.get_latest_snapshots(server_id, 1)
            
            if latest_snapshots:
                snapshot = latest_snapshots[0]
                return {
                    'success': True,
                    'source': 'memory_storage',
                    'statistics': snapshot.get('health_data', {}).get('statistics', {}),
                    'health_percentage': snapshot.get('health_data', {}).get('health_percentage', 75),
                    'timestamp': snapshot.get('timestamp'),
                    'data_quality': snapshot.get('data_quality', 'unknown')
                }
            else:
                return {'success': False, 'error': 'no_memory_data'}
                
        except Exception as e:
            logger.error(f"[Query Manager] Memory latest data error: {e}")
            return {'success': False, 'error': f'memory_error: {e}'}
    
    def _get_latest_from_mongodb(self, server_id: str) -> Dict[str, Any]:
        """Get latest health data from MongoDB"""
        try:
            latest_snapshots = self.mongo_storage.get_latest_snapshots(server_id, 1)
            
            if latest_snapshots:
                snapshot = latest_snapshots[0]
                health_data = snapshot.get('health_data', {})
                
                return {
                    'success': True,
                    'source': 'mongodb_storage',
                    'statistics': health_data.get('statistics', {}),
                    'health_percentage': snapshot.get('health_percentage', 75),
                    'timestamp': snapshot.get('timestamp'),
                    'data_quality': snapshot.get('data_quality', 'unknown')
                }
            else:
                return {'success': False, 'error': 'no_mongodb_data'}
                
        except Exception as e:
            logger.error(f"[Query Manager] MongoDB latest data error: {e}")
            return {'success': False, 'error': f'mongodb_error: {e}'}
    
    # ===== SERVER SUMMARY QUERIES =====
    
    def get_server_summary(self, server_id: str) -> Dict[str, Any]:
        """Get comprehensive server summary from all available sources"""
        start_time = time.time()
        
        try:
            logger.debug(f"[Query Manager] Getting server summary for {server_id}")
            
            summary = {
                'server_id': server_id,
                'timestamp': datetime.utcnow().isoformat(),
                'data_sources': []
            }
            
            # Get data from memory storage
            if self.memory_storage:
                memory_summary = self.memory_storage.get_server_summary(server_id)
                if memory_summary and not memory_summary.get('error'):
                    summary.update({
                        'memory_snapshots': memory_summary.get('snapshots_count', 0),
                        'memory_commands': memory_summary.get('commands_count', 0),
                        'memory_metrics': memory_summary.get('metrics_count', 0),
                        'last_memory_update': memory_summary.get('last_update'),
                        'recent_commands_1h': memory_summary.get('recent_commands_1h', 0)
                    })
                    summary['data_sources'].append('memory_storage')
            
            # Get performance summary from MongoDB
            if self.mongo_storage:
                try:
                    perf_summary = self.mongo_storage.get_performance_summary(server_id, 24)
                    if perf_summary:
                        summary['performance_24h'] = perf_summary
                        summary['data_sources'].append('mongodb_storage')
                except Exception as e:
                    logger.warning(f"[Query Manager] MongoDB performance summary error: {e}")
            
            # Get latest health data
            latest_health = self.get_latest_health_data(server_id)
            if latest_health.get('success'):
                summary.update({
                    'latest_health': latest_health,
                    'health_percentage': latest_health.get('health_percentage', 75),
                    'data_quality': latest_health.get('data_quality', 'unknown')
                })
            
            self._update_query_stats('combined_queries', start_time)
            logger.debug(f"[Query Manager] ✅ Server summary completed for {server_id}")
            
            return summary
            
        except Exception as e:
            self._update_query_stats('fallback_queries', start_time)
            logger.error(f"[Query Manager] Error getting server summary for {server_id}: {e}")
            return {
                'server_id': server_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    # ===== SEARCH AND ANALYTICS QUERIES =====
    
    def search_commands(self, server_id: str, search_term: str, 
                       limit: int = 50) -> List[Dict[str, Any]]:
        """Search commands across all storage systems"""
        try:
            logger.debug(f"[Query Manager] Searching commands for '{search_term}' in {server_id}")
            
            results = []
            
            # Search in memory first (faster)
            if self.memory_storage:
                memory_results = self.memory_storage.search_commands(server_id, search_term, limit)
                results.extend(memory_results)
            
            # Search in MongoDB if we need more results
            if len(results) < limit and self.mongo_storage:
                remaining_limit = limit - len(results)
                # MongoDB text search would go here
                # For now, fall back to basic filtering
                all_commands = self._get_commands_from_mongodb(server_id, 168, None)  # 1 week
                search_lower = search_term.lower()
                
                for cmd in all_commands:
                    if len(results) >= limit:
                        break
                    
                    cmd_text = cmd.get('command_text', '').lower()
                    user_name = cmd.get('user_name', '').lower()
                    
                    if search_lower in cmd_text or search_lower in user_name:
                        # Avoid duplicates
                        cmd_id = cmd.get('command_id')
                        if not any(r.get('command_id') == cmd_id for r in results):
                            results.append(cmd)
            
            # Sort by relevance (exact matches first, then by timestamp)
            results.sort(key=lambda x: (
                search_term.lower() not in x.get('command_text', '').lower(),
                x.get('timestamp', '')
            ), reverse=True)
            
            logger.debug(f"[Query Manager] ✅ Found {len(results)} matching commands")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"[Query Manager] Error searching commands: {e}")
            return []
    
    def get_health_analytics(self, server_id: str, days: int = 7) -> Dict[str, Any]:
        """Get advanced health analytics"""
        try:
            logger.debug(f"[Query Manager] Getting health analytics for {server_id} ({days} days)")
            
            analytics = {
                'server_id': server_id,
                'analysis_period_days': days,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get trend data for analysis
            hours = days * 24
            trends = self.get_health_trends(server_id, hours)
            
            if trends.get('success'):
                charts = trends.get('charts', {})
                
                # Calculate analytics for each metric
                for metric, data in charts.items():
                    if isinstance(data, dict) and 'data' in data:
                        values = [v for v in data['data'] if isinstance(v, (int, float)) and v > 0]
                        
                        if values:
                            analytics[f'{metric}_analytics'] = {
                                'avg': round(sum(values) / len(values), 2),
                                'min': min(values),
                                'max': max(values),
                                'trend': self._calculate_trend_direction(values),
                                'volatility': self._calculate_volatility(values),
                                'health_status': self._assess_metric_health(metric, values)
                            }
            
            # Get command activity analytics
            recent_commands = self.get_command_history(server_id, hours)
            if recent_commands:
                command_analytics = self._analyze_command_activity(recent_commands)
                analytics['command_analytics'] = command_analytics
            
            logger.debug(f"[Query Manager] ✅ Health analytics completed for {server_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"[Query Manager] Error getting health analytics: {e}")
            return {'error': str(e)}
    
    def _calculate_trend_direction(self, values: List[Union[int, float]]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 3:
            return 'insufficient_data'
        
        # Compare first third to last third
        third = len(values) // 3
        start_avg = sum(values[:third]) / third
        end_avg = sum(values[-third:]) / third
        
        if end_avg > start_avg * 1.1:
            return 'increasing'
        elif end_avg < start_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_volatility(self, values: List[Union[int, float]]) -> str:
        """Calculate volatility of values"""
        if len(values) < 2:
            return 'unknown'
        
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Calculate coefficient of variation
        cv = (std_dev / avg) * 100 if avg > 0 else 0
        
        if cv < 10:
            return 'low'
        elif cv < 25:
            return 'moderate'
        else:
            return 'high'
    
    def _assess_metric_health(self, metric: str, values: List[Union[int, float]]) -> str:
        """Assess health status of a metric"""
        if not values:
            return 'unknown'
        
        avg_value = sum(values) / len(values)
        
        # Metric-specific health thresholds
        health_thresholds = {
            'fps': {'good': 50, 'fair': 30},
            'memory_usage': {'good': 2500, 'fair': 3500},  # Lower is better
            'cpu_usage': {'good': 50, 'fair': 75},          # Lower is better
            'player_count': {'good': 5, 'fair': 1},
            'response_time': {'good': 50, 'fair': 100}      # Lower is better
        }
        
        if metric not in health_thresholds:
            return 'unknown'
        
        thresholds = health_thresholds[metric]
        
        if metric in ['memory_usage', 'cpu_usage', 'response_time']:
            # Lower is better
            if avg_value <= thresholds['good']:
                return 'good'
            elif avg_value <= thresholds['fair']:
                return 'fair'
            else:
                return 'poor'
        else:
            # Higher is better
            if avg_value >= thresholds['good']:
                return 'good'
            elif avg_value >= thresholds['fair']:
                return 'fair'
            else:
                return 'poor'
    
    def _analyze_command_activity(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze command activity patterns"""
        try:
            if not commands:
                return {'total_commands': 0, 'activity_level': 'none'}
            
            # Count by type
            type_counts = {}
            user_counts = {}
            
            for cmd in commands:
                cmd_type = cmd.get('command_type', 'unknown')
                user = cmd.get('user_name', 'unknown')
                
                type_counts[cmd_type] = type_counts.get(cmd_type, 0) + 1
                user_counts[user] = user_counts.get(user, 0) + 1
            
            # Determine activity level
            total_commands = len(commands)
            if total_commands > 100:
                activity_level = 'high'
            elif total_commands > 20:
                activity_level = 'moderate'
            elif total_commands > 5:
                activity_level = 'low'
            else:
                activity_level = 'minimal'
            
            return {
                'total_commands': total_commands,
                'activity_level': activity_level,
                'commands_by_type': type_counts,
                'top_users': dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
                'unique_users': len(user_counts)
            }
            
        except Exception as e:
            logger.error(f"[Query Manager] Error analyzing command activity: {e}")
            return {'error': str(e)}
    
    # ===== UTILITY METHODS =====
    
    def _update_query_stats(self, query_type: str, start_time: float):
        """Update query performance statistics"""
        try:
            execution_time = time.time() - start_time
            self.query_stats[query_type] += 1
            self.query_stats['total_query_time'] += execution_time
            
            if execution_time > 1.0:  # Log slow queries
                logger.warning(f"[Query Manager] Slow query ({query_type}): {execution_time:.2f}s")
                
        except Exception as e:
            logger.error(f"[Query Manager] Error updating query stats: {e}")
    
    def get_query_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        try:
            total_queries = sum(self.query_stats[key] for key in self.query_stats if 'queries' in key)
            avg_query_time = (self.query_stats['total_query_time'] / total_queries 
                             if total_queries > 0 else 0)
            
            return {
                **self.query_stats,
                'total_queries': total_queries,
                'avg_query_time_ms': round(avg_query_time * 1000, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[Query Manager] Error getting performance stats: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform query manager health check"""
        try:
            start_time = time.time()
            
            health_status = {
                'status': 'healthy',
                'storage_backends': {},
                'query_performance': self.get_query_performance_stats()
            }
            
            # Test MongoDB storage
            if self.mongo_storage:
                try:
                    mongo_health = self.mongo_storage.health_check()
                    health_status['storage_backends']['mongodb'] = mongo_health
                except Exception as e:
                    health_status['storage_backends']['mongodb'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Test memory storage
            if self.memory_storage:
                try:
                    memory_health = self.memory_storage.health_check()
                    health_status['storage_backends']['memory'] = memory_health
                except Exception as e:
                    health_status['storage_backends']['memory'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Overall health assessment
            unhealthy_backends = [name for name, backend in health_status['storage_backends'].items() 
                                if backend.get('status') != 'healthy']
            
            if unhealthy_backends:
                health_status['status'] = 'degraded'
                health_status['unhealthy_backends'] = unhealthy_backends
            
            response_time = (time.time() - start_time) * 1000
            health_status['response_time_ms'] = round(response_time, 2)
            health_status['timestamp'] = datetime.utcnow().isoformat()
            
            return health_status
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
