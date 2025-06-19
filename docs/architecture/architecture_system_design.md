# GUST-MARK-1 System Architecture

> **File Location**: `architecture/SYSTEM_DESIGN.md`

## 🏗️ Architecture Overview

GUST-MARK-1 implements a **modular Flask blueprint architecture** with enterprise-grade separation of concerns, real-time WebSocket integration, and dual storage capabilities.

## 📐 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        GUST-MARK-1 Architecture                 │
├─────────────────────────────────────────────────────────────────┤
│ Frontend Layer (Modular Templates)                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│ │ enhanced_       │ │ views/          │ │ scripts/        │    │
│ │ dashboard.html  │ │ 9 components    │ │ 9 modules       │    │
│ │ (50 lines)      │ │ (100-300 lines) │ │ (50-150 lines)  │    │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│ Application Layer (Flask)                                      │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│ │ app.py          │ │ routes/         │ │ utils/          │    │
│ │ GustBotEnhanced │ │ 10 blueprints   │ │ 4 utilities     │    │
│ │ (Main App)      │ │ (Feature APIs)  │ │ (Helpers)       │    │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│ Integration Layer                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│ │ websocket/      │ │ systems/        │ │ routes/         │    │
│ │ G-Portal WS     │ │ KOTH Engine     │ │ API Endpoints   │    │
│ │ (Real-time)     │ │ (Game Logic)    │ │ (REST + GraphQL)│    │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│ Data Layer                                                      │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│ │ MongoDB         │ │ InMemoryStorage │ │ File System     │    │
│ │ (Production)    │ │ (Demo/Fallback) │ │ (Logs/Config)   │    │
│ │ Collections     │ │ Dictionaries    │ │ JSON Files      │    │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│ External Layer                                                  │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│ │ G-Portal API    │ │ WebSocket API   │ │ Rust Servers    │    │
│ │ GraphQL/REST    │ │ Real-time       │ │ Game Servers    │    │
│ │ (Commands)      │ │ (Console)       │ │ (Target)        │    │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 🎨 Frontend Architecture

### **Template Hierarchy**
```
templates/
├── enhanced_dashboard.html (Master)
│   ├── Includes: base/sidebar.html
│   ├── Includes: 9 × views/*.html
│   └── Includes: 9 × scripts/*.js.html
│
├── base/
│   └── sidebar.html (Navigation)
│
├── views/ (Tab Components)
│   ├── dashboard.html (System overview)
│   ├── server_manager.html (Server CRUD)
│   ├── console.html (Live monitoring)
│   ├── events.html (KOTH management)
│   ├── economy.html (Player coins)
│   ├── gambling.html (Casino games)
│   ├── clans.html (Clan system)
│   ├── user_management.html (User admin)
│   └── logs.html (Log management)
│
└── scripts/ (JavaScript Modules)
    ├── main.js.html (Core functions)
    ├── dashboard.js.html (Dashboard logic)
    ├── server_manager.js.html (Server ops)
    ├── console.js.html (WebSocket)
    ├── events.js.html (Event logic)
    ├── economy.js.html (Economy ops)
    ├── gambling.js.html (Game logic)
    ├── clans.js.html (Clan ops)
    ├── user_management.js.html (User admin)
    └── logs.js.html (Log operations)
```

### **Component Communication Pattern**
```javascript
// Global Function Exposure Pattern
window.functionName = functionName;

// Cross-Module Dependencies
main.js (Core) ←── All modules depend on
├── showTab()
├── escapeHtml()
├── validateInput()
└── formatTimestamp()

server_manager.js ←── console.js, events.js
├── getServerById()
├── updateServerDropdowns()
└── getServerList()

console.js ←── Multiple modules
├── sendConsoleCommand()
├── refreshConsole()
└── addConsoleMessage()
```

## 🔧 Backend Architecture

### **Flask Application Structure**
```python
class GustBotEnhanced:
    def __init__(self):
        self.app = Flask(__name__)                    # Flask instance
        self.db = None                                # MongoDB connection
        self.user_storage = InMemoryUserStorage()     # User management
        self.websocket_manager = None                 # WebSocket manager
        self.console_output = deque(maxlen=1000)      # Message buffer
        self.rate_limiter = RateLimiter()             # API protection
        
    def setup_database(self):          # MongoDB with fallback
    def setup_routes(self):            # Blueprint registration
    def setup_websockets(self):        # WebSocket initialization  
    def run(self, host, port, debug):  # Application startup
```

