# GUST-MARK-1 Performance Optimization Guide

> **File Location**: `/doc/optimization/optimization_guide.md`
> **Last Updated**: June 19, 2025

## 🚀 Optimization Overview

This guide covers performance optimization strategies, best practices, and development workflow improvements for GUST-MARK-1's modular architecture with live player count monitoring.

## ⚡ Live Player Count Optimizations

### **Auto Command System Performance**
```javascript
// Optimized Auto Command Configuration
const autoConsoleConfig = {
    enabled: true,
    interval: 10000,              // 10 seconds - optimal for real-time feel
    commandsToSend: ['serverinfo'],
    rotateServers: true,          // Prevents API overload
    maxServersPerRound: 1,        // Conservative batch size
    debug: true,                  // Enable for monitoring
    
    // Performance optimizations
    maxConcurrentCommands: 3,     // Limit concurrent executions
    commandTimeout: 8000,         // 8-second timeout per command
    errorBackoffMs: 5000,         // 5-second delay on errors
    retryAttempts: 2              // Retry failed commands twice
};

// Enhanced auto command with performance monitoring
async function sendSingleAutoCommand(serverId, command) {
    const startTime = performance.now();
    
    try {
        // Performance tracking
        const performanceMetric = {
            serverId: serverId,
            command: command,
            startTime: startTime,
            status: 'executing'
        };
        
        // Execute command with timeout
        await Promise.race([
            executeCommand(serverId, command),
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Command timeout')), 
                autoConsoleConfig.commandTimeout)
            )
        ]);
        
        // Record success metrics
        const duration = performance.now() - startTime;
        performanceMetric.duration = duration;
        performanceMetric.status = 'success';
        
        recordPerformanceMetric(performanceMetric);
        
    } catch (error) {
        // Record error metrics
        const duration = performance.now() - startTime;
        recordPerformanceMetric({
            ...performanceMetric,
            duration: duration,
            status: 'error',
            error: error.message
        });
        
        throw error;
    }
}

// Performance metrics recorder
function recordPerformanceMetric(metric) {
    // Store in local metrics collection
    if (!window.playerCountMetrics) {
        window.playerCountMetrics = [];
    }
    
    window.playerCountMetrics.push(metric);
    
    // Keep only last 100 metrics
    if (window.playerCountMetrics.length > 100) {
        window.playerCountMetrics = window.playerCountMetrics.slice(-100);
    }
    
    // Log performance issues
    if (metric.duration > 5000) { // > 5 seconds
        console.warn(`Slow command execution: ${metric.command} for ${metric.serverId} took ${metric.duration.toFixed(2)}ms`);
    }
}
```

### **Logs-Based Polling Optimization**
```javascript
// Enhanced logs polling with intelligent batching
let logsBasedPlayerCountSystem = {
    enabled: false,
    polling: false,
    config: {
        interval: 30000,              // 30 seconds for logs (less frequent)
        maxRetries: 3,
        batchSize: 2,                 // Small batches to prevent overload
        staggerDelay: 5000,           // 5-second delay between batches
        adaptiveInterval: true,       // Adjust interval based on server count
        cacheTimeout: 60000           // 1-minute cache for repeated requests
    },
    cache: new Map(),                 // Response caching
    metrics: {
        requestCount: 0,
        errorCount: 0,
        avgResponseTime: 0,
        cacheHits: 0,
        cacheMisses: 0
    }
};

// Adaptive interval calculation
function calculateOptimalInterval(serverCount) {
    const baseInterval = 30000; // 30 seconds
    const serverMultiplier = Math.max(1, Math.floor(serverCount / 10));
    const maxInterval = 120000; // Max 2 minutes
    
    return Math.min(baseInterval * serverMultiplier, maxInterval);
}

// Intelligent caching system
class PlayerCountCache {
    constructor(ttl = 60000) {
        this.cache = new Map();
        this.ttl = ttl;
        this.hits = 0;
        this.misses = 0;
    }
    
    get(key) {
        const item = this.cache.get(key);
        if (item && Date.now() - item.timestamp < this.ttl) {
            this.hits++;
            return item.data;
        }
        
        if (item) {
            this.cache.delete(key); // Remove expired item
        }
        
        this.misses++;
        return null;
    }
    
    set(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
        
        // Cleanup old entries periodically
        if (this.cache.size > 100) {
            this.cleanup();
        }
    }
    
    cleanup() {
        const now = Date.now();
        for (const [key, item] of this.cache.entries()) {
            if (now - item.timestamp > this.ttl) {
                this.cache.delete(key);
            }
        }
    }
    
    getStats() {
        const total = this.hits + this.misses;
        return {
            hits: this.hits,
            misses: this.misses,
            hitRate: total > 0 ? ((this.hits / total) * 100).toFixed(1) + '%' : '0%',
            size: this.cache.size
        };
    }
}

// Global cache instance
const playerCountCache = new PlayerCountCache(60000); // 1-minute TTL
```

