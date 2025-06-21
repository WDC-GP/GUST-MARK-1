#!/usr/bin/env python3
"""
Corrected G-Portal API Test
===========================
Using the EXACT URLs and methods from GUST's implementation.
"""

import requests
import json
import time

def load_gust_token():
    """Load the G-Portal token exactly like GUST does"""
    try:
        with open('gp-session.json', 'r') as f:
            data = json.load(f)
        
        # Extract access_token exactly like GUST
        if isinstance(data, dict):
            token = data.get('access_token')
        elif isinstance(data, str):
            token = data
        else:
            print(f"❌ Unexpected token data type: {type(data)}")
            return None
            
        if not token or len(token) < 10:
            print("❌ Invalid token format")
            return None
            
        return token
    except Exception as e:
        print(f"❌ Error loading token: {e}")
        return None

def test_gust_command_implementation():
    """Test command using EXACT GUST implementation"""
    print("🔍 TESTING WITH GUST'S EXACT IMPLEMENTATION")
    print("=" * 50)
    
    token = load_gust_token()
    if not token:
        return False
    
    print(f"✅ Token loaded (length: {len(token)})")
    
    # Use EXACT endpoint from GUST config
    endpoint = "https://www.g-portal.com/ngpapi/graphql"
    
    # Use EXACT headers from GUST
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://www.g-portal.com",
        "Referer": "https://www.g-portal.com/"
    }
    
    # Use EXACT GraphQL payload from GUST
    payload = {
        "operationName": "sendConsoleMessage",
        "variables": {
            "sid": 1736296,  # Your server ID as integer
            "region": "US",
            "message": "say GUST CORRECTED TEST - This should appear in server logs!"
        },
        "query": """mutation sendConsoleMessage($sid: Int!, $region: REGION!, $message: String!) {
            sendConsoleMessage(sid: $sid, region: $region, message: $message) {
                ok
                error
                message
            }
        }"""
    }
    
    print(f"📡 Using GUST endpoint: {endpoint}")
    print(f"📊 Command: {payload['variables']['message']}")
    print(f"📊 Server ID: {payload['variables']['sid']}")
    print(f"🌍 Region: {payload['variables']['region']}")
    
    try:
        print("\n🔄 Sending command with GUST's exact method...")
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")
        print(f"📝 Response Body: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📋 Parsed JSON: {json.dumps(data, indent=2)}")
                
                if 'errors' in data:
                    print(f"❌ GraphQL Errors: {data['errors']}")
                    return False
                
                if 'data' in data and 'sendConsoleMessage' in data['data']:
                    result = data['data']['sendConsoleMessage']
                    success = result.get('ok', False)
                    error = result.get('error')
                    message = result.get('message')
                    
                    if success:
                        print("🎉 COMMAND SENT SUCCESSFULLY!")
                        print("🔍 Check your server logs for the test message")
                        print("✅ GUST command implementation is working!")
                        return True
                    else:
                        print(f"❌ Command failed: {error}")
                        if message:
                            print(f"📝 Message: {message}")
                        return False
                else:
                    print("❌ Unexpected response structure")
                    return False
                    
            except json.JSONDecodeError:
                print("❌ Response is not valid JSON")
                return False
                
        elif response.status_code == 401:
            print("❌ Authentication failed - token may be expired")
            return False
        elif response.status_code == 403:
            print("❌ Forbidden - insufficient permissions")
            return False
        elif response.status_code == 404:
            print("❌ Endpoint not found - API may have changed")
            return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - G-Portal API may be slow")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check internet connectivity")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_gust_validation_functions():
    """Test GUST's validation functions"""
    print("\n🔍 TESTING GUST VALIDATION FUNCTIONS")
    print("=" * 50)
    
    # Test server ID validation (from GUST code)
    def validate_server_id(sid):
        """GUST's server ID validation"""
        try:
            if isinstance(sid, str):
                sid = sid.strip()
                if not sid:
                    return False, None
                server_id = int(sid)
            elif isinstance(sid, int):
                server_id = sid
            else:
                return False, None
            
            if server_id <= 0:
                return False, None
                
            return True, server_id
        except (ValueError, TypeError):
            return False, None
    
    # Test region validation (from GUST code)
    def validate_region(region):
        """GUST's region validation"""
        if not region or not isinstance(region, str):
            return False
        
        valid_regions = ['US', 'EU', 'AS', 'AU']
        return region.upper() in valid_regions
    
    # Test command formatting (from GUST code)
    def format_command(command):
        """GUST's command formatting"""
        if not command or not isinstance(command, str):
            return None
        
        command = command.strip()
        if not command:
            return None
            
        # Don't double-escape quotes
        if command.startswith('"') and command.endswith('"'):
            return command
        
        return command
    
    # Test with your actual values
    print("Testing validation with your server data:")
    
    is_valid_id, server_id = validate_server_id("1736296")
    print(f"Server ID validation: {is_valid_id}, {server_id}")
    
    is_valid_region = validate_region("US")
    print(f"Region validation: {is_valid_region}")
    
    formatted_cmd = format_command("say GUST TEST")
    print(f"Command formatting: '{formatted_cmd}'")
    
    return is_valid_id and is_valid_region and formatted_cmd

