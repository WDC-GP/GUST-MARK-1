# GUST Bot Enhanced - Complete Documentation

## 🎯 Project Overview

**GUST Bot Enhanced** is a comprehensive, production-ready web application for managing Rust game servers through G-Portal integration. It features a complete web interface, real-time console monitoring, server log management, KOTH event management, economy system, and much more.

### Key Features
- ✅ **G-Portal Integration**: Full API integration with authentication
- ✅ **Real-time Console**: WebSocket-based live server monitoring
- ✅ **Server Log Management**: Direct log downloading and parsing from G-Portal
- ✅ **KOTH Events**: Vanilla Rust-compatible King of the Hill events
- ✅ **Economy System**: Complete coin management and transactions
- ✅ **Gambling Games**: Slots, coinflip, and dice games
- ✅ **Clan Management**: Full clan system with permissions
- ✅ **User Administration**: Temp/permanent bans and item management
- ✅ **Demo Mode**: Full functionality without G-Portal credentials
- ✅ **Modular Architecture**: Clean, maintainable code structure

## 📁 Project Structure

```
GUST-MARK-1/
├── 📄 main.py                    # Entry point with dependency checking
├── 📄 app.py                     # Main Flask application
├── 📄 config.py                  # Configuration and settings
├── 📄 requirements.txt           # Python dependencies
├── 📁 routes/                    # Flask route blueprints
│   ├── __init__.py              # Route package manager
│   ├── auth.py                  # Authentication routes
│   ├── servers.py               # Server management
│   ├── logs.py                  # Server log management (NEW!)
│   ├── events.py                # Event management
│   ├── economy.py               # Economy system
│   ├── gambling.py              # Gambling games
│   ├── clans.py                 # Clan management
│   └── users.py                 # User administration
├── 📁 systems/                   # Game systems
│   ├── __init__.py              # Systems package
│   └── koth.py                  # KOTH event system
├── 📁 utils/                     # Utility functions
│   ├── __init__.py              # Utils package
│   ├── helpers.py               # Helper functions
│   └── rate_limiter.py          # API rate limiting
├── 📁 websocket/                 # WebSocket components
│   ├── __init__.py              # WebSocket package
│   ├── manager.py               # WebSocket manager
│   └── client.py                # G-Portal WebSocket client
├── 📁 templates/                 # HTML templates
│   ├── login.html               # Login page
│   ├── enhanced_dashboard.html  # Main dashboard
│   ├── base/                    # Base components
│   │   └── sidebar.html         # Navigation sidebar
│   ├── views/                   # Tab view templates
│   │   ├── dashboard.html       # Dashboard content
│   │   ├── servers.html         # Server management
│   │   ├── console.html         # Live console
│   │   ├── logs.html            # Server logs (NEW!)
│   │   ├── events.html          # Event management
│   │   ├── economy.html         # Economy system
│   │   ├── gambling.html        # Gambling games
│   │   ├── clans.html           # Clan management
│   │   └── users.html           # User administration
│   └── scripts/                 # JavaScript modules
│       ├── dashboard.js.html    # Dashboard functionality
│       ├── servers.js.html      # Server management
│       ├── console.js.html      # Live console
│       ├── logs.js.html         # Log management (NEW!)
│       ├── events.js.html       # Event management
│       ├── economy.js.html      # Economy system
│       ├── gambling.js.html     # Gambling games
│       ├── clans.js.html        # Clan management
│       └── users.js.html        # User administration
├── 📁 static/                    # Static assets
│   ├── css/                     # Stylesheets
│   ├── js/                      # JavaScript files
│   └── images/                  # Image assets
└── 📁 data/                      # Data storage
    ├── sessions/                # Session data
    ├── logs/                    # Downloaded server logs (NEW!)
    └── backups/                 # Data backups
```

## 🎮 Application Features

### 🏠 Dashboard
- **Server Overview**: Real-time status of all configured servers
- **Recent Activities**: Latest events and transactions
- **Quick Actions**: Fast access to common tasks
- **System Status**: Application health and performance metrics

### 🖥️ Server Manager
- **Multi-server Support**: Manage multiple Rust servers
- **Server Configuration**: Set up and configure server connections
- **Status Monitoring**: Real-time server status and metrics
- **Connection Management**: G-Portal integration and authentication

### 📺 Live Console
- **Real-time Output**: Live server console monitoring via WebSocket
- **Command Execution**: Send console commands remotely
- **Command History**: Previous commands and responses
- **Auto-scroll**: Automatic scrolling to latest output

