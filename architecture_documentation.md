# GUST-MARK-1 Architecture & Dependency Documentation
*Generated: 2025-06-18 15:06:59*

## 📊 Project Overview
- **Python Files**: 29
- **Templates**: 30
- **JavaScript Files**: 21
- **API Endpoints**: 67

## 🛣️ Complete API Endpoints Map
### Auth Module (`routes/auth.py`)
- **GET, POST** `/login`
- **GET** `/logout`
- **GET** `/api/token/status`
- **POST** `/api/token/refresh`

### Clans Module (`routes/clans.py`)
- **GET** `/api/clans/<server_id>`
- **POST** `/api/clans/create`
- **POST** `/api/clans/join`
- **POST** `/api/clans/leave`
- **GET** `/api/clans/stats/<server_id>`
- **GET** `/api/clans/user/<user_id>/<server_id>`

### Economy Module (`routes/economy.py`)
- **GET** `/api/economy/balance/<user_id>/<server_id>`
- **POST** `/api/economy/set-balance/<user_id>/<server_id>`
- **POST** `/api/economy/adjust-balance/<user_id>/<server_id>`
- **POST** `/api/economy/transfer/<server_id>`
- **GET** `/api/economy/leaderboard/<server_id>`
- **GET** `/api/economy/transactions/<user_id>/<server_id>`
- **GET** `/api/economy/server-stats/<server_id>`
- **GET** `/api/economy/balance/<user_id>`
- **POST** `/api/economy/transfer`

### Events Module (`routes/events.py`)
- **POST** `/api/events/koth/start`
- **POST** `/api/events/koth/stop`
- **GET** `/api/events`
- **GET** `/api/events/<event_id>`
- **GET** `/api/events/server/<server_id>`
- **GET** `/api/events/stats`
- **GET** `/api/events/arena-locations`
- **GET** `/api/events/templates`

### Gambling Module (`routes/gambling.py`)
- **POST** `/api/gambling/slots/<user_id>/<server_id>`
- **POST** `/api/gambling/coinflip/<user_id>/<server_id>`
- **POST** `/api/gambling/dice/<user_id>/<server_id>`
- **GET** `/api/gambling/history/<user_id>/<server_id>`
- **GET** `/api/gambling/stats/<user_id>/<server_id>`
- **GET** `/api/gambling/leaderboard/<server_id>`
- **POST** `/api/gambling/slots`
- **POST** `/api/gambling/coinflip`
- **POST** `/api/gambling/dice`

### Logs Module (`routes/logs.py`)
- **GET** `/api/logs/servers`
- **GET** `/api/logs`
- **POST** `/api/logs/download`
- **GET** `/api/logs/<log_id>/download`
- **POST** `/api/logs/refresh`

### Servers Module (`routes/servers.py`)
- **GET** `/api/servers`
- **POST** `/api/servers/add`
- **POST** `/api/servers/update/<server_id>`
- **DELETE** `/api/servers/delete/<server_id>`
- **POST** `/api/servers/ping/<server_id>`
- **POST** `/api/servers/bulk-action`
- **GET** `/api/servers/<server_id>`
- **GET** `/api/servers/stats`

### Users Module (`routes/users.py`)
- **POST** `/api/bans/temp`
- **POST** `/api/bans/permanent`
- **POST** `/api/bans/unban`
- **POST** `/api/items/give`
- **POST** `/api/users/kick`
- **POST** `/api/users/teleport`
- **GET** `/api/bans`
- **GET** `/api/users/<user_id>/history`
- **GET** `/api/users/search`
- **GET** `/api/users/stats`

### User_Database Module (`routes/user_database.py`)
- **POST** `/api/users/register`
- **GET** `/api/users/profile/<user_id>`
- **PUT** `/api/users/profile/<user_id>`
- **GET** `/api/users/servers/<user_id>`
- **POST** `/api/users/join-server/<user_id>/<server_id>`
- **GET** `/api/users/leaderboard/<server_id>`
- **GET** `/api/users/stats/<server_id>`
- **GET** `/api/users/search`

## 🐍 Python Modules Analysis
### Root Files
#### `app.py`
- **Size**: 29.37KB
- **Complexity**: High
- **Functions** (1): debug_user_storage
- **Classes**: InMemoryUserStorage, GustBotEnhanced
- **Internal Dependencies**: 15
  - `from utils.rate_limiter import RateLimiter`
  - `from utils.helpers import load_token, format_command, validate_server_id, validate_region`
  - `from systems.koth import VanillaKothSystem`

#### `comprehensive_test.py`
- **Size**: 30.42KB
- **Complexity**: High
- **Functions** (1): main
- **Classes**: GustProjectValidator

