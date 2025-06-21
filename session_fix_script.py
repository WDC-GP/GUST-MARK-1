#!/usr/bin/env python3
"""
GUST Session Configuration Fix
=============================
This will fix common Flask session configuration issues.
"""

import os
import re
import shutil
from datetime import datetime

def backup_files():
    """Create backup of files we'll modify"""
    print("📦 Creating backup...")
    
    backup_dir = f"session_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = ["config.py", "app.py", "main.py"]
    
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"✅ Backed up: {file}")
    
    return backup_dir

def check_config_file():
    """Check and fix config.py session settings"""
    print("\n⚙️ Checking config.py...")
    
    if not os.path.exists('config.py'):
        print("❌ config.py not found")
        return False
    
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading config.py: {e}")
        return False
    
    # Check for SECRET_KEY
    if 'SECRET_KEY' not in content:
        print("❌ No SECRET_KEY found - adding one")
        secret_key_line = "\n# Session configuration\nSECRET_KEY = 'gust-secret-key-change-in-production'\n"
        content = content + secret_key_line
        
    # Check for session settings
    session_settings = [
        "SESSION_COOKIE_SECURE = False",
        "SESSION_COOKIE_HTTPONLY = True", 
        "SESSION_COOKIE_SAMESITE = 'Lax'",
        "PERMANENT_SESSION_LIFETIME = 3600"
    ]
    
    missing_settings = []
    for setting in session_settings:
        setting_name = setting.split('=')[0].strip()
        if setting_name not in content:
            missing_settings.append(setting)
    
    if missing_settings:
        print(f"❌ Missing session settings: {len(missing_settings)}")
        session_block = "\n# Flask session configuration\n" + "\n".join(missing_settings) + "\n"
        content = content + session_block
        
    # Write the updated config
    try:
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ config.py updated with session settings")
        return True
    except Exception as e:
        print(f"❌ Error writing config.py: {e}")
        return False

