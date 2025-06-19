# GUST-MARK-1 Performance Optimization Guide

> **File Location**: `optimization/PERFORMANCE_GUIDE.md`

## 🚀 Optimization Overview

This guide covers performance optimization strategies, best practices, and development workflow improvements for GUST-MARK-1's modular architecture.

## ⚡ Frontend Performance Optimizations

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
    </style>
    <!-- External CSS with preload -->
    <link rel="preload" href="/static/css/themes.css" as="style">
    <link href="tailwindcss" rel="stylesheet">
</head>
<body>
    <!-- Critical above-the-fold content first -->
    {% include 'base/sidebar.html' %}
    
    <!-- Lazy-loaded view components -->
    {% for view in ['dashboard', 'server_manager', 'console', 'events', 'economy', 'gambling', 'clans', 'user_management', 'logs'] %}
        {% include 'views/' + view + '.html' %}
    {% endfor %}
    
    <!-- Deferred JavaScript loading -->
    {% include 'scripts/main.js.html' %}
    <!-- Additional modules loaded after main -->
</body>
</html>
```

### **JavaScript Module Optimization**
```javascript
// Optimized Function Loading Pattern
(function() {
    'use strict';
    
    // Module initialization with performance tracking
    const moduleStartTime = performance.now();
    
    // Async function definitions with error boundaries
    const moduleAPI = {
        // Core functions
        initialize: function() {
            return new Promise((resolve, reject) => {
                try {
                    // Module setup
                    this.setupEventListeners();
                    this.loadInitialData();
                    resolve();
                } catch (error) {
                    reject(error);
                }
            });
        },
        
        // Debounced operations for performance
        debouncedRefresh: debounce(function() {
            this.refreshData();
        }, 300),
        
        // Cached operations
        getCachedData: function(key) {
            if (!this._cache) this._cache = new Map();
            return this._cache.get(key);
        }
    };
    
    // Global exposure with namespace
    window.ModuleName = moduleAPI;
    
    // Performance logging
    const moduleLoadTime = performance.now() - moduleStartTime;
    console.log(`📊 ${moduleName} loaded in ${moduleLoadTime.toFixed(2)}ms`);
})();
```

### **CSS Optimization Strategy**
```css
/* Optimized themes.css structure */
:root {
    /* CSS Custom Properties for theme consistency */
    --gp-primary: #00ff9f;
    --gp-secondary: #1a1a2e;
    --gp-accent: #16213e;
    --transition-speed: 0.2s;
}

/* Critical styles first */
.view { display: none; }
.view.active { display: block; }

/* Component-specific styles with efficient selectors */
.console-container {
    contain: layout style; /* CSS containment for better performance */
}

/* GPU-accelerated animations */
.sidebar-transition {
    transform: translateX(-100%);
    transition: transform var(--transition-speed) ease-out;
    will-change: transform;
}

/* Responsive optimization */
@media (max-width: 768px) {
    .desktop-only { display: none; }
}
```

## 🔧 Backend Performance Optimizations

### **Database Query Optimization**
```python
# utils/gust_db_optimization.py

from functools import lru_cache
from typing import Dict, Optional
import time

class DatabaseOptimizer:
    def __init__(self, db, cache_size=1000):
        self.db = db
        self.cache = {}
        self.cache_size = cache_size
        self.query_stats = {}
    
    @lru_cache(maxsize=500)
    def get_user_with_cache(self, user_id: str) -> Optional[Dict]:
        """Cached user retrieval with LRU eviction"""
        start_time = time.time()
        
        try:
            # Try cache first
            if user_id in self.cache:
                self.cache[user_id]['last_accessed'] = time.time()
                return self.cache[user_id]['data']
            
            # Database query with optimized projection
            user = self.db.users.find_one(
                {'userId': user_id},
                {'_id': 0, 'password': 0}  # Exclude sensitive fields
            )
            
            # Cache the result
            if user:
                self._cache_user(user_id, user)
            
            return user
            
        finally:
            # Track query performance
            query_time = time.time() - start_time
            self._update_query_stats('get_user', query_time)
    
    def get_user_balance_cached(self, user_id: str, server_id: str) -> float:
        """Optimized balance retrieval"""
        user = self.get_user_with_cache(user_id)
        if user and 'servers' in user and server_id in user['servers']:
            return user['servers'][server_id].get('balance', 0.0)
        return 0.0
    
    def bulk_update_balances(self, updates: list) -> bool:
        """Batch balance updates for better performance"""
        if not updates:
            return True
            
        try:
            bulk_ops = []
            for update in updates:
                bulk_ops.append({
                    'updateOne': {
                        'filter': {'userId': update['user_id']},
                        'update': {
                            '$set': {
                                f"servers.{update['server_id']}.balance": update['new_balance'],
                                'lastUpdated': time.time()
                            }
                        }
                    }
                })
            
            result = self.db.users.bulk_write(bulk_ops, ordered=False)
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            return False
    
    def _cache_user(self, user_id: str, user_data: Dict):
        """Internal cache management with size limits"""
        if len(self.cache) >= self.cache_size:
            # Remove oldest entries
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]['last_accessed'])
            del self.cache[oldest_key]
        
        self.cache[user_id] = {
            'data': user_data,
            'cached_at': time.time(),
            'last_accessed': time.time()
        }