### **Blueprint Architecture**
```
routes/
├── __init__.py (Lazy loading initialization)
├── auth.py (Authentication & sessions)
├── servers.py (Server CRUD operations)
├── events.py (KOTH event management)
├── economy.py (Player economy system)
├── gambling.py (Casino game logic)
├── clans.py (Clan management system)
├── users.py (User administration)
├── logs.py (Log management system)
└── user_database.py (Database operations)

Each blueprint follows pattern:
├── Blueprint definition
├── Route handlers with @require_auth
├── Input validation
├── Business logic
├── Database operations
├── Response formatting
└── Error handling
```

## 🔌 API Architecture

### **GraphQL Integration (G-Portal)**
```javascript
// Console Command Mutation (Verified)
{
  "operationName": "sendConsoleMessage",
  "variables": {
    "sid": 1736296,                    // Integer server ID
    "region": "US",                    // Region code
    "message": "say \"Hello World\""   // Console command
  },
  "query": `mutation sendConsoleMessage($sid: Int!, $region: REGION!, $message: String!) {
    sendConsoleMessage(rsid: {id: $sid, region: $region}, message: $message) {
      ok
      __typename
    }
  }`
}

// Endpoints:
// API: https://www.g-portal.com/ngpapi/
// WebSocket: wss://www.g-portal.com/ngpapi/
```

### **REST API Structure**
```
Authentication:
├── GET  /login                    # Login page
├── POST /login                    # Authenticate user
├── GET  /logout                   # Session termination
└── GET  /api/auth/status          # Auth verification

Server Management:
├── GET  /api/servers              # List servers
├── POST /api/servers/add          # Add server
├── PUT  /api/servers/update       # Update server
└── DEL  /api/servers/delete       # Remove server

Console Operations:
├── POST /api/console/send         # Send GraphQL commands
├── GET  /api/console/output       # Get console buffer
├── GET  /api/console/live/status  # WebSocket status
├── POST /api/console/live/connect # Live connection
├── GET  /api/console/live/messages # Real-time messages
└── GET  /api/console/live/test    # System test

[Additional 6 feature APIs with similar patterns]
```

## 🔄 Data Architecture

### **Storage Strategy**
```python
# Dual Storage Pattern
if mongodb_available:
    storage = MongoDBStorage()
    # Collections: users, clans, servers, events, logs
else:
    storage = InMemoryUserStorage()
    # Dictionaries: users, balances, clans

# Automatic Fallback
try:
    db = MongoClient(uri, timeout=2000)
    db.admin.command('ping')
except:
    db = None
    use_memory_storage = True
```

### **Database Schema (MongoDB)**
```javascript
// Users Collection
{
  _id: ObjectId,
  userId: String,           // Unique player ID
  nickname: String,         // Display name
  internalId: Number,       // 9-digit internal ID
  registeredAt: ISODate,
  lastSeen: ISODate,
  servers: {                // Multi-server support
    "server_1736296": {
      balance: Number,
      clanTag: String,
      joinedAt: ISODate,
      gamblingStats: {
        totalWagered: Number,
        totalWon: Number,
        gamesPlayed: Number,
        lastPlayed: ISODate
      },
      isActive: Boolean
    }
  },
  preferences: {
    displayNickname: Boolean,
    showInLeaderboards: Boolean
  },
  totalServers: Number
}

// Clans Collection
{
  _id: ObjectId,
  clanId: String,           // Unique clan ID
  name: String,             // Clan name
  leader: String,           // Leader user ID
  members: [String],        // Member user IDs
  memberCount: Number,
  serverId: String,         // Associated server
  tag: String,              // Clan tag (2-10 chars)
  description: String,
  createdAt: ISODate,
  lastUpdated: ISODate,
  stats: {                  // Calculated statistics
    totalMembers: Number,
    activeMembers: Number,
    totalWealth: Number,
    averageBalance: Number
  }
}
```

## 🌐 WebSocket Architecture