### 📋 Server Logs (NEW!)
- **Direct G-Portal Integration**: Download logs directly from G-Portal API using stored authentication tokens
- **Multi-server Support**: Access logs from all configured servers in the Server Manager
- **Structured Log Parsing**: Convert raw server logs into structured JSON format for analysis
- **Real-time Log Preview**: Preview recent log entries with proper formatting and timestamps
- **Download System**: Export parsed logs as JSON files for external analysis
- **Progress Tracking**: Real-time status updates during log download and processing operations
- **Auto-refresh Capability**: Live updates of log lists and download status
- **Secure Authentication**: Uses existing G-Portal session tokens without requiring additional credentials

#### Log Management Features:
- **Server Selection Dropdown**: Choose from all servers configured in Server Manager
- **One-click Log Download**: Simple interface for fetching the latest server logs
- **Structured Log Display**: Organized view of log entries with timestamps, levels, and context
- **JSON Export Functionality**: Download processed logs for use in external analysis tools
- **Download Progress Monitoring**: Clear visual feedback on download progress and completion
- **Error Handling**: Comprehensive error messages and status updates
- **Log Entry Preview**: Real-time preview of recent log entries with syntax highlighting
- **Metadata Display**: Show log file information including entry counts and parsing status

#### Technical Implementation:
- **Direct API Access**: Uses discovered G-Portal log endpoints for efficient data retrieval
- **Token Management**: Leverages existing authentication system with automatic token refresh
- **Headless Operation**: No browser automation required - pure HTTP API integration
- **Modular Architecture**: Seamlessly integrates with existing Flask blueprint system
- **No Additional Dependencies**: Uses existing project requirements without external additions

### 🏆 Events
- **KOTH System**: Complete King of the Hill event management
- **Event Scheduling**: Plan and automate events
- **Vanilla Compatible**: No server plugins required
- **Reward Distribution**: Automatic winner rewards
- **Event History**: Track past events and statistics

### 💰 Economy
- **User Balances**: Complete coin management system
- **Transaction Logging**: Full transaction history
- **Admin Controls**: Add/remove coins from users
- **Economy Statistics**: Spending and earning analytics

### 🎰 Gambling
- **Slot Machines**: Configurable slot game with payouts
- **Coinflip**: Simple betting game
- **Dice Games**: Various dice-based gambling options
- **Statistics Tracking**: Gambling analytics and leaderboards

### 👥 Clans
- **Clan Creation**: Users can create and join clans
- **Permission System**: Clan roles and permissions
- **Clan Management**: Admin tools for clan oversight
- **Member Statistics**: Clan member analytics

### 🔧 Users
- **User Administration**: Complete user management
- **Ban System**: Temporary and permanent bans
- **Item Giving**: Give items to players
- **User Profiles**: Player statistics and history

## 🔧 Technical Architecture

### Backend Components

#### Flask Application (`app.py`)
- **Modular Design**: Clean separation of concerns
- **Blueprint System**: Organized route management
- **Error Handling**: Comprehensive error management
- **Security**: Authentication and authorization

#### Route Blueprints (`routes/`)
- **Authentication** (`auth.py`): Login/logout functionality
- **Server Management** (`servers.py`): Server CRUD operations
- **Log Management** (`logs.py`): Server log downloading, parsing, and management
- **Event System** (`events.py`): KOTH event management
- **Economy** (`economy.py`): Coin and transaction management
- **Gambling** (`gambling.py`): Casino game implementations
- **Clan System** (`clans.py`): Clan management functionality
- **User Administration** (`users.py`): User management tools

#### Log Management System (`routes/logs.py`)
- **G-Portal API Client**: Direct integration with G-Portal log endpoints
- **Authentication Integration**: Uses existing token management system
- **Multi-server Support**: Automatically detects configured servers
- **Log Parsing Engine**: Converts raw logs to structured JSON format
- **File Management**: Organized storage and cleanup of downloaded logs
- **Error Handling**: Comprehensive error management and user feedback
- **Rate Limiting**: Respects G-Portal API limits and implements backoff strategies

#### Utility Systems (`utils/`)
- **Helper Functions** (`helpers.py`): Common utilities including token management
- **Rate Limiting** (`rate_limiter.py`): API protection
- **Configuration** (`config.py`): Application settings

#### WebSocket System (`websocket/`)
- **Manager** (`manager.py`): WebSocket connection management
- **Client** (`client.py`): G-Portal WebSocket integration

### Frontend Components

#### Modular Templates (`templates/`)
- **Master Template** (`enhanced_dashboard.html`): Main application layout
- **View Components** (`views/`): Individual tab content including new logs view
- **Script Modules** (`scripts/`): Feature-specific JavaScript including logs management
- **Base Components** (`base/`): Reusable UI elements

