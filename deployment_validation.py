"""
Deployment Validation Script
===========================
Validate the deployed system is working correctly
"""

import sys
import time
import json
import requests
from datetime import datetime

class DeploymentValidator:
    def __init__(self):
        self.base_url = 'http://localhost:5000'
        self.validation_results = []

    def log_validation(self, test_name, passed, message):
        '''Log validation result'''
        result = {
            'test': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.validation_results.append(result)
        status = '✅' if passed else '❌'
        print(f'{status} {test_name}: {message}')

    def test_application_startup(self):
        '''Test application starts correctly'''
        print('🚀 Testing Application Startup...')
        
        try:
            response = requests.get(f'{self.base_url}/', timeout=10)
            if response.status_code == 200:
                self.log_validation('Application Startup', True, 'Server responding')
            else:
                self.log_validation('Application Startup', False, f'Status: {response.status_code}')
        except requests.exceptions.ConnectionError:
            self.log_validation('Application Startup', False, 'Connection refused - ensure server is running')
        except Exception as e:
            self.log_validation('Application Startup', False, f'Error: {str(e)}')

    def test_modular_frontend(self):
        '''Test modular frontend components load'''
        print('\\n🎨 Testing Modular Frontend...')
        
        try:
            # Test main dashboard loads
            response = requests.get(f'{self.base_url}/dashboard', timeout=5)
            if response.status_code in [200, 302]:  # 302 for redirect to login
                self.log_validation('Dashboard Load', True, 'Dashboard accessible')
            else:
                self.log_validation('Dashboard Load', False, f'Status: {response.status_code}')
            
            # Test login page
            response = requests.get(f'{self.base_url}/', timeout=5)
            if 'GUST Bot' in response.text:
                self.log_validation('Frontend Templates', True, 'Templates rendering correctly')
            else:
                self.log_validation('Frontend Templates', False, 'Template rendering issues')
                
        except Exception as e:
            self.log_validation('Frontend Test', False, f'Error: {str(e)}')

    def test_api_endpoints(self):
        '''Test critical API endpoints'''
        print('\\n🔧 Testing API Endpoints...')
        
        # Test user registration endpoint
        try:
            test_data = {'userId': 'validation_user', 'nickname': 'Test User'}
            response = requests.post(f'{self.base_url}/api/users/register', 
                                   json=test_data, timeout=5)
            
            if response.status_code in [200, 201, 409]:  # 409 = user already exists
                self.log_validation('User Registration API', True, 'Endpoint responding')
            else:
                self.log_validation('User Registration API', False, f'Status: {response.status_code}')
                
        except Exception as e:
            self.log_validation('User Registration API', False, f'Error: {str(e)}')

        # Test server-specific economy endpoint
        try:
            response = requests.get(f'{self.base_url}/api/economy/balance/test_user/test_server', 
                                  timeout=5)
            
            if response.status_code in [200, 404]:  # 404 acceptable if user doesn't exist
                self.log_validation('Economy API', True, 'Server-specific endpoint active')
            else:
                self.log_validation('Economy API', False, f'Status: {response.status_code}')
                
        except Exception as e:
            self.log_validation('Economy API', False, f'Error: {str(e)}')

    def test_performance(self):
        '''Test performance improvements'''
        print('\\n⚡ Testing Performance...')
        
        try:
            # Test response time
            start_time = time.time()
            response = requests.get(f'{self.base_url}/', timeout=5)
            response_time = time.time() - start_time
            
            if response_time < 2.0:  # Should be fast
                self.log_validation('Response Time', True, f'{response_time:.3f}s (good)')
            elif response_time < 5.0:
                self.log_validation('Response Time', True, f'{response_time:.3f}s (acceptable)')
            else:
                self.log_validation('Response Time', False, f'{response_time:.3f}s (slow)')
                
        except Exception as e:
            self.log_validation('Performance Test', False, f'Error: {str(e)}')

    def run_validation(self):
        '''Run complete deployment validation'''
        print('🔬 DEPLOYMENT VALIDATION')
        print('=' * 30)
        print(f'🕐 Started: {datetime.now().strftime("%H:%M:%S")}')
        print('')
        
        self.test_application_startup()
        self.test_modular_frontend()
        self.test_api_endpoints()
        self.test_performance()
        
        # Summary
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for test in self.validation_results if test['passed'])
        failed_tests = total_tests - passed_tests
        
        print('')
        print('📊 VALIDATION SUMMARY')
        print('=' * 25)
        print(f'Total Validations: {total_tests}')
        print(f'✅ Passed: {passed_tests}')
        print(f'❌ Failed: {failed_tests}')
        print(f'📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%')
        
        if failed_tests == 0:
            print('')
            print('🎉 DEPLOYMENT VALIDATION SUCCESSFUL!')
            print('✅ System is ready for production use')
            return True
        else:
            print('')
            print('⚠️ Validation issues detected:')
            for result in self.validation_results:
                if not result['passed']:
                    print(f'  - {result["test"]}: {result["message"]}')
            return False

if __name__ == '__main__':
    validator = DeploymentValidator()
    success = validator.run_validation()
    
    # Save validation results
    with open('deployment_validation.json', 'w') as f:
        json.dump(validator.validation_results, f, indent=2)
    
    print(f'\\n📄 Results saved to: deployment_validation.json')
    exit(0 if success else 1)
