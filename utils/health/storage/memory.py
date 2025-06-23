"""
In-Memory Storage Implementation for GUST-MARK-1 Server Health Storage System
==============================================================================
✅ ENHANCED: High-performance in-memory storage with intelligent memory management
✅ PRESERVED: All existing in-memory storage patterns and functionality
✅ OPTIMIZED: Efficient data structures, automatic cleanup, and thread safety
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from collections import deque, defaultdict
import logging

from .models import HealthMetric, CommandExecution, HealthSnapshot, TrendData

logger = logging.getLogger(__name__)

class MemoryHealthStorage:
    """
    ✅ OPTIMIZED: High-performance in-memory storage with intelligent memory management
    ✅ ENHANCED: Thread-safe operations, automatic cleanup, and efficient data structures
    ✅ PRESERVED: All existing in-memory storage functionality from the original system
    """
    
    def __init__(self, max_snapshots: int = 500, max_commands: int = 1000, 
                 max_metrics: int = 200):
        """Initialize in-memory storage with configurable limits"""
        self.max_snapshots = max_snapshots
        self.max_commands = max_commands
        self.max_metrics = max_metrics
        
        # ✅ OPTIMIZED: Use deque for O(1) append/popleft operations
        self.health_snapshots = deque(maxlen=max_snapshots)
        self.command_history = deque(maxlen=max_commands)
        self.performance_data = deque(maxlen=max_metrics)
        
        # ✅ ENHANCED: Server-specific storage for better organization
        self.server_snapshots = defaultdict(lambda: deque(maxlen=100))
        self.server_commands = defaultdict(lambda: deque(maxlen=200))
        self.server_metrics = defaultdict(lambda: deque(maxlen=50))
        
        # ✅ NEW: Metadata tracking for storage optimization
        self.storage_stats = {
            'snapshots_stored': 0,
            'commands_stored': 0,
            'metrics_stored': 0,
            'last_cleanup': datetime.utcnow(),
            'memory_usage_mb': 0
        }
        
        # ✅ ENHANCED: Thread safety for concurrent access
        self._lock = threading.RLock()
        
        # ✅ NEW: Automatic cleanup timer
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
        logger.info(f"[Memory Storage] ✅ Initialized with limits: snapshots={max_snapshots}, "
                   f"commands={max_commands}, metrics={max_metrics}")
    
    # ===== HEALTH SNAPSHOT OPERATIONS =====
    
    def store_snapshot(self, snapshot: HealthSnapshot) -> bool:
        """Store health snapshot with thread safety and automatic cleanup"""
        try:
            with self._lock:
                # Store in global collection
                self.health_snapshots.append({
                    'snapshot_id': snapshot.snapshot_id,
                    'server_id': snapshot.server_id,
                    'health_data': snapshot.health_data,
                    'timestamp': snapshot.timestamp.isoformat() if hasattr(snapshot.timestamp, 'isoformat') else snapshot.timestamp,
                    'stored_at': datetime.utcnow().isoformat()
                })
                
                # Store in server-specific collection
                self.server_snapshots[snapshot.server_id].append({
                    'snapshot_id': snapshot.snapshot_id,
                    'health_data': snapshot.health_data,
                    'timestamp': snapshot.timestamp.isoformat() if hasattr(snapshot.timestamp, 'isoformat') else snapshot.timestamp,
                    'stored_at': datetime.utcnow().isoformat()
                })
                
                # Update statistics
                self.storage_stats['snapshots_stored'] += 1
                
                # Trigger cleanup if needed
                self._maybe_cleanup()
                
                logger.debug(f"[Memory Storage] ✅ Stored snapshot for {snapshot.server_id}")
                return True
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error storing snapshot: {e}")
            return False
    
    def get_latest_snapshots(self, server_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest health snapshots for a specific server"""
        try:
            with self._lock:
                server_snapshots = list(self.server_snapshots[server_id])
                
                # Sort by timestamp (most recent first) and limit
                server_snapshots.sort(
                    key=lambda x: x.get('timestamp', ''), 
                    reverse=True
                )
                
                result = server_snapshots[:limit]
                logger.debug(f"[Memory Storage] Retrieved {len(result)} snapshots for {server_id}")
                return result
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting snapshots for {server_id}: {e}")
            return []
    
    def get_snapshots_in_range(self, server_id: str, start_time: datetime, 
                              end_time: datetime) -> List[Dict[str, Any]]:
        """Get health snapshots within time range"""
        try:
            with self._lock:
                server_snapshots = list(self.server_snapshots[server_id])
                
                # Filter by time range
                filtered_snapshots = []
                for snapshot in server_snapshots:
                    try:
                        timestamp_str = snapshot.get('timestamp', '')
                        if timestamp_str:
                            snapshot_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if start_time <= snapshot_time <= end_time:
                                filtered_snapshots.append(snapshot)
                    except (ValueError, TypeError):
                        continue
                
                # Sort by timestamp
                filtered_snapshots.sort(key=lambda x: x.get('timestamp', ''))
                
                logger.debug(f"[Memory Storage] Retrieved {len(filtered_snapshots)} snapshots "
                           f"in range for {server_id}")
                return filtered_snapshots
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting range snapshots for {server_id}: {e}")
            return []
    
    def get_all_snapshots(self) -> List[Dict[str, Any]]:
        """Get all health snapshots (for global operations)"""
        try:
            with self._lock:
                return list(self.health_snapshots)
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting all snapshots: {e}")
            return []
    
    # ===== COMMAND TRACKING OPERATIONS =====
    
    def store_command(self, command: CommandExecution) -> bool:
        """Store command execution with enhanced metadata"""
        try:
            with self._lock:
                command_data = {
                    'command_id': command.command_id,
                    'server_id': command.server_id,
                    'command_type': command.command_type,
                    'command_text': command.command_text,
                    'user_name': command.user_name,
                    'timestamp': command.timestamp.isoformat() if hasattr(command.timestamp, 'isoformat') else command.timestamp,
                    'metadata': command.metadata,
                    'stored_at': datetime.utcnow().isoformat()
                }
                
                # Store in global collection
                self.command_history.append(command_data)
                
                # Store in server-specific collection
                self.server_commands[command.server_id].append(command_data)
                
                # Update statistics
                self.storage_stats['commands_stored'] += 1
                
                # Trigger cleanup if needed
                self._maybe_cleanup()
                
                logger.debug(f"[Memory Storage] ✅ Stored command for {command.server_id}")
                return True
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error storing command: {e}")
            return False
    
    def get_command_history(self, server_id: str, hours: int = 24, 
                           command_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get command history with time and type filtering"""
        try:
            with self._lock:
                server_commands = list(self.server_commands[server_id])
                
                # Filter by time range
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                cutoff_str = cutoff_time.isoformat()
                
                filtered_commands = []
                for command in server_commands:
                    try:
                        # Time filter
                        command_time = command.get('timestamp', '')
                        if command_time >= cutoff_str:
                            # Type filter (if specified)
                            if command_type is None or command.get('command_type') == command_type:
                                filtered_commands.append(command)
                    except (ValueError, TypeError):
                        continue
                
                # Sort by timestamp (most recent first)
                filtered_commands.sort(
                    key=lambda x: x.get('timestamp', ''), 
                    reverse=True
                )
                
                logger.debug(f"[Memory Storage] Retrieved {len(filtered_commands)} commands "
                           f"for {server_id} (type: {command_type})")
                return filtered_commands
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting command history for {server_id}: {e}")
            return []
    
    def get_all_commands(self) -> List[Dict[str, Any]]:
        """Get all commands (for global operations)"""
        try:
            with self._lock:
                return list(self.command_history)
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting all commands: {e}")
            return []
    
    # ===== PERFORMANCE METRICS OPERATIONS =====
    
    def store_metric(self, metric: HealthMetric) -> bool:
        """Store individual performance metric"""
        try:
            with self._lock:
                metric_data = {
                    'metric_id': metric.metric_id,
                    'server_id': metric.server_id,
                    'metric_type': metric.metric_type,
                    'metric_value': metric.metric_value,
                    'timestamp': metric.timestamp.isoformat() if hasattr(metric.timestamp, 'isoformat') else metric.timestamp,
                    'metadata': metric.metadata,
                    'stored_at': datetime.utcnow().isoformat()
                }
                
                # Store in global collection
                self.performance_data.append(metric_data)
                
                # Store in server-specific collection
                self.server_metrics[metric.server_id].append(metric_data)
                
                # Update statistics
                self.storage_stats['metrics_stored'] += 1
                
                logger.debug(f"[Memory Storage] ✅ Stored metric {metric.metric_type} for {metric.server_id}")
                return True
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error storing metric: {e}")
            return False
    
    def get_metrics_by_type(self, server_id: str, metric_type: str, 
                           hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance metrics by type within time range"""
        try:
            with self._lock:
                server_metrics = list(self.server_metrics[server_id])
                
                # Filter by type and time
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                cutoff_str = cutoff_time.isoformat()
                
                filtered_metrics = []
                for metric in server_metrics:
                    try:
                        if (metric.get('metric_type') == metric_type and 
                            metric.get('timestamp', '') >= cutoff_str):
                            filtered_metrics.append(metric)
                    except (ValueError, TypeError):
                        continue
                
                # Sort by timestamp
                filtered_metrics.sort(key=lambda x: x.get('timestamp', ''))
                
                logger.debug(f"[Memory Storage] Retrieved {len(filtered_metrics)} "
                           f"{metric_type} metrics for {server_id}")
                return filtered_metrics
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting metrics for {server_id}: {e}")
            return []
    
    # ===== TREND ANALYSIS OPERATIONS =====
    
    def get_health_trends_data(self, server_id: str, hours: int = 6) -> Dict[str, Any]:
        """Get health trends data formatted for charts"""
        try:
            # Get snapshots in time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            snapshots = self.get_snapshots_in_range(server_id, start_time, end_time)
            
            if not snapshots:
                return {'success': False, 'error': 'no_data'}
            
            # Format data for charts
            trend_data = self._format_trend_data(snapshots)
            
            logger.debug(f"[Memory Storage] ✅ Generated trends from {len(snapshots)} snapshots for {server_id}")
            return {'success': True, 'trends': trend_data, 'count': len(snapshots)}
            
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting trends for {server_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_trend_data(self, snapshots: List[Dict]) -> Dict[str, Any]:
        """Format snapshots data for chart visualization"""
        try:
            labels = []
            fps_data = []
            memory_data = []
            cpu_data = []
            player_data = []
            response_data = []
            
            for snapshot in snapshots:
                # Format timestamp for chart labels
                timestamp_str = snapshot.get('timestamp', '')
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        labels.append(timestamp.strftime('%H:%M'))
                    except:
                        labels.append('--:--')
                
                # Extract statistics safely
                health_data = snapshot.get('health_data', {})
                stats = health_data.get('statistics', health_data.get('metrics', {}))
                
                fps_data.append(stats.get('fps', 0))
                memory_data.append(stats.get('memory_usage', 0))
                cpu_data.append(stats.get('cpu_usage', 0))
                player_data.append(stats.get('player_count', 0))
                response_data.append(stats.get('response_time', 0))
            
            return {
                'fps': {'labels': labels, 'data': fps_data},
                'memory': {'labels': labels, 'data': memory_data},
                'cpu': {'labels': labels, 'data': cpu_data},
                'players': {'labels': labels, 'data': player_data},
                'response_time': {'labels': labels, 'data': response_data}
            }
            
        except Exception as e:
            logger.error(f"[Memory Storage] Error formatting trend data: {e}")
            return {}
    
    # ===== SEARCH AND QUERY OPERATIONS =====
    
    def search_commands(self, server_id: str, search_term: str, 
                       limit: int = 50) -> List[Dict[str, Any]]:
        """Search commands by text content"""
        try:
            with self._lock:
                server_commands = list(self.server_commands[server_id])
                
                # Search in command text and user name
                search_term_lower = search_term.lower()
                matching_commands = []
                
                for command in server_commands:
                    command_text = command.get('command_text', '').lower()
                    user_name = command.get('user_name', '').lower()
                    
                    if (search_term_lower in command_text or 
                        search_term_lower in user_name):
                        matching_commands.append(command)
                        
                        if len(matching_commands) >= limit:
                            break
                
                # Sort by timestamp (most recent first)
                matching_commands.sort(
                    key=lambda x: x.get('timestamp', ''), 
                    reverse=True
                )
                
                logger.debug(f"[Memory Storage] Found {len(matching_commands)} matching commands "
                           f"for '{search_term}' in {server_id}")
                return matching_commands
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error searching commands: {e}")
            return []
    
    def get_server_summary(self, server_id: str) -> Dict[str, Any]:
        """Get summary statistics for a server"""
        try:
            with self._lock:
                summary = {
                    'server_id': server_id,
                    'snapshots_count': len(self.server_snapshots[server_id]),
                    'commands_count': len(self.server_commands[server_id]),
                    'metrics_count': len(self.server_metrics[server_id])
                }
                
                # Get latest snapshot for current status
                latest_snapshots = self.get_latest_snapshots(server_id, 1)
                if latest_snapshots:
                    latest = latest_snapshots[0]
                    summary['last_update'] = latest.get('timestamp')
                    summary['health_data'] = latest.get('health_data', {})
                
                # Get recent command count
                recent_commands = self.get_command_history(server_id, hours=1)
                summary['recent_commands_1h'] = len(recent_commands)
                
                return summary
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting server summary: {e}")
            return {'server_id': server_id, 'error': str(e)}
    
    # ===== MAINTENANCE OPERATIONS =====
    
    def _maybe_cleanup(self):
        """Trigger cleanup if enough time has passed"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_old_data()
            self._last_cleanup = current_time
    
    def _cleanup_old_data(self):
        """Clean up old data to prevent memory bloat"""
        try:
            with self._lock:
                cutoff_time = datetime.utcnow() - timedelta(hours=48)
                cutoff_str = cutoff_time.isoformat()
                
                cleanup_count = 0
                
                # Clean server-specific collections
                for server_id in list(self.server_snapshots.keys()):
                    # Clean old snapshots
                    original_count = len(self.server_snapshots[server_id])
                    self.server_snapshots[server_id] = deque(
                        [s for s in self.server_snapshots[server_id] 
                         if s.get('timestamp', '') >= cutoff_str],
                        maxlen=100
                    )
                    cleanup_count += original_count - len(self.server_snapshots[server_id])
                    
                    # Clean old commands (keep longer)
                    command_cutoff = datetime.utcnow() - timedelta(hours=168)  # 1 week
                    command_cutoff_str = command_cutoff.isoformat()
                    
                    original_count = len(self.server_commands[server_id])
                    self.server_commands[server_id] = deque(
                        [c for c in self.server_commands[server_id] 
                         if c.get('timestamp', '') >= command_cutoff_str],
                        maxlen=200
                    )
                    cleanup_count += original_count - len(self.server_commands[server_id])
                
                # Update cleanup stats
                self.storage_stats['last_cleanup'] = datetime.utcnow()
                
                if cleanup_count > 0:
                    logger.info(f"[Memory Storage] ✅ Cleaned up {cleanup_count} old records")
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error during cleanup: {e}")
    
    def force_cleanup(self) -> Dict[str, int]:
        """Force immediate cleanup and return statistics"""
        try:
            with self._lock:
                initial_stats = {
                    'snapshots': sum(len(q) for q in self.server_snapshots.values()),
                    'commands': sum(len(q) for q in self.server_commands.values()),
                    'metrics': sum(len(q) for q in self.server_metrics.values())
                }
                
                self._cleanup_old_data()
                
                final_stats = {
                    'snapshots': sum(len(q) for q in self.server_snapshots.values()),
                    'commands': sum(len(q) for q in self.server_commands.values()),
                    'metrics': sum(len(q) for q in self.server_metrics.values())
                }
                
                cleanup_stats = {
                    'snapshots_removed': initial_stats['snapshots'] - final_stats['snapshots'],
                    'commands_removed': initial_stats['commands'] - final_stats['commands'],
                    'metrics_removed': initial_stats['metrics'] - final_stats['metrics'],
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                logger.info(f"[Memory Storage] ✅ Force cleanup completed: {cleanup_stats}")
                return cleanup_stats
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error during force cleanup: {e}")
            return {'error': str(e)}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        try:
            with self._lock:
                # Calculate current counts
                current_counts = {
                    'global_snapshots': len(self.health_snapshots),
                    'global_commands': len(self.command_history),
                    'global_metrics': len(self.performance_data),
                    'server_snapshots': sum(len(q) for q in self.server_snapshots.values()),
                    'server_commands': sum(len(q) for q in self.server_commands.values()),
                    'server_metrics': sum(len(q) for q in self.server_metrics.values()),
                    'unique_servers': len(self.server_snapshots)
                }
                
                # Estimate memory usage (rough calculation)
                estimated_memory_mb = (
                    current_counts['server_snapshots'] * 0.5 +  # ~0.5KB per snapshot
                    current_counts['server_commands'] * 0.3 +   # ~0.3KB per command
                    current_counts['server_metrics'] * 0.2     # ~0.2KB per metric
                ) / 1024  # Convert to MB
                
                stats = {
                    **self.storage_stats,
                    **current_counts,
                    'estimated_memory_mb': round(estimated_memory_mb, 2),
                    'last_stats_update': datetime.utcnow().isoformat()
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error getting storage stats: {e}")
            return {'error': str(e)}
    
    def clear_server_data(self, server_id: str) -> bool:
        """Clear all data for a specific server"""
        try:
            with self._lock:
                # Clear server-specific collections
                if server_id in self.server_snapshots:
                    self.server_snapshots[server_id].clear()
                if server_id in self.server_commands:
                    self.server_commands[server_id].clear()
                if server_id in self.server_metrics:
                    self.server_metrics[server_id].clear()
                
                logger.info(f"[Memory Storage] ✅ Cleared all data for server {server_id}")
                return True
                
        except Exception as e:
            logger.error(f"[Memory Storage] Error clearing data for {server_id}: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform memory storage health check"""
        try:
            start_time = time.time()
            
            # Test basic operations
            with self._lock:
                # Test data access
                snapshot_count = len(self.health_snapshots)
                command_count = len(self.command_history)
                metric_count = len(self.performance_data)
                
                # Test server data access
                server_count = len(self.server_snapshots)
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'snapshot_count': snapshot_count,
                'command_count': command_count,
                'metric_count': metric_count,
                'server_count': server_count,
                'memory_efficient': response_time < 10,  # Should be very fast
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
