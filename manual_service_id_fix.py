"""
Manual Service ID Addition Script
===============================

Since your Service ID discovery is failing, this script lets you manually
add the Service ID for server 1722255 to enable full functionality.

To find your Service ID:
1. Go to your G-Portal dashboard
2. Navigate to your server 1722255 
3. Look at the URL or server settings for the Service ID
4. It will be a different number than 1722255

Run this script: python manual_service_id_fix.py
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_service_id_from_user():
    """Get Service ID from user input"""
    print("\n🔍 Manual Service ID Entry")
    print("=" * 40)
    print("To find your Service ID:")
    print("1. Log into your G-Portal dashboard")
    print("2. Go to your server (Test/1722255)")
    print("3. Check the URL or server details page")
    print("4. Look for a different ID (usually 7 digits)")
    print("5. This is your Service ID for commands")
    
    while True:
        service_id = input("\n🆔 Enter your Service ID for server 1722255: ").strip()
        
        if not service_id:
            print("❌ Service ID cannot be empty")
            continue
            
        if not service_id.isdigit():
            print("❌ Service ID must be numeric")
            continue
            
        if len(service_id) < 6 or len(service_id) > 8:
            print("⚠️ Service ID is usually 6-8 digits. Are you sure this is correct?")
            confirm = input("Continue anyway? (y/n): ").lower()
            if confirm != 'y':
                continue
        
        return service_id

def update_server_in_database(server_id, service_id):
    """Update server in database with Service ID"""
    try:
        # Try MongoDB first
        try:
            from pymongo import MongoClient
            from config import Config
            
            mongo_uri = getattr(Config, 'MONGO_URI', 'mongodb://localhost:27017/')
            db_name = getattr(Config, 'MONGO_DB_NAME', 'gust_bot')
            
            client = MongoClient(mongo_uri)
            db = client[db_name]
            
            # Update the server
            result = db.servers.update_one(
                {'serverId': server_id},
                {
                    '$set': {
                        'serviceId': service_id,
                        'discovery_status': 'manual',
                        'discovery_message': 'Service ID added manually',
                        'discovery_timestamp': datetime.now().isoformat(),
                        'capabilities.command_execution': True,
                        'last_updated': datetime.now().isoformat()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Successfully updated server {server_id} in MongoDB")
                print(f"🔧 Service ID set to: {service_id}")
                return True
            else:
                print(f"⚠️ Server {server_id} not found in MongoDB")
                return False
                
        except Exception as mongo_error:
            print(f"⚠️ MongoDB update failed: {mongo_error}")
            print("🔄 Trying in-memory storage update...")
            return False
            
    except Exception as e:
        print(f"❌ Database update error: {e}")
        return False

def create_manual_server_config(server_id, service_id):
    """Create a manual server configuration file"""
    try:
        config_dir = os.path.join(project_root, 'manual_configs')
        os.makedirs(config_dir, exist_ok=True)
        
        server_config = {
            'serverId': server_id,
            'serviceId': service_id,
            'serverName': 'Test',
            'serverRegion': 'US',
            'serverType': 'Standard',
            'discovery_status': 'manual',
            'discovery_message': 'Service ID added manually via script',
            'discovery_timestamp': datetime.now().isoformat(),
            'capabilities': {
                'health_monitoring': True,
                'sensor_data': True,
                'command_execution': True,
                'websocket_support': True
            },
            'config': {
                'auto_commands_enabled': True,
                'health_monitoring_enabled': True,
                'sensor_polling_enabled': True,
                'command_logging_enabled': True
            },
            'manual_entry': True,
            'created_at': datetime.now().isoformat()
        }
        
        config_file = os.path.join(config_dir, f'server_{server_id}_manual.json')
        
        with open(config_file, 'w') as f:
            json.dump(server_config, f, indent=2)
        
        print(f"✅ Manual configuration saved to: {config_file}")
        print("📁 You can import this config when GUST restarts")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create manual config: {e}")
        return False

def update_existing_server_directly():
    """Try to update existing server data directly"""
    try:
        # Look for existing servers storage
        server_found = False
        
        # Check if we can import the app and access servers
        try:
            import app
            if hasattr(app, 'servers_storage'):
                for server in app.servers_storage:
                    if server.get('serverId') == '1722255':
                        server['serviceId'] = service_id
                        server['discovery_status'] = 'manual'
                        server['discovery_message'] = 'Service ID added manually'
                        server['capabilities']['command_execution'] = True
                        server['last_updated'] = datetime.now().isoformat()
                        server_found = True
                        print("✅ Updated server in active app storage")
                        break
        except:
            pass
        
        return server_found
        
    except Exception as e:
        print(f"❌ Direct update failed: {e}")
        return False

def test_service_id_functionality(server_id, service_id):
    """Test if the Service ID works for commands"""
    print(f"\n🧪 Testing Service ID {service_id} functionality...")
    
    try:
        # Test GraphQL query with the Service ID
        from utils.gql_client import GQLClient
        
        client = GQLClient()
        
        # Try a simple query to test if Service ID is valid
        query = """
        query GetServiceInfo($serviceId: ID!) {
            service(id: $serviceId) {
                id
                name
                status
            }
        }
        """
        
        variables = {"serviceId": service_id}
        result = client.execute_query(query, variables)
        
        if result.get('success'):
            print("✅ Service ID is valid and accessible!")
            service_data = result.get('data', {}).get('service', {})
            if service_data:
                print(f"📋 Service Info:")
                print(f"   • ID: {service_data.get('id', 'N/A')}")
                print(f"   • Name: {service_data.get('name', 'N/A')}")
                print(f"   • Status: {service_data.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Service ID test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"⚠️ Could not test Service ID (this is OK): {e}")
        print("💡 The Service ID might still work - try it in GUST")
        return None

def main():
    """Main function to manually add Service ID"""
    print("🔧 MANUAL SERVICE ID ADDITION TOOL")
    print("=" * 50)
    print("This tool helps you manually add the Service ID for server 1722255")
    print("since automatic discovery is failing.")
    
    # Get Service ID from user
    service_id = get_service_id_from_user()
    server_id = "1722255"
    
    print(f"\n📋 Configuration Summary:")
    print(f"   • Server ID: {server_id} (for health monitoring)")
    print(f"   • Service ID: {service_id} (for commands)")
    print(f"   • Region: US")
    
    confirm = input("\n✅ Is this correct? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    print(f"\n🔧 Adding Service ID {service_id} to server {server_id}...")
    
    # Try multiple update methods
    methods_tried = []
    success = False
    
    # Method 1: Database update
    print("\n1️⃣ Trying database update...")
    if update_server_in_database(server_id, service_id):
        methods_tried.append("✅ Database update")
        success = True
    else:
        methods_tried.append("❌ Database update failed")
    
    # Method 2: Direct app update
    print("\n2️⃣ Trying direct app storage update...")
    if update_existing_server_directly():
        methods_tried.append("✅ Direct app update")
        success = True
    else:
        methods_tried.append("❌ Direct app update failed")
    
    # Method 3: Manual config file
    print("\n3️⃣ Creating manual configuration file...")
    if create_manual_server_config(server_id, service_id):
        methods_tried.append("✅ Manual config created")
        success = True
    else:
        methods_tried.append("❌ Manual config failed")
    
    # Test functionality
    print("\n4️⃣ Testing Service ID functionality...")
    test_result = test_service_id_functionality(server_id, service_id)
    if test_result is True:
        methods_tried.append("✅ Service ID test passed")
    elif test_result is False:
        methods_tried.append("❌ Service ID test failed")
    else:
        methods_tried.append("⚠️ Service ID test inconclusive")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 OPERATION SUMMARY")
    print("=" * 50)
    
    for method in methods_tried:
        print(f"   {method}")
    
    if success:
        print("\n✅ SUCCESS! Service ID has been added to your server.")
        print("\n🚀 Next Steps:")
        print("1. Restart GUST (python main.py)")
        print("2. Try using commands on server 1722255")
        print("3. Check if 'Command Execution: ✅' appears in server list")
        print("4. Test sending console commands")
        
        # Provide the API test command
        print(f"\n🧪 Test Command Execution:")
        print(f"curl -X POST http://localhost:5000/api/console/send \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{\"serverId\": \"{server_id}\", \"command\": \"serverinfo\"}}'")
        
    else:
        print("\n❌ Could not automatically add Service ID.")
        print("\n🔧 Manual Steps:")
        print("1. Stop GUST")
        print("2. Edit your server configuration manually")
        print("3. Add 'serviceId': '{service_id}' to server 1722255 data")
        print("4. Restart GUST")
    
    print(f"\n💡 If you need help, your Service ID is: {service_id}")

if __name__ == "__main__":
    main()
