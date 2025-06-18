#!/usr/bin/env python3
"""
GUST Bot Enhanced - Main Entry Point
===================================
🚀 Complete GUST bot with working KOTH events AND live console monitoring
✅ Fixed KOTH system that works with vanilla Rust servers  
✅ Working GraphQL command sending (tested and verified)
✅ Real-time WebSocket console monitoring
✅ Enhanced web interface with live console tab
✅ Multi-server WebSocket management
✅ All features in modular file structure
"""

import os
import sys

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import GustBotEnhanced
from config import check_dependencies, print_startup_info

def main():
    """Main entry point for GUST Bot Enhanced"""
    
    # Check and report dependency status
    print("🔍 Checking dependencies...")
    websockets_available, mongodb_available, missing_deps = check_dependencies()
    
    if missing_deps:
        print("⚠️ Missing optional dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print()
        if not websockets_available:
            print("💡 To enable live console: pip install websockets")
            print()
    
    # Print startup information
    print_startup_info(websockets_available, mongodb_available)
    
    # Create and run the enhanced GUST bot
    try:
        gust = GustBotEnhanced()
        gust.run()
    except KeyboardInterrupt:
        print("\n👋 GUST Enhanced stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