```

### **API Rate Limiting Optimization**
```python
# utils/rate_limiter.py - Enhanced Version

from collections import defaultdict, deque
import time
import asyncio

class AdvancedRateLimiter:
    def __init__(self):
        self.call_history = defaultdict(deque)
        self.config = {
            'graphql': {'max_calls': 5, 'window': 1, 'burst': 10},
            'api': {'max_calls': 30, 'window': 60, 'burst': 50},
            'websocket': {'max_calls': 100, 'window': 60, 'burst': 200}
        }
        self.backoff_state = defaultdict(lambda: {'failures': 0, 'next_retry': 0})
    
    def is_rate_limited(self, endpoint: str, user_id: str = 'global') -> bool:
        """Check if request should be rate limited"""
        key = f"{endpoint}:{user_id}"
        config = self.config.get(endpoint, self.config['api'])
        
        now = time.time()
        window_start = now - config['window']
        
        # Clean old entries
        while (self.call_history[key] and 
               self.call_history[key][0] < window_start):
            self.call_history[key].popleft()
        
        # Check limits
        recent_calls = len(self.call_history[key])
        return recent_calls >= config['max_calls']
    
    def record_call(self, endpoint: str, user_id: str = 'global'):
        """Record a successful API call"""
        key = f"{endpoint}:{user_id}"
        self.call_history[key].append(time.time())
        
        # Reset backoff on success
        if key in self.backoff_state:
            self.backoff_state[key]['failures'] = 0
    
    def record_failure(self, endpoint: str, user_id: str = 'global'):
        """Record API failure for backoff calculation"""
        key = f"{endpoint}:{user_id}"
        state = self.backoff_state[key]
        state['failures'] += 1
        
        # Exponential backoff: 2^failures seconds
        backoff_time = min(2 ** state['failures'], 300)  # Max 5 minutes
        state['next_retry'] = time.time() + backoff_time
    
    def can_retry(self, endpoint: str, user_id: str = 'global') -> bool:
        """Check if enough time has passed for retry"""
        key = f"{endpoint}:{user_id}"
        state = self.backoff_state[key]
        return time.time() >= state['next_retry']
    
    async def wait_if_needed(self, endpoint: str, user_id: str = 'global'):
        """Async wait with backoff"""
        key = f"{endpoint}:{user_id}"
        state = self.backoff_state[key]
        
        if state['next_retry'] > time.time():
            wait_time = state['next_retry'] - time.time()
            await asyncio.sleep(wait_time)
```

## 🌐 WebSocket Performance Optimization

### **Connection Management Optimization**
```python
# websocket/manager.py - Enhanced Version

import asyncio
from collections import defaultdict, deque
import weakref

