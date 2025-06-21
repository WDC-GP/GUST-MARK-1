#!/usr/bin/env python3
"""
G-Portal GraphQL Schema Fix for GUST
====================================
This will update GUST's GraphQL mutation to match the current G-Portal API.
"""

import os
import re
import shutil
from datetime import datetime

def backup_files():
    """Create backup before making changes"""
    print("📦 Creating backup...")
    
    backup_dir = f"graphql_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = ["app.py", "utils/helpers.py", "utils/helpers1.py"]
    
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"✅ Backed up: {file}")
    
    return backup_dir

def test_current_schema():
    """Test what the current G-Portal GraphQL schema actually expects"""
    print("🧪 Testing current G-Portal GraphQL schema...")
    
    import requests
    import json
    
    try:
        with open('gp-session.json', 'r') as f:
            data = json.load(f)
        token = data.get('access_token')
    except:
        print("❌ Could not load token")
        return None
    
    endpoint = "https://www.g-portal.com/ngpapi/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://www.g-portal.com",
        "Referer": "https://www.g-portal.com/"
    }
    
    # Test the corrected schema based on the error message
    test_payloads = [
        # Test 1: Use rsid without region
        {
            "name": "rsid_only",
            "payload": {
                "operationName": "sendConsoleMessage",
                "variables": {
                    "rsid": 1736296,
                    "message": "say GUST Schema Test 1"
                },
                "query": """mutation sendConsoleMessage($rsid: Int!, $message: String!) {
                    sendConsoleMessage(rsid: $rsid, message: $message) {
                        ok
                    }
                }"""
            }
        },
        # Test 2: Use rsid as object without region
        {
            "name": "rsid_object_no_region",
            "payload": {
                "operationName": "sendConsoleMessage", 
                "variables": {
                    "rsid": {"id": 1736296},
                    "message": "say GUST Schema Test 2"
                },
                "query": """mutation sendConsoleMessage($rsid: ServerIdentifierInput!, $message: String!) {
                    sendConsoleMessage(rsid: $rsid, message: $message) {
                        ok
                    }
                }"""
            }
        },
        # Test 3: Try to find what the server identifier should be
        {
            "name": "introspection",
            "payload": {
                "query": """query IntrospectionQuery {
                    __schema {
                        mutationType {
                            fields {
                                name
                                args {
                                    name
                                    type {
                                        name
                                        kind
                                    }
                                }
                            }
                        }
                    }
                }"""
            }
        }
    ]
    
    working_schema = None
    
    for test in test_payloads:
        print(f"\n🔍 Testing schema: {test['name']}")
        
        try:
            response = requests.post(endpoint, json=test['payload'], headers=headers, timeout=15)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📝 Response: {json.dumps(data, indent=2)}")
                
                if 'errors' not in data and 'data' in data:
                    if test['name'] != 'introspection':
                        print(f"✅ WORKING SCHEMA FOUND: {test['name']}")
                        working_schema = test
                        break
                else:
                    print(f"❌ Errors: {data.get('errors', 'Unknown')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    return working_schema

def fix_graphql_mutation(file_path, working_schema):
    """Fix the GraphQL mutation in a file"""
    print(f"\n🔧 Fixing GraphQL mutation in {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False
    
    # Find and replace the old GraphQL mutation
    old_mutations = [
        # Pattern 1: Old schema with sid and region
        r'mutation sendConsoleMessage\(\$sid: Int!, \$region: REGION!, \$message: String!\)\s*\{\s*sendConsoleMessage\(sid: \$sid, region: \$region, message: \$message\)\s*\{\s*ok\s*error\s*message\s*\}\s*\}',
        
        # Pattern 2: Newer schema with rsid object but still with region
        r'mutation sendConsoleMessage\(\$sid: Int!, \$region: REGION!, \$message: String!\)\s*\{\s*sendConsoleMessage\(rsid: \{id: \$sid, region: \$region\}, message: \$message\)\s*\{\s*ok\s*__typename\s*\}\s*\}',
        
        # Pattern 3: Any sendConsoleMessage mutation
        r'mutation sendConsoleMessage.*?\{.*?sendConsoleMessage.*?\{.*?\}.*?\}'
    ]
    
    # Based on working schema, create the replacement
    if working_schema:
        if working_schema['name'] == 'rsid_only':
            new_mutation = '''mutation sendConsoleMessage($rsid: Int!, $message: String!) {
                sendConsoleMessage(rsid: $rsid, message: $message) {
                    ok
                }
            }'''
            new_variables = '''
                "variables": {
                    "rsid": server_id,
                    "message": formatted_command
                },'''
        else:
            new_mutation = '''mutation sendConsoleMessage($rsid: ServerIdentifierInput!, $message: String!) {
                sendConsoleMessage(rsid: $rsid, message: $message) {
                    ok
                }
            }'''
            new_variables = '''
                "variables": {
                    "rsid": {"id": server_id},
                    "message": formatted_command
                },'''
    else:
        # Fallback to most likely working schema
        new_mutation = '''mutation sendConsoleMessage($rsid: Int!, $message: String!) {
            sendConsoleMessage(rsid: $rsid, message: $message) {
                ok
            }
        }'''
        new_variables = '''
            "variables": {
                "rsid": server_id,
                "message": formatted_command
            },'''
    
    # Replace the mutation
    updated_content = content
    for pattern in old_mutations:
        if re.search(pattern, content, re.DOTALL):
            updated_content = re.sub(pattern, new_mutation.strip(), updated_content, flags=re.DOTALL)
            print(f"✅ Replaced GraphQL mutation pattern")
            break
    
    # Also fix the variables section
    var_patterns = [
        r'"variables":\s*\{\s*"sid":\s*server_id,\s*"region":\s*region,\s*"message":\s*formatted_command\s*\}',
        r'"variables":\s*\{\s*"sid":\s*server_id,\s*"region":\s*region,\s*"message":\s*formatted_command\s*\}'
    ]
    
    for pattern in var_patterns:
        if re.search(pattern, updated_content):
            updated_content = re.sub(pattern, new_variables.strip(), updated_content)
            print(f"✅ Updated variables section")
            break
    
    # Write the updated file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"✅ Updated {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error writing {file_path}: {e}")
        return False

def create_test_script(working_schema):
    """Create a test script to verify the fix"""
    test_script = f'''#!/usr/bin/env python3
"""
Test Fixed GraphQL Schema
========================
"""

import requests
import json

def test_fixed_schema():
    """Test the fixed GraphQL schema"""
    try:
        with open('gp-session.json', 'r') as f:
            data = json.load(f)
        token = data.get('access_token')
    except:
        print("❌ Could not load token")
        return False
    
    endpoint = "https://www.g-portal.com/ngpapi/graphql"
    headers = {{
        "Authorization": f"Bearer {{token}}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://www.g-portal.com",
        "Referer": "https://www.g-portal.com/"
    }}
    
    # Use the working schema
    payload = {working_schema['payload'] if working_schema else {
        "operationName": "sendConsoleMessage",
        "variables": {
            "rsid": 1736296,
            "message": "say GUST FIXED SCHEMA TEST - Commands should now work!"
        },
        "query": """mutation sendConsoleMessage($rsid: Int!, $message: String!) {
            sendConsoleMessage(rsid: $rsid, message: $message) {
                ok
            }
        }"""
    }}
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        print(f"📊 Status: {{response.status_code}}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📝 Response: {{json.dumps(data, indent=2)}}")
            
            if 'errors' not in data and 'data' in data:
                result = data['data']['sendConsoleMessage']
                if result.get('ok'):
                    print("🎉 FIXED SCHEMA WORKING!")
                    print("✅ Commands should now reach your server!")
                    return True
                else:
                    print("❌ Command failed")
                    return False
            else:
                print(f"❌ Errors: {{data.get('errors')}}")
                return False
        else:
            print(f"❌ HTTP Error: {{response.status_code}}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {{e}}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Fixed GraphQL Schema")
    print("=" * 40)
    
    if test_fixed_schema():
        print("\\n🎉 SUCCESS: Fixed schema is working!")
        print("✅ Your GUST commands should now work!")
        print("🔍 Check your server logs for the test message")
    else:
        print("\\n❌ Fixed schema still not working")
        print("🔧 May need further schema investigation")
'''
    
    with open('test_fixed_schema.py', 'w') as f:
        f.write(test_script)
    
    print("📝 Created test_fixed_schema.py")

def main():
    """Main fix function"""
    print("🔧 G-PORTAL GRAPHQL SCHEMA FIX")
    print("=" * 50)
    
    # Create backup
    backup_dir = backup_files()
    
    # Test current schema to find what works
    working_schema = test_current_schema()
    
    if working_schema:
        print(f"\n✅ Found working schema: {working_schema['name']}")
    else:
        print("\n⚠️ No working schema found, using best guess")
    
    # Fix the GraphQL mutations in GUST files
    files_to_fix = ["app.py", "utils/helpers.py", "utils/helpers1.py"]
    
    fixed_files = []
    for file in files_to_fix:
        if fix_graphql_mutation(file, working_schema):
            fixed_files.append(file)
    
    # Create test script
    create_test_script(working_schema)
    
    print(f"\n{'='*50}")
    print("🎯 GRAPHQL SCHEMA FIX COMPLETE")
    print(f"📁 Backup: {backup_dir}")
    print(f"✅ Fixed files: {fixed_files}")
    
    print("\n🔄 NEXT STEPS:")
    print("1. 🛑 Stop GUST (Ctrl+C)")
    print("2. 🚀 Restart GUST: python main.py")
    print("3. 🧪 Test fix: python test_fixed_schema.py")
    print("4. 🌐 Test in browser console commands")
    print("5. 🔍 Check server logs for actual command execution")
    
    if working_schema:
        print(f"\n✅ Using working schema: {working_schema['name']}")
        print("🎉 Commands should now reach your server!")
    else:
        print("\n⚠️ Schema fix applied but needs verification")
        print("🔧 Run the test script to verify functionality")

if __name__ == "__main__":
    main()
