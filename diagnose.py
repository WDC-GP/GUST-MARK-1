# Encoding-Safe Diagnostic Script
# ===============================
# Handles Unicode/emoji characters properly

import os
import re

def safe_read_file(filename):
    """Safely read file with multiple encoding attempts"""
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin1']
    
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"✅ Successfully read {filename} with {encoding} encoding")
            return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"❌ Error with {encoding}: {e}")
            continue
    
    print(f"❌ Could not read {filename} with any encoding")
    return None

def diagnose_register_issue():
    print("🔍 ENCODING-SAFE DIAGNOSTIC")
    print("=" * 35)
    
    # Read app.py safely
    content = safe_read_file('app.py')
    if not content:
        return False
    
    print(f"📊 File size: {len(content)} characters")
    
    # Check for methods
    checks = {
        'InMemoryUserStorage class': 'class InMemoryUserStorage:',
        'register method': 'def register(self, user_id',
        'register_user method': 'def register_user(self, user_id',
        '__init__ method': 'def __init__(self):'
    }
    
    for name, pattern in checks.items():
        exists = pattern in content
        print(f"{'✅' if exists else '❌'} {name}: {exists}")
    
    # Find .register() calls
    print("\n🔍 Searching for .register() calls...")
    try:
        calls = re.findall(r'(\w+)\.register\(', content)
        if calls:
            print(f"📍 Found .register() calls on: {set(calls)}")
            
            # Show context for each call
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '.register(' in line and 'def register(' not in line:
                    print(f"   Line {i+1}: {line.strip()}")
        else:
            print("🤔 No .register() calls found")
    except Exception as e:
        print(f"❌ Error searching for calls: {e}")
    
    # Check for None assignments
    print("\n🔍 Checking for None assignments...")
    try:
        none_patterns = [
            r'self\.user_storage\s*=\s*None',
            r'user_storage\s*=\s*None'
        ]
        
        for pattern in none_patterns:
            matches = re.findall(pattern, content)
            if matches:
                print(f"⚠️ Found None assignment: {pattern}")
    except Exception as e:
        print(f"❌ Error checking None assignments: {e}")
    
    # Show current InMemoryUserStorage structure
    print("\n🔍 InMemoryUserStorage structure:")
    try:
        lines = content.split('\n')
        in_class = False
        class_lines = []
        
        for i, line in enumerate(lines):
            if 'class InMemoryUserStorage:' in line:
                in_class = True
                class_lines.append(f"{i+1:3}: {line}")
            elif in_class:
                if line.strip().startswith('class ') and 'InMemoryUserStorage' not in line:
                    break
                class_lines.append(f"{i+1:3}: {line}")
                if len(class_lines) > 30:  # Limit output
                    class_lines.append("... (truncated)")
                    break
        
        for line in class_lines:
            print(f"  {line}")
            
    except Exception as e:
        print(f"❌ Error showing class structure: {e}")
    
    return True

def create_encoding_safe_fix():
    print("\n🔧 CREATING ENCODING-SAFE FIX...")
    
    # Read current file
    content = safe_read_file('app.py')
    if not content:
        return False
    
    # Create backup
    import shutil
    import time
    backup = f"app_encoding_backup_{int(time.time())}.py"
    try:
        shutil.copy2('app.py', backup)
        print(f"✅ Backup created: {backup}")
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")
    
    # Replace problematic emojis with ASCII
    emoji_replacements = {
        '📝': '[INFO]',
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]',
        '🛠️': '[FIX]',
        '🔄': '[RETRY]',
        '🚀': '[START]'
    }
    
    new_content = content
    for emoji, replacement in emoji_replacements.items():
        new_content = new_content.replace(emoji, replacement)
    
    # Ensure register method exists with ASCII-safe version
    register_method = '''    def register(self, user_id, nickname=None, server_id='default_server'):
        # Register method for compatibility - routes to register_user
        if nickname is None:
            nickname = user_id
        return self.register_user(user_id, nickname, server_id)'''
    
    # Check if register method is missing and add it
    if 'def register(self, user_id' not in new_content:
        # Find insertion point after __init__
        init_end = new_content.find("print('[INFO] In-memory user storage initialized')")
        if init_end == -1:
            init_end = new_content.find("print('In-memory user storage initialized')")
        
        if init_end != -1:
            # Find end of line
            line_end = new_content.find('\n', init_end)
            if line_end != -1:
                # Insert register method
                new_content = new_content[:line_end] + '\n\n' + register_method + new_content[line_end:]
                print("✅ Added register method")
            else:
                print("❌ Could not find insertion point")
        else:
            print("❌ Could not find __init__ method")
    else:
        print("✅ Register method already exists")
    
    # Write the fixed content with UTF-8 encoding
    try:
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Fixed file written with UTF-8 encoding")
        return True
    except Exception as e:
        print(f"❌ Error writing fixed file: {e}")
        return False

if __name__ == "__main__":
    success = diagnose_register_issue()
    
    if success:
        print("\n" + "="*50)
        response = input("Apply encoding-safe fix? (y/n): ").lower().strip()
        if response == 'y':
            if create_encoding_safe_fix():
                print("\n✅ Encoding-safe fix applied!")
                print("🚀 Try: python main.py")
            else:
                print("\n❌ Fix failed")
