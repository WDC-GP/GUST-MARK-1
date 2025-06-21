#!/usr/bin/env python3
"""
WebSocket Sensor System Test Script
==================================
Test script to verify WebSocket sensor functionality is working correctly
"""

import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_websocket_imports():
    """Test 1: Check if websockets package is installed"""
    print("🧪 Test 1: WebSocket Package Installation")
    print("-" * 50)
    
    try:
        import websockets
        print(f"✅ websockets package installed: {websockets.__version__}")
        return True
    except ImportError as e:
        print(f"❌ websockets package not installed: {e}")
        print("🔧 Fix: Run 'pip install websockets==11.0.3'")
        return False

def test_config_availability():
    """Test 2: Check if config detects websockets"""
    print("\n🧪 Test 2: Configuration Detection")
    print("-" * 50)
    
    try:
        from config import WEBSOCKETS_AVAILABLE
        if WEBSOCKETS_AVAILABLE:
            print("✅ Config correctly detects websockets as available")
            return True
        else:
            print("❌ Config shows websockets as unavailable")
            print("🔧 This usually means the websockets package isn't installed")
            return False
    except Exception as e:
        print(f"❌ Error importing config: {e}")
        return False

def test_websocket_package_imports():
    """Test 3: Check if WebSocket package imports work"""
    print("\n🧪 Test 3: WebSocket Package Imports")
    print("-" * 50)
    
    try:
        from websocket import get_websocket_status, check_websocket_support, check_sensor_support
        
        # Get status
        status = get_websocket_status()
        print(f"📊 WebSocket Status: {status}")
        
        if check_websocket_support():
            print("✅ WebSocket support is available")
        else:
            print("❌ WebSocket support is not available")
            
        if check_sensor_support():
            print("✅ Sensor support is available")
        else:
            print("❌ Sensor support is not available")
            
        return check_websocket_support() and check_sensor_support()
        
    except Exception as e:
        print(f"❌ Error importing websocket package: {e}")
        return False

def test_websocket_classes():
    """Test 4: Check if WebSocket classes can be imported"""
    print("\n🧪 Test 4: WebSocket Class Imports")
    print("-" * 50)
    
    try:
        from websocket import EnhancedWebSocketManager, GPortalWebSocketClient, WebSocketSensorBridge
        print("✅ EnhancedWebSocketManager imported successfully")
        print("✅ GPortalWebSocketClient imported successfully") 
        print("✅ WebSocketSensorBridge imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing WebSocket classes: {e}")
        return False

def test_app_integration():
    """Test 5: Check if app can initialize with WebSocket support"""
    print("\n🧪 Test 5: Application Integration")
    print("-" * 50)
    
    try:
        # Test import of main app components
        from config import WEBSOCKETS_AVAILABLE
        
        if WEBSOCKETS_AVAILABLE:
            from websocket.manager import EnhancedWebSocketManager
            print("✅ Can import EnhancedWebSocketManager from app context")
            
            # Test basic initialization
            class MockBot:
                pass
            
            mock_bot = MockBot()
            manager = EnhancedWebSocketManager(mock_bot)
            print("✅ EnhancedWebSocketManager initializes successfully")
            
            # Test sensor bridge initialization
            bridge = manager.initialize_sensor_bridge()
            if bridge:
                print("✅ Sensor bridge initializes successfully")
            else:
                print("⚠️ Sensor bridge initialization returned None")
            
            return True
        else:
            print("❌ WEBSOCKETS_AVAILABLE is False in app context")
            return False
            
    except Exception as e:
        print(f"❌ Error testing app integration: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def test_sensor_bridge_functionality():
    """Test 6: Check sensor bridge functionality"""
    print("\n🧪 Test 6: Sensor Bridge Functionality")
    print("-" * 50)
    
    try:
        from websocket.sensor_bridge import WebSocketSensorBridge
        
        # Create mock manager
        class MockManager:
            def get_connection(self, server_id):
                return None
        
        mock_manager = MockManager()
        bridge = WebSocketSensorBridge(mock_manager)
        
        print("✅ WebSocketSensorBridge creates successfully")
        
        # Test statistics method
        stats = bridge.get_sensor_statistics()
        print(f"✅ Sensor statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing sensor bridge: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 GUST WebSocket Sensor System Test Suite")
    print("=" * 60)
    
    tests = [
        ("WebSocket Package Installation", test_websocket_imports),
        ("Configuration Detection", test_config_availability), 
        ("WebSocket Package Imports", test_websocket_package_imports),
        ("WebSocket Class Imports", test_websocket_classes),
        ("Application Integration", test_app_integration),
        ("Sensor Bridge Functionality", test_sensor_bridge_functionality)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! WebSocket sensor system is ready!")
        print("🚀 You can now start the application with WebSocket sensor support")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed. WebSocket sensor system needs fixes.")
        print("\n🔧 QUICK FIXES:")
        print("1. Install websockets: pip install websockets==11.0.3")
        print("2. Replace your websocket/__init__.py with the fixed version")
        print("3. Restart your application")
    
    return passed == len(results)

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
