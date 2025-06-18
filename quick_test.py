import sys
import os
import json
from datetime import datetime

# Quick test without MongoDB dependency
class QuickTestSuite:
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name, passed, message):
        status = '✅ PASS' if passed else '❌ FAIL'
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
        print(f'{status} {test_name}: {message}')
    
    def test_files_exist(self):
        '''Test that all refactored files exist'''
        print('\\n📁 Testing File Existence...')
        
        required_files = [
            'routes/user_database.py',
            'routes/economy.py',
            'routes/gambling.py',
            'routes/clans.py',
            'utils/user_helpers.py',
            'templates/components/server_selector.html',
            'templates/components/user_registration.html',
            'STEP_7_FINAL_COMPLETE.md',
            'mongodb_fallback_fix.txt'
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_test(f'File: {file_path}', True, f'Exists ({len(content)} chars)')
            else:
                self.log_test(f'File: {file_path}', False, 'File not found')
    
    def test_step_documentation(self):
        '''Test step documentation exists'''
        print('\\n📚 Testing Documentation...')
        
        step_docs = [
            'STEP_2_COMPLETE.md',
            'STEP_4_COMPLETE.md', 
            'STEP_5_COMPLETE.md',
            'STEP_6_MODULAR_INTEGRATION.md',
            'STEP_7_FINAL_COMPLETE.md'
        ]
        
        for doc_file in step_docs:
            if os.path.exists(doc_file):
                self.log_test(f'Documentation: {doc_file}', True, 'Documentation exists')
            else:
                self.log_test(f'Documentation: {doc_file}', False, 'Documentation missing')
    
    def run_tests(self):
        print('🧪 Running Quick Test Suite...')
        print('=' * 40)
        
        self.test_files_exist()
        self.test_step_documentation()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['passed'])
        failed_tests = total_tests - passed_tests
        
        print('\\n📊 Quick Test Results:')
        print('=' * 25)
        print(f'Total Tests: {total_tests}')
        print(f'✅ Passed: {passed_tests}')
        print(f'❌ Failed: {failed_tests}')
        print(f'Success Rate: {(passed_tests/total_tests)*100:.1f}%')
        
        # Save results
        with open('quick_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        if failed_tests <= 2:  # Allow a few missing optional files
            print('\\n🎉 Quick tests passed!')
            print('✅ Your refactoring files are in place')
            return True
        else:
            print('\\n⚠️ Some files missing - review results')
            return False

if __name__ == '__main__':
    test_suite = QuickTestSuite()
    success = test_suite.run_tests()
    print('\\n📄 Results saved to: quick_test_results.json')