### **Enhanced UX Performance**
```javascript
// Optimized display updates with value preservation
function updatePlayerCountDisplay(serverId, playerData, status = 'success') {
    // Use requestAnimationFrame for smooth updates
    requestAnimationFrame(() => {
        const elements = getPlayerCountElements(serverId);
        
        // Batch DOM updates
        if (document.startBatch) {
            document.startBatch();
        }
        
        try {
            // Update status with optimized class changes
            updateStatusIndicator(elements.statusElement, status);
            
            // Only update values if we have new data (preserve old values)
            if (playerData && elements.countElement && elements.maxElement) {
                // Smooth number transitions
                animateValueChange(elements.countElement, playerData.current);
                animateValueChange(elements.maxElement, playerData.max);
                
                // Smooth progress bar animation
                animateProgressBar(elements.progressBar, playerData.percentage);
                
                // Update source with debounced animation
                updateSourceIndicator(elements.sourceElement, playerData.source);
            }
            
        } finally {
            if (document.endBatch) {
                document.endBatch();
            }
        }
    });
}

// Debounced animation functions
const animateValueChange = debounce((element, newValue) => {
    if (!element || element.textContent === String(newValue)) {
        return;
    }
    
    element.style.transition = 'color 0.3s ease';
    element.style.color = '#10b981'; // Green flash for updates
    element.textContent = newValue;
    
    setTimeout(() => {
        element.style.color = ''; // Return to original color
    }, 300);
}, 100);

// Optimized progress bar animation
function animateProgressBar(progressBar, targetPercentage) {
    if (!progressBar) return;
    
    const currentWidth = parseFloat(progressBar.style.width) || 0;
    const distance = targetPercentage - currentWidth;
    
    if (Math.abs(distance) < 0.5) {
        progressBar.style.width = `${targetPercentage}%`;
        return;
    }
    
    // Use CSS transitions for smooth animation
    progressBar.style.transition = 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
    progressBar.style.width = `${targetPercentage}%`;
    
    // Update color based on percentage
    requestAnimationFrame(() => {
        updateProgressBarColor(progressBar, targetPercentage);
    });
}

function updateProgressBarColor(progressBar, percentage) {
    progressBar.className = 'player-count-fill bg-gradient-to-r rounded-full h-full transition-all duration-500';
    
    if (percentage >= 90) {
        progressBar.className += ' from-red-500 to-red-600';
    } else if (percentage >= 75) {
        progressBar.className += ' from-orange-500 to-red-500';
    } else if (percentage >= 50) {
        progressBar.className += ' from-yellow-500 to-orange-500';
    } else {
        progressBar.className += ' from-green-400 to-cyan-400';
    }
}

// Utility functions for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, wait) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, wait);
        }
    };
}
```

## 📈 Frontend Performance Optimizations

### **Template Loading Optimization**
```html
<!-- Optimized Master Template Structure -->
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Critical CSS inline for faster first paint -->
    <style>
        .hidden { display: none; }
        .view { min-height: 100vh; }
        .player-count-container { 
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.08));
            transition: all 0.3s ease;
        }
        .player-count-value {
            color: #00ff9f !important;
            font-weight: 600;
            text-shadow: 0 0 4px rgba(0, 255, 159, 0.2);
            transition: color 0.3s ease;
        }
    </style>
    
    <!-- Preload critical resources -->
    <link rel="preload" href="/static/css/themes.css" as="style">
    <link rel="preload" href="/static/js/components/player-count.js" as="script">
    
    <!-- External CSS with media queries for better loading -->
    <link href="tailwindcss" rel="stylesheet" media="screen">
    <link href="/static/css/themes.css" rel="stylesheet" media="screen">
</head>
<body>
    <!-- Critical above-the-fold content first -->
    {% include 'base/sidebar.html' %}
    
    <!-- Lazy-loaded view components with loading="lazy" optimization -->
    {% for view in ['dashboard', 'server_manager', 'console', 'events', 'economy', 'gambling', 'clans', 'user_management', 'logs'] %}
        {% include 'views/' + view + '.html' %}
    {% endfor %}
    
    <!-- Optimized JavaScript loading order -->
    {% include 'scripts/main.js.html' %}       <!-- Core + Player Count Display -->
    {% include 'scripts/logs.js.html' %}       <!-- Auto Commands + Logs API -->
    {% include 'scripts/console.js.html' %}    <!-- Logs-integrated triggers -->
    <!-- Additional modules loaded after core with defer -->
    <script defer>
        // Initialize non-critical components after page load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initializeNonCriticalComponents, 100);
        });
    </script>
</body>
</html>
```

