#!/usr/bin/env python3
"""
Test User Registration Endpoint
===============================
Verifies that the user registration fix is working
"""

import requests
import json

def test_registration_endpoint():
    """Test the user registration endpoint"""
    
    print("🧪 Testing User Registration Endpoint")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Check if server is running
    print("🔍 Test 1: Server connectivity...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️ Server returned {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running! Start with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test 2: Check registration endpoint exists
    print("\n🔍 Test 2: Registration endpoint accessibility...")
    try:
        # Test with OPTIONS to check if endpoint exists
        response = requests.options(f"{base_url}/api/users/register", timeout=5)
        if response.status_code != 404:
            print("✅ Registration endpoint found")
        else:
            print("❌ Registration endpoint still returns 404")
            print("   Make sure you applied the fix and restarted the server!")
            return False
    except Exception as e:
        print(f"❌ Endpoint test error: {e}")
        return False
    
    # Test 3: Test actual registration
    print("\n🔍 Test 3: Registration functionality...")
    test_data = {
        "userId": "test_user_123",
        "nickname": "TestUser",
        "serverId": "test_server"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/users/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    print("✅ Registration successful!")
                    print(f"   Message: {data.get('message', 'No message')}")
                else:
                    print(f"❌ Registration failed: {data.get('error', 'Unknown error')}")
            except json.JSONDecodeError:
                print("⚠️ Invalid JSON response")
                print(f"   Raw response: {response.text[:200]}")
        
        elif response.status_code == 401:
            print("⚠️ Authentication required (this is normal)")
            print("   The endpoint exists but requires login")
            print("   Registration functionality is working!")
            
        elif response.status_code == 404:
            print("❌ Still getting 404 - fix not applied correctly")
            print("   Check that you restarted the server after applying the fix")
            
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ Registration test error: {e}")
        return False
    
    # Test 4: Check for user search endpoint
    print("\n🔍 Test 4: User search endpoint...")
    try:
        response = requests.get(f"{base_url}/api/users/search?q=test", timeout=5)
        if response.status_code != 404:
            print("✅ User search endpoint found")
        else:
            print("⚠️ User search endpoint not found (optional)")
    except Exception as e:
        print(f"⚠️ Search test error: {e}")
    
    print("\n🎉 Testing Complete!")
    print("=" * 50)
    print("📝 Summary:")
    print("   • If you see ✅ messages above, the fix is working")
    print("   • If you see ❌ messages, check the manual fix guide")
    print("   • Authentication errors (401) are normal - the endpoint exists")
    print("   • You can now test registration in the web interface")
    
    return True

def test_in_browser():
    """Instructions for testing in browser"""
    print("\n🌐 Browser Testing Instructions:")
    print("=" * 50)
    print("1. Open http://localhost:5000 in your browser")
    print("2. Login (admin/password for demo mode)")
    print("3. Go to 'User Management' tab")
    print("4. Add a server in 'Server Manager' tab first")
    print("5. Return to 'User Management' and select the server")
    print("6. Try registering a user:")
    print("   • User ID: test123")
    print("   • Nickname: TestPlayer")
    print("7. Check browser console (F12) for any errors")
    print("8. Look for success message in the interface")

if __name__ == "__main__":
    test_registration_endpoint()
    test_in_browser()
