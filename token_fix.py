#!/usr/bin/env python3
"""
GUST Bot Enhanced - Token Fix Diagnostic Script
===============================================
Run this script to diagnose and fix the token refresh issues.
"""

import json
import os
import time
from datetime import datetime

def check_current_token_status():
    """Check the current state of the token file"""
    print("🔍 CHECKING CURRENT TOKEN STATUS")
    print("=" * 40)
    
    if not os.path.exists('gp-session.json'):
        print("❌ No token file found")
        print("   This means you need to login again")
        return False
    
    try:
        with open('gp-session.json', 'r') as f:
            data = json.load(f)
        
        current_time = time.time()
        
        # Check access token
        access_token = data.get('access_token', '')
        access_exp = data.get('access_token_exp', 0)
        
        print(f"✅ Token file exists")
        print(f"📊 Access token length: {len(access_token)}")
        
        if access_exp:
            access_time_left = access_exp - current_time
            access_expires_at = datetime.fromtimestamp(access_exp)
            print(f"⏰ Access token expires: {access_expires_at}")
            print(f"⏰ Time left: {access_time_left:.0f} seconds")
            
            if access_time_left <= 0:
                print("❌ Access token has EXPIRED")
            elif access_time_left <= 60:
                print("⚠️ Access token expires within 60 seconds")
            else:
                print("✅ Access token is still valid")
        
        # Check refresh token
        refresh_token = data.get('refresh_token', '')
        refresh_exp = data.get('refresh_token_exp', 0)
        
        print(f"📊 Refresh token length: {len(refresh_token)}")
        
        if refresh_exp:
            refresh_time_left = refresh_exp - current_time
            refresh_expires_at = datetime.fromtimestamp(refresh_exp)
            print(f"⏰ Refresh token expires: {refresh_expires_at}")
            print(f"⏰ Refresh time left: {refresh_time_left:.0f} seconds")
            
            if refresh_time_left <= 0:
                print("❌ Refresh token has EXPIRED - LOGIN REQUIRED")
                return False
            elif refresh_time_left <= 300:  # 5 minutes
                print("⚠️ Refresh token expires very soon")
            else:
                print("✅ Refresh token is still valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading token file: {e}")
        return False

def check_buffer_time_in_code():
    """Check what buffer time is currently set in the code"""
    print("\n🔧 CHECKING BUFFER TIME IN CODE")
    print("=" * 40)
    
    if os.path.exists('utils/helpers.py'):
        try:
            with open('utils/helpers.py', 'r') as f:
                content = f.read()
            
            # Look for buffer_time assignments
            import re
            buffer_matches = re.findall(r'buffer_time\s*=\s*(\d+)', content)
            
            if buffer_matches:
                for i, match in enumerate(buffer_matches):
                    print(f"📝 Found buffer_time = {match} seconds (occurrence {i+1})")
                
                # Check if we have the problematic 180 seconds
                if '180' in buffer_matches:
                    print("❌ FOUND PROBLEM: Buffer time is set to 180 seconds")
                    print("   This is TOO LONG for G-Portal tokens!")
                    print("   Need to change to 60 seconds or less")
                    return False
                elif '60' in buffer_matches or any(int(x) <= 60 for x in buffer_matches):
                    print("✅ Buffer time appears to be correctly set")
                    return True
            else:
                print("⚠️ Could not find buffer_time setting in code")
                return False
                
        except Exception as e:
            print(f"❌ Error reading helpers.py: {e}")
            return False
    else:
        print("❌ utils/helpers.py not found")
        return False

def provide_immediate_fix():
    """Provide immediate steps to fix the issue"""
    print("\n🚨 IMMEDIATE FIX STEPS")
    print("=" * 40)
    
    print("1. 🛑 STOP the application (Ctrl+C)")
    print("2. 🗑️ DELETE the token file:")
    print("   del gp-session.json   (Windows)")
    print("   rm gp-session.json    (Linux/Mac)")
    print("")
    print("3. 📝 EDIT utils/helpers.py:")
    print("   Find the line: buffer_time = 180")
    print("   Change it to: buffer_time = 60")
    print("")
    print("4. 🚀 RESTART the application:")
    print("   python main.py")
    print("")
    print("5. 🔐 LOGIN AGAIN with your G-Portal credentials")
    print("   (Not demo mode - use real G-Portal username/password)")
    print("")
    print("6. ✅ Test functionality immediately after login")

def advanced_diagnosis():
    """Provide advanced diagnosis for persistent issues"""
    print("\n🔬 ADVANCED DIAGNOSIS")
    print("=" * 40)
    
    print("If the problem persists after the immediate fix:")
    print("")
    print("Issue A: G-Portal tokens expire faster than expected")
    print("   • G-Portal refresh tokens may only last 2-3 minutes")
    print("   • Need even more aggressive refresh (30-45 second buffer)")
    print("")
    print("Issue B: G-Portal API endpoint changes")
    print("   • G-Portal may have changed their OAuth endpoints")
    print("   • Need to verify correct API URLs")
    print("")
    print("Issue C: Account-specific token limitations")
    print("   • Some G-Portal accounts have shorter token lifespans")
    print("   • Check G-Portal account settings")
    print("")
    print("🔍 To debug further:")
    print("   1. Enable debug logging in config.py")
    print("   2. Monitor exact token expiration times")
    print("   3. Test with different G-Portal accounts")

def main():
    """Main diagnostic function"""
    print("🚨 GUST BOT ENHANCED - TOKEN DIAGNOSTIC")
    print("=" * 50)
    
    token_ok = check_current_token_status()
    code_ok = check_buffer_time_in_code()
    
    if not token_ok:
        print("\n❌ TOKEN ISSUE DETECTED")
        print("The tokens are expired or invalid")
    
    if not code_ok:
        print("\n❌ CODE ISSUE DETECTED") 
        print("Buffer time is set incorrectly")
    
    if not token_ok or not code_ok:
        provide_immediate_fix()
    else:
        print("\n✅ TOKENS AND CODE APPEAR OK")
        print("The issue might be network-related or G-Portal API changes")
        advanced_diagnosis()

if __name__ == "__main__":
    main()