### **JavaScript Module Performance**
```javascript
// Performance-optimized module initialization
(function() {
    'use strict';
    
    // Module initialization with performance tracking
    const moduleStartTime = performance.now();
    
    // Lazy loading for non-critical functions
    const lazyFunctions = new Map();
    
    // Core module API with performance optimization
    const moduleAPI = {
        initialize: async function() {
            try {
                // Prioritized initialization order
                await this.setupCriticalEventListeners();
                await this.initializePlayerCountSystem();
                await this.loadInitialData();
                
                const initTime = performance.now() - moduleStartTime;
                console.log(`✅ Module initialized in ${initTime.toFixed(2)}ms`);
                
                // Preload non-critical functions in background
                this.preloadNonCriticalFunctions();
                
            } catch (error) {
                console.error('Module initialization failed:', error);
                throw error;
            }
        },
        
        // Debounced operations for performance
        debouncedRefresh: debounce(function() {
            this.refreshPlayerCounts();
        }, 1000),
        
        // Throttled updates for high-frequency events
        throttledUpdate: throttle(function(data) {
            this.updateDisplay(data);
        }, 100),
        
        // Lazy function loader
        getLazyFunction: function(name) {
            if (!lazyFunctions.has(name)) {
                // Load function on demand
                const func = this.loadFunction(name);
                lazyFunctions.set(name, func);
            }
            return lazyFunctions.get(name);
        },
        
        preloadNonCriticalFunctions: function() {
            // Preload in idle time
            if (window.requestIdleCallback) {
                window.requestIdleCallback(() => {
                    this.loadNonCriticalFunctions();
                });
            } else {
                setTimeout(() => this.loadNonCriticalFunctions(), 1000);
            }
        }
    };
    
    // Immediate module exposure
    window.moduleAPI = moduleAPI;
    
    // Deferred initialization to avoid blocking
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => moduleAPI.initialize(), 0);
        });
    } else {
        setTimeout(() => moduleAPI.initialize(), 0);
    }
})();

// Performance monitoring utilities
class PerformanceTracker {
    constructor() {
        this.marks = new Map();
        this.measures = new Map();
    }
    
    mark(name) {
        this.marks.set(name, performance.now());
        if (performance.mark) {
            performance.mark(name);
        }
    }
    
    measure(name, startMark, endMark = null) {
        const start = this.marks.get(startMark);
        const end = endMark ? this.marks.get(endMark) : performance.now();
        
        if (start !== undefined) {
            const duration = end - start;
            this.measures.set(name, duration);
            
            if (performance.measure) {
                performance.measure(name, startMark, endMark);
            }
            
            return duration;
        }
        return null;
    }
    
    getReport() {
        return {
            marks: Object.fromEntries(this.marks),
            measures: Object.fromEntries(this.measures)
        };
    }
}

// Global performance tracker
window.performanceTracker = new PerformanceTracker();
```

## 🗄️ Backend Performance Optimizations