#### `config.py`
- **Size**: 7.43KB
- **Complexity**: Medium
- **Functions** (4): check_dependencies, ensure_directories, ensure_data_files, print_startup_info
- **Classes**: Config

#### `dependency_mapper.py`
- **Size**: 17.92KB
- **Complexity**: High
- **Functions** (1): main
- **Classes**: SimpleDependencyMapper

#### `main.py`
- **Size**: 1.57KB
- **Complexity**: Low
- **Functions** (1): main

#### `quick_test.py`
- **Size**: 18.46KB
- **Complexity**: High
- **Functions** (1): main
- **Classes**: QuickProjectValidator

#### `routes\auth.py`
- **Size**: 8.25KB
- **Complexity**: Medium
- **Functions** (8): login, logout, token_status, refresh_token_endpoint, authenticate_gportal
  *...and 3 more*
- **Routes**: 4 endpoints
- **Internal Dependencies**: 2
  - `from utils.helpers import save_token`
  - `from utils.helpers import refresh_token`

#### `routes\clans.py`
- **Size**: 19.92KB
- **Complexity**: High
- **Functions** (6): init_clans_routes, ensure_user_on_server, set_user_clan_tag, get_user_info, update_clan_stats
  *...and 1 more*
- **Routes**: 6 endpoints
- **Internal Dependencies**: 2
  - `from routes.auth import require_auth`
  - `from utils.user_helpers import (`

#### `routes\client.py`
- **Size**: 13.85KB
- **Complexity**: Medium
- **Classes**: GPortalWebSocketClient
- **Internal Dependencies**: 1
  - `from utils.helpers import classify_message`

#### `routes\economy.py`
- **Size**: 14.75KB
- **Complexity**: High
- **Functions** (3): init_economy_routes, log_transaction, get_user_transactions
- **Routes**: 9 endpoints
- **Internal Dependencies**: 2
  - `from routes.auth import require_auth`
  - `from utils.user_helpers import (`

#### `routes\events.py`
- **Size**: 11.56KB
- **Complexity**: Medium
- **Functions** (1): init_events_routes
- **Routes**: 8 endpoints
- **Internal Dependencies**: 1
  - `from routes.auth import require_auth`

#### `routes\gambling.py`
- **Size**: 21.49KB
- **Complexity**: High
- **Functions** (7): init_gambling_routes, calculate_slot_winnings, update_gambling_stats, log_gambling_game, get_user_gambling_history
  *...and 2 more*
- **Routes**: 9 endpoints
- **Internal Dependencies**: 2
  - `from routes.auth import require_auth`
  - `from utils.user_helpers import (`

#### `routes\koth.py`
- **Size**: 12.5KB
- **Complexity**: Medium
- **Classes**: VanillaKothSystem
- **Internal Dependencies**: 1
  - `from utils.helpers import get_countdown_announcements`

#### `routes\logs.py`
- **Size**: 12.31KB
- **Complexity**: Medium
- **Functions** (1): init_logs_routes
- **Classes**: GPortalLogAPI
- **Routes**: 5 endpoints
- **Internal Dependencies**: 2
  - `from routes.auth import require_auth`
  - `from utils.helpers import load_token, refresh_token`

#### `routes\manager.py`
- **Size**: 9.99KB
- **Complexity**: Medium
- **Classes**: WebSocketManager

#### `routes\servers.py`
- **Size**: 13.52KB
- **Complexity**: Medium
- **Functions** (1): init_servers_routes
- **Routes**: 8 endpoints
- **Internal Dependencies**: 2
  - `from routes.auth import require_auth`
  - `from utils.helpers import create_server_data, validate_server_id, validate_region`

#### `routes\users.py`
- **Size**: 19.23KB
- **Complexity**: High
- **Functions** (1): init_users_routes
- **Routes**: 10 endpoints
- **Internal Dependencies**: 1
  - `from routes.auth import require_auth`

#### `routes\user_database.py`
- **Size**: 18.23KB
- **Complexity**: High
- **Functions** (7): init_user_database_routes, get_user_profile, update_user_last_seen, get_user_display_name, get_server_balance
  *...and 2 more*
- **Routes**: 8 endpoints
- **Internal Dependencies**: 1
  - `from routes.auth import require_auth`

#### `routes\__init__.py`
- **Size**: 0.88KB
- **Complexity**: Low
- **Functions** (1): init_all_routes

#### `systems\koth.py`
- **Size**: 12.5KB
- **Complexity**: Medium
- **Classes**: VanillaKothSystem
- **Internal Dependencies**: 1
  - `from utils.helpers import get_countdown_announcements`

#### `systems\__init__.py`
- **Size**: 7.14KB
- **Complexity**: Medium
- **Functions** (6): get_systems_status, get_available_systems, create_systems_manager, create_koth_system, get_system_registry
  *...and 1 more*
