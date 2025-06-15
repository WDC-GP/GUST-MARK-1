# 🚀 GUST Bot Enhanced

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

**Complete Rust Server Management Solution with Real-time Monitoring**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Demo](#-demo) • [Contributing](#-contributing)

</div>

## 📋 Overview

GUST Bot Enhanced is a comprehensive web application for managing Rust game servers through G-Portal integration. Features include real-time console monitoring, KOTH event management, economy system, gambling games, clan management, and much more.

### ✨ Key Highlights

- 🎯 **Production Ready**: Complete, tested, and deployable
- 🔌 **Real-time Console**: WebSocket-based live server monitoring  
- 🏆 **KOTH Events**: Vanilla Rust-compatible King of the Hill
- 💰 **Economy System**: Complete coin management and gambling
- 👥 **Clan Management**: Full clan system with permissions
- 🎮 **Demo Mode**: Full functionality without G-Portal credentials
- 🏗️ **Modular Design**: Clean, maintainable architecture

## 🎮 Features

### Server Management
- ✅ **Multi-server Support**: Manage multiple Rust servers
- ✅ **Real-time Monitoring**: Live console output and status
- ✅ **Remote Commands**: Send console commands remotely
- ✅ **Server Diagnostics**: Performance and status monitoring

### Event System
- 🏆 **KOTH Events**: Automated King of the Hill events
- 📅 **Event Scheduling**: Plan and automate events
- 🎯 **Vanilla Compatible**: No server plugins required
- 🏅 **Reward System**: Automatic winner rewards

### Economy & Gaming
- 💰 **Economy System**: User balance management
- 🎰 **Gambling Games**: Slots, coinflip, dice games
- 💳 **Transactions**: Complete transaction logging
- 📊 **Statistics**: Gambling and economy statistics

### User Management
- 👥 **Clan System**: Complete clan management
- 🔨 **Admin Tools**: Ban management and moderation
- 🎁 **Item Giving**: Give items to players
- 📋 **User Profiles**: Player statistics and history

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/WDC-GP/GUST-MARK-1.git
cd GUST-MARK-1

# Create directories
mkdir -p data templates static/css static/js

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
# Start the application
python main.py

# Access the web interface
# http://localhost:5000
```

### 3. Login

**Demo Mode** (No G-Portal account needed):
- Username: `admin`
- Password: `password`

**Live Mode** (With G-Portal credentials):
- Use your G-Portal username and password

## 📖 Documentation

### Quick Links
- [📚 Complete Documentation](.github/DOCUMENTATION.md)
- [🎨 Theme Customization](.github/THEME_QUICK_REF.md)
- [🤝 Contributing Guidelines](.github/CONTRIBUTING.md)

## 🎯 Demo

Try the demo mode to explore all features:

1. Start the application: `python main.py`
2. Open http://localhost:5000
3. Login with `admin`/`password`
4. Explore all 8 tabs:
   - 📊 Dashboard
   - 🖥️ Server Manager  
   - 📺 Live Console
   - 🏆 Events
   - 💰 Economy
   - 🎰 Gambling
   - 👥 Clans
   - 🔧 Users

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](.github/CONTRIBUTING.md) for details.

## 📊 System Requirements

### Minimum Requirements
- Python 3.7+
- 512MB RAM
- 100MB disk space

### Dependencies
- Flask 2.3.3
- requests 2.31.0
- schedule 1.2.0
- websockets 11.0.3 (optional)
- pymongo 4.5.0 (optional)

## 🐛 Troubleshooting

### Common Issues

**WebSocket support not available**
```bash
pip install websockets
```

**G-Portal authentication failed**
- Try demo mode first: `admin`/`password`
- Verify your G-Portal credentials
- Check internet connection

## 📞 Support

- 🐛 **Bug Reports**: [Create an issue](https://github.com/WDC-GP/GUST-MARK-1/issues)
- 💡 **Feature Requests**: [Create an issue](https://github.com/WDC-GP/GUST-MARK-1/issues)
- 💬 **Questions**: [Start a discussion](https://github.com/WDC-GP/GUST-MARK-1/discussions)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the Rust community**

[⭐ Star this repo](https://github.com/WDC-GP/GUST-MARK-1) • [🍴 Fork it](https://github.com/WDC-GP/GUST-MARK-1/fork) • [📖 Read the docs](.github/DOCUMENTATION.md)

</div>