### **Database Query Optimization**
```python
# Optimized server data retrieval with advanced caching
import functools
import time
import redis
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class AdvancedServerCache:
    def __init__(self, redis_client=None, ttl: int = 60):
        self.memory_cache: Dict = {}
        self.redis_client = redis_client
        self.ttl = ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'redis_hits': 0
        }
    
    def get(self, key: str) -> Optional[Dict]:
        # Try memory cache first (fastest)
        if key in self.memory_cache:
            data, timestamp = self.memory_cache[key]
            if time.time() - timestamp < self.ttl:
                self.stats['hits'] += 1
                self.stats['memory_hits'] += 1
                return data
            else:
                del self.memory_cache[key]
        
        # Try Redis cache (network but persistent)
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    data = json.loads(cached_data)
                    # Store in memory cache for next time
                    self.memory_cache[key] = (data, time.time())
                    self.stats['hits'] += 1
                    self.stats['redis_hits'] += 1
                    return data
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        self.stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Dict):
        # Store in memory cache
        self.memory_cache[key] = (value, time.time())
        
        # Store in Redis cache
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key, 
                    self.ttl, 
                    json.dumps(value, default=str)
                )
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
    
    def get_stats(self):
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': f"{hit_rate:.1f}%",
            'memory_cache_size': len(self.memory_cache)
        }

# Initialize enhanced cache
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # Test connection
except:
    redis_client = None
    logger.info("Redis not available, using memory cache only")

server_cache = AdvancedServerCache(redis_client, ttl=30)

@functools.lru_cache(maxsize=100)
def get_optimized_server_list():
    """Cached server list retrieval with multiple optimization layers"""
    cache_key = 'server_list_active'
    
    # Check cache first
    cached_data = server_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Optimized database query with projection and indexing
        servers = db.servers.find(
            {
                'isActive': True,
                'status': {'$ne': 'deleted'}
            },
            {
                '_id': 0,
                'serverId': 1, 
                'serverName': 1, 
                'serverRegion': 1, 
                'status': 1,
                'lastPlayerCount': 1,
                'lastPlayerUpdate': 1
            }
        ).sort('serverName', 1).limit(50)  # Reasonable limit with sorting
        
        server_list = list(servers)
        
        # Enhance with cached player count data
        for server in server_list:
            player_cache_key = f"player_count_{server['serverId']}"
            cached_player_data = server_cache.get(player_cache_key)
            if cached_player_data:
                server['cachedPlayerCount'] = cached_player_data
        
        # Cache the results
        server_cache.set(cache_key, server_list)
        
        return server_list
        
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return []

# Database connection optimization
class OptimizedDatabaseManager:
    def __init__(self, mongo_uri=None):
        self.mongo_client = None
        self.db = None
        self.connection_pool_size = 50
        self.max_idle_time = 30000
        
        if mongo_uri:
            try:
                self.mongo_client = MongoClient(
                    mongo_uri,
                    maxPoolSize=self.connection_pool_size,
                    minPoolSize=10,
                    maxIdleTimeMS=self.max_idle_time,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=20000
                )
                self.db = self.mongo_client.gust_db
                self.use_mongodb = True
                
                # Create indexes for performance
                self.create_indexes()
                
            except Exception as e:
                logger.error(f"MongoDB connection failed: {e}")
                self.use_mongodb = False
        else:
            self.use_mongodb = False
    
    def create_indexes(self):
        """Create database indexes for optimal query performance"""
        try:
            # Server collection indexes
            self.db.servers.create_index([('serverId', 1)], unique=True)
            self.db.servers.create_index([('isActive', 1), ('status', 1)])
            self.db.servers.create_index([('lastPlayerUpdate', -1)])
            
            # Player count specific indexes
            self.db.servers.create_index([('serverId', 1), ('lastPlayerUpdate', -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
```

