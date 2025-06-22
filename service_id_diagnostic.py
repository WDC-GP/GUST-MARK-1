"""
Service ID Discovery Diagnostic Script for GUST
==============================================

This script helps diagnose and fix Service ID discovery issues.
Run this to identify why server 1722255 Service ID discovery is failing.
"""
import sys
import os
import traceback
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test if all required modules can be imported"""
    print("🔧 Testing module imports...")
    
    results = {}
    
    # Test Service ID discovery import
    try:
        from utils.service_id_discovery import ServiceIDMapper, discover_service_id, validate_service_id_discovery
        results['service_id_discovery'] = "✅ SUCCESS"
        print("   ✅ Service ID discovery module imported successfully")
    except ImportError as e:
        results['service_id_discovery'] = f"❌ FAILED: {e}"
        print(f"   ❌ Service ID discovery import failed: {e}")
    except Exception as e:
        results['service_id_discovery'] = f"❌ ERROR: {e}"
        print(f"   ❌ Service ID discovery import error: {e}")
    
    # Test GraphQL client import
    try:
        from utils.gql_client import GQLClient
        results['gql_client'] = "✅ SUCCESS"
        print("   ✅ GraphQL client imported successfully")
    except ImportError as e:
        results['gql_client'] = f"❌ FAILED: {e}"
        print(f"   ❌ GraphQL client import failed: {e}")
    except Exception as e:
        results['gql_client'] = f"❌ ERROR: {e}"
        print(f"   ❌ GraphQL client import error: {e}")
    
    # Test config import
    try:
        from config import Config
        results['config'] = "✅ SUCCESS"
        print("   ✅ Config imported successfully")
    except ImportError as e:
        results['config'] = f"❌ FAILED: {e}"
        print(f"   ❌ Config import failed: {e}")
    except Exception as e:
        results['config'] = f"❌ ERROR: {e}"
        print(f"   ❌ Config import error: {e}")
    
    return results

def test_config():
    """Test configuration settings"""
    print("\n🔧 Testing configuration...")
    
    try:
        from config import Config
        
        # Check for G-Portal authentication token
        token = getattr(Config, 'GPORTAL_TOKEN', None) or getattr(Config, 'GRAPHQL_TOKEN', None)
        if token:
            print(f"   ✅ Authentication token found (length: {len(token)} chars)")
            # Mask token for security
            masked_token = token[:8] + "..." + token[-8:] if len(token) > 16 else "***"
            print(f"   🔐 Token preview: {masked_token}")
        else:
            print("   ❌ No authentication token found")
            print("   💡 Add GPORTAL_TOKEN or GRAPHQL_TOKEN to config.py")
        
        # Check GraphQL endpoint
        gql_endpoint = getattr(Config, 'GRAPHQL_ENDPOINT', None) or getattr(Config, 'GPORTAL_GRAPHQL_ENDPOINT', None)
        if gql_endpoint:
            print(f"   ✅ GraphQL endpoint: {gql_endpoint}")
        else:
            print("   ❌ No GraphQL endpoint found")
            print("   💡 Add GRAPHQL_ENDPOINT to config.py")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Config test failed: {e}")
        return False

def test_service_id_discovery():
    """Test Service ID discovery functionality"""
    print("\n🔧 Testing Service ID discovery system...")
    
    try:
        from utils.service_id_discovery import validate_service_id_discovery
        
        print("   🔍 Running system validation...")
        validation_result = validate_service_id_discovery()
        
        if validation_result.get('valid'):
            print("   ✅ Service ID discovery system is valid")
            capabilities = validation_result.get('capabilities', [])
            if capabilities:
                print(f"   📋 Available capabilities: {', '.join(capabilities)}")
        else:
            print(f"   ❌ Service ID discovery validation failed: {validation_result.get('error')}")
            recommendations = validation_result.get('recommendations', [])
            if recommendations:
                print("   💡 Recommendations:")
                for rec in recommendations:
                    print(f"      • {rec}")
        
        return validation_result.get('valid', False)
        
    except Exception as e:
        print(f"   ❌ Service ID discovery test failed: {e}")
        traceback.print_exc()
        return False

def test_specific_server_discovery(server_id="1722255", region="US"):
    """Test Service ID discovery for your specific server"""
    print(f"\n🔧 Testing Service ID discovery for server {server_id}...")
    
    try:
        from utils.service_id_discovery import discover_service_id, ServiceIDMapper
        
        print(f"   🔍 Attempting to discover Service ID for server {server_id} in region {region}...")
        
        # Test using the main discovery function
        result = discover_service_id(server_id, region)
        
        print(f"   📊 Discovery result:")
        print(f"      • Success: {result.get('success', False)}")
        print(f"      • Server ID: {result.get('server_id', 'N/A')}")
        print(f"      • Service ID: {result.get('service_id', 'N/A')}")
        print(f"      • Region: {result.get('region', 'N/A')}")
        
        if not result.get('success'):
            print(f"      • Error: {result.get('error', 'Unknown error')}")
            print(f"      • Details: {result.get('details', 'No details available')}")
        
        # Also test using ServiceIDMapper directly
        print(f"\n   🔍 Testing ServiceIDMapper directly...")
        mapper = ServiceIDMapper()
        success, service_id, error = mapper.get_service_id_from_server_id(server_id, region)
        
        print(f"   📊 ServiceIDMapper result:")
        print(f"      • Success: {success}")
        print(f"      • Service ID: {service_id}")
        print(f"      • Error: {error}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"   ❌ Server discovery test failed: {e}")
        traceback.print_exc()
        return False

def test_network_connectivity():
    """Test network connectivity to G-Portal"""
    print("\n🔧 Testing network connectivity...")
    
    try:
        import requests
        from config import Config
        
        # Test basic connectivity to G-Portal
        gql_endpoint = getattr(Config, 'GRAPHQL_ENDPOINT', None) or getattr(Config, 'GPORTAL_GRAPHQL_ENDPOINT', None)
        
        if not gql_endpoint:
            print("   ❌ No GraphQL endpoint configured")
            return False
        
        print(f"   🌐 Testing connection to {gql_endpoint}...")
        
        response = requests.get(gql_endpoint, timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Successfully connected to G-Portal GraphQL endpoint")
        elif response.status_code == 405:
            print("   ✅ GraphQL endpoint accessible (405 Method Not Allowed is expected for GET)")
        else:
            print(f"   ⚠️ Unexpected response code: {response.status_code}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("   ❌ Connection timeout - check your internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - G-Portal may be unavailable")
        return False
    except Exception as e:
        print(f"   ❌ Network test failed: {e}")
        return False

def test_frontend_response_structure():
    """Test the API response structure that might be causing the frontend error"""
    print("\n🔧 Testing API response structure...")
    
    try:
        # Simulate the server addition response structure
        test_response = {
            'success': True,
            'message': 'Server added successfully',
            'server_data': {
                'serverId': '1722255',
                'serviceId': None,  # This is what happens when discovery fails
                'serverName': 'Test',
                'serverRegion': 'US',
                'discovery_status': 'failed',
                'capabilities': {
                    'health_monitoring': True,
                    'command_execution': False
                }
            },
            'discovery': {
                'status': 'failed',
                'message': 'Server not found or endpoint not available',
                'has_service_id': False
            }
        }
        
        print("   📋 Simulated API response structure:")
        import json
        print(json.dumps(test_response, indent=6))
        
        # Check if server_data exists and has serverId
        if 'server_data' in test_response and 'serverId' in test_response['server_data']:
            print("   ✅ Response structure looks correct for frontend")
            print("   💡 The JavaScript error might be in how the frontend processes this response")
        else:
            print("   ❌ Response structure missing required fields")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Response structure test failed: {e}")
        return False

def recommend_fixes():
    """Provide specific recommendations based on test results"""
    print("\n🔧 DIAGNOSTIC RECOMMENDATIONS:")
    print("\n📋 Based on your error logs, here are the likely fixes:")
    
    print("\n1. 🔍 SERVICE ID DISCOVERY FAILURE:")
    print("   The error 'Server 1722255 not found or endpoint not available' suggests:")
    print("   • Your G-Portal authentication token may be invalid/expired")
    print("   • The server might not be accessible via the GraphQL API")
    print("   • Network connectivity issues to G-Portal")
    
    print("\n2. 🔧 JAVASCRIPT ERROR FIX:")
    print("   The 'Cannot read properties of undefined (reading 'serverId')' error suggests:")
    print("   • Frontend code is trying to access serverId on an undefined object")
    print("   • Add null checks in your JavaScript code:")
    print("   • if (result && result.server_data && result.server_data.serverId) { ... }")
    
    print("\n3. 🚀 IMMEDIATE SOLUTIONS:")
    print("   A. Add the server manually with Service ID:")
    print("      • Server ID: 1722255 (for health monitoring)")
    print("      • Service ID: You'll need to find this from G-Portal dashboard")
    print("   B. Fix the authentication:")
    print("      • Update your GPORTAL_TOKEN in config.py")
    print("      • Get a fresh token from G-Portal settings")
    print("   C. Use the retry discovery button after adding the server")
    
    print("\n4. 🛠️ TESTING STEPS:")
    print("   • Run: python test_service_discovery.py")
    print("   • Check GUST startup logs for Service ID discovery validation")
    print("   • Test manual discovery: /api/servers/discover-service-id/1722255")

def main():
    """Run all diagnostic tests"""
    print("=" * 60)
    print("🔍 GUST SERVICE ID DISCOVERY DIAGNOSTIC")
    print("=" * 60)
    print(f"📅 Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏠 Project root: {project_root}")
    
    # Run all tests
    import_results = test_imports()
    config_ok = test_config()
    discovery_ok = test_service_id_discovery()
    server_discovery_ok = test_specific_server_discovery()
    network_ok = test_network_connectivity()
    response_ok = test_frontend_response_structure()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Module Imports", "✅" if all("SUCCESS" in v for v in import_results.values()) else "❌"),
        ("Configuration", "✅" if config_ok else "❌"),
        ("Service ID Discovery System", "✅" if discovery_ok else "❌"),
        ("Server 1722255 Discovery", "✅" if server_discovery_ok else "❌"),
        ("Network Connectivity", "✅" if network_ok else "❌"),
        ("API Response Structure", "✅" if response_ok else "❌")
    ]
    
    for test_name, status in tests:
        print(f"{status} {test_name}")
    
    # Provide recommendations
    recommend_fixes()
    
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
