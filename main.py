#!/usr/bin/env python3
"""
GUST Bot Enhanced - Main Entry Point
====================================
This is the main entry point that starts the GUST Bot Enhanced application
"""

import os
import sys
import logging

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def check_dependencies():
    """Check and report dependency status"""
    websockets_available = False
    mongodb_available = False
    missing_deps = []
    
    # Check for websockets
    try:
        import websockets
        websockets_available = True
        print("✅ WebSockets: Available")
    except ImportError:
        missing_deps.append("websockets (for live console)")
        print("⚠️ WebSockets: Not available")
    
    # Check for MongoDB
    try:
        import pymongo
        mongodb_available = True
        print("✅ MongoDB: Available")
    except ImportError:
        missing_deps.append("pymongo (for persistent storage)")
        print("⚠️ MongoDB: Not available")
    
    # Check for requests
    try:
        import requests
        print("✅ Requests: Available")
    except ImportError:
        missing_deps.append("requests (REQUIRED)")
        print("❌ Requests: Missing (REQUIRED)")
        return False, websockets_available, mongodb_available, missing_deps
    
    # Check for flask
    try:
        import flask
        print("✅ Flask: Available")
    except ImportError:
        missing_deps.append("flask (REQUIRED)")
        print("❌ Flask: Missing (REQUIRED)")
        return False, websockets_available, mongodb_available, missing_deps
    
    return True, websockets_available, mongodb_available, missing_deps

def print_startup_info(websockets_available, mongodb_available):
    """Print startup information"""
    print("\n" + "="*60)
    print("🚀 GUST Bot Enhanced - Starting Up")
    print("="*60)
    print(f"🔧 WebSocket Support: {'Available' if websockets_available else 'Not Available'}")
    print(f"🗄️ MongoDB Support: {'Available' if mongodb_available else 'Not Available (using in-memory)'}")
    print(f"🌐 Live Console: {'Enabled' if websockets_available else 'Disabled'}")
    print(f"💾 Data Storage: {'MongoDB + In-Memory' if mongodb_available else 'In-Memory Only'}")
    print("="*60)
    if not websockets_available:
        print("💡 To enable live console: pip install websockets")
    if not mongodb_available:
        print("💡 To enable persistent storage: pip install pymongo")
    print("="*60 + "\n")

def main():
    """Main entry point for GUST Bot Enhanced"""
    
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Check dependencies
    print("[INFO] Checking dependencies...")
    deps_ok, websockets_available, mongodb_available, missing_deps = check_dependencies()
    
    if not deps_ok:
        print("\n❌ CRITICAL: Missing required dependencies!")
        for dep in missing_deps:
            print(f"   * {dep}")
        print("\n💡 Install missing dependencies with:")
        print("   pip install flask requests")
        if missing_deps:
            print("   pip install " + " ".join([dep.split()[0] for dep in missing_deps if 'REQUIRED' not in dep]))
        sys.exit(1)
    
    if missing_deps:
        print("\n⚠️ WARNING: Missing optional dependencies:")
        for dep in missing_deps:
            print(f"   * {dep}")
        print()
    
    # Print startup information
    print_startup_info(websockets_available, mongodb_available)
    
    # Import the main application
    try:
        print("[INFO] Loading GUST Bot Enhanced...")
        from app import GustBotEnhanced
        print("[✅ OK] GUST Bot Enhanced loaded successfully")
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        print(f"\n❌ Failed to import GUST Bot Enhanced:")
        print(f"   Error: {e}")
        print("\n📋 Troubleshooting steps:")
        print("   1. Make sure app.py exists in the current directory")
        print("   2. Check that all required modules are installed")
        print("   3. Verify the project structure is correct")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"\n❌ Unexpected error loading GUST Bot Enhanced:")
        print(f"   Error: {e}")
        sys.exit(1)
    
    # Create and run the enhanced GUST bot
    try:
        print("[INFO] Initializing GUST Bot Enhanced...")
        gust = GustBotEnhanced()
        print("[✅ OK] GUST Bot Enhanced initialized successfully")
        print("\n🚀 Starting web server...")
        gust.run()
        
    except KeyboardInterrupt:
        print("\n[EXIT] GUST Enhanced stopped by user")
        logger.info("Application stopped by user")
        
    except Exception as e:
        logger.error(f"❌ Runtime error: {e}")
        print(f"\n❌ Error running GUST Bot Enhanced:")
        print(f"   Error: {e}")
        
        # Provide helpful debugging info
        if "Address already in use" in str(e):
            print("\n🔧 Port 5000 is already in use. Try:")
            print("   1. Kill other Flask apps: pkill -f flask")
            print("   2. Use a different port in config.py")
        elif "Permission denied" in str(e):
            print("\n🔧 Permission denied. Try:")
            print("   1. Run with appropriate permissions")
            print("   2. Check file/directory permissions")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