def check_app_session_config():
    """Check Flask app session configuration"""
    print("\n🔧 Checking Flask app session configuration...")
    
    app_files = ['app.py', 'main.py']
    
    for app_file in app_files:
        if not os.path.exists(app_file):
            continue
            
        print(f"📄 Checking {app_file}...")
        
        try:
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {app_file}: {e}")
            continue
        
        # Check if session config is applied to app
        if 'app.config.update' not in content and 'app.config[' not in content:
            print(f"⚠️ {app_file} might not be applying session config")
            
            # Look for Flask app creation
            if 'Flask(__name__)' in content or 'app = Flask' in content:
                print(f"✅ Found Flask app in {app_file}")
                
                # Add session configuration after app creation
                session_config = '''
# Configure Flask session settings
app.config.update(
    SECRET_KEY=Config.SECRET_KEY if hasattr(Config, 'SECRET_KEY') else 'gust-secret-key',
    SESSION_COOKIE_SECURE=getattr(Config, 'SESSION_COOKIE_SECURE', False),
    SESSION_COOKIE_HTTPONLY=getattr(Config, 'SESSION_COOKIE_HTTPONLY', True),
    SESSION_COOKIE_SAMESITE=getattr(Config, 'SESSION_COOKIE_SAMESITE', 'Lax'),
    PERMANENT_SESSION_LIFETIME=getattr(Config, 'PERMANENT_SESSION_LIFETIME', 3600)
)
'''
                
                # Find a good place to insert this
                if 'def __init__' in content:
                    # Inside a class - add after app creation
                    pattern = r'(self\.app = Flask\(__name__\).*?)\n'
                    replacement = r'\1\n' + session_config
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                else:
                    # Simple script - add after app creation
                    pattern = r'(app = Flask\(__name__\).*?)\n'
                    replacement = r'\1\n' + session_config
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                
                # Write the updated file
                try:
                    with open(app_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Added session config to {app_file}")
                except Exception as e:
                    print(f"❌ Error writing {app_file}: {e}")

def check_auth_decorator():
    """Check authentication decorator implementation"""
    print("\n🔐 Checking authentication decorator...")
    
    auth_files = ['utils/auth_decorators.py', 'routes/auth.py']
    
    for auth_file in auth_files:
        if not os.path.exists(auth_file):
            continue
            
        print(f"📄 Checking {auth_file}...")
        
        try:
            with open(auth_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {auth_file}: {e}")
            continue
        
        # Check for require_auth function
        if 'def require_auth' in content:
            print(f"✅ Found require_auth in {auth_file}")
            
            # Check if it properly checks session
            if "'logged_in' not in session" in content:
                print("✅ Checks for 'logged_in' in session")
            else:
                print("⚠️ Might not be checking session properly")
                
            # Check for debug logging
            if 'print(' not in content and 'logger.' not in content:
                print("⚠️ No debug logging in auth decorator")
                print("   Consider adding debug prints to diagnose issues")

def create_session_test_endpoint():
    """Create a test endpoint to verify session state"""
    print("\n🧪 Creating session test endpoint...")
    
    test_endpoint = '''
# Add this to your main app file for testing
@app.route('/api/debug/session')
def debug_session():
    """Debug endpoint to check session state"""
    from flask import session, jsonify
    
    session_data = {
        'session_keys': list(session.keys()),
        'logged_in': session.get('logged_in', 'NOT_SET'),
        'username': session.get('username', 'NOT_SET'),
        'demo_mode': session.get('demo_mode', 'NOT_SET'),
        'session_id': session.get('_id', 'NOT_SET')
    }
    
    return jsonify({
        'session_active': len(session) > 0,
        'session_data': session_data,
        'cookies_present': len(request.cookies) > 0,
        'cookie_names': list(request.cookies.keys())
    })
'''
    
    with open('session_test_endpoint.py', 'w') as f:
        f.write(test_endpoint)
    
    print("✅ Created session_test_endpoint.py")
    print("   Add this endpoint to your app to debug session state")

def create_quick_session_test():
    """Create a quick test script for session functionality"""
    print("\n🔬 Creating quick session test...")
    
    test_script = '''#!/usr/bin/env python3
"""
Quick Session Test
==================
Test if sessions are working after fixes.
"""

import requests

def test_session_after_fixes():
    print("🧪 Testing session functionality after fixes...")
    
    session = requests.Session()
    
    # Test 1: Login
    login_response = session.post(
        'http://localhost:5000/login',
        json={'username': 'admin', 'password': 'password'}
    )
    
    print(f"Login: {login_response.status_code}")
    if login_response.status_code == 200:
        data = login_response.json()
        print(f"Success: {data.get('success', False)}")
        print(f"Demo Mode: {data.get('demo_mode', 'Unknown')}")
    
    # Test 2: API Access
    api_response = session.get('http://localhost:5000/api/token/status')
    print(f"API Access: {api_response.status_code}")
    
    # Test 3: Debug endpoint (if added)
    debug_response = session.get('http://localhost:5000/api/debug/session')
    if debug_response.status_code == 200:
        debug_data = debug_response.json()
        print(f"Session Active: {debug_data.get('session_active', False)}")
        print(f"Session Data: {debug_data.get('session_data', {})}")

if __name__ == "__main__":
    test_session_after_fixes()
'''
    
    with open('quick_session_test.py', 'w') as f:
        f.write(test_script)
    
    print("✅ Created quick_session_test.py")

def main():
    """Main fix function"""
    print("🔧 GUST SESSION CONFIGURATION FIX")
    print("=" * 50)
    
    # Create backup
    backup_dir = backup_files()
    
    # Check and fix configuration
    config_fixed = check_config_file()
    check_app_session_config()
    check_auth_decorator()
    
    # Create testing tools
    create_session_test_endpoint()
    create_quick_session_test()
    
    print(f"\n{'='*50}")
    print("🎯 SESSION FIX COMPLETE")
    print(f"📁 Backup created: {backup_dir}")
    
    if config_fixed:
        print("\n✅ Configuration fixes applied:")
        print("   - SECRET_KEY added/verified")
        print("   - Session cookie settings configured")
        print("   - Flask app session config updated")
        
        print("\n🔄 NEXT STEPS:")
        print("1. 🛑 Stop GUST (Ctrl+C)")
        print("2. 🚀 Restart GUST: python main.py")
        print("3. 🧪 Test sessions: python session_diagnostic_script.py")
        print("4. 🔬 Quick test: python quick_session_test.py")
        print("5. 🌐 Test in browser: http://localhost:5000")
        
        print("\n💡 If still not working:")
        print("   - Add the debug session endpoint to your app")
        print("   - Check session state with /api/debug/session")
        print("   - Review authentication decorator logs")
        
    else:
        print("\n⚠️ Some fixes could not be applied automatically")
        print("   - Check the config.py file manually")
        print("   - Ensure SECRET_KEY is set")
        print("   - Add session configuration to Flask app")

if __name__ == "__main__":
    main()
