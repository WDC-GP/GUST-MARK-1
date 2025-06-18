"""
Economy Integration Test Suite
=============================
Test server-specific economy functionality
"""

import unittest
import json
import os
from datetime import datetime
import sys

sys.path.append('.')

class EconomyIntegrationTests(unittest.TestCase):
    def setUp(self):
        '''Set up test environment'''
        self.test_user_storage = {
            'user1': {
                'userId': 'user1',
                'nickname': 'TestUser1',
                'servers': {
                    'server1': {'balance': 1000, 'clanTag': None},
                    'server2': {'balance': 1500, 'clanTag': 'CLAN'}
                }
            },
            'user2': {
                'userId': 'user2',
                'nickname': 'TestUser2',
                'servers': {
                    'server1': {'balance': 2000, 'clanTag': 'ELITE'}
                }
            }
        }
        
    def test_server_specific_balances(self):
        '''Test server-specific balance operations'''
        from utils.user_helpers import get_server_balance, set_server_balance
        
        # Test getting balances
        balance1 = get_server_balance('user1', 'server1', None, self.test_user_storage)
        balance2 = get_server_balance('user1', 'server2', None, self.test_user_storage)
        
        self.assertEqual(balance1, 1000)
        self.assertEqual(balance2, 1500)
        
        # Test setting balance
        set_result = set_server_balance('user1', 'server1', 1200, None, self.test_user_storage)
        new_balance = get_server_balance('user1', 'server1', None, self.test_user_storage)
        
        self.assertTrue(set_result)
        self.assertEqual(new_balance, 1200)
        
        # Ensure other server balance unchanged
        balance2_check = get_server_balance('user1', 'server2', None, self.test_user_storage)
        self.assertEqual(balance2_check, 1500)
        
    def test_balance_adjustments(self):
        '''Test balance adjustment operations'''
        from utils.user_helpers import adjust_server_balance, get_server_balance
        
        initial_balance = get_server_balance('user1', 'server1', None, self.test_user_storage)
        
        # Test positive adjustment
        adjust_result = adjust_server_balance('user1', 'server1', 500, None, self.test_user_storage)
        new_balance = get_server_balance('user1', 'server1', None, self.test_user_storage)
        
        self.assertTrue(adjust_result)
        self.assertEqual(new_balance, initial_balance + 500)
        
        # Test negative adjustment
        adjust_result2 = adjust_server_balance('user1', 'server1', -200, None, self.test_user_storage)
        final_balance = get_server_balance('user1', 'server1', None, self.test_user_storage)
        
        self.assertTrue(adjust_result2)
        self.assertEqual(final_balance, initial_balance + 500 - 200)
        
    def test_server_leaderboard(self):
        '''Test server-specific leaderboard'''
        from utils.user_helpers import get_server_leaderboard
        
        leaderboard = get_server_leaderboard('server1', None, self.test_user_storage, 10)
        
        # Should have 2 users on server1
        self.assertEqual(len(leaderboard), 2)
        
        # Should be sorted by balance (descending)
        self.assertEqual(leaderboard[0]['userId'], 'user2')  # 2000 balance
        self.assertEqual(leaderboard[1]['userId'], 'user1')  # 1000 balance
        
        # Test server2 leaderboard
        leaderboard2 = get_server_leaderboard('server2', None, self.test_user_storage, 10)
        self.assertEqual(len(leaderboard2), 1)  # Only user1 on server2
        self.assertEqual(leaderboard2[0]['userId'], 'user1')
        
    def test_user_transfers(self):
        '''Test user-to-user transfers'''
        from utils.user_helpers import transfer_between_users, get_server_balance
        
        # Get initial balances
        user1_initial = get_server_balance('user1', 'server1', None, self.test_user_storage)
        user2_initial = get_server_balance('user2', 'server1', None, self.test_user_storage)
        
        # Test successful transfer
        success, message = transfer_between_users('user2', 'user1', 300, 'server1', None, self.test_user_storage)
        
        self.assertTrue(success)
        self.assertIn('successful', message.lower())
        
        # Check new balances
        user1_final = get_server_balance('user1', 'server1', None, self.test_user_storage)
        user2_final = get_server_balance('user2', 'server1', None, self.test_user_storage)
        
        self.assertEqual(user1_final, user1_initial + 300)
        self.assertEqual(user2_final, user2_initial - 300)
        
        # Test insufficient funds transfer
        success2, message2 = transfer_between_users('user1', 'user2', 10000, 'server1', None, self.test_user_storage)
        
        self.assertFalse(success2)
        self.assertIn('insufficient', message2.lower())

class EconomyMigrationTests(unittest.TestCase):
    def setUp(self):
        '''Set up migration test environment'''
        self.old_economy_data = {
            'player1': 1500,
            'player2': 2500,
            'player3': 800
        }
        
        self.clan_data = [
            {'name': 'TestClan', 'members': ['player1', 'player2']},
            {'name': 'EliteClan', 'members': ['player3']}
        ]
        
    def test_economy_migration(self):
        '''Test migration from old economy to user database'''
        from utils.user_migration import UserDatabaseMigration
        
        test_user_storage = {}
        
        # Create migrator
        migrator = UserDatabaseMigration(None, test_user_storage, self.old_economy_data)
        
        # Simulate migration
        migration_report = migrator.migrate_existing_data('test_server')
        
        # Test migration results
        self.assertEqual(migration_report['users_migrated'], 3)
        self.assertEqual(migration_report['users_failed'], 0)
        self.assertEqual(len(test_user_storage), 3)
        
        # Test migrated data structure
        user1 = test_user_storage.get('player1')
        self.assertIsNotNone(user1)
        self.assertEqual(user1['userId'], 'player1')
        self.assertIn('test_server', user1['servers'])
        self.assertEqual(user1['servers']['test_server']['balance'], 1500)

def run_economy_tests():
    '''Run all economy integration tests'''
    print("🧪 Running Economy Integration Tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(EconomyIntegrationTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(EconomyMigrationTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Save results
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful(),
        'failure_details': [str(f) for f in result.failures],
        'error_details': [str(e) for e in result.errors]
    }
    
    os.makedirs('analysis', exist_ok=True)
    with open('analysis/economy_integration_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📊 Economy Test Results:")
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"❌ Errors: {len(result.errors)}")
    print(f"Success: {'✅' if result.wasSuccessful() else '❌'}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_economy_tests()
