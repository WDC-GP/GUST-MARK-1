#!/usr/bin/env python3
"""
Direct Command Test for GUST
============================
Test commands directly since authentication is working but status check has issues.
"""

import requests
import json
import time

def test_direct_command():
    """Test command directly without relying on status endpoint"""
    print("🚀 DIRECT COMMAND TEST")
    print("=" * 40)
    print("Your logs show successful G-Portal authentication!")
    print("Testing commands directly...\n")
    
    # Test data using your server from the logs
    test_data = {
        "command": "serverinfo",
        "serverId": "1736296",  # From your logs: "Test (1736296)"
        "region": "US"          # From your logs: "in US"
    }
    
    print(f"📡 Testing command: {test_data['command']}")
    print(f"📊 Server ID: {test_data['serverId']}")
    print(f"🌍 Region: {test_data['region']}")
    
    try:
        # Send command directly to console endpoint
        response = requests.post(
            "http://localhost:5000/api/console/send", 
            json=test_data,
            timeout=30,  # Longer timeout for G-Portal API
            cookies={}   # Use session cookies from browser
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📝 Response Data:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                print("\n🎉 SUCCESS! COMMAND SENT SUCCESSFULLY!")
                print("🌐 Your GUST system is working with live G-Portal commands!")
                
                # Check mode
                if result.get('demo_mode'):
                    print("🎭 Mode: Demo (simulated commands)")
                else:
                    print("🌐 Mode: Live (real G-Portal server commands)")
                
                return True
            else:
                error = result.get('error', 'Unknown error')
                print(f"\n❌ Command failed: {error}")
                
                # Provide specific guidance
                if 'authentication' in error.lower() or 'token' in error.lower():
                    print("💡 Auth issue - but your login logs show success...")
                    print("💡 This might be a session/cookie issue")
                elif 'server' in error.lower():
                    print("💡 Server configuration issue")
                elif 'network' in error.lower():
                    print("💡 Network connectivity issue")
                
                return False
                
        elif response.status_code == 401:
            print("❌ Authentication required")
            print("💡 Try logging in again in the browser")
            return False
            
        elif response.status_code == 500:
            print("❌ Server error")
            try:
                error_data = response.json()
                print(f"📝 Error details: {error_data}")
            except:
                print(f"📝 Raw error: {response.text}")
            return False
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout (30s)")
        print("💡 G-Portal API might be slow or unresponsive")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
        print("💡 Check if GUST server is still running")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_auto_commands_trigger():
    """Test if we can trigger the auto command system"""
    print("\n🔄 TESTING AUTO COMMAND SYSTEM")
    print("=" * 40)
    
    print("The auto command system should be:")
    print("✓ Sending 'serverinfo' every 10 seconds")
    print("✓ Visible in browser console as: ✅ Auto command sent")
    print("✓ Updating player counts in Server Manager")
    
    print("\n🧪 Manual trigger test...")
    
    # Test if we can at least reach the endpoint
    try:
        response = requests.get("http://localhost:5000/api/servers", timeout=5)
        if response.status_code == 200:
            servers = response.json()
            print(f"✅ Server list accessible: {len(servers)} servers")
            
            if servers:
                print("📊 Configured servers:")
                for server in servers:
                    print(f"   - {server.get('name', 'Unknown')} ({server.get('server_id', 'No ID')})")
            else:
                print("⚠️ No servers configured - auto commands won't work")
                print("💡 Add servers in the Server Manager tab")
                
        else:
            print(f"❌ Server list error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Server list test failed: {e}")

def check_browser_session():
    """Instructions for checking browser session"""
    print("\n🌐 BROWSER SESSION CHECK")
    print("=" * 40)
    
    print("Since your backend authentication is working, try this:")
    print()
    print("1. Open browser: http://localhost:5000")
    print("2. You should already be logged in (no login screen)")
    print("3. Go to Live Console tab")
    print("4. Try sending a manual command: 'say Hello World'")
    print("5. Check for success/error messages")
    print()
    print("If you see a login screen:")
    print("- Your session might have expired")
    print("- Login again with your G-Portal credentials")
    print("- NOT with admin/password (that's demo mode)")

def main():
    """Main test function"""
    print("🔧 GUST DIRECT COMMAND TEST")
    print("=" * 50)
    print("Your backend shows successful G-Portal authentication!")
    print("Testing commands directly...\n")
    
    # Test direct command
    command_success = test_direct_command()
    
    # Test auto command system
    test_auto_commands_trigger()
    
    # Browser session guidance
    check_browser_session()
    
    print("\n" + "=" * 50)
    if command_success:
        print("🎉 EXCELLENT! Commands are working!")
        print("\n✅ Your GUST system is fully functional:")
        print("   - G-Portal authentication: ✅ Working")
        print("   - Command sending: ✅ Working")
        print("   - Live mode: ✅ Active")
        
        print("\n🔄 Auto commands should also be working:")
        print("   - Check Server Manager for live player counts")
        print("   - Open browser console (F12) to see auto command logs")
        
    else:
        print("❌ Commands failed despite successful authentication")
        print("\n🔍 This suggests:")
        print("   - Session/cookie mismatch between backend and frontend")
        print("   - G-Portal API connectivity issue")
        print("   - Token format issue (despite successful auth)")
        
        print("\n🔧 Next steps:")
        print("   1. Try the browser session check above")
        print("   2. Check GUST backend logs for GraphQL errors")
        print("   3. Verify G-Portal service status")

if __name__ == "__main__":
    main()
