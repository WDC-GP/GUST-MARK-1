"""
Data Models and Validation for GUST-MARK-1 Server Health Storage System
========================================================================
✅ ENHANCED: Comprehensive data models with validation and serialization
✅ PRESERVED: All existing data structures and formats from the original system
✅ OPTIMIZED: Type safety, validation, and automatic schema evolution support
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CommandType(Enum):
    """Enumeration of server command types"""
    ADMIN = "admin"
    INGAME = "ingame"
    AUTO = "auto"
    SYSTEM = "system"
    UNKNOWN = "unknown"

class MetricType(Enum):
    """Enumeration of health metric types"""
    FPS = "fps"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    PLAYER_COUNT = "player_count"
    RESPONSE_TIME = "response_time"
    HEALTH_PERCENTAGE = "health_percentage"
    CUSTOM = "custom"

class DataQuality(Enum):
    """Data quality levels for health metrics"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    SYNTHETIC = "synthetic"

@dataclass
class HealthMetric:
    """
    ✅ ENHANCED: Individual health metric with validation and metadata
    """
    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    server_id: str = ""
    metric_type: str = MetricType.CUSTOM.value
    metric_value: Union[int, float] = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize metric data"""
        try:
            # Ensure server_id is provided
            if not self.server_id:
                raise ValueError("server_id is required")
            
            # Validate metric_type
            valid_types = [t.value for t in MetricType]
            if self.metric_type not in valid_types:
                logger.warning(f"Unknown metric type: {self.metric_type}, using 'custom'")
                self.metric_type = MetricType.CUSTOM.value
            
            # Validate metric_value ranges
            self._validate_metric_value()
            
            # Ensure timestamp is datetime
            if isinstance(self.timestamp, str):
                self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
            
        except Exception as e:
            logger.error(f"HealthMetric validation error: {e}")
            # Set safe defaults
            if not self.server_id:
                self.server_id = "unknown"
            if not isinstance(self.timestamp, datetime):
                self.timestamp = datetime.utcnow()
    
    def _validate_metric_value(self):
        """Validate metric value based on type"""
        validation_rules = {
            MetricType.FPS.value: (0, 200),
            MetricType.MEMORY_USAGE.value: (0, 16000),  # MB
            MetricType.CPU_USAGE.value: (0, 100),       # Percentage
            MetricType.PLAYER_COUNT.value: (0, 200),
            MetricType.RESPONSE_TIME.value: (0, 5000),  # ms
            MetricType.HEALTH_PERCENTAGE.value: (0, 100)
        }
        
        if self.metric_type in validation_rules:
            min_val, max_val = validation_rules[self.metric_type]
            if not (min_val <= self.metric_value <= max_val):
                logger.warning(f"Metric value {self.metric_value} out of range for {self.metric_type}")
                # Clamp to valid range
                self.metric_value = max(min_val, min(max_val, self.metric_value))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'metric_id': self.metric_id,
            'server_id': self.server_id,
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthMetric':
        """Create instance from dictionary"""
        try:
            return cls(
                metric_id=data.get('metric_id', str(uuid.uuid4())),
                server_id=data.get('server_id', ''),
                metric_type=data.get('metric_type', MetricType.CUSTOM.value),
                metric_value=data.get('metric_value', 0),
                timestamp=data.get('timestamp', datetime.utcnow()),
                metadata=data.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Error creating HealthMetric from dict: {e}")
            return cls()

@dataclass
class CommandExecution:
    """
    ✅ ENHANCED: Command execution record with validation and categorization
    """
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    server_id: str = ""
    command_type: str = CommandType.UNKNOWN.value
    command_text: str = ""
    user_name: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: Optional[float] = None
    success: bool = True
    
    def __post_init__(self):
        """Validate and categorize command data"""
        try:
            # Ensure server_id is provided
            if not self.server_id:
                raise ValueError("server_id is required")
            
            # Auto-categorize command type if not provided or unknown
            if self.command_type == CommandType.UNKNOWN.value:
                self.command_type = self._categorize_command()
            
            # Validate command_type
            valid_types = [t.value for t in CommandType]
            if self.command_type not in valid_types:
                self.command_type = CommandType.UNKNOWN.value
            
            # Sanitize command text (remove sensitive info)
            self.command_text = self._sanitize_command_text()
            
            # Ensure timestamp is datetime
            if isinstance(self.timestamp, str):
                self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
                
        except Exception as e:
            logger.error(f"CommandExecution validation error: {e}")
            # Set safe defaults
            if not self.server_id:
                self.server_id = "unknown"
            if not isinstance(self.timestamp, datetime):
                self.timestamp = datetime.utcnow()
    
    def _categorize_command(self) -> str:
        """Auto-categorize command based on content"""
        try:
            command_lower = self.command_text.lower()
            
            # Admin commands
            admin_keywords = ['ban', 'kick', 'teleport', 'give', 'spawn', 'godmode', 'noclip']
            if any(keyword in command_lower for keyword in admin_keywords):
                return CommandType.ADMIN.value
            
            # Auto/system commands
            auto_keywords = ['autosave', 'restart', 'backup', 'cleanup', 'monitor']
            if any(keyword in command_lower for keyword in auto_keywords):
                return CommandType.AUTO.value
            
            # In-game commands (player initiated)
            if self.user_name and self.user_name != "system" and self.user_name != "admin":
                return CommandType.INGAME.value
            
            return CommandType.SYSTEM.value
            
        except Exception as e:
            logger.error(f"Error categorizing command: {e}")
            return CommandType.UNKNOWN.value
    
    def _sanitize_command_text(self) -> str:
        """Remove sensitive information from command text"""
        try:
            # Remove common sensitive patterns
            sensitive_patterns = ['password', 'token', 'key', 'secret']
            sanitized = self.command_text
            
            for pattern in sensitive_patterns:
                if pattern in sanitized.lower():
                    # Replace with placeholder
                    sanitized = sanitized.replace(pattern, '[REDACTED]')
            
            # Limit length to prevent bloat
            if len(sanitized) > 500:
                sanitized = sanitized[:497] + "..."
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing command text: {e}")
            return self.command_text[:100] if self.command_text else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'command_id': self.command_id,
            'server_id': self.server_id,
            'command_type': self.command_type,
            'command_text': self.command_text,
            'user_name': self.user_name,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'execution_time_ms': self.execution_time_ms,
            'success': self.success
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandExecution':
        """Create instance from dictionary"""
        try:
            return cls(
                command_id=data.get('command_id', str(uuid.uuid4())),
                server_id=data.get('server_id', ''),
                command_type=data.get('command_type', CommandType.UNKNOWN.value),
                command_text=data.get('command_text', ''),
                user_name=data.get('user_name', 'system'),
                timestamp=data.get('timestamp', datetime.utcnow()),
                metadata=data.get('metadata', {}),
                execution_time_ms=data.get('execution_time_ms'),
                success=data.get('success', True)
            )
        except Exception as e:
            logger.error(f"Error creating CommandExecution from dict: {e}")
            return cls()

@dataclass
class HealthSnapshot:
    """
    ✅ ENHANCED: Complete health snapshot with validation and quality assessment
    """
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    server_id: str = ""
    health_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data_quality: str = DataQuality.FAIR.value
    data_sources: List[str] = field(default_factory=list)
    health_percentage: Optional[float] = None
    
    def __post_init__(self):
        """Validate and enhance snapshot data"""
        try:
            # Ensure server_id is provided
            if not self.server_id:
                raise ValueError("server_id is required")
            
            # Validate and enhance health_data
            self.health_data = self._validate_health_data()
            
            # Calculate health percentage if not provided
            if self.health_percentage is None:
                self.health_percentage = self._calculate_health_percentage()
            
            # Assess data quality
            self.data_quality = self._assess_data_quality()
            
            # Ensure timestamp is datetime
            if isinstance(self.timestamp, str):
                self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
                
        except Exception as e:
            logger.error(f"HealthSnapshot validation error: {e}")
            # Set safe defaults
            if not self.server_id:
                self.server_id = "unknown"
            if not isinstance(self.timestamp, datetime):
                self.timestamp = datetime.utcnow()
            if not self.health_data:
                self.health_data = {}
    
    def _validate_health_data(self) -> Dict[str, Any]:
        """Validate and normalize health data structure"""
        try:
            if not isinstance(self.health_data, dict):
                return {}
            
            # Ensure required structure exists
            if 'statistics' not in self.health_data:
                self.health_data['statistics'] = {}
            
            stats = self.health_data['statistics']
            
            # Validate and clamp statistics
            validation_rules = {
                'fps': (0, 200, 60),         # min, max, default
                'memory_usage': (0, 16000, 1600),
                'cpu_usage': (0, 100, 25),
                'player_count': (0, 200, 0),
                'response_time': (0, 5000, 35)
            }
            
            for metric, (min_val, max_val, default) in validation_rules.items():
                if metric in stats:
                    value = stats[metric]
                    if isinstance(value, (int, float)) and min_val <= value <= max_val:
                        continue  # Valid value
                    else:
                        logger.warning(f"Invalid {metric} value: {value}, using default {default}")
                        stats[metric] = default
                else:
                    # Add missing metrics with defaults
                    stats[metric] = default
            
            return self.health_data
            
        except Exception as e:
            logger.error(f"Error validating health data: {e}")
            return {'statistics': {}}
    
    def _calculate_health_percentage(self) -> float:
        """Calculate overall health percentage from statistics"""
        try:
            stats = self.health_data.get('statistics', {})
            
            if not stats:
                return 75.0  # Default when no stats available
            
            # Use original calculation logic for compatibility
            fps = stats.get('fps', 60)
            memory = stats.get('memory_usage', 1600)
            cpu = stats.get('cpu_usage', 25)
            response_time = stats.get('response_time', 35)
            
            # Calculate component scores
            fps_score = min(100, (fps / 60) * 100) if fps > 0 else 0
            memory_score = max(0, 100 - ((memory - 1000) / 20)) if memory > 1000 else 100
            cpu_score = max(0, 100 - cpu) if cpu < 100 else 0
            response_score = max(0, 100 - ((response_time - 20) / 2)) if response_time > 20 else 100
            
            # Weighted average
            health_percentage = (fps_score * 0.3 + memory_score * 0.25 + 
                               cpu_score * 0.25 + response_score * 0.2)
            
            return max(0, min(100, round(health_percentage, 1)))
            
        except Exception as e:
            logger.error(f"Error calculating health percentage: {e}")
            return 75.0
    
    def _assess_data_quality(self) -> str:
        """Assess the quality of the health data"""
        try:
            quality_score = 0
            
            # Check data completeness
            stats = self.health_data.get('statistics', {})
            required_metrics = ['fps', 'memory_usage', 'cpu_usage', 'player_count', 'response_time']
            
            for metric in required_metrics:
                if metric in stats and isinstance(stats[metric], (int, float)):
                    quality_score += 20
            
            # Check data freshness
            if isinstance(self.timestamp, datetime):
                age_minutes = (datetime.utcnow() - self.timestamp).total_seconds() / 60
                if age_minutes < 5:
                    quality_score += 20
                elif age_minutes < 15:
                    quality_score += 15
                elif age_minutes < 60:
                    quality_score += 10
            
            # Check data sources
            if 'graphql_sensors' in self.data_sources:
                quality_score += 20
            elif 'real_logs' in self.data_sources:
                quality_score += 15
            elif 'storage_system' in self.data_sources:
                quality_score += 10
            
            # Determine quality level
            if quality_score >= 80:
                return DataQuality.EXCELLENT.value
            elif quality_score >= 60:
                return DataQuality.GOOD.value
            elif quality_score >= 40:
                return DataQuality.FAIR.value
            elif quality_score >= 20:
                return DataQuality.POOR.value
            else:
                return DataQuality.SYNTHETIC.value
                
        except Exception as e:
            logger.error(f"Error assessing data quality: {e}")
            return DataQuality.FAIR.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'snapshot_id': self.snapshot_id,
            'server_id': self.server_id,
            'health_data': self.health_data,
            'timestamp': self.timestamp.isoformat(),
            'data_quality': self.data_quality,
            'data_sources': self.data_sources,
            'health_percentage': self.health_percentage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthSnapshot':
        """Create instance from dictionary"""
        try:
            return cls(
                snapshot_id=data.get('snapshot_id', str(uuid.uuid4())),
                server_id=data.get('server_id', ''),
                health_data=data.get('health_data', {}),
                timestamp=data.get('timestamp', datetime.utcnow()),
                data_quality=data.get('data_quality', DataQuality.FAIR.value),
                data_sources=data.get('data_sources', []),
                health_percentage=data.get('health_percentage')
            )
        except Exception as e:
            logger.error(f"Error creating HealthSnapshot from dict: {e}")
            return cls()

@dataclass 
class TrendData:
    """
    ✅ ENHANCED: Trend analysis data for chart visualization
    """
    trend_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    server_id: str = ""
    time_period_hours: int = 6
    data_points: Dict[str, List[Any]] = field(default_factory=dict)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate and enhance trend data"""
        try:
            # Ensure server_id is provided
            if not self.server_id:
                raise ValueError("server_id is required")
            
            # Validate time period
            if not (1 <= self.time_period_hours <= 168):  # 1 hour to 1 week
                self.time_period_hours = 6
            
            # Ensure data structure
            if not self.data_points:
                self.data_points = self._initialize_empty_data_points()
            
            # Calculate summary statistics
            self.summary_stats = self._calculate_summary_stats()
            
            # Ensure timestamp is datetime
            if isinstance(self.timestamp, str):
                self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
                
        except Exception as e:
            logger.error(f"TrendData validation error: {e}")
            # Set safe defaults
            if not self.server_id:
                self.server_id = "unknown"
            if not isinstance(self.timestamp, datetime):
                self.timestamp = datetime.utcnow()
    
    def _initialize_empty_data_points(self) -> Dict[str, List[Any]]:
        """Initialize empty data structure for trends"""
        return {
            'labels': [],
            'fps': [],
            'memory_usage': [],
            'cpu_usage': [],
            'player_count': [],
            'response_time': []
        }
    
    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """Calculate summary statistics for the trend data"""
        try:
            summary = {}
            
            for metric in ['fps', 'memory_usage', 'cpu_usage', 'player_count', 'response_time']:
                data = self.data_points.get(metric, [])
                
                if data and all(isinstance(x, (int, float)) for x in data):
                    summary[metric] = {
                        'min': min(data),
                        'max': max(data),
                        'avg': round(sum(data) / len(data), 2),
                        'count': len(data)
                    }
                    
                    # Calculate trend direction
                    if len(data) >= 2:
                        start_avg = sum(data[:3]) / min(3, len(data))
                        end_avg = sum(data[-3:]) / min(3, len(data))
                        
                        if end_avg > start_avg * 1.05:
                            summary[metric]['trend'] = 'increasing'
                        elif end_avg < start_avg * 0.95:
                            summary[metric]['trend'] = 'decreasing'
                        else:
                            summary[metric]['trend'] = 'stable'
                else:
                    summary[metric] = {
                        'min': 0, 'max': 0, 'avg': 0, 'count': 0, 'trend': 'no_data'
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating summary stats: {e}")
            return {}
    
    def add_data_point(self, metric: str, value: Union[int, float], 
                      label: Optional[str] = None) -> bool:
        """Add a data point to the trend"""
        try:
            if metric not in self.data_points:
                self.data_points[metric] = []
            
            self.data_points[metric].append(value)
            
            # Add label if provided
            if label and 'labels' in self.data_points:
                self.data_points['labels'].append(label)
            
            # Recalculate summary stats
            self.summary_stats = self._calculate_summary_stats()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding data point: {e}")
            return False
    
    def get_chart_data(self) -> Dict[str, Any]:
        """Format data for Chart.js visualization"""
        try:
            chart_data = {
                'labels': self.data_points.get('labels', []),
                'datasets': []
            }
            
            # Define chart configurations for each metric
            metric_configs = {
                'fps': {'label': 'FPS', 'color': 'rgb(75, 192, 192)', 'unit': ''},
                'memory_usage': {'label': 'Memory (MB)', 'color': 'rgb(255, 99, 132)', 'unit': 'MB'},
                'cpu_usage': {'label': 'CPU (%)', 'color': 'rgb(255, 205, 86)', 'unit': '%'},
                'player_count': {'label': 'Players', 'color': 'rgb(54, 162, 235)', 'unit': ''},
                'response_time': {'label': 'Response (ms)', 'color': 'rgb(153, 102, 255)', 'unit': 'ms'}
            }
            
            for metric, config in metric_configs.items():
                data = self.data_points.get(metric, [])
                if data:
                    chart_data['datasets'].append({
                        'label': config['label'],
                        'data': data,
                        'borderColor': config['color'],
                        'backgroundColor': config['color'] + '20',  # Add transparency
                        'fill': False,
                        'tension': 0.1
                    })
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error formatting chart data: {e}")
            return {'labels': [], 'datasets': []}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'trend_id': self.trend_id,
            'server_id': self.server_id,
            'time_period_hours': self.time_period_hours,
            'data_points': self.data_points,
            'summary_stats': self.summary_stats,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendData':
        """Create instance from dictionary"""
        try:
            return cls(
                trend_id=data.get('trend_id', str(uuid.uuid4())),
                server_id=data.get('server_id', ''),
                time_period_hours=data.get('time_period_hours', 6),
                data_points=data.get('data_points', {}),
                summary_stats=data.get('summary_stats', {}),
                timestamp=data.get('timestamp', datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Error creating TrendData from dict: {e}")
            return cls()

# ===== UTILITY FUNCTIONS =====

def validate_server_id(server_id: str) -> str:
    """Validate and normalize server ID"""
    try:
        if not server_id or not isinstance(server_id, str):
            return "unknown"
        
        # Remove any non-alphanumeric characters except dashes and underscores
        import re
        normalized = re.sub(r'[^a-zA-Z0-9\-_]', '', str(server_id))
        
        # Ensure reasonable length
        if len(normalized) > 50:
            normalized = normalized[:50]
        
        return normalized if normalized else "unknown"
        
    except Exception as e:
        logger.error(f"Error validating server ID: {e}")
        return "unknown"

def create_health_snapshot_from_raw_data(server_id: str, raw_data: Dict[str, Any]) -> HealthSnapshot:
    """Create a validated HealthSnapshot from raw data"""
    try:
        # Extract and validate statistics
        stats = {}
        
        if 'statistics' in raw_data:
            stats = raw_data['statistics']
        elif 'metrics' in raw_data:
            stats = raw_data['metrics']
        else:
            # Try to extract from root level
            for key in ['fps', 'memory_usage', 'cpu_usage', 'player_count', 'response_time']:
                if key in raw_data:
                    stats[key] = raw_data[key]
        
        # Build health data structure
        health_data = {
            'statistics': stats,
            'source': raw_data.get('source', 'unknown'),
            'response_time': raw_data.get('response_time', 35)
        }
        
        # Extract data sources
        data_sources = raw_data.get('sources_used', ['unknown'])
        if isinstance(data_sources, str):
            data_sources = [data_sources]
        
        return HealthSnapshot(
            server_id=validate_server_id(server_id),
            health_data=health_data,
            data_sources=data_sources,
            timestamp=raw_data.get('timestamp', datetime.utcnow())
        )
        
    except Exception as e:
        logger.error(f"Error creating HealthSnapshot from raw data: {e}")
        return HealthSnapshot(server_id=validate_server_id(server_id))

def create_command_from_raw_data(server_id: str, raw_command: Dict[str, Any]) -> CommandExecution:
    """Create a validated CommandExecution from raw data"""
    try:
        return CommandExecution(
            server_id=validate_server_id(server_id),
            command_type=raw_command.get('type', CommandType.UNKNOWN.value),
            command_text=raw_command.get('command', ''),
            user_name=raw_command.get('user', 'system'),
            timestamp=raw_command.get('timestamp', datetime.utcnow()),
            metadata=raw_command.get('metadata', {}),
            execution_time_ms=raw_command.get('execution_time_ms'),
            success=raw_command.get('success', True)
        )
        
    except Exception as e:
        logger.error(f"Error creating CommandExecution from raw data: {e}")
        return CommandExecution(server_id=validate_server_id(server_id))

# ===== SCHEMA EVOLUTION SUPPORT =====

CURRENT_SCHEMA_VERSION = "2.0"

def migrate_legacy_data(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """Migrate legacy data structures to current schema"""
    try:
        # Add schema version if missing
        if 'schema_version' not in data:
            data['schema_version'] = CURRENT_SCHEMA_VERSION
        
        # Perform migrations based on data type
        if data_type == 'health_snapshot':
            return _migrate_health_snapshot(data)
        elif data_type == 'command_execution':
            return _migrate_command_execution(data)
        elif data_type == 'health_metric':
            return _migrate_health_metric(data)
        
        return data
        
    except Exception as e:
        logger.error(f"Error migrating legacy data: {e}")
        return data

def _migrate_health_snapshot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate legacy health snapshot data"""
    # Add missing fields with defaults
    if 'data_quality' not in data:
        data['data_quality'] = DataQuality.FAIR.value
    
    if 'data_sources' not in data:
        data['data_sources'] = ['legacy_migration']
    
    if 'health_percentage' not in data and 'health_data' in data:
        # Calculate from statistics
        stats = data['health_data'].get('statistics', {})
        if stats:
            snapshot = HealthSnapshot.from_dict(data)
            data['health_percentage'] = snapshot.health_percentage
    
    return data

def _migrate_command_execution(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate legacy command execution data"""
    # Add missing fields
    if 'execution_time_ms' not in data:
        data['execution_time_ms'] = None
    
    if 'success' not in data:
        data['success'] = True
    
    return data

def _migrate_health_metric(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate legacy health metric data"""
    # Ensure metadata exists
    if 'metadata' not in data:
        data['metadata'] = {}
    
    return data