def test_with_session_cookies():
    """Test using session cookies like browser"""
    print("\n🍪 TESTING WITH SESSION COOKIES")
    print("=" * 50)
    
    session = requests.Session()
    
    # Login first to get session
    try:
        login_response = session.post(
            'http://localhost:5000/login',
            json={'username': 'admin', 'password': 'password'},
            timeout=10
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            if login_data.get('success'):
                print("✅ Logged into GUST successfully")
                
                # Now test command with session
                command_response = session.post(
                    'http://localhost:5000/api/console/send',
                    json={
                        'command': 'say GUST Session Test',
                        'serverId': '1736296',
                        'region': 'US'
                    },
                    timeout=15
                )
                
                print(f"📊 GUST command status: {command_response.status_code}")
                
                if command_response.status_code == 200:
                    cmd_data = command_response.json()
                    print(f"📝 GUST response: {json.dumps(cmd_data, indent=2)}")
                    
                    if cmd_data.get('success'):
                        print("✅ GUST internal command successful!")
                        print("🔍 This means GUST → G-Portal pipeline should be working")
                        return True
                    else:
                        print(f"❌ GUST command failed: {cmd_data.get('error')}")
                        return False
                else:
                    print(f"❌ GUST command HTTP error: {command_response.status_code}")
                    return False
            else:
                print(f"❌ GUST login failed: {login_data}")
                return False
        else:
            print(f"❌ GUST login HTTP error: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Session test error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 CORRECTED G-PORTAL API TEST")
    print("=" * 60)
    print("Using GUST's exact URLs and implementation...")
    print()
    
    # Test validation functions
    validation_ok = test_gust_validation_functions()
    
    if validation_ok:
        # Test direct G-Portal API
        api_success = test_gust_command_implementation()
        
        # Test through GUST
        gust_success = test_with_session_cookies()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL DIAGNOSIS:")
        
        if api_success:
            print("✅ Direct G-Portal API: WORKING")
            print("🎉 Commands should be reaching your server!")
            
            if gust_success:
                print("✅ GUST Internal: WORKING")  
                print("🎉 Your entire pipeline is functional!")
            else:
                print("❌ GUST Internal: Has issues")
                print("🔧 Problem is in GUST's command handling")
                
        else:
            print("❌ Direct G-Portal API: NOT WORKING")
            
            if gust_success:
                print("✅ GUST Internal: Claims success")
                print("🔧 GUST is reporting false positives")
            else:
                print("❌ GUST Internal: Also failing")
                print("🔧 Multiple issues in the pipeline")
                
        print("\n💡 Check your server logs to see if any test messages appeared!")
        
    else:
        print("❌ Validation functions failed - fix these first")

if __name__ == "__main__":
    main()
