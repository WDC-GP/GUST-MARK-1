#!/usr/bin/env python3
"""
GUST Authentication Diagnostic Tool
==================================
This script will help diagnose authentication issues and fix command sending problems.
"""

import os
import json
import sys
from datetime import datetime

def check_session_file():
    """Check if G-Portal session file exists and is valid"""
    print("🔍 CHECKING AUTHENTICATION STATE...")
    print("=" * 50)
    
    session_file = "gp-session.json"
    
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            print(f"✅ Session file found: {session_file}")
            
            # Check for access token
            if 'access_token' in session_data:
                token = session_data['access_token']
                print(f"✅ Access token found (length: {len(token)})")
                
                if len(token) > 100:
                    print("✅ Token appears to be valid G-Portal token")
                    return "LIVE_MODE"
                else:
                    print("❌ Token too short - invalid G-Portal token")
                    return "INVALID_TOKEN"
            else:
                print("❌ No access_token in session file")
                return "INVALID_SESSION"
                
        except json.JSONDecodeError:
            print("❌ Session file corrupted (invalid JSON)")
            return "CORRUPTED_SESSION"
        except Exception as e:
            print(f"❌ Error reading session file: {e}")
            return "READ_ERROR"
    else:
        print("⚠️ No session file found - likely demo mode")
        return "DEMO_MODE"

def check_current_login_state():
    """Check what the current login state should be"""
    print("\n🎭 DETERMINING CORRECT MODE...")
    print("=" * 50)
    
    auth_state = check_session_file()
    
    if auth_state == "LIVE_MODE":
        print("🌐 You should be in LIVE MODE with real G-Portal commands")
        print("   - Commands sent to actual servers")
        print("   - Real player counts from G-Portal API")
        print("   - WebSocket connections to G-Portal")
        
    elif auth_state == "DEMO_MODE":
        print("🎭 You should be in DEMO MODE with simulated commands") 
        print("   - Commands simulated locally")
        print("   - Mock player counts")
        print("   - No external API calls")
        
    else:
        print(f"❌ INVALID STATE: {auth_state}")
        print("   - Commands will fail")
        print("   - Authentication required")
        print("   - Need to re-login")
    
    return auth_state

def provide_fix_instructions(auth_state):
    """Provide specific fix instructions based on the authentication state"""
    print("\n🔧 FIX INSTRUCTIONS...")
    print("=" * 50)
    
    if auth_state == "LIVE_MODE":
        print("Your authentication looks correct. If commands still aren't working:")
        print("\n1. Check network connectivity:")
        print("   curl -I https://api.g-portal.com")
        print("\n2. Verify server configuration:")
        print("   - Go to Server Manager in GUST")
        print("   - Ensure servers are properly configured") 
        print("   - Check server IDs and regions are correct")
        print("\n3. Check G-Portal API status:")
        print("   - Visit https://www.g-portal.com")
        print("   - Ensure your account has server access")
        
    elif auth_state in ["DEMO_MODE", "INVALID_TOKEN", "INVALID_SESSION", "CORRUPTED_SESSION"]:
        print("🚨 AUTHENTICATION ISSUE DETECTED")
        print("\nFIX STEPS:")
        print("1. Clean up authentication:")
        if os.path.exists("gp-session.json"):
            print(f"   rm gp-session.json  # Remove invalid session")
        
        print("\n2. Re-login with proper credentials:")
        print("   - Open GUST in browser: http://localhost:5000")
        print("   - Click logout if already logged in")
        print("   - Login with REAL G-Portal credentials:")
        print("     Username: your-gportal-email@domain.com")
        print("     Password: your-actual-gportal-password")
        print("   - Do NOT use: admin/password (that's demo mode)")
        
        print("\n3. Verify successful login:")
        print("   - Check that session file is created")
        print("   - Look for long access_token in session")
        print("   - Console should show 'Live mode' not 'Demo mode'")
        
    print(f"\n📋 Current timestamp: {datetime.now().isoformat()}")

def check_command_flow():
    """Check the command execution flow"""
    print("\n🔄 COMMAND EXECUTION FLOW...")
    print("=" * 50)
    
    print("Normal command flow should be:")
    print("1. Auto commands (every 10s) → frontend")
    print("2. Frontend → /api/console/send")
    print("3. Backend → G-Portal GraphQL API")
    print("4. G-Portal → Execute on game server")
    print("5. Response → Backend → Frontend")
    
    print("\nIf commands are failing, check:")
    print("✓ Step 2-3: Backend logs for GraphQL errors")
    print("✓ Step 3-4: Network connectivity to G-Portal")
    print("✓ Step 4: G-Portal server status and permissions")

def main():
    print("🚀 GUST AUTHENTICATION DIAGNOSTIC")
    print("=" * 50)
    print("This tool will help diagnose why commands aren't being sent.\n")
    
    # Check authentication state
    auth_state = check_current_login_state()
    
    # Provide fix instructions
    provide_fix_instructions(auth_state)
    
    # Check command flow
    check_command_flow()
    
    print("\n" + "=" * 50)
    print("💡 TIP: Run this script after making changes to verify fixes")
    print("📧 If issues persist, check the backend Python logs for GraphQL errors")

if __name__ == "__main__":
    main()
