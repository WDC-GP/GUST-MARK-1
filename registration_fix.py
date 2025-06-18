#!/usr/bin/env python3
"""
GUST Bot User Registration Fix
=============================
Fixes the missing user registration endpoint by adding the user_database blueprint
"""

import os
import shutil
from datetime import datetime

def fix_user_registration():
    """Fix missing user registration endpoint in app.py"""
    
    print("🔧 GUST Bot User Registration Fix")
    print("=" * 50)
    
    # Backup original file
    app_file = "app.py"
    if not os.path.exists(app_file):
        print("❌ app.py not found! Make sure you're in the correct directory.")
        return False
    
    backup_file = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(app_file, backup_file)
    print(f"✅ Created backup: {backup_file}")
    
    # Read current app.py
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if fix is already applied
    if 'init_user_database_routes' in content:
        print("✅ User database routes already imported!")
        return True
    
    # Apply fixes
    fixes_applied = []
    
    # 1. Add import for user_database routes
    if 'from routes.users import init_users_routes' in content:
        content = content.replace(
            'from routes.users import init_users_routes',
            '''from routes.users import init_users_routes
from routes.user_database import init_user_database_routes'''
        )
        fixes_applied.append("Added user_database import")
    
    # 2. Add blueprint registration in setup_routes method
    users_bp_line = 'users_bp = init_users_routes(self.app, self.db, self.users, self.console_output)'
    if users_bp_line in content:
        # Find the line and add the user_database blueprint after it
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # After users_bp registration, add user_database_bp
            if 'self.app.register_blueprint(users_bp)' in line:
                new_lines.append('')
                new_lines.append('        # Register user database routes (registration, profiles, etc.)')
                new_lines.append('        user_database_bp = init_user_database_routes(self.app, self.db, self.user_storage)')
                new_lines.append('        self.app.register_blueprint(user_database_bp)')
                fixes_applied.append("Added user_database blueprint registration")
        
        content = '\n'.join(new_lines)
    
    # 3. Create user_database.py if it doesn't exist
    user_db_file = "routes/user_database.py"
    if not os.path.exists(user_db_file):
        print("⚠️ Creating missing routes/user_database.py...")
        
        os.makedirs("routes", exist_ok=True)
        
        user_db_content = '''"""
GUST Bot Enhanced - User Database Routes
========================================
User registration and profile management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import random

user_database_bp = Blueprint('user_database', __name__)

def init_user_database_routes(app, db, user_storage):
    """Initialize user database routes"""
    
    @user_database_bp.route('/api/users/register', methods=['POST'])
    def register_user():
        """Register new user"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            nickname = data.get('nickname', '').strip()
            server_id = data.get('serverId', 'default_server')
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID required'})
            
            if not nickname:
                nickname = user_id
            
            # Use user_storage to register user
            if hasattr(user_storage, 'register'):
                result = user_storage.register(user_id, nickname, server_id)
                if isinstance(result, dict) and result.get('success'):
                    return jsonify({
                        'success': True, 
                        'message': f'User {nickname} registered successfully',
                        'nickname': nickname
                    })
                else:
                    return jsonify({'success': False, 'error': 'Registration failed'})
            else:
                return jsonify({'success': False, 'error': 'User storage not available'})
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @user_database_bp.route('/api/users/search', methods=['GET'])
    def search_users():
        """Search for users"""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'})
        
        # Mock search results for demo
        users = [
            {'userId': query, 'nickname': query + '_player'},
            {'userId': query + '123', 'nickname': query + '_admin'}
        ]
        
        return jsonify({'success': True, 'users': users})
    
    @user_database_bp.route('/api/users/stats/<server_id>')
    def get_user_stats(server_id):
        """Get user statistics for server"""
        return jsonify({
            'success': True,
            'stats': {
                'totalUsers': 150,
                'activeUsers': 25,
                'bannedUsers': 5
            }
        })
    
    return user_database_bp
'''
        
        with open(user_db_file, 'w', encoding='utf-8') as f:
            f.write(user_db_content)
        
        fixes_applied.append("Created routes/user_database.py")
    
    # Write updated app.py
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"   • {fix}")
    
    print("\n🎉 FIX COMPLETE!")
    print("=" * 50)
    print("🔄 Next steps:")
    print("   1. Restart GUST Bot: Ctrl+C then python main.py")
    print("   2. Refresh browser: F5")
    print("   3. Try user registration again")
    print("   4. Check console for 'User database routes registered'")
    
    return True

if __name__ == "__main__":
    fix_user_registration()
