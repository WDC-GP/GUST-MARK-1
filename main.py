#!/usr/bin/env python3
"""
GUST Bot Enhanced - Main Entry Point
===================================
[ROCKET] Complete GUST bot with working KOTH events AND live console monitoring
[CHECK] Fixed KOTH system that works with vanilla Rust servers  
[CHECK] Working GraphQL command sending (tested and verified)
[CHECK] Real-time WebSocket console monitoring
[CHECK] Enhanced web interface with live console tab
[CHECK] Multi-server WebSocket management
[CHECK] All features in modular file structure
"""

# Standard library imports
import os
import sys

# Local imports
from config import check_dependencies, print_startup_info

# Other imports
from app import GustBotEnhanced

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)


def main():
    """Main entry point for GUST Bot Enhanced"""
    
    # Check and report dependency status
    print("[INFO] Checking dependencies...")
    websockets_available, mongodb_available, missing_deps = check_dependencies()
    
    if missing_deps:
        print("[WARNING] Missing optional dependencies:")
        for dep in missing_deps:
            print(f"   * {dep}")
        print()
        if not websockets_available:
            print("[TIP] To enable live console: pip install websockets")
            print()
    
    # Print startup information
    print_startup_info(websockets_available, mongodb_available)
    
    # Create and run the enhanced GUST bot
    try:
        gust = GustBotEnhanced()
        gust.run()
    except KeyboardInterrupt:
        print("\n[EXIT] GUST Enhanced stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")


if __name__ == "__main__":
    main()