- **Classes**: SystemsManager

#### `utils\helpers.py`
- **Size**: 10.65KB
- **Complexity**: Medium
- **Functions** (16): load_token, refresh_token, save_token, classify_message, get_type_icon
  *...and 11 more*

#### `utils\rate_limiter.py`
- **Size**: 3.62KB
- **Complexity**: Low
- **Classes**: RateLimiter

#### `utils\user_helpers.py`
- **Size**: 8.73KB
- **Complexity**: Medium
- **Functions** (11): generate_internal_id, get_user_profile, get_server_balance, set_server_balance, adjust_server_balance
  *...and 6 more*

#### `utils\user_migration.py`
- **Size**: 8.96KB
- **Complexity**: Medium
- **Functions** (1): generate_internal_id
- **Classes**: UserDatabaseMigration

#### `utils\__init__.py`
- **Size**: 0.95KB
- **Complexity**: Low

#### `websocket\client.py`
- **Size**: 13.85KB
- **Complexity**: Medium
- **Classes**: GPortalWebSocketClient
- **Internal Dependencies**: 1
  - `from utils.helpers import classify_message`

#### `websocket\manager.py`
- **Size**: 9.99KB
- **Complexity**: Medium
- **Classes**: WebSocketManager

#### `websocket\__init__.py`
- **Size**: 2.49KB
- **Complexity**: Low
- **Functions** (2): get_websocket_status, check_websocket_support

## 🎨 Template Analysis
### Root Templates
#### `enhanced_dashboard.html`
- **Size**: 1.64KB
- **Includes**: base/sidebar.html, views/dashboard.html, views/server_manager.html, views/console.html, views/events.html, views/economy.html, views/gambling.html, views/clans.html, views/user_management.html, views/logs.html, scripts/main.js.html, scripts/dashboard.js.html, scripts/server_manager.js.html, scripts/console.js.html, scripts/events.js.html, scripts/economy.js.html, scripts/gambling.js.html, scripts/clans.js.html, scripts/user_management.js.html, scripts/logs.js.html
- **Variables Used**: url_for

#### `login.html`
- **Size**: 4.3KB

#### `base\layout.html`
- **Size**: 0.32KB

#### `base\sidebar.html`
- **Size**: 4.24KB

#### `components\console_message.html`
- **Size**: 0.05KB

#### `components\server_selector.html`
- **Size**: 2.69KB

#### `components\user_registration.html`
- **Size**: 2.78KB

#### `partials\notification_toast.html`
- **Size**: 0.08KB

#### `scripts\clans.js.html`
- **Size**: 0.63KB

#### `scripts\console.js.html`
- **Size**: 0.64KB

#### `scripts\dashboard.js.html`
- **Size**: 0.65KB

#### `scripts\economy.js.html`
- **Size**: 0.64KB

#### `scripts\enhanced_api.js.html`
- **Size**: 7.31KB

#### `scripts\events.js.html`
- **Size**: 0.64KB

#### `scripts\gambling.js.html`
- **Size**: 0.64KB

#### `scripts\logs.js.html`
- **Size**: 13.35KB

#### `scripts\main.js.html`
- **Size**: 63.85KB

#### `scripts\server_manager.js.html`
- **Size**: 0.67KB

#### `scripts\user_management.js.html`
- **Size**: 22.51KB

#### `views\clans.html`
- **Size**: 2.41KB

#### `views\console.html`
- **Size**: 9.39KB

#### `views\dashboard.html`
- **Size**: 5.47KB

#### `views\dashboard_enhanced.html`
- **Size**: 3.54KB
- **Includes**: components/server_selector.html

#### `views\economy.html`
- **Size**: 2.08KB

#### `views\events.html`
- **Size**: 4.46KB

#### `views\gambling.html`
- **Size**: 2.4KB

#### `views\logs.html`
- **Size**: 2.64KB

#### `views\server_manager.html`
- **Size**: 5.12KB

#### `views\users.html`
- **Size**: 3.36KB

#### `views\user_management.html`
- **Size**: 8.73KB

## 📦 JavaScript Components Analysis
### `static/js/components\clans.js`
- **Size**: 34.34KB
- **Complexity**: High
- **Classes**: ClansComponent

### `static/js/components\console.js`
- **Size**: 34.55KB
- **Complexity**: High
- **Classes**: ConsoleComponent

### `static/js/components\dashboard.js`
- **Size**: 27.84KB
- **Complexity**: High
- **Classes**: ServerManagerComponent

### `static/js/components\economy.js`
- **Size**: 20.53KB
- **Complexity**: High
- **Classes**: EconomyComponent

