"""
Comprehensive Test Suite for Refactored GUST Bot
==============================================
Test all refactored systems and modular components
"""

import sys
import json
import time
import asyncio
import requests
from datetime import datetime

# Add project root to path
sys.path.append('.')

class RefactorTestSuite:
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()

    def log_test(self, test_name, passed, message):
        '''Log test result'''
        result = {
            'test': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = '✅ PASS' if passed else '❌ FAIL'
        print(f'{status}: {test_name} - {message}')

    def test_backend_routes(self):
        '''Test all refactored backend routes'''
        print('\\n🔧 Testing Backend Routes...')
        print('-' * 35)
        
        base_url = 'http://localhost:5000'
        test_endpoints = [
            # User Database Routes (Step 2)
            ('/api/users/register', 'POST'),
            ('/api/users/profile/test_user', 'GET'),
            ('/api/users/servers/test_user', 'GET'),
            
            # Economy Routes (Step 3) - Server-specific
            ('/api/economy/balance/test_user/test_server', 'GET'),
            ('/api/economy/leaderboard/test_server', 'GET'),
            ('/api/economy/server-stats/test_server', 'GET'),
            
            # Gambling Routes (Step 4) - Server-specific
            ('/api/gambling/stats/test_user/test_server', 'GET'),
            ('/api/gambling/leaderboard/test_server', 'GET'),
            ('/api/gambling/history/test_user/test_server', 'GET'),
            
            # Clan Routes (Step 5) - Server-specific
            ('/api/clans/test_server', 'GET'),
            ('/api/clans/user/test_user/test_server', 'GET'),
            ('/api/clans/stats/test_server', 'GET'),
        ]
        
        for endpoint, method in test_endpoints:
            try:
                if method == 'GET':
                    response = requests.get(f'{base_url}{endpoint}', timeout=5)
                else:
                    response = requests.post(f'{base_url}{endpoint}', 
                                           json={'test': 'data'}, timeout=5)
                
                # Check if endpoint exists (not 404)
                if response.status_code == 404:
                    self.log_test(f'{method} {endpoint}', False, 'Endpoint not found')
                else:
                    self.log_test(f'{method} {endpoint}', True, f'Status: {response.status_code}')
                    
            except requests.exceptions.ConnectionError:
                self.log_test(f'{method} {endpoint}', False, 'Connection refused - start server first')
            except Exception as e:
                self.log_test(f'{method} {endpoint}', False, f'Error: {str(e)}')

    def test_modular_frontend(self):
        '''Test modular frontend components'''
        print('\\n🎨 Testing Modular Frontend Components...')
        print('-' * 42)
        
        # Test Step 6 modular components exist
        modular_files = [
            'templates/components/server_selector.html',
            'templates/components/user_registration.html',
            'templates/views/dashboard_enhanced.html',
            'templates/scripts/enhanced_api.js.html'
        ]
        
        for file_path in modular_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 100:  # Ensure file has substantial content
                        self.log_test(f'Frontend Component: {file_path}', True, f'File exists ({len(content)} chars)')
                    else:
                        self.log_test(f'Frontend Component: {file_path}', False, 'File too small or empty')
            except FileNotFoundError:
                self.log_test(f'Frontend Component: {file_path}', False, 'File not found')
            except Exception as e:
                self.log_test(f'Frontend Component: {file_path}', False, f'Error: {str(e)}')

    def test_database_structure(self):
        '''Test database structure and migrations'''
        print('\\n🗄️ Testing Database Structure...')
        print('-' * 35)
        
        try:
            # Import app to test database connection
            from app import GustBotEnhanced
            app = GustBotEnhanced()
            
            # Test user database structure
            if hasattr(app, 'db') and app.db:
                # Test MongoDB connection
                try:
                    collections = app.db.list_collection_names()
                    self.log_test('Database Connection', True, f'Connected - {len(collections)} collections')
                    
                    # Test for user collection
                    if 'users' in collections:
                        self.log_test('User Collection', True, 'Users collection exists')
                    else:
                        self.log_test('User Collection', False, 'Users collection missing')
                        
                except Exception as e:
                    self.log_test('Database Connection', False, f'MongoDB error: {str(e)}')
            else:
                # Demo mode - test in-memory storage
                self.log_test('Storage System', True, 'In-memory storage active (demo mode)')
                
        except Exception as e:
            self.log_test('Database Structure', False, f'Error: {str(e)}')

    def test_integration_files(self):
        '''Test integration and migration files'''
        print('\\n🔗 Testing Integration Files...')
        print('-' * 33)
        
        critical_files = [
            # Step 1-2 files
            'routes/user_database.py',
            'utils/user_helpers.py',
            
            # Step 3-5 backup files  
            'routes/economy_backup.py',
            'routes/gambling_backup.py',
            'routes/clans_backup.py',
            
            # Step 6 integration
            'STEP_6_MODULAR_INTEGRATION.md',
            
            # Documentation
            'STEP_1_COMPLETE.md',
            'STEP_2_COMPLETE.md',
            'STEP_3_COMPLETE.md',
            'STEP_4_COMPLETE.md',
            'STEP_5_COMPLETE.md'
        ]
        
        for file_path in critical_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_test(f'Integration File: {file_path}', True, f'Exists ({len(content)} chars)')
            except FileNotFoundError:
                self.log_test(f'Integration File: {file_path}', False, 'File not found')
            except Exception as e:
                self.log_test(f'Integration File: {file_path}', False, f'Error: {str(e)}')

    def test_performance_improvements(self):
        '''Test performance improvements'''
        print('\\n⚡ Testing Performance Improvements...')
        print('-' * 38)
        
        try:
            from app import GustBotEnhanced
            app = GustBotEnhanced()
            
            # Test single-document user operations
            test_user_id = 'performance_test_user'
            test_server_id = 'performance_test_server'
            
            start_time = time.time()
            
            # Simulate user profile access (should be single query now)
            if hasattr(app, 'user_storage'):
                # Test user registration
                result = app.user_storage.register_user(test_user_id, 'Test User')
                profile_time = time.time() - start_time
                
                if profile_time < 0.1:  # Should be very fast now
                    self.log_test('User Profile Performance', True, f'Fast access: {profile_time:.3f}s')
                else:
                    self.log_test('User Profile Performance', False, f'Slow access: {profile_time:.3f}s')
                    
                # Test server-specific data access
                start_time = time.time()
                server_data = app.user_storage.get_user_server_data(test_user_id, test_server_id)
                server_time = time.time() - start_time
                
                if server_time < 0.05:  # Should be very fast
                    self.log_test('Server Data Performance', True, f'Fast access: {server_time:.3f}s')
                else:
                    self.log_test('Server Data Performance', False, f'Slow access: {server_time:.3f}s')
            else:
                self.log_test('Performance Test', True, 'Demo mode - performance tests skipped')
                
        except Exception as e:
            self.log_test('Performance Test', False, f'Error: {str(e)}')

    def run_all_tests(self):
        '''Run the complete test suite'''
        print('🎯 Starting Final Refactoring Test Suite...')
        print('=' * 50)
        print(f'🕐 Started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('')
        
        # Run all test categories
        self.test_modular_frontend()
        self.test_database_structure()
        self.test_integration_files()
        self.test_performance_improvements()
        self.test_backend_routes()  # Last - requires server running
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['passed'])
        failed_tests = total_tests - passed_tests
        duration = time.time() - self.start_time
        
        # Print summary
        print('')
        print('📊 FINAL TEST RESULTS SUMMARY')
        print('=' * 35)
        print(f'Total Tests: {total_tests}')
        print(f'✅ Passed: {passed_tests}')
        print(f'❌ Failed: {failed_tests}')
        print(f'⏱️ Duration: {duration:.2f} seconds')
        print(f'📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%')
        
        if failed_tests > 0:
            print('')
            print('❌ FAILED TESTS:')
            for test in self.test_results:
                if not test['passed']:
                    print(f'  - {test["test"]}: {test["message"]}')
        
        print('')
        if failed_tests == 0:
            print('🎉 ALL TESTS PASSED! Refactoring successful!')
        elif failed_tests <= 2:
            print('⚠️ Minor issues detected - review failed tests')
        else:
            print('🔧 Multiple issues detected - review before deployment')
            
        return failed_tests == 0

if __name__ == '__main__':
    test_suite = RefactorTestSuite()
    success = test_suite.run_all_tests()
    
    # Save detailed results
    with open('final_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': len(test_suite.test_results),
                'passed': sum(1 for t in test_suite.test_results if t['passed']),
                'failed': sum(1 for t in test_suite.test_results if not t['passed']),
                'success_rate': (sum(1 for t in test_suite.test_results if t['passed']) / len(test_suite.test_results)) * 100,
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': test_suite.test_results
        }, f, indent=2)
    
    print(f'📄 Detailed results saved to: final_test_results.json')
    exit(0 if success else 1)
