#!/usr/bin/env python3
"""
G-Portal API Debug Script
========================
This will test the actual G-Portal API integration and find why commands aren't reaching the server.
"""

import requests
import json
import time

def load_gust_token():
    """Load the G-Portal token from GUST"""
    try:
        with open('gp-session.json', 'r') as f:
            data = json.load(f)
        return data.get('access_token')
    except Exception as e:
        print(f"❌ Error loading token: {e}")
        return None

def test_gportal_api_direct():
    """Test G-Portal API directly"""
    print("🔍 TESTING G-PORTAL API DIRECTLY")
    print("=" * 50)
    
    token = load_gust_token()
    if not token:
        print("❌ No token available")
        return False
    
    print(f"✅ Token loaded (length: {len(token)})")
    
    # Test G-Portal GraphQL endpoint
    endpoint = "https://api.g-portal.com/gameserver/graphql"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://www.g-portal.com",
        "Referer": "https://www.g-portal.com/"
    }
    
    # First, test a simple query to verify authentication
    print("\n1️⃣ Testing G-Portal authentication...")
    
    auth_query = {
        "operationName": "GetUserInfo",
        "query": "query GetUserInfo { me { id username } }",
        "variables": {}
    }
    
    try:
        response = requests.post(endpoint, 
                               json=auth_query, 
                               headers=headers, 
                               timeout=15)
        
        print(f"📊 Auth test status: {response.status_code}")
        print(f"📝 Auth response: {response.text}")
        
        if response.status_code != 200:
            print("❌ G-Portal authentication failed")
            return False
            
        try:
            auth_data = response.json()
            if 'errors' in auth_data:
                print(f"❌ GraphQL errors: {auth_data['errors']}")
                return False
            else:
                print("✅ G-Portal authentication successful")
        except:
            print("⚠️ Non-JSON response from G-Portal")
            
    except Exception as e:
        print(f"❌ G-Portal connection error: {e}")
        return False
    
    # Test server list to verify server access
    print("\n2️⃣ Testing server list access...")
    
    servers_query = {
        "operationName": "GetGameServers", 
        "query": """query GetGameServers {
            gameServers {
                id
                name
                game
                region
                status
            }
        }""",
        "variables": {}
    }
    
    try:
        response = requests.post(endpoint,
                               json=servers_query,
                               headers=headers,
                               timeout=15)
        
        print(f"📊 Server list status: {response.status_code}")
        
        if response.status_code == 200:
            servers_data = response.json()
            
            if 'errors' in servers_data:
                print(f"❌ Server list errors: {servers_data['errors']}")
                return False
            
            if 'data' in servers_data and 'gameServers' in servers_data['data']:
                servers = servers_data['data']['gameServers']
                print(f"✅ Found {len(servers)} servers")
                
                # Look for our specific server
                target_server = None
                for server in servers:
                    print(f"   Server: {server.get('name', 'Unknown')} (ID: {server.get('id', 'Unknown')}) - {server.get('game', 'Unknown')}")
                    if str(server.get('id')) == '1736296':
                        target_server = server
                        print(f"   🎯 Found target server: {server}")
                
                if target_server:
                    print(f"✅ Target server found and accessible")
                    return target_server
                else:
                    print(f"❌ Server 1736296 not found in server list")
                    print(f"💡 Available server IDs: {[s.get('id') for s in servers]}")
                    return False
            else:
                print("❌ No servers in response")
                return False
        else:
            print(f"❌ Server list failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Server list error: {e}")
        return False

