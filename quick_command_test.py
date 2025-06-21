#!/usr/bin/env python3
"""
Quick Command Test for GUST
===========================
Test if commands are working with your current valid token.
"""

import requests
import json

def test_current_functionality():
    """Test if commands work with current setup"""
    print("🧪 QUICK COMMAND TEST")
    print("=" * 30)
    
    # Check if GUST server is running
    try:
        health_response = requests.get("http://localhost:5000/api/token/status", timeout=5)
        if health_response.status_code == 200:
            data = health_response.json()
            print("✅ GUST server is running")
            print(f"📊 Demo Mode: {data.get('demo_mode', 'Unknown')}")
            print(f"📊 Has Token: {data.get('has_token', 'Unknown')}")
            print(f"📊 Token Valid: {data.get('token_valid', 'Unknown')}")
            
            if data.get('has_token') and data.get('token_valid'):
                print("✅ Valid token detected - should be in LIVE MODE")
            elif data.get('demo_mode'):
                print("🎭 Demo mode detected")
            else:
                print("❌ No valid authentication")
                return False
                
        else:
            print(f"❌ GUST server responded with status: {health_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ GUST server is not running!")
        print("💡 Start it with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False
    
    # Test sending a command
    print("\n📡 Testing command sending...")
    
    test_data = {
        "command": "serverinfo",
        "serverId": "1736296",  # From your logs
        "region": "US"
    }
    
    try:
        response = requests.post("http://localhost:5000/api/console/send", 
                               json=test_data,
                               timeout=15)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📝 Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("\n🎉 COMMAND SENT SUCCESSFULLY!")
                
                if result.get('demo_mode'):
                    print("🎭 Mode: Demo (simulated)")
                else:
                    print("🌐 Mode: Live (real G-Portal server)")
                
                return True
            else:
                print(f"\n❌ Command failed: {result.get('error', 'Unknown error')}")
                
                # Provide specific guidance based on error
                error = result.get('error', '').lower()
                if 'token' in error or 'auth' in error:
                    print("💡 Authentication issue - token may be expired")
                elif 'network' in error or 'connection' in error:
                    print("💡 Network issue - check internet connection")
                elif 'server' in error:
                    print("💡 Server configuration issue")
                
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Error: {error_data}")
            except:
                print(f"📝 Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Command test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 GUST QUICK COMMAND TEST")
    print("=" * 40)
    print("Testing current functionality with your valid token...\n")
    
    success = test_current_functionality()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 SUCCESS: Commands are working!")
        print("\n✅ Your GUST system is functional:")
        print("   - Authentication: Working")
        print("   - Command sending: Working") 
        print("   - Auto commands should be working too")
        
        print("\n🔍 To verify auto commands:")
        print("   1. Open browser: http://localhost:5000")
        print("   2. Go to Server Manager")
        print("   3. Watch player counts update every 10-30 seconds")
        
    else:
        print("❌ Commands are not working yet")
        print("\n🔧 Try these fixes:")
        print("   1. Run: python encoding_fix_script.py")
        print("   2. Restart GUST: python main.py") 
        print("   3. Re-test: python quick_command_test.py")
        
        print("\n🆘 If still failing:")
        print("   - Check GUST backend logs for GraphQL errors")
        print("   - Verify G-Portal server status")
        print("   - Check network connectivity to G-Portal API")

if __name__ == "__main__":
    main()
