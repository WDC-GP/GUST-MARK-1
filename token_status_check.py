#!/usr/bin/env python3
"""
Token Status Check - Quick diagnosis
"""

import os
import json
import time
from datetime import datetime

def check_current_session():
    """Check current login status and token"""
    print("🔍 CHECKING CURRENT SESSION STATUS...")
    
    # Check if token file exists
    if os.path.exists('gp-session.json'):
        try:
            with open('gp-session.json', 'r') as f:
                data = json.load(f)
            
            print(f"✅ Token file exists")
            print(f"📊 Username: {data.get('username', 'Unknown')}")
            
            # Check token details
            access_token = data.get('access_token', '')
            if access_token:
                print(f"🔑 Access token length: {len(access_token)}")
                print(f"🔑 Token starts with: {access_token[:20]}...")
                
                # Check if it looks like a real token
                if len(access_token) > 100 and access_token.replace('-', '').replace('_', '').isalnum():
                    print("✅ Token format looks valid")
                else:
                    print("❌ Token format looks invalid")
            else:
                print("❌ No access token found")
            
            # Check expiration
            exp_time = data.get('access_token_exp', 0)
            if exp_time:
                current_time = time.time()
                time_left = exp_time - current_time
                print(f"⏰ Token expires in: {time_left:.1f} seconds")
                
                if time_left > 0:
                    print("✅ Token is not expired")
                else:
                    print("❌ Token is EXPIRED")
            
        except Exception as e:
            print(f"❌ Error reading token file: {e}")
    else:
        print("❌ No token file found - likely in demo mode")

def test_load_token_function():
    """Test the load_token function directly"""
    print("\n🧪 TESTING load_token() FUNCTION...")
    
    try:
        from utils.helpers import load_token
        
        token = load_token()
        
        if token:
            print(f"✅ load_token() returned: {len(token)} characters")
            print(f"🔍 Token preview: {token[:20]}...")
            
            # Test validation that might be in logs.py
            if len(token) < 20:
                print("❌ Token too short - this triggers 'Invalid token format'")
            elif not token.replace('-', '').replace('_', '').isalnum():
                print("❌ Token contains invalid characters")
            else:
                print("✅ Token passes basic validation")
        else:
            print("❌ load_token() returned empty/None")
            print("   This would trigger 'Invalid authentication token'")
        
    except Exception as e:
        print(f"❌ Error testing load_token(): {e}")

def check_demo_vs_real_mode():
    """Check if we're in demo mode"""
    print("\n🎭 CHECKING DEMO VS REAL MODE...")
    
    # The logs show login was successful, so check what type
    if os.path.exists('gp-session.json'):
        print("✅ Token file exists - suggests real G-Portal login")
    else:
        print("⚠️ No token file - suggests demo mode login")
    
    print("\n💡 To verify your login mode:")
    print("   - Real G-Portal login: Creates gp-session.json with long token")
    print("   - Demo mode login: No token file, uses demo credentials")

def main():
    print("🔍 TOKEN STATUS DIAGNOSTIC")
    print("=" * 40)
    
    check_current_session()
    test_load_token_function()
    check_demo_vs_real_mode()
    
    print("\n🎯 NEXT STEPS:")
    print("1. If you see 'Token too short' or 'empty/None', you're likely in demo mode")
    print("2. Re-login with REAL G-Portal credentials (not demo/test/admin)")
    print("3. Verify the token file has a long access_token")

if __name__ == "__main__":
    main()
