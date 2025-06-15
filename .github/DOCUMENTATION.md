# GUST Bot Enhanced - Complete Documentation

## 🎯 Project Overview

**GUST Bot Enhanced** is a comprehensive, production-ready web application for managing Rust game servers through G-Portal integration. It features a complete web interface, real-time console monitoring, KOTH event management, economy system, and much more.

### Key Features
- ✅ **G-Portal Integration**: Full API integration with authentication
- ✅ **Real-time Console**: WebSocket-based live server monitoring
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
│   ├── dashboard.html           # Dashboard components
│   ├── notification_toast.html  # Notifications
│   └── console_message.html     # Console formatting
├── 📁 static/css/               # CSS styling
│   ├── themes.css               # Primary theme file
│   ├── base.css                 # Foundation styles
│   ├── components.css           # Component styling
│   ├── animations.css           # Hover/transitions
│   └── layout.css               # Layout structure
├── 📁 static/js/                # Frontend JavaScript
│   ├── config.js                # Frontend configuration
│   ├── api.js                   # API communication
│   ├── router.js                # Frontend routing
│   ├── validation-service.js    # Form validation
│   └── websocket-service.js     # WebSocket management
└── 📁 data/                     # Data storage (auto-created)
    ├── servers.json             # Server configurations
    ├── events.json              # Event data
    └── gp-session.json          # G-Portal session
```

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.7+ 
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/WDC-GP/GUST-MARK-1.git
cd GUST-MARK-1
```

2. **Create required directories**
```bash
mkdir -p data templates static/css static/js
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python main.py
```

5. **Access the web interface**
- Open http://localhost:5000
- Login with `admin`/`password` for demo mode
- Or use G-Portal credentials for live mode

## 🎨 Complete Theme Customization Guide

### Files to Modify for Complete Theme Change

#### **1. Core Theme Files (Required)**

##### `static/css/themes.css` - **PRIMARY THEME FILE**
**Purpose**: Main theme colors, component styling, and visual appearance

```css
:root {
    /* Purple Theme - MAIN BRAND COLORS TO CHANGE */
    --purple-400: #a855f7;      /* Light brand accent */
    --purple-500: #8b5cf6;      /* Medium brand color */
    --purple-600: #7c3aed;      /* **PRIMARY BRAND COLOR** */
    --purple-700: #6d28d9;      /* Dark brand color */
}
```

##### `static/css/base.css` - **FOUNDATION STYLES**
**Purpose**: Core CSS variables and foundation styling

```css
:root {
  --primary-500: #8B5CF6;      /* **MAIN BRAND COLOR** */
  --primary-600: #7C3AED;      /* Dark brand */
}
```

##### `templates/enhanced_dashboard.html` - **MAIN DASHBOARD**
**Purpose**: Main application interface with embedded styles

```html
<style>
    .nav-tab.active {
        background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
        /* CHANGE TO: background: linear-gradient(135deg, #YOUR_PRIMARY 0%, #YOUR_LIGHT 100%); */
    }
</style>
```

### Quick Color Replacement

Search and replace these colors throughout your project:

| Current Color | Hex Code | Usage | Replace With |
|---------------|----------|-------|--------------|
| **Purple 600** | `#7C3AED` | **PRIMARY BRAND** | `#YOUR_PRIMARY` |
| **Purple 500** | `#8B5CF6` | Medium brand | `#YOUR_MEDIUM` |
| **Purple 400** | `#A855F7` | Light brand | `#YOUR_LIGHT` |
| **Purple 700** | `#6D28D9` | Dark brand | `#YOUR_DARK` |

### Pre-built Color Schemes

#### **Blue Theme**
```css
--purple-400: #60a5fa;  /* Blue 400 */
--purple-500: #3b82f6;  /* Blue 500 */
--purple-600: #2563eb;  /* Blue 600 */
--purple-700: #1d4ed8;  /* Blue 700 */
```

#### **Green Theme**
```css
--purple-400: #4ade80;  /* Green 400 */
--purple-500: #22c55e;  /* Green 500 */
--purple-600: #16a34a;  /* Green 600 */
--purple-700: #15803d;  /* Green 700 */
```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 for Python
- Use ES6+ for JavaScript
- Include comprehensive docstrings
- Use type hints where possible

### Adding New Features
1. Create route file in `routes/`
2. Implement blueprint
3. Add to `routes/__init__.py`
4. Register in `app.py`
5. Add tests

## 🐛 Troubleshooting

### Common Issues

**"WebSocket support not available"**
```bash
pip install websockets
```

**"G-Portal authentication failed"**
- Try demo mode: `admin`/`password`
- Verify credentials
- Check internet connection

**"MongoDB connection failed"**
- MongoDB is optional
- Demo mode works without database

## 📞 Support

- 🐛 **Bug Reports**: [Create an issue](https://github.com/WDC-GP/GUST-MARK-1/issues)
- 💡 **Feature Requests**: [Create an issue](https://github.com/WDC-GP/GUST-MARK-1/issues)
- 💬 **Questions**: [Start a discussion](https://github.com/WDC-GP/GUST-MARK-1/discussions)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**GUST Bot Enhanced** - Complete Rust server management solution with real-time monitoring, event management, and economy system. Production-ready with demo mode for testing.