### **API Response Optimization**
```python
# Optimized logs API with comprehensive performance monitoring
from flask import Blueprint, request, jsonify, g
import time
import threading
from collections import deque
from contextlib import contextmanager

# Performance monitoring decorator
def performance_monitor(operation_name):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record successful operation
                performance_tracker.record_operation(
                    operation_name, 
                    duration, 
                    'success'
                )
                
                # Add performance headers
                if hasattr(result, 'headers'):
                    result.headers['X-Response-Time'] = f"{duration*1000:.2f}ms"
                    result.headers['X-Cache-Status'] = getattr(g, 'cache_status', 'miss')
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record failed operation
                performance_tracker.record_operation(
                    operation_name, 
                    duration, 
                    'error',
                    str(e)
                )
                
                raise
                
        return decorated_function
    return decorator

@logs_bp.route('/api/logs/player-count/<server_id>', methods=['POST'])
@require_auth_and_rate_limit('player_count')
@performance_monitor('player_count_api')
def get_player_count_from_logs(server_id):
    """Highly optimized player count retrieval from logs"""
    start_time = time.time()
    
    try:
        # Input validation with early return
        if not server_id or len(server_id) > 20 or not server_id.isalnum():
            return jsonify({
                'success': False, 
                'error': 'Invalid server ID',
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }), 400
        
        # Check cache first
        cache_key = f'player_count_{server_id}'
        cached_result = server_cache.get(cache_key)
        if cached_result:
            g.cache_status = 'hit'
            cached_result['cached'] = True
            cached_result['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            return jsonify({'success': True, 'data': cached_result})
        
        g.cache_status = 'miss'
        
        # Optimized log parsing with streaming
        with performance_tracker.measure_time('log_parsing'):
            log_data = parse_server_logs_optimized(server_id)
        
        with performance_tracker.measure_time('player_extraction'):
            player_data = extract_player_count_fast(log_data)
        
        if player_data:
            result = {
                'current': player_data['current'],
                'max': player_data['max'],
                'percentage': player_data['percentage'],
                'timestamp': datetime.now().isoformat(),
                'source': 'server_logs',
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }
            
            # Cache successful results with shorter TTL for real-time feel
            server_cache.set(cache_key, result)
            
            # Update database with latest player count (async)
            threading.Thread(
                target=update_server_player_count_async,
                args=(server_id, player_data),
                daemon=True
            ).start()
            
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({
                'success': False, 
                'error': 'No recent player count data available',
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }), 404
            
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"Player count API error for {server_id}: {e}")
        
        return jsonify({
            'success': False, 
            'error': 'Internal server error',
            'response_time_ms': round(error_duration * 1000, 2)
        }), 500

def parse_server_logs_optimized(server_id: str) -> Dict:
    """Highly optimized log parsing with streaming and limited scope"""
    try:
        # Only parse very recent logs (last 2 minutes for real-time)
        cutoff_time = datetime.now() - timedelta(minutes=2)
        
        log_file_path = f'data/logs/{server_id}.log'
        
        if not os.path.exists(log_file_path):
            return {'entries': []}
        
        # Use memory mapping for large files
        import mmap
        
        log_entries = []
        with open(log_file_path, 'rb') as f:
            # Memory map the file for efficient reading
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Read from end of file (most recent entries first)
                mm.seek(0, 2)  # Seek to end
                file_size = mm.tell()
                
                # Read last 64KB (should contain recent entries)
                read_size = min(65536, file_size)
                mm.seek(max(0, file_size - read_size))
                
                # Read and split lines
                content = mm.read().decode('utf-8', errors='ignore')
                lines = content.split('\n')
                
                # Process lines in reverse order (most recent first)
                for line in reversed(lines):
                    if len(log_entries) >= 50:  # Limit for performance
                        break
                        
                    try:
                        # Quick timestamp check
                        if len(line) < 19:
                            continue
                            
                        timestamp_str = line[:19]
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        if timestamp < cutoff_time:
                            break  # Stop processing older entries
                        
                        # Quick keyword check
                        line_lower = line.lower()
                        if any(keyword in line_lower for keyword in ['players:', 'serverinfo', 'online:', 'connected:']):
                            log_entries.append(line.strip())
                            
                    except (ValueError, IndexError):
                        continue
        
        return {'entries': log_entries}
        
    except Exception as e:
        logger.error(f"Optimized log parsing error for {server_id}: {e}")
        return {'entries': []}

def extract_player_count_fast(log_data: Dict) -> Optional[Dict]:
    """Ultra-fast extraction using compiled regex patterns"""
    import re
    
    # Pre-compiled regex patterns for performance
    if not hasattr(extract_player_count_fast, 'patterns'):
        extract_player_count_fast.patterns = [
            re.compile(r'players:\s*(\d+)/(\d+)', re.IGNORECASE),
            re.compile(r'online:\s*(\d+)\s*of\s*(\d+)', re.IGNORECASE),
            re.compile(r'connected:\s*(\d+)/(\d+)', re.IGNORECASE),
            re.compile(r'population:\s*(\d+)/(\d+)', re.IGNORECASE)
        ]
    
    entries = log_data.get('entries', [])
    
    # Process most recent entries first
    for entry in entries:
        for pattern in extract_player_count_fast.patterns:
            match = pattern.search(entry)
            if match:
                try:
                    current = int(match.group(1))
                    max_players = int(match.group(2))
                    
                    # Validate reasonable values
                    if 0 <= current <= max_players <= 1000:
                        percentage = round((current / max_players) * 100) if max_players > 0 else 0
                        
                        return {
                            'current': current,
                            'max': max_players,
                            'percentage': percentage,
                            'raw_entry': entry,
                            'extraction_method': 'regex_optimized'
                        }
                except (ValueError, ZeroDivisionError):
                    continue
    
    return None

def update_server_player_count_async(server_id, player_data):
    """Async database update to avoid blocking API response"""
    try:
        if db and hasattr(db, 'servers'):
            db.servers.update_one(
                {'serverId': server_id},
                {
                    '$set': {
                        'lastPlayerCount': player_data,
                        'lastPlayerUpdate': datetime.now()
                    }
                },
                upsert=False
            )
    except Exception as e:
        logger.error(f"Async player count update error for {server_id}: {e}")
```

## 📊 Performance Monitoring

