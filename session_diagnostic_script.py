#!/usr/bin/env python3
"""
GUST Session Diagnostic Script
=============================
This will identify the exact session management issue.
"""

import requests
import json
import time

def test_session_flow():
    """Test the complete session flow to identify the break point"""
    print("🔍 GUST SESSION DIAGNOSTIC")
    print("=" * 50)
    
    session = requests.Session()  # Maintain cookies across requests
    
    # Step 1: Test if GUST server is responding
    print("\n1️⃣ Testing GUST server connectivity...")
    try:
        response = session.get('http://localhost:5000', timeout=5)
        print(f"✅ Server responding: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        print(f"🍪 Initial cookies: {response.cookies}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Step 2: Test login endpoint (without actual login)
    print("\n2️⃣ Testing login endpoint accessibility...")
    try:
        response = session.get('http://localhost:5000/login', timeout=5)
        print(f"✅ Login page accessible: {response.status_code}")
        print(f"🍪 Login page cookies: {response.cookies}")
    except Exception as e:
        print(f"❌ Login page error: {e}")
        return False
    
    # Step 3: Test API endpoint (should fail with 401)
    print("\n3️⃣ Testing API endpoint without authentication...")
    try:
        response = session.get('http://localhost:5000/api/token/status', timeout=5)
        print(f"📊 API status (expected 401): {response.status_code}")
        print(f"📝 API response: {response.text}")
        print(f"🍪 API cookies: {response.cookies}")
        
        if response.status_code == 401:
            print("✅ Expected 401 - authentication is being checked")
        else:
            print("⚠️ Unexpected response - auth might be bypassed")
            
    except Exception as e:
        print(f"❌ API endpoint error: {e}")
        return False
    
    # Step 4: Try to login (this will test if session setting works)
    print("\n4️⃣ Testing login process...")
    
    # First, get any CSRF tokens or session setup
    login_page = session.get('http://localhost:5000/login')
    print(f"📊 Login page setup: {login_page.status_code}")
    
    # Try demo login first (simpler)
    login_data = {
        'username': 'admin',
        'password': 'password'
    }
    
    try:
        response = session.post(
            'http://localhost:5000/login',
            json=login_data,
            timeout=10
        )
        
        print(f"📊 Login attempt result: {response.status_code}")
        print(f"🍪 Post-login cookies: {response.cookies}")
        
        if response.status_code == 200:
            try:
                login_result = response.json()
                print(f"📝 Login response: {login_result}")
                
                if login_result.get('success'):
                    print("✅ Login reported success")
                    
                    # Test API access after login
                    print("\n5️⃣ Testing API access after login...")
                    api_response = session.get('http://localhost:5000/api/token/status')
                    print(f"📊 Post-login API status: {api_response.status_code}")
                    
                    if api_response.status_code == 200:
                        print("✅ API access working after login!")
                        api_data = api_response.json()
                        print(f"📝 API data: {api_data}")
                        return True
                    else:
                        print(f"❌ API still failing after login: {api_response.status_code}")
                        print(f"📝 API error: {api_response.text}")
                        return False
                else:
                    print(f"❌ Login failed: {login_result.get('error', 'Unknown error')}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"❌ Login response not JSON: {response.text}")
                return False
        else:
            print(f"❌ Login HTTP error: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login process error: {e}")
        return False

def test_direct_file_access():
    """Test if we can access session files directly"""
    print("\n📁 TESTING DIRECT FILE ACCESS")
    print("=" * 40)
    
    import os
    
    # Check session file
    if os.path.exists('gp-session.json'):
        try:
            with open('gp-session.json', 'r') as f:
                session_data = json.load(f)
            print("✅ Session file accessible")
            print(f"📊 Token length: {len(session_data.get('access_token', ''))}")
            print(f"📊 Has refresh token: {'refresh_token' in session_data}")
        except Exception as e:
            print(f"❌ Session file error: {e}")
    else:
        print("❌ No session file found")
    
    # Check Flask session configuration
    print("\n⚙️ Checking Flask session configuration...")
    try:
        # Try to import and check config
        import sys
        import os
        
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        try:
            from config import Config
            print("✅ Config importable")
            
            # Check for session-related settings
            config_attrs = dir(Config)
            session_attrs = [attr for attr in config_attrs if 'SESSION' in attr or 'SECRET' in attr]
            
            if session_attrs:
                print(f"📊 Session config found: {session_attrs}")
                for attr in session_attrs:
                    value = getattr(Config, attr, 'Not set')
                    if 'SECRET' in attr and value != 'Not set':
                        print(f"   {attr}: [HIDDEN]")
                    else:
                        print(f"   {attr}: {value}")
            else:
                print("⚠️ No session configuration found in Config")
                
        except ImportError as e:
            print(f"❌ Config import error: {e}")
            
    except Exception as e:
        print(f"❌ Config check error: {e}")

def provide_diagnosis():
    """Provide diagnosis based on test results"""
    print("\n🎯 DIAGNOSIS AND NEXT STEPS")
    print("=" * 50)
    
    print("Based on the test results above:")
    print()
    
    print("✅ If login succeeded AND API access worked:")
    print("   → Your system is actually working!")
    print("   → The browser issue might be CORS or JavaScript related")
    print("   → Try refreshing your browser page")
    print()
    
    print("❌ If login succeeded but API access failed:")
    print("   → Session cookies are not being maintained")
    print("   → Fix: Flask session configuration issue")
    print("   → Action: Check SECRET_KEY and session settings")
    print()
    
    print("❌ If login failed:")
    print("   → Authentication endpoint has issues")
    print("   → Fix: Check authentication route implementation")
    print("   → Action: Review routes/auth.py")
    print()
    
    print("❌ If server connection failed:")
    print("   → GUST server is not running properly")
    print("   → Fix: Restart with python main.py")
    print("   → Action: Check console for startup errors")

def main():
    """Main diagnostic function"""
    print("🚀 GUST SESSION DIAGNOSTIC TOOL")
    print("=" * 60)
    print("This will identify why commands are not working.")
    print("Make sure GUST is running on localhost:5000")
    print()
    
    # Run session flow test
    session_success = test_session_flow()
    
    # Check file access
    test_direct_file_access()
    
    # Provide diagnosis
    provide_diagnosis()
    
    print("\n" + "=" * 60)
    if session_success:
        print("🎉 SESSION DIAGNOSTIC: SUCCESS!")
        print("Your authentication system is working.")
        print("The issue might be browser-specific.")
        print()
        print("Next steps:")
        print("1. Refresh your browser page")
        print("2. Clear browser cache/cookies")
        print("3. Try commands again in browser")
    else:
        print("🔧 SESSION DIAGNOSTIC: ISSUES FOUND")
        print("Authentication system needs fixing.")
        print()
        print("Priority fixes:")
        print("1. Fix Flask session configuration")
        print("2. Check authentication decorator")
        print("3. Verify session persistence")

if __name__ == "__main__":
    main()