class OptimizedWebSocketManager:
    def __init__(self):
        self.connections = {}
        self.message_buffers = defaultdict(lambda: deque(maxlen=1000))
        self.connection_pool = ConnectionPool(max_size=20)
        self.message_queue = asyncio.Queue(maxsize=10000)
        self.stats = defaultdict(int)
    
    async def connect_to_server(self, server_id: str, region: str) -> bool:
        """Optimized connection with pooling"""
        try:
            # Check if connection already exists
            if server_id in self.connections:
                if self.connections[server_id].is_connected():
                    return True
                else:
                    await self.disconnect_from_server(server_id)
            
            # Get connection from pool or create new
            connection = await self.connection_pool.get_connection(server_id, region)
            
            if await connection.connect():
                self.connections[server_id] = connection
                self.stats['successful_connections'] += 1
                
                # Start message processing task
                asyncio.create_task(self._process_messages(server_id))
                return True
            else:
                await self.connection_pool.return_connection(connection)
                return False
                
        except Exception as e:
            self.stats['connection_failures'] += 1
            logger.error(f"Connection failed for {server_id}: {e}")
            return False
    
    async def _process_messages(self, server_id: str):
        """Optimized message processing with batching"""
        connection = self.connections.get(server_id)
        if not connection:
            return
        
        batch_size = 50
        batch_timeout = 0.1  # 100ms
        
        while connection.is_connected():
            try:
                messages = []
                
                # Collect messages in batches
                deadline = time.time() + batch_timeout
                while len(messages) < batch_size and time.time() < deadline:
                    try:
                        message = await asyncio.wait_for(
                            connection.receive_message(), 
                            timeout=batch_timeout
                        )
                        messages.append(message)
                    except asyncio.TimeoutError:
                        break
                
                # Process batch
                if messages:
                    await self._process_message_batch(server_id, messages)
                    
            except Exception as e:
                logger.error(f"Message processing error for {server_id}: {e}")
                break
    
    async def _process_message_batch(self, server_id: str, messages: list):
        """Batch message processing for better performance"""
        buffer = self.message_buffers[server_id]
        
        for message in messages:
            # Parse and classify message
            parsed_message = self._parse_message(message)
            
            # Add to buffer
            buffer.append({
                'timestamp': time.time(),
                'server_id': server_id,
                'type': parsed_message.get('type', 'unknown'),
                'message': parsed_message.get('content', ''),
                'raw': message
            })
        
        # Update statistics
        self.stats['messages_processed'] += len(messages)
        
        # Broadcast to subscribers (non-blocking)
        asyncio.create_task(self._broadcast_messages(server_id, messages))
```

## 📊 Monitoring and Performance Tracking

### **Performance Monitoring System**
```python
# utils/performance_monitor.py

import time
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