### `static/js/components\events.js`
- **Size**: 33.44KB
- **Complexity**: High
- **Classes**: EventsComponent

### `static/js/components\gambling.js`
- **Size**: 29.2KB
- **Complexity**: High
- **Classes**: GamblingComponent

### `static/js/components\server-manager.js`
- **Size**: 0.31KB
- **Complexity**: Low
- **Classes**: ServerManager

### `static/js/components\user-management.js`
- **Size**: 30.33KB
- **Complexity**: High
- **Classes**: UserManagementComponent
- **Functions** (6): formatter, formatter, formatter, onSelectionChange, executedFunction
  *...and 1 more*

### `static/js/components\base\base-component.js`
- **Size**: 17.76KB
- **Complexity**: High
- **Classes**: for, BaseComponent, to
- **Functions** (7): get, post, put, delete, on
  *...and 2 more*

### `static/js/components\base\form-component.js`
- **Size**: 24.54KB
- **Complexity**: High
- **Classes**: for, FormComponent
- **Functions** (1): custom

### `static/js/components\base\list-component.js`
- **Size**: 37.57KB
- **Complexity**: High
- **Classes**: for, ListComponent
- **Functions** (5): render, action, calls, executedFunction, later

### `static/js/services\notification-service.js`
- **Size**: 25.45KB
- **Complexity**: High
- **Classes**: NotificationService
- **Functions** (1): onclick

### `static/js/services\storage-service.js`
- **Size**: 24.07KB
- **Complexity**: High
- **Classes**: StorageService
- **Functions** (1): return

### `static/js/services\validation-service.js`
- **Size**: 22.81KB
- **Complexity**: High
- **Classes**: ValidationService
- **Functions** (46): string, number, integer, boolean, array
  *...and 41 more*

### `static/js/services\websocket-service.js`
- **Size**: 21.52KB
- **Complexity**: High
- **Classes**: WebSocketService
- **Functions** (5): onopen, onmessage, onclose, onerror, return
- **API Calls**: /api/token/status

### `static/js/widgets\console-output.js`
- **Size**: 30.12KB
- **Complexity**: High
- **Classes**: ConsoleOutput, to
- **Functions** (4): action, action, executedFunction, later

### `static/js/widgets\data-table.js`
- **Size**: 31.25KB
- **Complexity**: High
- **Classes**: DataTable
- **Functions** (2): executedFunction, later

### `static/js/widgets\form-builder.js`
- **Size**: 18.03KB
- **Complexity**: High
- **Classes**: FormBuilder

### `static/js/widgets\modal.js`
- **Size**: 22.63KB
- **Complexity**: High
- **Classes**: Modal, to, document, document
- **Functions** (8): onConfirm, onCancel, onClose, onConfirm, onClose
  *...and 3 more*

### `static/js/widgets\server-card.js`
- **Size**: 18.99KB
- **Complexity**: High
- **Classes**: ServerCard
- **Functions** (3): onSelect, onConfirm, onCancel

### `static/js/widgets\status-indicator.js`
- **Size**: 19.49KB
- **Complexity**: High
- **Classes**: StatusIndicator, indicator, after
- **Functions** (1): animate

## 🔗 Data Flow Patterns
### User Authentication Flow
```
Browser → templates/login.html
       → static/js/components/user-management.js
       → templates/scripts/enhanced_api.js.html
       → routes/auth.py
       → Session Storage
       → templates/enhanced_dashboard.html
```

### Economy Operations Flow
```
Browser → templates/views/economy.html
       → static/js/components/economy.js
       → templates/scripts/economy.js.html
       → /api/economy/* endpoints
       → routes/economy.py
       → utils/user_helpers.py
       → MongoDB/JSON Storage
       → JSON Response
```

### Real-time Console Flow
```
G-Portal WebSocket → websocket/client.py
                  → websocket/manager.py
                  → static/js/components/console.js
                  → templates/views/console.html
                  → Live DOM Updates
```

## 🏗️ Architecture Summary
### Application Layers
1. **Presentation Layer**
   - HTML Templates (`templates/views/`, `templates/components/`)
   - JavaScript Components (`static/js/components/`)
   - CSS Styling (`static/css/`)

2. **Application Layer**
   - Flask Route Handlers (`routes/*.py`)
   - Business Logic and API Endpoints
   - Request/Response Processing

3. **Service Layer**
   - Utility Functions (`utils/*.py`)
   - Helper Services and Data Processing
   - Cross-cutting Concerns

4. **Integration Layer**
   - WebSocket Management (`websocket/*.py`)
   - External API Integration (G-Portal)
   - Real-time Communication

5. **Data Layer**
   - MongoDB/JSON Storage
   - File-based Configuration
   - Session Management