def test_console_command():
    """Test sending a console command"""
    print("\n3️⃣ Testing console command sending...")
    
    token = load_gust_token()
    if not token:
        return False
    
    endpoint = "https://api.g-portal.com/gameserver/graphql"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://www.g-portal.com",
        "Referer": "https://www.g-portal.com/"
    }
    
    # Send console command
    command_mutation = {
        "operationName": "sendConsoleMessage",
        "variables": {
            "sid": 1736296,  # Server ID as integer
            "region": "US",
            "message": "say GUST Test Command - If you see this, commands are working!"
        },
        "query": """mutation sendConsoleMessage($sid: Int!, $region: REGION!, $message: String!) {
            sendConsoleMessage(sid: $sid, region: $region, message: $message) {
                ok
                error
            }
        }"""
    }
    
    try:
        print(f"📡 Sending command: {command_mutation['variables']['message']}")
        print(f"📊 Server ID: {command_mutation['variables']['sid']}")
        print(f"🌍 Region: {command_mutation['variables']['region']}")
        
        response = requests.post(endpoint,
                               json=command_mutation,
                               headers=headers,
                               timeout=30)  # Longer timeout for commands
        
        print(f"📊 Command status: {response.status_code}")
        print(f"📝 Command response: {response.text}")
        
        if response.status_code == 200:
            command_data = response.json()
            
            if 'errors' in command_data:
                print(f"❌ Command errors: {command_data['errors']}")
                return False
            
            if 'data' in command_data and 'sendConsoleMessage' in command_data['data']:
                result = command_data['data']['sendConsoleMessage']
                success = result.get('ok', False)
                error = result.get('error')
                
                if success:
                    print("✅ COMMAND SENT SUCCESSFULLY!")
                    print("🎯 Check your server logs for the test message")
                    return True
                else:
                    print(f"❌ Command failed: {error}")
                    return False
            else:
                print("❌ Unexpected command response format")
                return False
        else:
            print(f"❌ Command HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Command sending error: {e}")
        return False

def check_gust_command_implementation():
    """Check how GUST is implementing commands"""
    print("\n4️⃣ Checking GUST command implementation...")
    
    # Try to call GUST's own command endpoint
    try:
        response = requests.post('http://localhost:5000/api/console/send',
                               json={
                                   'command': 'say GUST Internal Test',
                                   'serverId': '1736296',
                                   'region': 'US'
                               },
                               timeout=10)
        
        print(f"📊 GUST command status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📝 GUST response: {data}")
            
            if data.get('success'):
                print("✅ GUST reports command success")
                print("💡 But we need to verify if it actually reaches G-Portal")
                return True
            else:
                print(f"❌ GUST command failed: {data.get('error')}")
                return False
        elif response.status_code == 401:
            print("❌ GUST authentication required")
            print("💡 Login to GUST first, then run this test")
            return False
        else:
            print(f"❌ GUST command error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ GUST command test error: {e}")
        return False

def main():
    """Main debug function"""
    print("🔍 G-PORTAL API INTEGRATION DEBUG")
    print("=" * 60)
    print("This will test if commands are actually reaching G-Portal servers.")
    print()
    
    # Test G-Portal API access
    server_info = test_gportal_api_direct()
    
    if server_info:
        # Test command sending
        command_success = test_console_command()
        
        if command_success:
            print("\n🎉 SUCCESS: Commands are reaching G-Portal!")
            print("✅ Your GUST → G-Portal integration is working")
            print("📋 Check your server logs to confirm the test message appeared")
        else:
            print("\n❌ Commands are NOT reaching G-Portal")
            print("🔧 The issue is in the GraphQL command implementation")
    else:
        print("\n❌ Cannot access G-Portal API or server")
        print("🔧 Fix G-Portal authentication/server access first")
    
    # Test GUST's internal implementation
    gust_success = check_gust_command_implementation()
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS:")
    
    if server_info and command_success:
        print("✅ G-Portal API: Working")
        print("✅ Command sending: Working")
        print("🎉 Your commands should be reaching the server!")
    elif server_info and not command_success:
        print("✅ G-Portal API: Working")
        print("❌ Command sending: Broken")
        print("🔧 Fix: GraphQL command mutation implementation")
    elif not server_info:
        print("❌ G-Portal API: Not accessible")
        print("🔧 Fix: Authentication or server permissions")
    
    if gust_success:
        print("✅ GUST internal: Reports success")
    else:
        print("❌ GUST internal: Has issues")

if __name__ == "__main__":
    main()