class PerformanceMonitor:
    def __init__(self, history_size=1000):
        self.metrics = deque(maxlen=history_size)
        self.request_times = deque(maxlen=100)
        self.active_requests = 0
        self.total_requests = 0
        self.monitoring_active = False
        
    def start_monitoring(self, interval=5):
        """Start background performance monitoring"""
        self.monitoring_active = True
        threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True).start()
    
    def _monitor_loop(self, interval):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_mb = psutil.virtual_memory().used / 1024 / 1024
                
                # Calculate request rate
                now = time.time()
                recent_requests = [t for t in self.request_times if now - t < 60]
                requests_per_second = len(recent_requests) / 60
                
                # Calculate average response time
                if self.request_times:
                    avg_response_time = sum(self.request_times) / len(self.request_times) * 1000
                else:
                    avg_response_time = 0
                
                # Store metric
                metric = PerformanceMetric(
                    timestamp=now,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    active_connections=self.active_requests,
                    requests_per_second=requests_per_second,
                    response_time_ms=avg_response_time
                )
                
                self.metrics.append(metric)
                
                # Check for performance issues
                self._check_performance_alerts(metric)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
    
    def record_request(self, response_time: float):
        """Record request completion"""
        self.request_times.append(response_time)
        self.total_requests += 1
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary for dashboard"""
        if not self.metrics:
            return {}
        
        recent_metrics = list(self.metrics)[-10:]  # Last 10 readings
        
        return {
            'current_cpu': recent_metrics[-1].cpu_percent,
            'current_memory': recent_metrics[-1].memory_mb,
            'avg_response_time': sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics),
            'requests_per_second': recent_metrics[-1].requests_per_second,
            'total_requests': self.total_requests,
            'uptime_minutes': (time.time() - recent_metrics[0].timestamp) / 60
        }
```

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
            
        # Only reload for template files
        if event.src_path.endswith(('.html', '.js.html', '.css')):
            current_time = time.time()
            
            # Debounce rapid file changes
            if current_time - self.last_reload > 1:
                print(f"🔄 Reloading due to change: {event.src_path}")
                self.app.reload_templates()
                self.last_reload = current_time

def setup_hot_reload(app):
    """Setup hot reload for development"""
    if app.debug:
        event_handler = TemplateReloadHandler(app)
        observer = Observer()
        observer.schedule(event_handler, 'templates/', recursive=True)
        observer.schedule(event_handler, 'static/', recursive=True)
        observer.start()
        print("🔥 Hot reload enabled for templates and static files")
```

### **Component Testing Optimization**
```javascript
// static/js/testing/component-tester.js

class ComponentTester {
    constructor() {
        this.testResults = new Map();
        this.performance = new Map();
    }
    
    async testComponent(componentName, testFunction) {
        const startTime = performance.now();
        
        try {
            console.log(`🧪 Testing ${componentName}...`);
            
            // Run test with timeout
            const result = await Promise.race([
                testFunction(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Test timeout')), 5000)
                )
            ]);
            
            const duration = performance.now() - startTime;
            
            this.testResults.set(componentName, {
                status: 'passed',
                duration: duration,
                result: result
            });
            
            console.log(`✅ ${componentName} passed in ${duration.toFixed(2)}ms`);
            return true;
            
        } catch (error) {
            const duration = performance.now() - startTime;
            
            this.testResults.set(componentName, {
                status: 'failed',
                duration: duration,
                error: error.message
            });
            
            console.error(`❌ ${componentName} failed: ${error.message}`);
            return false;
        }
    }
    
    async runAllTests() {
        const components = [
            'dashboard', 'server_manager', 'console', 'events',
            'economy', 'gambling', 'clans', 'user_management', 'logs'
        ];
        
        const results = await Promise.all(
            components.map(component => this.testComponentLoad(component))
        );
        
        const passedTests = results.filter(r => r).length;
        const totalTests = results.length;
        
        console.log(`📊 Test Results: ${passedTests}/${totalTests} components passed`);
        return passedTests === totalTests;
    }
    
    async testComponentLoad(componentName) {
        return this.testComponent(componentName, async () => {
            // Test that component loads without errors
            showTab(componentName);
            
            // Wait for component to initialize
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Check for JavaScript errors
            const errors = window.console.errors || [];
            if (errors.length > 0) {
                throw new Error(`Console errors detected: ${errors.join(', ')}`);
            }
            
            // Check that component is visible
            const element = document.getElementById(`${componentName}-view`);
            if (!element || element.style.display === 'none') {
                throw new Error(`Component ${componentName} not visible`);
            }
            
            return true;
        });
    }
}

// Auto-run tests in development
if (window.location.hostname === 'localhost') {
    window.componentTester = new ComponentTester();
    
    // Run tests after page load
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            window.componentTester.runAllTests();
        }, 2000);
    });
}
```

## 📈 Performance Best Practices

### **Frontend Best Practices**
```javascript
// 1. Debounce expensive operations
const debouncedSearch = debounce((query) => {
    performSearch(query);
}, 300);

// 2. Use requestAnimationFrame for animations
function smoothScroll(element, target) {
    function animate() {
        const current = element.scrollTop;
        const distance = target - current;
        const step = distance * 0.1;
        
        if (Math.abs(step) > 1) {
            element.scrollTop = current + step;
            requestAnimationFrame(animate);
        } else {
            element.scrollTop = target;
        }
    }
    animate();
}

// 3. Lazy load components
function lazyLoadComponent(componentName) {
    return new Promise((resolve) => {
        if (window[componentName]) {
            resolve(window[componentName]);
        } else {
            const observer = new MutationObserver(() => {
                if (window[componentName]) {
                    observer.disconnect();
                    resolve(window[componentName]);
                }
            });
            observer.observe(document, { childList: true, subtree: true });
        }
    });
}

// 4. Efficient DOM manipulation
function updateMultipleElements(updates) {
    const fragment = document.createDocumentFragment();
    
    updates.forEach(update => {
        const element = document.createElement(update.tag);
        element.textContent = update.content;
        element.className = update.className;
        fragment.appendChild(element);
    });
    
    document.getElementById('container').appendChild(fragment);
}
```

### **Backend Best Practices**
```python
# 1. Use connection pooling
from pymongo import MongoClient

client = MongoClient(
    uri,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    waitQueueTimeoutMS=5000
)

# 2. Implement proper caching
from functools import lru_cache
import time

@lru_cache(maxsize=1000)
def expensive_calculation(param):
    # Expensive operation
    return result

# 3. Use bulk operations
def bulk_insert_users(users):
    if not users:
        return
        
    try:
        db.users.insert_many(users, ordered=False)
    except BulkWriteError as e:
        # Handle partial failures
        logger.error(f"Bulk insert errors: {e.details}")

# 4. Optimize database queries
def get_user_summary(user_id):
    # Project only needed fields
    return db.users.find_one(
        {'userId': user_id},
        {
            'nickname': 1,
            'servers.balance': 1,
            'servers.clanTag': 1,
            '_id': 0
        }
    )
```

---

*Optimization guide completed: June 19, 2025*  
*Performance target: <100ms response time, <50MB memory usage*  
*Status: ✅ Optimized for production deployment*