#### Log Management Frontend (`templates/views/logs.html` & `templates/scripts/logs.js.html`)
- **Server Selection Interface**: Dropdown populated from Server Manager configuration
- **Download Controls**: Intuitive buttons for log operations
- **Progress Indicators**: Real-time status updates and progress bars
- **Log Preview Panel**: Formatted display of recent log entries
- **Download Links**: Direct access to parsed JSON files
- **Status Messages**: Clear feedback for all operations
- **Responsive Design**: Mobile-friendly interface matching G-Portal theme

#### Static Assets (`static/`)
- **Stylesheets**: Tailwind CSS with custom G-Portal theme
- **JavaScript**: Modular frontend functionality
- **Images**: Application icons and graphics

## 🔐 Authentication & Security

### G-Portal Integration
- **Token Management**: Secure token storage and refresh in `gp-session.json`
- **Session Handling**: Automatic session management
- **API Protection**: Rate limiting and request validation
- **Secure Headers**: Security headers for web protection

### Log Security
- **Authenticated Access**: All log operations require valid G-Portal authentication
- **Secure Token Usage**: Uses existing session tokens without exposing credentials
- **Input Validation**: Comprehensive validation of server selections and parameters
- **Rate Limiting**: Protects against excessive API calls
- **Error Sanitization**: Prevents sensitive information exposure in error messages

### Demo Mode
- **Full Functionality**: Complete feature access without credentials
- **Safe Testing**: No external API calls in demo mode
- **Development Support**: Easy development and testing

## 📊 Data Management

### Storage Systems
- **Memory Storage**: In-memory data for development
- **File Storage**: JSON-based persistent storage
- **MongoDB Support**: Optional database integration
- **Session Management**: Secure session handling

### Log Storage and Management
- **Download Directory Structure**: Organized storage in `data/logs/` with server-specific subdirectories
- **Parsed Log Format**: Structured JSON format with timestamps, levels, contexts, and messages
- **Metadata Tracking**: Complete log download history with timestamps and status
- **Automatic Cleanup**: Configurable retention policies for old logs
- **File Organization**: Server-specific directories with timestamp-based file naming
- **Storage Optimization**: Compressed storage options for large log files

#### Log File Structure:
```
data/logs/
├── server_1736296/              # Server-specific directories
│   ├── raw/                     # Original downloaded logs
│   │   └── public_20250617.log  # Raw log files
│   ├── parsed/                  # Processed JSON logs
│   │   └── parsed_20250617.json # Structured log data
│   └── metadata.json            # Download history and status
└── server_1234567/              # Additional servers
    ├── raw/
    ├── parsed/
    └── metadata.json
```

#### Log Data Format:
```json
{
  "metadata": {
    "server_id": "1736296",
    "download_time": "2025-06-17T12:00:00Z",
    "total_entries": 1247,
    "parsed_entries": 1198,
    "file_size": 2048576
  },
  "entries": [
    {
      "timestamp": "2025-06-17T11:59:58",
      "level": "INFO",
      "context": "Server",
      "message": "Player connected: SteamID[12345]",
      "raw": "[11:59:58] [INFO] [Server] Player connected: SteamID[12345]"
    }
  ]
}
```

## 🚀 Development Guide

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/WDC-GP/GUST-MARK-1.git
cd GUST-MARK-1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p data/logs data/sessions data/backups
mkdir -p templates/views templates/scripts
mkdir -p static/css static/js static/images

# Run in development mode
export FLASK_ENV=development  # Linux/Mac
# set FLASK_ENV=development   # Windows
python main.py
```

### Adding New Features

#### Backend Route
1. Create route file in `routes/`
2. Implement blueprint pattern
3. Add to `routes/__init__.py`
4. Register in `app.py`
5. Add error handling

#### Frontend Component
1. Create view template in `templates/views/`
2. Create script module in `templates/scripts/`
3. Update sidebar navigation
4. Add to main dashboard includes
5. Test integration

### Log System Development

#### Adding New Log Sources
1. Extend `routes/logs.py` with new API endpoints
2. Add parsing logic for different log formats
3. Update frontend to support new log types
4. Add appropriate error handling

#### Customizing Log Display
1. Modify `templates/views/logs.html` for new UI elements
2. Update `templates/scripts/logs.js.html` for new functionality
3. Add CSS styling in existing theme files
4. Test across different screen sizes

### Testing

#### Manual Testing
- Demo mode functionality
- G-Portal integration (if credentials available)
- All tab navigation including logs
- WebSocket connections
- Log download and parsing operations
- Mobile responsiveness

#### Log System Testing
- Server selection and configuration
- Log download with various server states
- Error handling for network issues
- Large log file processing
- Concurrent download operations

#### Automated Testing
```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest tests/