### **Real-time Performance Metrics**
```python
# Comprehensive performance monitoring system
import psutil
import threading
from collections import deque
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PerformanceMetric:
    timestamp: float
    cpu_percent: float
    memory_mb: float
    active_connections: int
    requests_per_second: float
    response_time_ms: float
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0

class AdvancedPerformanceMonitor:
    def __init__(self, max_metrics=1000):
        self.metrics = deque(maxlen=max_metrics)
        self.active_requests = 0
        self.total_requests = 0
        self.request_times = deque(maxlen=200)
        self.error_count = 0
        self.operation_stats = {}
        self.alerts = []
        self.monitoring = False
        
    def start_monitoring(self, interval: int = 30):
        """Start comprehensive performance monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        
        def monitor():
            while self.monitoring:
                try:
                    # Collect system metrics
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    memory_mb = memory.used / 1024 / 1024
                    
                    # Calculate request metrics
                    now = time.time()
                    recent_requests = [t for t in self.request_times if now - t < 60]
                    requests_per_second = len(recent_requests) / 60
                    
                    # Calculate average response time
                    if self.request_times:
                        avg_response_time = sum(self.request_times) / len(self.request_times) * 1000
                    else:
                        avg_response_time = 0
                    
                    # Calculate cache hit rate
                    cache_stats = server_cache.get_stats() if 'server_cache' in globals() else {}
                    cache_hit_rate = float(cache_stats.get('hit_rate', '0%').rstrip('%'))
                    
                    # Calculate error rate
                    error_rate = (self.error_count / max(self.total_requests, 1)) * 100
                    
                    # Store metric
                    metric = PerformanceMetric(
                        timestamp=now,
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                        active_connections=self.active_requests,
                        requests_per_second=requests_per_second,
                        response_time_ms=avg_response_time,
                        cache_hit_rate=cache_hit_rate,
                        error_rate=error_rate
                    )
                    
                    self.metrics.append(metric)
                    
                    # Check for performance issues
                    self._check_performance_alerts(metric)
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Performance monitoring error: {e}")
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.info("Advanced performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        logger.info("Performance monitoring stopped")
    
    def record_request(self, response_time: float, error: bool = False):
        """Record request completion with detailed metrics"""
        self.request_times.append(response_time)
        self.total_requests += 1
        
        if error:
            self.error_count += 1
    
    def record_operation(self, operation_name: str, duration: float, status: str, error_msg: str = None):
        """Record specific operation performance"""
        if operation_name not in self.operation_stats:
            self.operation_stats[operation_name] = {
                'count': 0,
                'total_time': 0,
                'error_count': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }
        
        stats = self.operation_stats[operation_name]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        
        if status == 'error':
            stats['error_count'] += 1
        
        # Log slow operations
        if duration > 2.0:  # > 2 seconds
            logger.warning(f"Slow operation: {operation_name} took {duration:.2f}s")
            if error_msg:
                logger.warning(f"Error details: {error_msg}")
    
    @contextmanager
    def measure_time(self, operation_name):
        """Context manager for measuring operation time"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_operation(operation_name, duration, 'success')
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        if not self.metrics:
            return {}
        
        recent_metrics = list(self.metrics)[-10:]  # Last 10 readings
        
        summary = {
            'current_cpu': recent_metrics[-1].cpu_percent,
            'current_memory': recent_metrics[-1].memory_mb,
            'avg_response_time': sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics),
            'requests_per_second': recent_metrics[-1].requests_per_second,
            'total_requests': self.total_requests,
            'error_rate': recent_metrics[-1].error_rate,
            'cache_hit_rate': recent_metrics[-1].cache_hit_rate,
            'uptime_minutes': (time.time() - recent_metrics[0].timestamp) / 60,
            'active_alerts': len(self.alerts),
            'operation_stats': self.operation_stats
        }
        
        return summary
    
    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check for performance issues and generate alerts"""
        alerts = []
        
        # CPU alerts
        if metric.cpu_percent > 80:
            alerts.append({
                'type': 'high_cpu',
                'severity': 'warning' if metric.cpu_percent < 90 else 'critical',
                'message': f"High CPU usage: {metric.cpu_percent:.1f}%",
                'timestamp': metric.timestamp
            })
        
        # Memory alerts
        if metric.memory_mb > 1024:  # > 1GB
            alerts.append({
                'type': 'high_memory',
                'severity': 'warning' if metric.memory_mb < 2048 else 'critical',
                'message': f"High memory usage: {metric.memory_mb:.1f}MB",
                'timestamp': metric.timestamp
            })
        
        # Response time alerts
        if metric.response_time_ms > 2000:  # > 2 seconds
            alerts.append({
                'type': 'slow_response',
                'severity': 'warning' if metric.response_time_ms < 5000 else 'critical',
                'message': f"Slow response time: {metric.response_time_ms:.1f}ms",
                'timestamp': metric.timestamp
            })
        
        # Error rate alerts
        if metric.error_rate > 5:  # > 5% error rate
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'warning' if metric.error_rate < 10 else 'critical',
                'message': f"High error rate: {metric.error_rate:.1f}%",
                'timestamp': metric.timestamp
            })
        
        # Cache performance alerts
        if metric.cache_hit_rate < 70:  # < 70% hit rate
            alerts.append({
                'type': 'low_cache_hit_rate',
                'severity': 'info',
                'message': f"Low cache hit rate: {metric.cache_hit_rate:.1f}%",
                'timestamp': metric.timestamp
            })
        
        # Add new alerts
        for alert in alerts:
            # Avoid duplicate alerts (within 5 minutes)
            recent_alerts = [a for a in self.alerts if metric.timestamp - a['timestamp'] < 300]
            if not any(a['type'] == alert['type'] for a in recent_alerts):
                self.alerts.append(alert)
                logger.warning(f"Performance Alert: {alert['message']}")
        
        # Clean old alerts (older than 1 hour)
        self.alerts = [a for a in self.alerts if metric.timestamp - a['timestamp'] < 3600]

# Global performance monitor instance
performance_tracker = AdvancedPerformanceMonitor()

# Auto-start monitoring
performance_tracker.start_monitoring(30)  # 30-second intervals
```

