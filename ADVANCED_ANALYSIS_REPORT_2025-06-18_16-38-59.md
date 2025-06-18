# GUST Bot Enhanced - Advanced Analysis Report
Generated: 06/18/2025 16:39:00
Analysis Run: 2025-06-18_16-38-59

## 🌐 Complete API Endpoint Analysis

**Total API Endpoints Found: 77**

| File | Function | Route Pattern |
|------|----------|---------------|
| auth.py | login | @auth_bp.route('/login', methods=['GET', 'POST'])
def login |
| auth.py | logout | @auth_bp.route('/logout')
def logout |
| auth.py | token_status | @auth_bp.route('/api/token/status')
def token_status |
| auth.py | refresh_token_endpoint | @auth_bp.route('/api/token/refresh', methods=['POST'])
def refresh_token_endpoint |
| clans.py | get_server_clans | @clans_bp.route('/api/clans/<server_id>')
    @require_auth
    def get_server_clans |
| clans.py | create_clan | @clans_bp.route('/api/clans/create', methods=['POST'])
    @require_auth  
    def create_clan |
| clans.py | join_clan | @clans_bp.route('/api/clans/join', methods=['POST'])
    @require_auth
    def join_clan |
| clans.py | leave_clan | @clans_bp.route('/api/clans/leave', methods=['POST'])
    @require_auth
    def leave_clan |
| clans.py | get_clan_stats | @clans_bp.route('/api/clans/stats/<server_id>')
    @require_auth
    def get_clan_stats |
| clans.py | get_user_clan_info | @clans_bp.route('/api/clans/user/<user_id>/<server_id>')
    @require_auth
    def get_user_clan_info |
| economy.py | get_user_balance_server | @economy_bp.route('/api/economy/balance/<user_id>/<server_id>')
    @require_auth
    def get_user_balance_server |