### **Connection Management**
```python
# WebSocket Manager (websocket/manager.py)
class WebSocketManager:
    def __init__(self):
        self.connections = {}     # server_id -> connection
        self.message_buffers = {} # server_id -> message_deque
        
    async def connect_to_server(self, server_id, region)
    async def disconnect_from_server(self, server_id)
    def get_connection_status(self)
    def get_messages(self, server_id, limit=50)
    def broadcast_message(self, message)

# G-Portal WebSocket Client (websocket/client.py)  
class GPortalWebSocketClient:
    async def connect(self)                # Establish connection
    async def subscribe_to_console(self)   # Subscribe to messages
    async def send_command(self, command)  # Send GraphQL commands
    def get_messages(self, limit)          # Retrieve buffer
```

### **Message Flow**
```
G-Portal Server
    ↓ WebSocket Message
GPortalWebSocketClient 
    ↓ Parse & Buffer
WebSocketManager
    ↓ Broadcast
Frontend Console
    ↓ Display
User Interface
```

## 🛡️ Security Architecture

### **Authentication Flow**
```python
# Multi-mode Authentication
def authenticate():
    if demo_mode:
        return validate_demo_credentials()  # admin/password
    else:
        return validate_gportal_token()     # G-Portal API token

# Session Management
@require_auth
def protected_route():
    if 'logged_in' not in session:
        return redirect('/login')
    # Route logic
```

### **Input Validation Pipeline**
```python
# utils/validation_helpers.py
class ValidationHelper:
    @staticmethod
    def validate_username(username)     # Format validation
    def validate_server_id(server_id)   # ID validation  
    def validate_balance(balance)       # Numeric validation
    def validate_clan_tag(clan_tag)     # Tag validation
    def sanitize_string(value)          # XSS prevention
```

### **Rate Limiting**
```python
# utils/rate_limiter.py
class RateLimiter:
    def __init__(self):
        self.calls = defaultdict(list)
        self.max_calls = 5
        self.time_window = 1  # second
        
    def wait_if_needed(self, endpoint)  # Enforce limits
    def is_rate_limited(self, endpoint) # Check status
```

## 🚀 Deployment Architecture

### **Application Startup Flow**
```python
# main.py
if __name__ == '__main__':
    bot = GustBotEnhanced()
    bot.run(host='127.0.0.1', port=5000)

# Startup Sequence:
1. Load configuration (config.py)
2. Check dependencies (websockets, mongodb)
3. Initialize Flask app
4. Setup database connection (with fallback)
5. Register route blueprints  
6. Initialize WebSocket manager (if available)
7. Start background tasks
8. Begin serving requests
```

### **Configuration Management**
```python
# config.py
class Config:
    # Server settings
    DEFAULT_HOST = '127.0.0.1'
    DEFAULT_PORT = 5000
    SECRET_KEY = secrets.token_hex(32)
    
    # External APIs
    GPORTAL_API_ENDPOINT = "https://www.g-portal.com/ngpapi/"
    WEBSOCKET_URI = "wss://www.g-portal.com/ngpapi/"
    
    # Database
    MONGODB_URI = 'mongodb://localhost:27017/'
    MONGODB_DATABASE = 'gust'
    
    # Performance
    CONSOLE_MESSAGE_BUFFER_SIZE = 1000
    RATE_LIMIT_MAX_CALLS = 5
```

## 📊 Performance Architecture

### **Optimization Strategies**
```python
# Message Buffering
console_output = deque(maxlen=1000)  # Fixed-size buffer

# Database Caching (utils/gust_db_optimization.py)
def get_user_with_cache(user_id):
    if user_id in cache:
        return cache[user_id]
    # Fetch from database
    
# Connection Pooling
MongoClient(uri, maxPoolSize=50)

# Rate Limiting
RateLimiter.wait_if_needed("graphql")
```

### **Scalability Patterns**
- **Horizontal Scaling**: Multiple Flask instances behind load balancer
- **Database Scaling**: MongoDB replica sets and sharding
- **WebSocket Scaling**: WebSocket connection pooling
- **Caching**: Redis for session and data caching
- **CDN**: Static asset distribution

---

*Architecture documented: June 19, 2025*  
*Pattern: Modular Flask with WebSocket integration*  
*Status: ✅ Production-ready enterprise architecture*