# Run log-specific tests
pytest tests/test_logs.py
```

## 🔌 API Reference

### Log Management Endpoints

#### GET `/api/logs/servers`
Get list of configured servers for log access.
```json
{
  "servers": [
    {
      "id": "1736296",
      "name": "My Rust Server",
      "region": "us"
    }
  ]
}
```

#### POST `/api/logs/download`
Download logs for a specific server.
```json
{
  "server_id": "1736296"
}
```

#### GET `/api/logs`
Get list of downloaded logs with metadata.
```json
{
  "logs": [
    {
      "id": "logs_1736296_20250617",
      "server_id": "1736296",
      "server_name": "My Rust Server",
      "download_time": "2025-06-17T12:00:00Z",
      "total_entries": 1247,
      "parsed_entries": 1198
    }
  ]
}
```

#### GET `/api/logs/<log_id>`
Get specific log entries with pagination.
```json
{
  "log_id": "logs_1736296_20250617",
  "entries": [...],
  "total": 1198,
  "page": 1,
  "per_page": 50
}
```

#### GET `/api/logs/<log_id>/download`
Download parsed log file as JSON.

#### POST `/api/logs/refresh`
Refresh the list of available logs.

## 🐛 Troubleshooting

### Common Issues

**"WebSocket support not available"**
```bash
pip install websockets
```

**"G-Portal authentication failed"**
- Try demo mode: `admin`/`password`
- Verify credentials are correct
- Check internet connection
- Ensure G-Portal service is accessible

**"MongoDB connection failed"**
- MongoDB is optional for basic functionality
- Demo mode works without database
- Check MongoDB service status if using

**"Logs not downloading"**
- Ensure you're using G-Portal credentials (not demo mode)
- Verify servers are configured in Server Manager
- Check G-Portal API service availability
- Review browser console for JavaScript errors
- Verify `data/logs/` directory permissions

**"Log parsing errors"**
- Check raw log file format for corruption
- Verify sufficient disk space for processing
- Review application logs for specific parsing errors
- Ensure log files are not locked by other processes

**"Templates not loading"**
- Verify template directory structure
- Check file permissions
- Ensure Flask template path configuration

**"Log preview not displaying"**
- Check JavaScript console for errors
- Verify log entries are properly formatted
- Ensure CSS styles are loading correctly
- Test with smaller log files first

### Log System Debugging

#### Enable Debug Logging
```python
# In config.py
LOG_LEVEL = 'DEBUG'
```

#### Check Log Directory Structure
```bash
# Verify directory exists and has proper permissions
ls -la data/logs/
find data/logs/ -type f -name "*.log"
```

#### Test API Endpoints
```bash
# Test server list endpoint
curl -X GET http://localhost:5000/api/logs/servers

# Test log download
curl -X POST http://localhost:5000/api/logs/download \
  -H "Content-Type: application/json" \
  -d '{"server_id": "1736296"}'
```

## 📈 Performance Optimization

### Frontend Optimization
- **Lazy Loading**: Load log components as needed
- **Caching**: Browser caching for static assets
- **Minification**: Compressed CSS and JavaScript
- **CDN Support**: Ready for CDN deployment

### Backend Optimization
- **Connection Pooling**: Efficient database connections
- **Caching**: In-memory caching for frequent data
- **Rate Limiting**: Protect against API abuse
- **Async Operations**: Non-blocking operations where possible

### Log System Optimization
- **Streaming Downloads**: Process large logs without memory issues
- **Background Processing**: Parse logs asynchronously
- **Compression**: Compress stored logs to save space
- **Pagination**: Load log entries in manageable chunks
- **Caching**: Cache frequently accessed log data
- **Cleanup Jobs**: Automatic removal of old log files

## 📞 Support & Contributing

### Getting Help
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/WDC-GP/GUST-MARK-1/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/WDC-GP/GUST-MARK-1/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/WDC-GP/GUST-MARK-1/discussions)

### Contributing
- See [Contributing Guidelines](.github/CONTRIBUTING.md)
- Follow modular architecture patterns
- Include tests for new features
- Update documentation for changes
- Test log functionality with various server configurations

### Development Resources
- [Theme Customization](.github/THEME_QUICK_REF.md)
- [API Documentation](.github/API_REFERENCE.md)
- [Deployment Guide](.github/DEPLOYMENT.md)

---

**GUST Bot Enhanced** - Complete Rust server management solution with comprehensive logging, real-time monitoring, event management, and economy system. Production-ready with demo mode for testing and development.