| economy.py | set_user_balance_server | @economy_bp.route('/api/economy/set-balance/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def set_user_balance_server |
| economy.py | adjust_user_balance_server | @economy_bp.route('/api/economy/adjust-balance/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def adjust_user_balance_server |
| economy.py | transfer_coins_server | @economy_bp.route('/api/economy/transfer/<server_id>', methods=['POST'])
    @require_auth
    def transfer_coins_server |
| economy.py | get_economy_leaderboard_server | @economy_bp.route('/api/economy/leaderboard/<server_id>')
    @require_auth
    def get_economy_leaderboard_server |
| economy.py | get_user_transactions_server | @economy_bp.route('/api/economy/transactions/<user_id>/<server_id>')
    @require_auth
    def get_user_transactions_server |
| economy.py | get_server_economy_stats | @economy_bp.route('/api/economy/server-stats/<server_id>')
    @require_auth
    def get_server_economy_stats |
| economy.py | get_user_balance_legacy | @economy_bp.route('/api/economy/balance/<user_id>')
    @require_auth
    def get_user_balance_legacy |
| economy.py | transfer_coins_legacy | @economy_bp.route('/api/economy/transfer', methods=['POST'])
    @require_auth
    def transfer_coins_legacy |
| events.py | start_koth_event | @events_bp.route('/api/events/koth/start', methods=['POST'])
    @require_auth
    def start_koth_event |
| events.py | stop_koth_event | @events_bp.route('/api/events/koth/stop', methods=['POST'])
    @require_auth
    def stop_koth_event |
| events.py | get_events | @events_bp.route('/api/events')
    @require_auth
    def get_events |
| events.py | get_event | @events_bp.route('/api/events/<event_id>')
    @require_auth
    def get_event |
| events.py | get_events_for_server | @events_bp.route('/api/events/server/<server_id>')
    @require_auth
    def get_events_for_server |
| events.py | get_event_stats | @events_bp.route('/api/events/stats')
    @require_auth
    def get_event_stats |
| events.py | get_arena_locations | @events_bp.route('/api/events/arena-locations')
    @require_auth
    def get_arena_locations |
| events.py | get_event_templates | @events_bp.route('/api/events/templates')
    @require_auth
    def get_event_templates |
| gambling.py | play_slots_server | @gambling_bp.route('/api/gambling/slots/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def play_slots_server |
| gambling.py | play_coinflip_server | @gambling_bp.route('/api/gambling/coinflip/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def play_coinflip_server |
| gambling.py | play_dice_server | @gambling_bp.route('/api/gambling/dice/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def play_dice_server |
| gambling.py | get_gambling_history_server | @gambling_bp.route('/api/gambling/history/<user_id>/<server_id>')
    @require_auth
    def get_gambling_history_server |
| gambling.py | get_gambling_stats_server | @gambling_bp.route('/api/gambling/stats/<user_id>/<server_id>')
    @require_auth
    def get_gambling_stats_server |
| gambling.py | get_gambling_leaderboard_server | @gambling_bp.route('/api/gambling/leaderboard/<server_id>')
    @require_auth
    def get_gambling_leaderboard_server |
| gambling.py | play_slots_legacy | @gambling_bp.route('/api/gambling/slots', methods=['POST'])
    @require_auth
    def play_slots_legacy |
| gambling.py | play_coinflip_legacy | @gambling_bp.route('/api/gambling/coinflip', methods=['POST'])
    @require_auth
    def play_coinflip_legacy |
| gambling.py | play_dice_legacy | @gambling_bp.route('/api/gambling/dice', methods=['POST'])
    @require_auth
    def play_dice_legacy |
| logs.py | get_servers | @logs_bp.route('/api/logs/servers')
    def get_servers |
| logs.py | get_logs | @logs_bp.route('/api/logs')
    @require_auth
    def get_logs |
| logs.py | download_logs | @logs_bp.route('/api/logs/download', methods=['POST'])
    @require_auth
    def download_logs |
| logs.py | download_log_file | @logs_bp.route('/api/logs/<log_id>/download')
    @require_auth
    def download_log_file |
| logs.py | refresh_logs | @logs_bp.route('/api/logs/refresh', methods=['POST'])
    @require_auth
    def refresh_logs |
| servers.py | get_servers | @servers_bp.route('/api/servers')
    @require_auth
    def get_servers |
| servers.py | add_server | @servers_bp.route('/api/servers/add', methods=['POST'])
    @require_auth
    def add_server |
| servers.py | update_server | @servers_bp.route('/api/servers/update/<server_id>', methods=['POST'])
    @require_auth
    def update_server |
| servers.py | delete_server | @servers_bp.route('/api/servers/delete/<server_id>', methods=['DELETE'])
    @require_auth
    def delete_server |
| servers.py | ping_server | @servers_bp.route('/api/servers/ping/<server_id>', methods=['POST'])
    @require_auth
    def ping_server |
| servers.py | bulk_server_action | @servers_bp.route('/api/servers/bulk-action', methods=['POST'])
    @require_auth
    def bulk_server_action |
| servers.py | get_server | @servers_bp.route('/api/servers/<server_id>')
    @require_auth
    def get_server |
| servers.py | get_server_stats | @servers_bp.route('/api/servers/stats')
    @require_auth
    def get_server_stats |
| users.py | temp_ban_user | @users_bp.route('/api/bans/temp', methods=['POST'])
    @require_auth
    def temp_ban_user |
| users.py | permanent_ban_user | @users_bp.route('/api/bans/permanent', methods=['POST'])
    @require_auth
    def permanent_ban_user |
| users.py | unban_user | @users_bp.route('/api/bans/unban', methods=['POST'])
    @require_auth
    def unban_user |
| users.py | give_item | @users_bp.route('/api/items/give', methods=['POST'])
    @require_auth
    def give_item |
| users.py | kick_user | @users_bp.route('/api/users/kick', methods=['POST'])
    @require_auth
    def kick_user |
| users.py | teleport_user | @users_bp.route('/api/users/teleport', methods=['POST'])
    @require_auth
    def teleport_user |
| users.py | get_bans | @users_bp.route('/api/bans')
    @require_auth
    def get_bans |
| users.py | get_user_history | @users_bp.route('/api/users/<user_id>/history')
    @require_auth
    def get_user_history |
| users.py | search_users | @users_bp.route('/api/users/search')
    @require_auth
    def search_users |
| users.py | get_user_stats | @users_bp.route('/api/users/stats')
    @require_auth
    def get_user_stats |
| user_database.py | register_user | @user_database_bp.route('/api/users/register', methods=['POST'])
    @require_auth
    def register_user |
| user_database.py | get_user_profile_route | @user_database_bp.route('/api/users/profile/<user_id>')
    @require_auth  
    def get_user_profile_route |
| user_database.py | update_user_profile | @user_database_bp.route('/api/users/profile/<user_id>', methods=['PUT'])
    @require_auth
    def update_user_profile |
| user_database.py | get_user_servers | @user_database_bp.route('/api/users/servers/<user_id>')
    @require_auth
    def get_user_servers |
| user_database.py | join_server | @user_database_bp.route('/api/users/join-server/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def join_server |
| user_database.py | get_server_leaderboard | @user_database_bp.route('/api/users/leaderboard/<server_id>')
    @require_auth
    def get_server_leaderboard |
| user_database.py | get_server_user_stats | @user_database_bp.route('/api/users/stats/<server_id>')
    @require_auth
    def get_server_user_stats |
| user_database.py | search_users | @user_database_bp.route('/api/users/search')
    @require_auth
    def search_users |
| app.py | index | @self.app.route('/')
        def index |
| app.py | health_check | @self.app.route('/health')
        def health_check |
| app.py | get_console_output | @self.app.route('/api/console/output')
        @require_auth
        def get_console_output |
| app.py | send_console_command | @self.app.route('/api/console/send', methods=['POST'])
        @require_auth
        def send_console_command |
| app.py | connect_live_console | @self.app.route('/api/console/live/connect', methods=['POST'])
        @require_auth
        def connect_live_console |
| app.py | disconnect_live_console | @self.app.route('/api/console/live/disconnect', methods=['POST'])
        @require_auth
        def disconnect_live_console |
| app.py | get_live_console_status | @self.app.route('/api/console/live/status')
        @require_auth
        def get_live_console_status |
| app.py | get_live_console_messages | @self.app.route('/api/console/live/messages')
        @require_auth
        def get_live_console_messages |
| app.py | test_live_console | @self.app.route('/api/console/live/test')
        @require_auth
        def test_live_console |
| app.py | get_clans | @self.app.route('/api/clans')
        @require_auth
        def get_clans |


## 🔧 Function & Class Analysis

**Python Code Statistics:**
- **Total Files**: 26
- **Total Lines**: 7928
- **Total Functions**: 269
- **Total Classes**: 13
- **Total Imports**: 145
- **Total Docstrings**: 252
- **Total Comments**: 418

**Top 10 Largest Python Files:**
| File | Lines | Functions | Classes | Size (KB) |
|------|-------|-----------|---------|-----------|
| app.py | 730 | 37 | 2 | 30.09 |
| gambling.py | 524 | 16 | 0 | 21.56 |
| clans.py | 489 | 12 | 0 | 20.43 |
| users.py | 480 | 11 | 0 | 19.29 |
| user_database.py | 449 | 15 | 0 | 18.23 |
| helpers.py | 395 | 16 | 0 | 10.7 |
| koth.py | 380 | 14 | 1 | 12.54 |
| koth.py | 380 | 14 | 1 | 12.54 |
| economy.py | 352 | 12 | 0 | 14.75 |
| client.py | 346 | 4 | 1 | 13.93 |


## ⚙️ Configuration & Environment Analysis

**Configuration Patterns Found: 38**

**Configuration Setting**: 38 references


## 🛡️ Authentication & Security Analysis

**Security Patterns Found: 80**

**Authentication Decorator**: 74 references
**Permission Check**: 6 references


## 🎨 Frontend Architecture Analysis

**JavaScript Files: 21**

| File | Lines | Functions | Classes | Events | AJAX | Size (KB) |
|------|-------|-----------|---------|--------|------|-----------|
| base-component.js | 591 | 0 | 3 | 12 | 0 | 17.76 |
| form-component.js | 784 | 1 | 2 | 11 | 0 | 24.54 |
| list-component.js | 1211 | 5 | 2 | 18 | 0 | 37.58 |
| clans.js | 833 | 3 | 1 | 25 | 0 | 34.4 |
| console.js | 812 | 5 | 1 | 34 | 0 | 34.71 |
| dashboard.js | 645 | 3 | 1 | 20 | 0 | 27.9 |
| economy.js | 498 | 0 | 1 | 14 | 0 | 20.55 |
| events.js | 769 | 3 | 1 | 27 | 0 | 33.48 |
| gambling.js | 724 | 3 | 1 | 23 | 0 | 29.36 |
| server-manager.js | 10 | 0 | 1 | 0 | 0 | 0.31 |
| user-management.js | 740 | 4 | 1 | 14 | 0 | 30.33 |
| notification-service.js | 804 | 0 | 1 | 34 | 0 | 25.48 |
| storage-service.js | 819 | 1 | 1 | 24 | 0 | 24.07 |
| validation-service.js | 659 | 1 | 1 | 6 | 0 | 22.81 |
| websocket-service.js | 665 | 4 | 1 | 33 | 1 | 21.52 |
| console-output.js | 842 | 5 | 2 | 30 | 0 | 30.19 |
| data-table.js | 924 | 10 | 1 | 21 | 0 | 31.25 |
| form-builder.js | 543 | 0 | 1 | 31 | 0 | 18.03 |
| modal.js | 677 | 1 | 4 | 26 | 0 | 22.63 |
| server-card.js | 524 | 0 | 1 | 13 | 0 | 19.01 |
| status-indicator.js | 661 | 1 | 3 | 14 | 0 | 19.49 |

**HTML Templates: 30**

| File | Lines | Variables | Forms | Includes | Size (KB) |
|------|-------|-----------|-------|----------|-----------|
| layout.html | 8 | 0 | 0 | 0 | 0.32 |
| sidebar.html | 90 | 0 | 0 | 0 | 4.37 |
| console_message.html | 2 | 0 | 0 | 0 | 0.05 |
| server_selector.html | 52 | 0 | 0 | 0 | 2.7 |
| user_registration.html | 54 | 0 | 0 | 0 | 2.79 |
| notification_toast.html | 3 | 0 | 0 | 0 | 0.08 |
| clans.js.html | 17 | 0 | 0 | 0 | 0.64 |
| console.js.html | 17 | 0 | 0 | 0 | 0.64 |
| dashboard.js.html | 17 | 0 | 0 | 0 | 0.65 |
| economy.js.html | 17 | 0 | 0 | 0 | 0.64 |
| enhanced_api.js.html | 233 | 0 | 0 | 0 | 7.32 |
| events.js.html | 17 | 0 | 0 | 0 | 0.64 |
| gambling.js.html | 17 | 0 | 0 | 0 | 0.65 |
| logs.js.html | 391 | 0 | 0 | 0 | 13.38 |
| main.js.html | 1469 | 0 | 0 | 0 | 65.44 |
| server_manager.js.html | 17 | 0 | 0 | 0 | 0.67 |
| user_management.js.html | 697 | 0 | 0 | 0 | 23.24 |
| clans.html | 37 | 0 | 0 | 0 | 2.42 |
| console.html | 139 | 0 | 0 | 0 | 9.46 |
| dashboard.html | 88 | 0 | 0 | 0 | 5.54 |
| dashboard_enhanced.html | 70 | 1 | 0 | 1 | 3.56 |
| economy.html | 32 | 0 | 0 | 0 | 2.09 |
| events.html | 62 | 0 | 0 | 0 | 4.52 |
| gambling.html | 37 | 0 | 0 | 0 | 2.4 |
| logs.html | 61 | 0 | 0 | 0 | 2.66 |
| server_manager.html | 84 | 0 | 0 | 0 | 5.14 |
| users.html | 48 | 0 | 0 | 0 | 3.36 |
| user_management.html | 170 | 0 | 0 | 0 | 8.93 |
| enhanced_dashboard.html | 47 | 21 | 0 | 20 | 1.68 |
| login.html | 91 | 0 | 1 | 0 | 4.33 |


## 📊 Database Operations Analysis

**Database Operations Found: 258**

**SQL Operation**: 181 operations
**MongoDB Operation**: 77 operations


## 🔗 Error Handling & Logging Analysis

**Error Handling Analysis:**
| File | Try Blocks | Except Blocks | Log Statements | Raise Statements |
|------|------------|---------------|----------------|------------------|
| auth.py | 4 | 5 | 20 | 0 |
| clans.py | 10 | 9 | 16 | 0 |
| client.py | 12 | 18 | 33 | 3 |
| economy.py | 11 | 11 | 16 | 0 |
| events.py | 6 | 6 | 13 | 0 |
| gambling.py | 14 | 14 | 21 | 0 |
| koth.py | 2 | 2 | 16 | 0 |
| logs.py | 10 | 8 | 13 | 0 |
| manager.py | 2 | 2 | 20 | 0 |
| servers.py | 9 | 9 | 20 | 0 |
| users.py | 10 | 10 | 21 | 0 |
| user_database.py | 14 | 8 | 15 | 2 |
| __init__.py | 0 | 0 | 3 | 0 |
| koth.py | 2 | 2 | 16 | 0 |
| __init__.py | 1 | 1 | 7 | 0 |
| helpers.py | 7 | 7 | 4 | 0 |
| user_helpers.py | 10 | 10 | 11 | 0 |
| user_migration.py | 4 | 4 | 13 | 0 |
| client.py | 12 | 18 | 33 | 3 |
| manager.py | 2 | 2 | 20 | 0 |
| __init__.py | 1 | 1 | 0 | 4 |
| app.py | 12 | 14 | 63 | 0 |
| config.py | 3 | 2 | 77 | 0 |
| main.py | 1 | 2 | 8 | 0 |


## 📦 Dependency Usage Analysis

**Requirements.txt packages**: 14
**Actual imports found**: 20

**Top imported modules:**
- **logging**: 20 times
- **datetime**: 19 times
- **routes**: 17 times
- **utils**: 11 times
- **config**: 11 times
- **flask**: 10 times
- **time**: 8 times
- **json**: 6 times
- **uuid**: 6 times
- **threading**: 5 times
- **os**: 5 times
- **random**: 4 times
- **asyncio**: 4 times
- **collections**: 4 times
- **secrets**: 4 times


## 🔍 File Relationships & Dependencies

**Internal Module Dependencies:**
- **app.py**: imports 15 local modules
  - utils.rate_limiter
  - utils.helpers
  - systems.koth
  - routes.auth
  - routes.servers
  - routes.events
  - routes.economy
  - routes.gambling
  - routes.clans
  - routes.users
  - routes.user_database
  - routes.logs
  - websocket.manager
  - utils.user_helpers
  - routes.auth
- **auth.py**: imports 2 local modules
  - utils.helpers
  - utils.helpers
- **clans.py**: imports 2 local modules
  - routes.auth
  - utils.user_helpers
- **client.py**: imports 6 local modules
  - utils.helpers
  - websocket
  - websocket
  - utils.helpers
  - websocket
  - websocket
- **config.py**: imports 1 local modules
  - websocket
- **economy.py**: imports 2 local modules
  - routes.auth
  - utils.user_helpers
- **events.py**: imports 1 local modules
  - routes.auth
- **gambling.py**: imports 2 local modules
  - routes.auth
  - utils.user_helpers
- **koth.py**: imports 2 local modules
  - utils.helpers
  - utils.helpers
- **logs.py**: imports 2 local modules
  - routes.auth
  - utils.helpers
- **servers.py**: imports 2 local modules
  - routes.auth
  - utils.helpers
- **user_database.py**: imports 1 local modules
  - routes.auth
- **user_helpers.py**: imports 1 local modules
  - routes.user_database
- **users.py**: imports 1 local modules
  - routes.auth


## 📈 Performance Metrics Analysis

**Performance Concerns Found:**
**Long Function**: 31 instances
- auth.py: authenticate_gportal (61 lines)
- clans.py: create_clan (73 lines)
- clans.py: join_clan (69 lines)
- clans.py: leave_clan (85 lines)
- clans.py: ensure_user_on_server (59 lines)
- client.py: __init__ (145 lines)
- client.py: _is_connection_open (134 lines)
- events.py: start_koth_event (51 lines)
- gambling.py: play_slots_server (56 lines)
- gambling.py: play_coinflip_server (58 lines)
- gambling.py: play_dice_server (58 lines)
- koth.py: _active_phase (57 lines)
- logs.py: get_server_logs (58 lines)
- logs.py: download_logs (84 lines)
- manager.py: add_connection (100 lines)
- servers.py: bulk_server_action (63 lines)
- users.py: temp_ban_user (69 lines)
- users.py: permanent_ban_user (57 lines)
- users.py: give_item (57 lines)
- user_database.py: register_user (76 lines)
- user_database.py: join_server (53 lines)
- koth.py: _active_phase (57 lines)
- helpers.py: refresh_token (51 lines)
- user_helpers.py: ensure_user_on_server (61 lines)
- user_migration.py: migrate_existing_data (82 lines)
- client.py: __init__ (145 lines)
- client.py: _is_connection_open (134 lines)
- manager.py: add_connection (100 lines)
- app.py: __init__ (73 lines)
- app.py: setup_routes (57 lines)
- config.py: print_startup_info (99 lines)
**Nested Loops**: 24 instances
- auth.py: Multiple (2 lines)
- clans.py: Multiple (8 lines)
- client.py: Multiple (15 lines)
- economy.py: Multiple (6 lines)
- events.py: Multiple (6 lines)
- gambling.py: Multiple (10 lines)
- koth.py: Multiple (7 lines)
- logs.py: Multiple (5 lines)
- manager.py: Multiple (10 lines)
- servers.py: Multiple (9 lines)
- users.py: Multiple (9 lines)
- user_database.py: Multiple (7 lines)
- koth.py: Multiple (7 lines)
- __init__.py: Multiple (4 lines)
- helpers.py: Multiple (7 lines)
- rate_limiter.py: Multiple (7 lines)
- user_helpers.py: Multiple (7 lines)
- user_migration.py: Multiple (5 lines)
- client.py: Multiple (15 lines)
- manager.py: Multiple (10 lines)
- __init__.py: Multiple (1 lines)
- app.py: Multiple (5 lines)
- config.py: Multiple (4 lines)
- main.py: Multiple (1 lines)