## 📈 Performance Best Practices

### **Frontend Best Practices**
```javascript
// 1. Debounce expensive operations
const debouncedPlayerCountRefresh = debounce((serverId) => {
    refreshPlayerCount(serverId);
}, 1000);

// 2. Use requestAnimationFrame for smooth animations
function smoothProgressBarUpdate(element, targetPercentage) {
    const currentWidth = parseFloat(element.style.width) || 0;
    const distance = targetPercentage - currentWidth;
    const step = distance * 0.1;
    
    function animate() {
        const newWidth = currentWidth + step;
        
        if (Math.abs(targetPercentage - newWidth) > 0.5) {
            element.style.width = `${newWidth}%`;
            requestAnimationFrame(animate);
        } else {
            element.style.width = `${targetPercentage}%`;
        }
    }
    animate();
}

// 3. Efficient DOM queries with caching
const elementCache = new Map();
function getCachedElement(id) {
    if (!elementCache.has(id)) {
        const element = document.getElementById(id);
        if (element) {
            elementCache.set(id, element);
        }
    }
    return elementCache.get(id);
}

// 4. Batch DOM updates
function batchPlayerCountUpdates(updates) {
    // Use DocumentFragment for multiple updates
    const fragment = document.createDocumentFragment();
    
    updates.forEach(update => {
        const element = getCachedElement(update.elementId);
        if (element) {
            const clone = element.cloneNode(true);
            clone.textContent = update.value;
            fragment.appendChild(clone);
        }
    });
    
    // Single DOM update
    requestAnimationFrame(() => {
        const container = document.getElementById('player-counts-container');
        if (container) {
            container.appendChild(fragment);
        }
    });
}

// 5. Intersection Observer for lazy loading
const lazyLoadObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const element = entry.target;
            const serverId = element.dataset.serverId;
            
            if (serverId && !element.dataset.loaded) {
                loadPlayerCountForServer(serverId);
                element.dataset.loaded = 'true';
                lazyLoadObserver.unobserve(element);
            }
        }
    });
});

// 6. Memory management
function cleanupPlayerCountSystem() {
    // Clear intervals
    if (logsBasedPlayerCountSystem.intervalId) {
        clearInterval(logsBasedPlayerCountSystem.intervalId);
    }
    
    // Clear caches
    playerCountCache.cache.clear();
    elementCache.clear();
    
    // Remove event listeners
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    
    console.log('Player count system cleaned up');
}

// Handle page visibility for performance
function handleVisibilityChange() {
    if (document.hidden) {
        // Pause polling when page is hidden
        if (logsBasedPlayerCountSystem.polling) {
            stopPlayerCountPolling();
            logsBasedPlayerCountSystem.wasPolling = true;
        }
    } else {
        // Resume polling when page becomes visible
        if (logsBasedPlayerCountSystem.wasPolling) {
            startPlayerCountPolling();
            logsBasedPlayerCountSystem.wasPolling = false;
        }
    }
}

document.addEventListener('visibilitychange', handleVisibilityChange);
```

