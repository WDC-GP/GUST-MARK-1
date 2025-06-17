# 🚀 GUST Bot Enhanced

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

**Complete Rust Server Management Solution with Real-time Monitoring & Logs**

[Quick Start](#-quick-start) • [Features](#-features) • [Demo](#-demo) • [Documentation](.github/DOCUMENTATION.md)

</div>

## 📋 Overview

GUST Bot Enhanced is a comprehensive web application for managing Rust game servers through G-Portal integration. Features real-time console monitoring, server log management, KOTH events, economy system, gambling games, clan management, and more.

## ✨ Key Features

- 🎯 **Production Ready**: Complete, tested, and deployable
- 🔌 **Real-time Console**: WebSocket-based live server monitoring  
- 📋 **Server Logs**: Direct G-Portal log downloading and parsing
- 🏆 **KOTH Events**: Vanilla Rust-compatible King of the Hill
- 💰 **Economy & Gambling**: Complete coin management and casino games
- 👥 **Clan Management**: Full clan system with permissions
- 🔧 **User Administration**: Player management and moderation tools
- 🎮 **Demo Mode**: Full functionality without G-Portal credentials
- 🏗️ **Modular Architecture**: Clean, maintainable codebase

## 🚀 Quick Start

### Installation & Setup
```bash
# Clone and install
git clone https://github.com/WDC-GP/GUST-MARK-1.git
cd GUST-MARK-1
mkdir -p data templates static/css static/js
pip install -r requirements.txt

# Run the application
python main.py

# Access at http://localhost:5000
```

### Login Options
- **Demo Mode**: Username `admin`, Password `password`
- **Live Mode**: Your G-Portal credentials

## 🎯 Features Overview

Explore all **9 management tabs**:

| Tab | Feature | Description |
|-----|---------|-------------|
| 📊 | **Dashboard** | Server overview and system status |
| 🖥️ | **Server Manager** | Multi-server configuration |
| 📺 | **Live Console** | Real-time console monitoring |
| 📋 | **Server Logs** | Log download and management |
| 🏆 | **Events** | KOTH event system |
| 💰 | **Economy** | User balance management |
| 🎰 | **Gambling** | Casino games and betting |
| 👥 | **Clans** | Clan system administration |
| 🔧 | **Users** | Player management tools |

## 🆕 Server Logs (Latest Feature)

- **Direct G-Portal Integration**: Download logs using stored authentication
- **Multi-server Support**: Access logs from all configured servers
- **Structured Parsing**: Convert logs to JSON format for analysis
- **Real-time Preview**: Formatted display of recent entries
- **Export Functionality**: Download parsed logs as files

## 🎮 Demo Mode

Perfect for testing and development:
1. Start with `python main.py`
2. Login with `admin`/`password`  
3. Explore all features safely without external API calls

## 📊 System Requirements

- **Python**: 3.7+
- **RAM**: 512MB minimum, 1GB+ recommended
- **Storage**: 100MB minimum, 500MB+ recommended
- **Network**: Required for G-Portal live features

## 🐛 Troubleshooting

**Common Solutions:**
```bash
# WebSocket issues
pip install websockets

# G-Portal authentication
# Use demo mode first: admin/password

# Logs not downloading
# Ensure G-Portal credentials (not demo mode)
# Verify Server Manager configuration
```

## 📖 Documentation

### 📚 Complete Documentation
For detailed information, see our comprehensive documentation:

**[📋 Complete Documentation](.github/DOCUMENTATION.md)**

Includes:
- Detailed setup instructions
- Complete API reference  
- Architecture documentation
- Development guidelines
- Advanced troubleshooting
- Performance optimization
- Security best practices

### 🎨 Additional Resources
- [Theme Customization](.github/THEME_QUICK_REF.md)
- [Contributing Guidelines](.github/CONTRIBUTING.md)
- [API Reference](.github/API_REFERENCE.md)

## 🤝 Contributing

We welcome contributions! See [Contributing Guidelines](.github/CONTRIBUTING.md) for:
- Development setup
- Code standards
- Testing procedures
- Pull request process

## 📞 Support

- 🐛 **Bug Reports**: [Create an issue](https://github.com/WDC-GP/GUST-MARK-1/issues)
- 💡 **Feature Requests**: [Create an issue](https://github.com/WDC-GP/GUST-MARK-1/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/WDC-GP/GUST-MARK-1/discussions)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the Rust community**

[⭐ Star this repo](https://github.com/WDC-GP/GUST-MARK-1) • [🍴 Fork it](https://github.com/WDC-GP/GUST-MARK-1/fork) • [📖 Full Documentation](.github/DOCUMENTATION.md)

</div>