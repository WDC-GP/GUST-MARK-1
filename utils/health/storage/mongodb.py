"""
MongoDB Storage Implementation for GUST-MARK-1 Server Health Storage System
============================================================================
✅ ENHANCED: Optimized MongoDB operations with proper indexing and aggregation
✅ PRESERVED: All existing functionality with improved performance and reliability
✅ OPTIMIZED: Query performance, connection handling, and error recovery
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from .models import HealthMetric, CommandExecution, HealthSnapshot, TrendData

logger = logging.getLogger(__name__)

class MongoHealthStorage:
    """
    ✅ OPTIMIZED: MongoDB storage operations with enhanced performance and reliability
    ✅ ENHANCED: Proper indexing, aggregation pipelines, and connection management
    ✅ PRESERVED: All existing MongoDB patterns from the original system
    """
    
    def __init__(self, db=None):
        """Initialize MongoDB storage with enhanced connection handling"""
        self.db = db
        self.collections = {}
        self.indexes_created = False
        
        if self.db:
            try:
                self._setup_collections()
                self._ensure_indexes()
                logger.info("[MongoDB Storage] ✅ Initialized with optimized collections and indexes")
            except Exception as e:
                logger.error(f"[MongoDB Storage] Initialization error: {e}")
                self.db = None
        else:
            logger.warning("[MongoDB Storage] No database connection provided")
    
    def _setup_collections(self):
        """Setup MongoDB collections with proper references"""
        try:
            self.collections = {
                'health_snapshots': self.db['server_health_snapshots'],
                'command_history': self.db['server_health_commands'],
                'performance_metrics': self.db['server_performance_metrics'],
                'health_trends': self.db['server_health_trends']
            }
            logger.debug("[MongoDB Storage] Collections configured")
        except Exception as e:
            logger.error(f"[MongoDB Storage] Collection setup error: {e}")
            raise
    
    def _ensure_indexes(self):
        """Create optimized indexes for better query performance"""
        if self.indexes_created or not self.db:
            return
        
        try:
            # Health snapshots indexes
            health_collection = self.collections['health_snapshots']
            health_collection.create_index([
                ("server_id", ASCENDING),
                ("timestamp", DESCENDING)
            ], name="server_timestamp_idx")
            
            # TTL index for automatic cleanup (7 days)
            health_collection.create_index(
                "timestamp", 
                expireAfterSeconds=604800,  # 7 days
                name="ttl_cleanup_idx"
            )
            
            # Command history indexes
            command_collection = self.collections['command_history']
            command_collection.create_index([
                ("server_id", ASCENDING),
                ("timestamp", DESCENDING),
                ("command_type", ASCENDING)
            ], name="command_lookup_idx")
            
            # TTL index for command cleanup (30 days)
            command_collection.create_index(
                "timestamp",
                expireAfterSeconds=2592000,  # 30 days
                name="command_ttl_idx"
            )
            
            # Performance metrics indexes
            metrics_collection = self.collections['performance_metrics']
            metrics_collection.create_index([
                ("server_id", ASCENDING),
                ("metric_type", ASCENDING),
                ("timestamp", DESCENDING)
            ], name="metrics_lookup_idx")
            
            self.indexes_created = True
            logger.info("[MongoDB Storage] ✅ Optimized indexes created")
            
        except Exception as e:
            logger.error(f"[MongoDB Storage] Index creation error: {e}")
    
    def get_collection(self, collection_name: str):
        """✅ PRESERVED: Get MongoDB collection with error handling"""
        try:
            if collection_name in self.collections:
                return self.collections[collection_name]
            elif self.db and collection_name in self.db.list_collection_names():
                return self.db[collection_name]
            else:
                logger.warning(f"[MongoDB Storage] Collection {collection_name} not found")
                return None
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error accessing collection {collection_name}: {e}")
            return None
    
    # ===== HEALTH SNAPSHOT OPERATIONS =====
    
    def store_snapshot(self, snapshot: HealthSnapshot) -> bool:
        """Store health snapshot with optimized document structure"""
        try:
            if not self.db:
                return False
            
            collection = self.collections['health_snapshots']
            document = {
                'snapshot_id': snapshot.snapshot_id,
                'server_id': snapshot.server_id,
                'health_data': snapshot.health_data,
                'timestamp': snapshot.timestamp,
                'created_at': datetime.utcnow(),
                'data_version': '2.0'  # Version for schema evolution
            }
            
            result = collection.insert_one(document)
            
            if result.inserted_id:
                logger.debug(f"[MongoDB Storage] ✅ Stored snapshot {snapshot.snapshot_id}")
                return True
            else:
                logger.error(f"[MongoDB Storage] Failed to store snapshot {snapshot.snapshot_id}")
                return False
                
        except PyMongoError as e:
            logger.error(f"[MongoDB Storage] PyMongo error storing snapshot: {e}")
            return False
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error storing snapshot: {e}")
            return False
    
    def get_latest_snapshots(self, server_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest health snapshots with optimized query"""
        try:
            if not self.db:
                return []
            
            collection = self.collections['health_snapshots']
            cursor = collection.find(
                {"server_id": server_id}
            ).sort("timestamp", DESCENDING).limit(limit)
            
            snapshots = list(cursor)
            logger.debug(f"[MongoDB Storage] Retrieved {len(snapshots)} snapshots for {server_id}")
            return snapshots
            
        except PyMongoError as e:
            logger.error(f"[MongoDB Storage] PyMongo error getting snapshots: {e}")
            return []
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error getting snapshots: {e}")
            return []
    
    def get_snapshots_in_range(self, server_id: str, start_time: datetime, 
                              end_time: datetime) -> List[Dict[str, Any]]:
        """Get health snapshots within time range using optimized query"""
        try:
            if not self.db:
                return []
            
            collection = self.collections['health_snapshots']
            query = {
                "server_id": server_id,
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }
            
            cursor = collection.find(query).sort("timestamp", ASCENDING)
            snapshots = list(cursor)
            
            logger.debug(f"[MongoDB Storage] Retrieved {len(snapshots)} snapshots in range for {server_id}")
            return snapshots
            
        except PyMongoError as e:
            logger.error(f"[MongoDB Storage] PyMongo error getting range snapshots: {e}")
            return []
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error getting range snapshots: {e}")
            return []
    
    # ===== COMMAND TRACKING OPERATIONS =====
    
    def store_command(self, command: CommandExecution) -> bool:
        """Store command execution with enhanced metadata"""
        try:
            if not self.db:
                return False
            
            collection = self.collections['command_history']
            document = {
                'command_id': command.command_id,
                'server_id': command.server_id,
                'command_type': command.command_type,
                'command_text': command.command_text,
                'user_name': command.user_name,
                'timestamp': command.timestamp,
                'metadata': command.metadata,
                'created_at': datetime.utcnow(),
                'data_version': '2.0'
            }
            
            result = collection.insert_one(document)
            
            if result.inserted_id:
                logger.debug(f"[MongoDB Storage] ✅ Stored command {command.command_id}")
                return True
            else:
                logger.error(f"[MongoDB Storage] Failed to store command {command.command_id}")
                return False
                
        except PyMongoError as e:
            logger.error(f"[MongoDB Storage] PyMongo error storing command: {e}")
            return False
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error storing command: {e}")
            return False
    
    def get_command_history(self, server_id: str, hours: int = 24, 
                           command_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get command history with optimized filtering"""
        try:
            if not self.db:
                return []
            
            collection = self.collections['command_history']
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = {
                "server_id": server_id,
                "timestamp": {"$gte": cutoff_time}
            }
            
            if command_type:
                query["command_type"] = command_type
            
            cursor = collection.find(query).sort("timestamp", DESCENDING).limit(1000)
            commands = list(cursor)
            
            logger.debug(f"[MongoDB Storage] Retrieved {len(commands)} commands for {server_id}")
            return commands
            
        except PyMongoError as e:
            logger.error(f"[MongoDB Storage] PyMongo error getting commands: {e}")
            return []
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error getting commands: {e}")
            return []
    
    # ===== TREND ANALYSIS OPERATIONS =====
    
    def get_health_trends_aggregated(self, server_id: str, hours: int = 6) -> Dict[str, Any]:
        """Get health trends using optimized aggregation pipeline"""
        try:
            if not self.db:
                return {'success': False, 'error': 'no_database'}
            
            collection = self.collections['health_snapshots']
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            pipeline = [
                {
                    "$match": {
                        "server_id": server_id,
                        "timestamp": {"$gte": cutoff_time}
                    }
                },
                {
                    "$sort": {"timestamp": 1}
                },
                {
                    "$project": {
                        "_id": 0,
                        "timestamp": 1,
                        "health_data.statistics.fps": 1,
                        "health_data.statistics.memory_usage": 1,
                        "health_data.statistics.cpu_usage": 1,
                        "health_data.statistics.player_count": 1,
                        "health_data.statistics.response_time": 1
                    }
                },
                {
                    "$limit": 100  # Prevent excessive data
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            results = list(cursor)
            
            if results:
                trend_data = self._format_trend_data(results)
                logger.debug(f"[MongoDB Storage] ✅ Aggregated {len(results)} trend points for {server_id}")
                return {'success': True, 'trends': trend_data, 'count': len(results)}
            else:
                logger.debug(f"[MongoDB Storage] No trend data found for {server_id}")
                return {'success': False, 'error': 'no_data'}
                
        except PyMongoError as e:
            logger.error(f"[MongoDB Storage] PyMongo error in trend aggregation: {e}")
            return {'success': False, 'error': f'database_error: {e}'}
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error in trend aggregation: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_trend_data(self, raw_results: List[Dict]) -> Dict[str, Any]:
        """Format aggregated trend data for charts"""
        try:
            labels = []
            fps_data = []
            memory_data = []
            cpu_data = []
            player_data = []
            response_data = []
            
            for result in raw_results:
                # Format timestamp for chart labels
                timestamp = result.get('timestamp')
                if timestamp:
                    labels.append(timestamp.strftime('%H:%M'))
                
                # Extract statistics safely
                health_data = result.get('health_data', {})
                stats = health_data.get('statistics', {})
                
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
            logger.error(f"[MongoDB Storage] Error formatting trend data: {e}")
            return {}
    
    # ===== PERFORMANCE METRICS OPERATIONS =====
    
    def store_performance_metric(self, metric: HealthMetric) -> bool:
        """Store individual performance metric"""
        try:
            if not self.db:
                return False
            
            collection = self.collections['performance_metrics']
            document = {
                'metric_id': metric.metric_id,
                'server_id': metric.server_id,
                'metric_type': metric.metric_type,
                'metric_value': metric.metric_value,
                'timestamp': metric.timestamp,
                'metadata': metric.metadata,
                'created_at': datetime.utcnow()
            }
            
            result = collection.insert_one(document)
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error storing metric: {e}")
            return False
    
    def get_performance_summary(self, server_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary using aggregation"""
        try:
            if not self.db:
                return {}
            
            collection = self.collections['performance_metrics']
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            pipeline = [
                {
                    "$match": {
                        "server_id": server_id,
                        "timestamp": {"$gte": cutoff_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$metric_type",
                        "avg_value": {"$avg": "$metric_value"},
                        "min_value": {"$min": "$metric_value"},
                        "max_value": {"$max": "$metric_value"},
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            results = {doc["_id"]: doc for doc in cursor}
            
            logger.debug(f"[MongoDB Storage] Performance summary for {server_id}: {len(results)} metrics")
            return results
            
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error getting performance summary: {e}")
            return {}
    
    # ===== MAINTENANCE OPERATIONS =====
    
    def cleanup_old_data(self, days: int = 7) -> Dict[str, int]:
        """Clean up old data manually (TTL indexes handle this automatically)"""
        try:
            if not self.db:
                return {'error': 'no_database'}
            
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            cleanup_stats = {}
            
            # Clean health snapshots
            result = self.collections['health_snapshots'].delete_many({
                "timestamp": {"$lt": cutoff_time}
            })
            cleanup_stats['health_snapshots_deleted'] = result.deleted_count
            
            # Clean old commands (keep longer)
            command_cutoff = datetime.utcnow() - timedelta(days=days*4)
            result = self.collections['command_history'].delete_many({
                "timestamp": {"$lt": command_cutoff}
            })
            cleanup_stats['commands_deleted'] = result.deleted_count
            
            logger.info(f"[MongoDB Storage] Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"[MongoDB Storage] Cleanup error: {e}")
            return {'error': str(e)}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for monitoring"""
        try:
            if not self.db:
                return {'error': 'no_database'}
            
            stats = {}
            
            for name, collection in self.collections.items():
                try:
                    stats[name] = {
                        'document_count': collection.count_documents({}),
                        'size_bytes': self.db.command("collStats", collection.name)['size']
                    }
                except Exception as e:
                    stats[name] = {'error': str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"[MongoDB Storage] Error getting stats: {e}")
            return {'error': str(e)}
    
    # ===== HEALTH CHECK OPERATIONS =====
    
    def health_check(self) -> Dict[str, Any]:
        """Perform MongoDB storage health check"""
        try:
            if not self.db:
                return {
                    'status': 'unhealthy',
                    'error': 'no_database_connection',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Test basic operations
            start_time = time.time()
            
            # Test read operation
            test_collection = self.collections['health_snapshots']
            test_collection.find_one({}, {'_id': 1})
            
            # Test write operation (minimal document)
            test_doc = {
                'test': True,
                'timestamp': datetime.utcnow()
            }
            result = test_collection.insert_one(test_doc)
            
            # Clean up test document
            test_collection.delete_one({'_id': result.inserted_id})
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'indexes_created': self.indexes_created,
                'collections_available': len(self.collections),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
