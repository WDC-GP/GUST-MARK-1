#!/usr/bin/env python3
"""
Correct GraphQL Schema Test
===========================
Now that we know the exact schema, test the correct RSID_input format.
"""

import requests
import json

def test_rsid_input_formats():
    """Test different RSID_input object formats"""
    print("🧪 TESTING RSID_INPUT FORMATS")
    print("=" * 50)
    
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
    
    # Test different RSID_input formats based on the schema
    test_formats = [
        {
            "name": "rsid_with_id_only",
            "rsid": {"id": 1736296},
            "message": "say GUST Schema Test - ID Only"
        },
        {
            "name": "rsid_with_id_and_region", 
            "rsid": {"id": 1736296, "region": "US"},
            "message": "say GUST Schema Test - ID and Region"
        },
        {
            "name": "rsid_string_format",
            "rsid": "1736296",
            "message": "say GUST Schema Test - String Format"
        },
        {
            "name": "rsid_different_region_format",
            "rsid": {"server_id": 1736296, "region": "US"},
            "message": "say GUST Schema Test - Different Keys"
        }
    ]
    
    working_format = None
    
    for test_format in test_formats:
        print(f"\n🔍 Testing: {test_format['name']}")
        print(f"📊 RSID format: {test_format['rsid']}")
        
        payload = {
            "operationName": "sendConsoleMessage",
            "variables": {
                "rsid": test_format['rsid'],
                "message": test_format['message']
            },
            "query": """mutation sendConsoleMessage($rsid: RSID_input!, $message: String!) {
                sendConsoleMessage(rsid: $rsid, message: $message) {
                    ok
                }
            }"""
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📝 Response: {json.dumps(data, indent=2)}")
                
                if 'errors' not in data and 'data' in data:
                    result = data['data']['sendConsoleMessage']
                    if result and result.get('ok'):
                        print(f"✅ SUCCESS: {test_format['name']} WORKS!")
                        working_format = test_format
                        break
                    else:
                        print(f"❌ Command failed: {result}")
                else:
                    print(f"❌ Errors: {data.get('errors', 'Unknown')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    return working_format

def create_final_fix(working_format):
    """Create the final GraphQL mutation fix"""
    print("\n🔧 CREATING FINAL GRAPHQL FIX")
    print("=" * 50)
    
    if not working_format:
        print("❌ No working format found")
        return False
    
    print(f"✅ Working format: {working_format['name']}")
    print(f"📊 RSID structure: {working_format['rsid']}")
    
    # Create the correct GraphQL mutation and variables
    if working_format['name'] == 'rsid_with_id_only':
        correct_mutation = '''mutation sendConsoleMessage($rsid: RSID_input!, $message: String!) {
            sendConsoleMessage(rsid: $rsid, message: $message) {
                ok
            }
        }'''
        correct_variables = '''
        "variables": {
            "rsid": {"id": server_id},
            "message": formatted_command
        },'''
        
    elif working_format['name'] == 'rsid_with_id_and_region':
        correct_mutation = '''mutation sendConsoleMessage($rsid: RSID_input!, $message: String!) {
            sendConsoleMessage(rsid: $rsid, message: $message) {
                ok
            }
        }'''
        correct_variables = '''
        "variables": {
            "rsid": {"id": server_id, "region": region},
            "message": formatted_command
        },'''
    
    else:
        print(f"⚠️ Unexpected working format: {working_format['name']}")
        return False
    
    # Write the fix instructions
    fix_instructions = f'''# FINAL GRAPHQL MUTATION FIX
# ============================

Replace the GraphQL mutation in your GUST files with:

## Mutation:
{correct_mutation}

## Variables:
{correct_variables}

## Working RSID format:
{working_format['rsid']}

## Files to update:
- app.py (send_console_command_graphql function)
- utils/helpers.py (if contains GraphQL mutations)
- utils/helpers1.py (if contains GraphQL mutations)

## Test command that worked:
{working_format['message']}
'''
    
    with open('FINAL_GRAPHQL_FIX.txt', 'w', encoding='utf-8') as f:
        f.write(fix_instructions)
    
    print("📝 Created FINAL_GRAPHQL_FIX.txt with exact fix instructions")
    return True

def test_gust_internal_after_fix():
    """Test GUST internal commands after the partial fix"""
    print("\n🔧 TESTING GUST INTERNAL COMMANDS")
    print("=" * 50)
    
    session = requests.Session()
    
    try:
        # Login to GUST
        login_response = session.post(
            'http://localhost:5000/login',
            json={'username': 'admin', 'password': 'password'},
            timeout=10
        )
        
        if login_response.status_code == 200 and login_response.json().get('success'):
            print("✅ Logged into GUST")
            
            # Test command through GUST
            command_response = session.post(
                'http://localhost:5000/api/console/send',
                json={
                    'command': 'say GUST Internal Test After Fix',
                    'serverId': '1736296',
                    'region': 'US'
                },
                timeout=15
            )
            
            print(f"📊 GUST command status: {command_response.status_code}")
            
            if command_response.status_code == 200:
                data = command_response.json()
                print(f"📝 GUST response: {json.dumps(data, indent=2)}")
                
                if data.get('success'):
                    print("✅ GUST internal command reports success")
                    print("🔍 Check server logs to see if it actually worked")
                    return True
                else:
                    print(f"❌ GUST command failed: {data.get('error')}")
                    return False
            else:
                print(f"❌ GUST HTTP error: {command_response.status_code}")
                return False
        else:
            print("❌ GUST login failed")
            return False
            
    except Exception as e:
        print(f"❌ GUST test error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 CORRECT GRAPHQL SCHEMA TEST")
    print("=" * 60)
    print("Testing the exact RSID_input format from GraphQL introspection...")
    print()
    
    # Test different RSID formats
    working_format = test_rsid_input_formats()
    
    # Create final fix instructions
    fix_created = create_final_fix(working_format)
    
    # Test GUST internal (might work now with partial fix)
    gust_works = test_gust_internal_after_fix()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    
    if working_format:
        print(f"✅ Found working GraphQL format: {working_format['name']}")
        print(f"📊 RSID structure: {working_format['rsid']}")
        print("🔍 Check your server logs for the test message!")
        
        if fix_created:
            print("📝 Fix instructions created in FINAL_GRAPHQL_FIX.txt")
        
        if gust_works:
            print("✅ GUST internal commands working!")
            print("🎉 Your commands should now reach the server!")
        else:
            print("❌ GUST internal still has issues")
            print("🔧 Apply the final fix from FINAL_GRAPHQL_FIX.txt")
            
    else:
        print("❌ No working GraphQL format found")
        print("🔧 G-Portal API may have additional restrictions")
        
        if gust_works:
            print("✅ GUST internal claims to work")
            print("🔍 Check server logs to verify actual execution")

if __name__ == "__main__":
    main()