### **Backend Best Practices**
```python
# 1. Connection pooling optimization
from pymongo import MongoClient
from pymongo.pool import Pool

# Optimized connection settings
client = MongoClient(
    host='localhost',
    port=27017,
    maxPoolSize=50,          # Max connections
    minPoolSize=10,          # Min connections to keep alive
    maxIdleTimeMS=30000,     # 30 seconds idle timeout
    serverSelectionTimeoutMS=5000,  # 5 seconds connection timeout
    connectTimeoutMS=10000,  # 10 seconds connect timeout
    socketTimeoutMS=20000,   # 20 seconds socket timeout
    retryWrites=True,        # Retry failed writes
    w='majority'             # Write concern
)

# 2. Async request handling with connection pooling
import asyncio
import aiohttp
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

async def create_optimized_app():
    """Create optimized async application"""
    app = aiohttp.web.Application()
    
    # Setup session with encryption
    secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')
    setup(app, EncryptedCookieStorage(secret_key.encode()))
    
    # Connection pooling for external APIs
    connector = aiohttp.TCPConnector(
        limit=100,              # Total connection pool size
        limit_per_host=30,      # Connections per host
        ttl_dns_cache=300,      # DNS cache TTL
        use_dns_cache=True,     # Enable DNS caching
        keepalive_timeout=30,   # Keep connections alive
        enable_cleanup_closed=True
    )
    
    app['http_session'] = aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=30)
    )
    
    return app

async def fetch_multiple_server_data(server_ids):
    """Fetch data for multiple servers concurrently"""
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
        
        async def fetch_single_server(server_id):
            async with semaphore:
                try:
                    return await fetch_server_player_count(session, server_id)
                except Exception as e:
                    logger.error(f"Failed to fetch data for {server_id}: {e}")
                    return None
        
        tasks = [fetch_single_server(server_id) for server_id in server_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and None results
        valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        return valid_results

# 3. Response compression and caching
from flask import Flask
from flask_compress import Compress
from flask_caching import Cache

app = Flask(__name__)

# Enable gzip compression
Compress(app)

# Setup caching
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 1,
    'CACHE_DEFAULT_TIMEOUT': 300
})

# 4. Advanced caching strategies
from functools import wraps
import hashlib

def smart_cache(ttl=60, key_prefix=''):
    """Smart caching decorator with automatic invalidation"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{key_prefix}_{func.__name__}_{str(args)}_{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, timeout=ttl)
            
            return result
        return wrapper
    return decorator

# 5. Database query optimization
def create_optimized_indexes():
    """Create optimized database indexes"""
    indexes = [
        # Player count queries
        [('serverId', 1), ('lastPlayerUpdate', -1)],
        [('isActive', 1), ('status', 1)],
        [('serverRegion', 1), ('isActive', 1)],
        
        # Compound indexes for complex queries
        [('isActive', 1), ('lastPlayerUpdate', -1), ('serverId', 1)],
        [('status', 1), ('serverRegion', 1), ('isActive', 1)]
    ]
    
    for index in indexes:
        try:
            db.servers.create_index(index, background=True)
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

# 6. Memory management
import gc
import tracemalloc

def monitor_memory_usage():
    """Monitor memory usage and trigger cleanup when needed"""
    tracemalloc.start()
    
    def check_memory():
        current, peak = tracemalloc.get_traced_memory()
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024
        
        logger.info(f"Memory usage: {current_mb:.2f}MB (peak: {peak_mb:.2f}MB)")
        
        # Trigger garbage collection if memory usage is high
        if current_mb > 512:  # > 512MB
            logger.info("High memory usage detected, triggering garbage collection")
            gc.collect()
            
        return current_mb, peak_mb
    
    return check_memory

memory_monitor = monitor_memory_usage()
```

## 🎯 Performance Targets

### **Target Metrics**
- **Page Load Time**: < 2 seconds
- **First Contentful Paint**: < 1.5 seconds
- **Player Count Update**: < 500ms from trigger
- **Auto Command Execution**: < 3 seconds per command
- **Logs API Response**: < 1 second
- **Memory Usage**: < 512MB for 50+ servers
- **CPU Usage**: < 30% under normal load
- **Cache Hit Rate**: > 80%
- **Error Rate**: < 2%

### **Monitoring Alerts**
- **High Memory**: > 1GB usage
- **Slow Responses**: > 5 seconds API response
- **High Error Rate**: > 5% failed requests
- **Connection Issues**: > 10 failed WebSocket connections
- **Low Cache Performance**: < 70% hit rate
- **High CPU**: > 80% sustained usage

### **Performance Testing Schedule**
- **Daily**: Automated performance regression tests
- **Weekly**: Load testing with simulated traffic
- **Monthly**: Comprehensive performance audit
- **Quarterly**: Capacity planning and optimization review

## 🔧 Development Workflow Optimization

### **Hot Reload Development Setup**
```python
# development/hot_reload.py
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TemplateReloadHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        self.last_reload = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only reload for relevant files
        if event.src_path.endswith(('.html', '.js.html', '.css', '.py')):
            current_time = time.time()
            
            # Debounce rapid file changes
            if current_time - self.last_reload > 1:
                print(f"🔄 Reloading due to change: {event.src_path}")
                
                if event.src_path.endswith('.py'):
                    # Python file changed - restart required
                    print("🔄 Python file changed - restart required")
                    os._exit(1)
                else:
                    # Template/static file - reload templates
                    if hasattr(self.app, 'jinja_env'):
                        self.app.jinja_env.cache = {}
                
                self.last_reload = current_time

def setup_hot_reload(app):
    """Setup hot reload for development"""
    if app.debug:
        event_handler = TemplateReloadHandler(app)
        observer = Observer()
        observer.schedule(event_handler, 'templates/', recursive=True)
        observer.schedule(event_handler, 'static/', recursive=True)
        observer.schedule(event_handler, 'routes/', recursive=True)
        observer.start()
        print("🔥 Hot reload enabled for templates, static files, and routes")
        return observer
    return None
```

---

*Performance guide updated: June 19, 2025*  
*Includes comprehensive live player count optimizations and monitoring*  
*Next review: September 19, 2025*

**Summary**: This optimization guide provides comprehensive performance strategies for GUST-MARK-1's modular architecture with live player count monitoring, covering frontend optimizations, backend performance, caching strategies, and real-time monitoring systems to ensure optimal performance under all conditions.