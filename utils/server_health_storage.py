"""
Server Health Storage System for WDC-GP/GUST-MARK-1
Layout-focused implementation: Commands for right column, health data for left side charts
Extends verified existing systems only - preserves all functionality
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ServerHealthStorage:
    """
    Server Health Storage System for layout-specific monitoring
    Integrates with verified existing systems:
    - utils/gust_db_optimization.py (perform_optimization_health_check)
    - routes/economy.py (log_transaction pattern)
    - app.py (InMemoryUserStorage pattern)
    """
    
    def __init__(self, db=None, user_storage=None):
        """Initialize using verified storage patterns from existing systems"""
        self.db = db  # MongoDB connection (verified working)
        self.user_storage = user_storage  # InMemoryUserStorage (verified working)
        
        # Memory fallback storage (following verified app.py patterns)
        self.command_history = []  # For right column command feed
        self.health_snapshots = []  # For left side health data
        self.performance_data = []  # For trend analysis
        
        logger.info("[Server Health Storage] Initialized with verified storage patterns")
    
    def _get_collection(self, collection_name: str):
        """Use verified MongoDB pattern from economy.py"""
        if self.db:
            try:
                return self.db[collection_name]
            except Exception as e:
                logger.warning(f"[Server Health Storage] MongoDB collection error: {e}")
                return None
        return None
    
    def _store_memory_fallback(self, data_type: str, data: Dict[str, Any]):
        """Use verified memory storage pattern following InMemoryUserStorage"""
        try:
            if data_type == "command":
                self.command_history.append(data)
                # Keep only last 24 hours in memory (verified pattern)
                cutoff = datetime.utcnow() - timedelta(hours=24)
                self.command_history = [
                    cmd for cmd in self.command_history 
                    if datetime.fromisoformat(cmd.get('timestamp', '')) > cutoff
                ]
            elif data_type == "health":
                self.health_snapshots.append(data)
                # Keep only last 48 hours for trend analysis
                cutoff = datetime.utcnow() - timedelta(hours=48)
                self.health_snapshots = [
                    snap for snap in self.health_snapshots 
                    if datetime.fromisoformat(snap.get('timestamp', '')) > cutoff
                ]
            elif data_type == "performance":
                self.performance_data.append(data)
                # Keep only last 7 days for performance trends
                cutoff = datetime.utcnow() - timedelta(days=7)
                self.performance_data = [
                    perf for perf in self.performance_data 
                    if datetime.fromisoformat(perf.get('timestamp', '')) > cutoff
                ]
        except Exception as e:
            logger.error(f"[Server Health Storage] Memory fallback error: {e}")
    
    # ===== RIGHT COLUMN COMMAND HISTORY FUNCTIONS =====
    
    def get_command_history_24h(self, server_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get last 24 hours of commands for right column display"""
        try:
            collection = self._get_collection('server_health_commands')
            if collection:
                # MongoDB query for last 24 hours
                cutoff = datetime.utcnow() - timedelta(hours=24)
                query = {"timestamp": {"$gte": cutoff}}
                if server_id:
                    query["server_id"] = server_id
                
                commands = list(collection.find(query).sort("timestamp", -1))
                
                # Format for right column display
                formatted_commands = []
                for cmd in commands:
                    formatted_commands.append({
                        "timestamp": cmd['timestamp'].strftime("%H:%M:%S"),
                        "command": cmd.get('command', ''),
                        "type": cmd.get('command_type', 'unknown'),
                        "user": cmd.get('user', 'System'),
                        "server_id": cmd.get('server_id', '')
                    })
                return formatted_commands
            else:
                # Memory fallback - filter last 24 hours
                cutoff = datetime.utcnow() - timedelta(hours=24)
                recent_commands = [
                    {
                        "timestamp": datetime.fromisoformat(cmd['timestamp']).strftime("%H:%M:%S"),
                        "command": cmd.get('command', ''),
                        "type": cmd.get('command_type', 'unknown'),
                        "user": cmd.get('user', 'System'),
                        "server_id": cmd.get('server_id', '')
                    }
                    for cmd in self.command_history
                    if datetime.fromisoformat(cmd.get('timestamp', '')) > cutoff
                ]
                return sorted(recent_commands, key=lambda x: x['timestamp'], reverse=True)
                
        except Exception as e:
            logger.error(f"[Server Health Storage] Get command history error: {e}")
            return []
    
    def store_command_execution(self, server_id: str, command: str, command_type: str, user: str):
        """Store command execution for 24h history tracking (following log_transaction pattern)"""
        try:
            command_data = {
                "command_id": str(uuid.uuid4()),
                "server_id": server_id,
                "command": command,
                "command_type": command_type,  # "admin", "ingame", "auto"
                "user": user,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            collection = self._get_collection('server_health_commands')
            if collection:
                # MongoDB storage (verified pattern from economy.py)
                collection.insert_one(command_data)
            else:
                # Memory fallback
                self._store_memory_fallback("command", {
                    **command_data,
                    "timestamp": command_data["timestamp"].isoformat()
                })
            
            logger.info(f"[Server Health Storage] Command stored: {command} ({command_type})")
            return True
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Store command error: {e}")
            return False
    
    # ===== LEFT SIDE HEALTH DATA FUNCTIONS =====
    
    def get_health_trends(self, server_id: Optional[str] = None, hours: int = 6) -> Dict[str, Any]:
        """Get health data for left-side charts and metrics"""
        try:
            collection = self._get_collection('server_health_snapshots')
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            if collection:
                query = {"timestamp": {"$gte": cutoff}}
                if server_id:
                    query["server_id"] = server_id
                
                snapshots = list(collection.find(query).sort("timestamp", 1))
            else:
                # Memory fallback
                snapshots = [
                    snap for snap in self.health_snapshots
                    if datetime.fromisoformat(snap.get('timestamp', '')) > cutoff
                ]
                if server_id:
                    snapshots = [s for s in snapshots if s.get('server_id') == server_id]
            
            # Process data for charts
            timestamps = []
            fps_data = []
            memory_data = []
            player_data = []
            response_times = []
            
            for snap in snapshots:
                timestamps.append(snap.get('timestamp'))
                health_data = snap.get('health_data', {})
                stats = health_data.get('statistics', {})
                
                fps_data.append(stats.get('fps', 0))
                memory_data.append(stats.get('memory_usage', 0))
                player_data.append(stats.get('player_count', 0))
                response_times.append(health_data.get('response_time', 0))
            
            return {
                "timestamps": timestamps,
                "fps": fps_data,
                "memory": memory_data,
                "players": player_data,
                "response_times": response_times,
                "data_points": len(timestamps)
            }
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Get health trends error: {e}")
            return {"timestamps": [], "fps": [], "memory": [], "players": [], "response_times": [], "data_points": 0}
    
    def store_health_snapshot(self, server_id: str, health_data: Dict[str, Any]):
        """Store current health snapshot from verified perform_optimization_health_check()"""
        try:
            snapshot = {
                "snapshot_id": str(uuid.uuid4()),
                "server_id": server_id,
                "health_data": health_data,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            collection = self._get_collection('server_health_snapshots')
            if collection:
                collection.insert_one(snapshot)
            else:
                # Memory fallback
                self._store_memory_fallback("health", {
                    **snapshot,
                    "timestamp": snapshot["timestamp"].isoformat()
                })
            
            return True
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Store health snapshot error: {e}")
            return False
    
    def calculate_averages(self, server_id: Optional[str] = None, hours: int = 24) -> Dict[str, float]:
        """Calculate average metrics for performance trends display"""
        try:
            trends = self.get_health_trends(server_id, hours)
            
            if not trends["data_points"]:
                return {"response_time": 0, "memory_usage": 0, "fps": 0, "player_count": 0}
            
            return {
                "response_time": sum(trends["response_times"]) / len(trends["response_times"]) if trends["response_times"] else 0,
                "memory_usage": sum(trends["memory"]) / len(trends["memory"]) if trends["memory"] else 0,
                "fps": sum(trends["fps"]) / len(trends["fps"]) if trends["fps"] else 0,
                "player_count": sum(trends["players"]) / len(trends["players"]) if trends["players"] else 0
            }
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Calculate averages error: {e}")
            return {"response_time": 0, "memory_usage": 0, "fps": 0, "player_count": 0}
    
    def get_current_metrics(self, server_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current real-time metrics for display"""
        try:
            # Integrate with verified perform_optimization_health_check()
            from utils.gust_db_optimization import perform_optimization_health_check
            health_data = perform_optimization_health_check()
            
            stats = health_data.get('statistics', {})
            
            return {
                "status": health_data.get('status', 'unknown'),
                "response_time": health_data.get('response_time', 0),
                "memory_usage": stats.get('memory_usage', 0),
                "cpu_usage": stats.get('cpu_usage', 0),
                "player_count": stats.get('player_count', 0),
                "cache_hit_rate": stats.get('cache_hit_rate', 0),
                "uptime": stats.get('uptime', 0),
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Get current metrics error: {e}")
            return {
                "status": "error",
                "response_time": 0,
                "memory_usage": 0,
                "cpu_usage": 0,
                "player_count": 0,
                "cache_hit_rate": 0,
                "uptime": 0,
                "last_check": datetime.utcnow().isoformat()
            }
    
    # ===== VERIFIED SYSTEM INTEGRATION =====
    
    def integrate_with_health_check(self):
        """Integrate with verified perform_optimization_health_check()"""
        try:
            from utils.gust_db_optimization import perform_optimization_health_check
            health_data = perform_optimization_health_check()
            return health_data
        except Exception as e:
            logger.error(f"[Server Health Storage] Health check integration error: {e}")
            return {"status": "error", "message": str(e)}
    
    def integrate_with_transaction_logging(self, command_data: Dict[str, Any]):
        """Use verified log_transaction pattern from economy.py"""
        try:
            # Follow exact pattern from routes/economy.py log_transaction()
            self.store_command_execution(
                server_id=command_data.get('server_id', 'default'),
                command=command_data.get('command', ''),
                command_type=command_data.get('type', 'unknown'),
                user=command_data.get('user', 'System')
            )
            return True
        except Exception as e:
            logger.error(f"[Server Health Storage] Transaction logging integration error: {e}")
            return False
    
    def cleanup_old_data(self):
        """Clean up old data following verified patterns"""
        try:
            # Clean MongoDB collections
            cutoff_commands = datetime.utcnow() - timedelta(hours=24)
            cutoff_health = datetime.utcnow() - timedelta(days=7)
            
            collection_commands = self._get_collection('server_health_commands')
            if collection_commands:
                collection_commands.delete_many({"timestamp": {"$lt": cutoff_commands}})
            
            collection_health = self._get_collection('server_health_snapshots')
            if collection_health:
                collection_health.delete_many({"timestamp": {"$lt": cutoff_health}})
            
            # Clean memory storage
            self._store_memory_fallback("command", {})  # Triggers cleanup
            self._store_memory_fallback("health", {})   # Triggers cleanup
            
            logger.info("[Server Health Storage] Old data cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Cleanup error: {e}")
            return False

    # ===== ADDITIONAL METHODS FROM PASTE.TXT =====

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health score (called by app.py health endpoint)"""
        try:
            # Get recent health data
            recent_snapshots = self.health_snapshots[-10:] if self.health_snapshots else []
            
            if not recent_snapshots:
                return {
                    "overall_score": 95,
                    "status": "healthy",
                    "last_check": datetime.utcnow().isoformat(),
                    "metrics_count": 0
                }
            
            # Calculate average health from recent snapshots
            total_score = 0
            healthy_count = 0
            
            for snapshot in recent_snapshots:
                health_data = snapshot.get('health_data', {})
                status = health_data.get('status', 'unknown')
                
                if status == 'healthy':
                    total_score += 95
                    healthy_count += 1
                elif status == 'warning':
                    total_score += 70
                elif status == 'critical':
                    total_score += 30
                else:
                    total_score += 50
            
            avg_score = total_score // len(recent_snapshots) if recent_snapshots else 95
            
            return {
                "overall_score": avg_score,
                "status": "healthy" if avg_score >= 80 else "warning" if avg_score >= 60 else "critical",
                "last_check": recent_snapshots[-1].get('timestamp', datetime.utcnow().isoformat()),
                "metrics_count": len(recent_snapshots),
                "healthy_percentage": (healthy_count / len(recent_snapshots)) * 100 if recent_snapshots else 0
            }
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Get system health error: {e}")
            return {
                "overall_score": 50,
                "status": "error", 
                "last_check": datetime.utcnow().isoformat(),
                "metrics_count": 0,
                "error": str(e)
            }

    def store_system_health(self, health_data: Dict[str, Any]):
        """Store system health data (called by app.py background task)"""
        try:
            system_health_entry = {
                "system_health_id": str(uuid.uuid4()),
                "health_data": health_data,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            collection = self._get_collection('system_health_snapshots')
            if collection:
                # MongoDB storage
                collection.insert_one(system_health_entry)
            else:
                # Memory fallback - store in health_snapshots
                self._store_memory_fallback("health", {
                    **system_health_entry,
                    "timestamp": system_health_entry["timestamp"].isoformat()
                })
            
            logger.info(f"[Server Health Storage] System health stored successfully")
            return True
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Store system health error: {e}")
            return False

    def get_performance_trends_summary(self, server_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance trends summary for enhanced analysis"""
        try:
            # Get recent trends
            trends_24h = self.get_health_trends(server_id, 24)
            trends_7d = self.get_health_trends(server_id, 168)  # 7 days
            
            # Calculate trend indicators
            def get_trend_indicator(current_avg, old_avg):
                if old_avg == 0:
                    return "➡️"
                change = ((current_avg - old_avg) / old_avg) * 100
                if change > 5:
                    return "📈"
                elif change < -5:
                    return "📉"
                else:
                    return "➡️"
            
            # Calculate averages
            avg_24h = self.calculate_averages(server_id, 24)
            avg_7d = self.calculate_averages(server_id, 168)
            
            return {
                "trends": {
                    "response_time": get_trend_indicator(avg_24h["response_time"], avg_7d["response_time"]),
                    "memory_usage": get_trend_indicator(avg_24h["memory_usage"], avg_7d["memory_usage"]),
                    "fps": get_trend_indicator(avg_24h["fps"], avg_7d["fps"]),
                    "player_count": get_trend_indicator(avg_24h["player_count"], avg_7d["player_count"])
                },
                "data_points_24h": trends_24h["data_points"],
                "data_points_7d": trends_7d["data_points"],
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[Server Health Storage] Get performance trends summary error: {e}")
            return {
                "trends": {"response_time": "➡️", "memory_usage": "➡️", "fps": "➡️", "player_count": "➡️"},
                "data_points_24h": 0,
                "data_points_7d": 0,
                "last_updated": datetime.utcnow().isoformat()
            }
