#!/usr/bin/env python3
"""
Fixed Diagnostic Script - Handles encoding issues
================================================
"""

import os
import json
import time
from datetime import datetime

def safe_read_file(filepath):
    """Safely read file with different encodings"""
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"❌ Error reading {filepath} with {encoding}: {e}")
            continue
    
    print(f"❌ Could not read {filepath} with any encoding")
    return None

def check_files_for_fixes():
    """Check if the fixed files are in place"""
    print("🔍 CHECKING IF FIXED FILES ARE IN PLACE...")
    
    files_to_check = {
        'utils/helpers.py': [
            ('buffer_time = 180', '180-second buffer fix'),
            ('COMPREHENSIVE FIX', 'Comprehensive fix markers'),
            ('def refresh_token():', 'Enhanced refresh function')
        ],
        'routes/logs.py': [
            ('return False', 'PROBLEMATIC fallback (should NOT be found)'),
            ('COMPREHENSIVE AUTHENTICATION FIX', 'Authentication fix markers'),
            ('from utils.helpers import load_token, refresh_token', 'Proper imports')
        ],
        'app.py': [
            ('centralized token management', 'Centralized auth'),
            ('COMPREHENSIVE FIX', 'Comprehensive fixes')
        ]
    }
    
    for filepath, checks in files_to_check.items():
        print(f"\n📄 Checking {filepath}:")
        
        if not os.path.exists(filepath):
            print(f"   ❌ File not found")
            continue
        
        content = safe_read_file(filepath)
        if not content:
            continue
        
        for check_text, description in checks:
            if check_text in content:
                if 'return False' in check_text and filepath == 'routes/logs.py':
                    # Special case - this should NOT be found
                    print(f"   ❌ FOUND: {description} - THIS IS THE PROBLEM!")
                else:
                    print(f"   ✅ FOUND: {description}")
            else:
                if 'return False' in check_text:
                    print(f"   ✅ NOT FOUND: {description} - Good!")
                else:
                    print(f"   ❌ NOT FOUND: {description}")

def test_refresh_token_manually():
    """Test refresh token manually"""
    print("\n🔧 TESTING MANUAL TOKEN REFRESH...")
    
    try:
        import sys
        sys.path.insert(0, os.getcwd())
        
        # Try to manually refresh the token
        print("📥 Attempting to import refresh_token function...")
        from utils.helpers import refresh_token
        print("✅ Successfully imported refresh_token")
        
        print("🔄 Attempting manual token refresh...")
        result = refresh_token()
        
        if result:
            print("✅ Manual token refresh SUCCESSFUL!")
            
            # Check if token file was updated
            if os.path.exists('gp-session.json'):
                with open('gp-session.json', 'r') as f:
                    data = json.load(f)
                
                current_time = time.time()
                exp_time = data.get('access_token_exp', 0)
                time_left = exp_time - current_time
                
                print(f"📊 New token expires in: {time_left:.1f} seconds")
                
                if time_left > 0:
                    print("✅ Token refresh fixed the expiration!")
                else:
                    print("❌ Token is still expired after refresh")
        else:
            print("❌ Manual token refresh FAILED")
            print("   This confirms the refresh function is not working properly")
        
    except ImportError as e:
        print(f"❌ Cannot import refresh_token: {e}")
    except Exception as e:
        print(f"❌ Error during manual refresh: {e}")

def check_token_file_details():
    """Check token file in detail"""
    print("🔍 DETAILED TOKEN ANALYSIS...")
    
    if not os.path.exists('gp-session.json'):
        print("❌ No token file")
        return
    
    try:
        with open('gp-session.json', 'r') as f:
            data = json.load(f)
        
        current_time = time.time()
        
        # Access token details
        access_exp = data.get('access_token_exp', 0)
        access_time_left = access_exp - current_time
        
        # Refresh token details  
        refresh_exp = data.get('refresh_token_exp', 0)
        refresh_time_left = refresh_exp - current_time
        
        print(f"📊 Current time: {datetime.fromtimestamp(current_time)}")
        print(f"📊 Access token expires: {datetime.fromtimestamp(access_exp)}")
        print(f"📊 Access token time left: {access_time_left:.1f} seconds")
        print(f"📊 Refresh token expires: {datetime.fromtimestamp(refresh_exp)}")
        print(f"📊 Refresh token time left: {refresh_time_left:.1f} seconds")
        
        # Check if tokens are valid
        if access_time_left <= 0:
            print("❌ Access token is EXPIRED")
            if refresh_time_left > 0:
                print("✅ Refresh token is still valid - should be able to refresh")
                print("🔧 The refresh mechanism is not working properly")
            else:
                print("❌ Refresh token is also EXPIRED - need to re-login")
        else:
            print("✅ Access token is still valid")
        
    except Exception as e:
        print(f"❌ Error analyzing token file: {e}")

def provide_solution():
    """Provide specific solution based on findings"""
    print("\n🎯 SOLUTION:")
    print("=" * 40)
    
    # Check if problematic logs.py exists
    logs_content = safe_read_file('routes/logs.py')
    if logs_content and 'return False' in logs_content:
        print("🚨 MAIN ISSUE FOUND:")
        print("   Your routes/logs.py file contains the problematic fallback:")
        print("   def refresh_token():")
        print("       return False")
        print("")
        print("💡 IMMEDIATE FIX:")
        print("   1. Replace routes/logs.py with the fixed version I provided")
        print("   2. Replace utils/helpers.py with the fixed version")
        print("   3. Replace app.py with the fixed version")
        print("   4. Delete gp-session.json")
        print("   5. Restart the application")
        print("   6. Re-login with G-Portal credentials")
    else:
        print("🔍 FILES APPEAR TO BE UPDATED")
        print("   The authentication issue may be due to:")
        print("   1. Expired tokens that can't refresh")
        print("   2. G-Portal API issues")
        print("   3. Network connectivity problems")
        print("")
        print("💡 TRY THESE STEPS:")
        print("   1. Delete gp-session.json (force fresh login)")
        print("   2. Restart the application")
        print("   3. Login again with G-Portal credentials")
        print("   4. Test manual refresh with the script above")

def main():
    """Run enhanced diagnostics"""
    print("🚨 ENHANCED AUTHENTICATION DIAGNOSTIC")
    print("=" * 50)
    
    check_token_file_details()
    check_files_for_fixes()
    test_refresh_token_manually()
    provide_solution()

if __name__ == "__main__":
    main()
