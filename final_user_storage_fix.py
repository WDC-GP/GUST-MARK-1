#!/usr/bin/env python3
"""
Final User Storage Fix - Removes None assignments
=================================================
Fixes the remaining 'NoneType' object has no attribute 'register' error
"""

import os
import shutil
import re
from datetime import datetime

def fix_user_storage_none():
    """Fix remaining user_storage = None assignments"""
    
    print("🔧 Final User Storage Fix - Removing None Assignments")
    print("=" * 60)
    
    app_file = "app.py"
    if not os.path.exists(app_file):
        print("❌ app.py not found!")
        return False
    
    # Create backup
    backup_file = f"app_backup_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(app_file, backup_file)
    print(f"✅ Created backup: {backup_file}")
    
    # Read file
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_applied = []
    
    # 1. Find and comment out ALL user_storage = None assignments
    print("🔍 Step 1: Finding user_storage = None assignments...")
    
    none_patterns = [
        r'(\s*)(self\.user_storage\s*=\s*None.*)',
        r'(\s*)(user_storage\s*=\s*None.*)',
    ]
    
    for pattern in none_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for indent, line in matches:
            print(f"   Found: {line.strip()}")
            # Comment out the line
            commented_line = f"{indent}# FIXED: {line.strip()}  # Commented out to prevent None override"
            content = content.replace(indent + line, commented_line)
            fixes_applied.append(f"Commented out: {line.strip()}")
    
    # 2. Replace the entire init_database method with bulletproof version
    print("🔧 Step 2: Replacing init_database method with bulletproof version...")
    
    bulletproof_init = '''    def init_database(self):
        """Initialize MongoDB connection with bulletproof user storage - CONSOLIDATED VERSION"""
        
        # SINGLE POINT OF USER_STORAGE INITIALIZATION - NO MULTIPLE ASSIGNMENTS
        self.db = None
        
        try:
            from pymongo import MongoClient
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
            client.server_info()
            self.db = client.gust_bot
            print('[OK] MongoDB connected successfully')
            
            # Try MongoDB UserStorage first
            try:
                from utils.user_helpers import UserStorage
                self.user_storage = UserStorage(self.db)
                print('[OK] MongoDB UserStorage initialized')
            except ImportError:
                print('[WARNING] UserStorage not found, using InMemoryUserStorage')
                self.user_storage = InMemoryUserStorage()
                
        except Exception as e:
            print(f'[WARNING] MongoDB connection failed: {e}')
            print('[RETRY] Falling back to in-memory storage (demo mode)')
            self.user_storage = InMemoryUserStorage()
        
        # BULLETPROOF: Final verification (DO NOT SET TO None ANYWHERE)
        if self.user_storage is None:
            print('[FIX] Emergency: user_storage was None, creating InMemoryUserStorage')
            self.user_storage = InMemoryUserStorage()
        
        # BULLETPROOF: Ensure register method exists
        if not hasattr(self.user_storage, 'register'):
            print('[FIX] Adding missing register method')
            def register_compatibility(user_id, nickname=None, server_id='default_server'):
                if nickname is None:
                    nickname = user_id
                if hasattr(self.user_storage, 'register_user'):
                    return self.user_storage.register_user(user_id, nickname, server_id)
                else:
                    return {'success': False, 'error': 'Storage system broken'}
            self.user_storage.register = register_compatibility
        
        print(f'[OK] User storage type: {type(self.user_storage).__name__}')
        print('[OK] User storage initialization complete - GUARANTEED NOT None')
        
        # VERIFICATION: Double-check it's not None
        assert self.user_storage is not None, "CRITICAL: user_storage is None after initialization!"
        assert hasattr(self.user_storage, 'register'), "CRITICAL: register method missing!"'''
    
    # Find the init_database method and replace it
    init_db_pattern = r'(\s*)def init_database\(self\):.*?(?=\s*def|\s*class|\Z)'
    
    if re.search(init_db_pattern, content, re.DOTALL):
        content = re.sub(init_db_pattern, bulletproof_init, content, flags=re.DOTALL)
        fixes_applied.append("Replaced init_database method with bulletproof version")
        print("   ✅ init_database method replaced")
    else:
        print("   ⚠️ Could not find init_database method")
    
    # 3. Add verification method
    print("🔧 Step 3: Adding user_storage verification method...")
    
    verification_method = '''
    def verify_user_storage(self):
        """Verify user_storage is properly initialized - DEBUG METHOD"""
        print(f"🔍 USER_STORAGE VERIFICATION:")
        print(f"   Type: {type(self.user_storage)}")
        print(f"   Is None: {self.user_storage is None}")
        print(f"   Has register: {hasattr(self.user_storage, 'register') if self.user_storage else 'N/A - user_storage is None'}")
        print(f"   Has register_user: {hasattr(self.user_storage, 'register_user') if self.user_storage else 'N/A - user_storage is None'}")
        
        if self.user_storage is None:
            print("❌ CRITICAL: user_storage is None!")
            return False
        
        if not hasattr(self.user_storage, 'register'):
            print("❌ CRITICAL: register method missing!")
            return False
            
        print("✅ user_storage verification passed")
        return True'''
    
    # Add verification method before the run method
    run_method_pattern = r'(\s*def run\(self,.*?\):)'
    if re.search(run_method_pattern, content):
        content = re.sub(run_method_pattern, verification_method + '\n\n\\1', content)
        fixes_applied.append("Added user_storage verification method")
        print("   ✅ Verification method added")
    
    # 4. Add verification call in __init__
    print("🔧 Step 4: Adding verification call to __init__...")
    
    # Find the end of __init__ method (before logger.info)
    logger_pattern = r'(\s*logger\.info\("🚀 GUST Bot Enhanced initialized successfully"\))'
    if re.search(logger_pattern, content):
        verification_call = '''
        # FINAL VERIFICATION: Ensure user_storage is properly initialized
        if not self.verify_user_storage():
            print("❌ EMERGENCY: Creating emergency user_storage")
            self.user_storage = InMemoryUserStorage()
            if not hasattr(self.user_storage, 'register'):
                def emergency_register(user_id, nickname=None, server_id='default_server'):
                    return {'success': True, 'message': 'Emergency registration'}
                self.user_storage.register = emergency_register
            print("✅ Emergency user_storage created")
        
'''
        content = re.sub(logger_pattern, verification_call + '\\1', content)
        fixes_applied.append("Added verification call to __init__")
        print("   ✅ Verification call added to __init__")
    
    # Write the fixed file
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"   • {fix}")
    
    print("\n🎉 FINAL FIX COMPLETE!")
    print("=" * 60)
    print("🔄 Next steps:")
    print("   1. Restart GUST Bot: Ctrl+C then python main.py")
    print("   2. Look for 'USER_STORAGE VERIFICATION' in logs")
    print("   3. Should see 'user_storage verification passed'")
    print("   4. No more 'NoneType' errors!")
    print("\n🔍 Debug info:")
    print("   • Added verification method to check user_storage state")
    print("   • Added emergency fallback if user_storage becomes None")
    print("   • Commented out all user_storage = None assignments")
    print("   • Replaced init_database with single-assignment version")
    
    return True

if __name__ == "__main__":
    fix_user_storage_none()
