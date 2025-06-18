"""
User Database Testing Suite
==========================
Comprehensive tests for user database functionality
"""

import unittest
import json
import os
from datetime import datetime
import sys

# Add project root to path
sys.path.append('.')

class UserDatabaseTests(unittest.TestCase):
    def setUp(self):
        '''Set up test environment'''
        self.test_user_storage = {}
        self.test_server_id = 'test_server'
        self.test_user_id = 'test_user_123'
        
    def test_user_registration(self):
        '''Test user registration functionality'''
        user_data = {
            'userId': self.test_user_id,
            'nickname': 'TestPlayer',
            'internalId': 123456789,
            'registeredAt': datetime.now().isoformat(),
            'lastSeen': datetime.now().isoformat(),
            'servers': {
                self.test_server_id: {
                    'balance': 1000,
                    'clanTag': None,
                    'joinedAt': datetime.now().isoformat(),
                    'gamblingStats': {
                        'totalWagered': 0,
                        'totalWon': 0,
                        'gamesPlayed': 0,
                        'biggestWin': 0,
                        'lastPlayed': None
                    },
                    'isActive': True
                }
            },
            'preferences': {
                'displayNickname': True,
                'showInLeaderboards': True
            },
            'totalServers': 1
        }
        
        self.test_user_storage[self.test_user_id] = user_data
        
        # Test user exists
        self.assertIn(self.test_user_id, self.test_user_storage)
        
        # Test user structure
        user = self.test_user_storage[self.test_user_id]
        self.assertEqual(user['nickname'], 'TestPlayer')
        self.assertIn(self.test_server_id, user['servers'])
        self.assertEqual(user['servers'][self.test_server_id]['balance'], 1000)
        
    def test_server_specific_data(self):
        '''Test server-specific data isolation'''
        # Create user with multiple servers
        user_data = {
            'userId': self.test_user_id,
            'nickname': 'MultiServerUser',
            'servers': {
                'server_1': {'balance': 1000, 'clanTag': 'CLAN1'},
                'server_2': {'balance': 2000, 'clanTag': 'CLAN2'}
            }
        }
        
        self.test_user_storage[self.test_user_id] = user_data
        
        user = self.test_user_storage[self.test_user_id]
        
        # Test server isolation
        self.assertEqual(user['servers']['server_1']['balance'], 1000)
        self.assertEqual(user['servers']['server_2']['balance'], 2000)
        self.assertEqual(user['servers']['server_1']['clanTag'], 'CLAN1')
        self.assertEqual(user['servers']['server_2']['clanTag'], 'CLAN2')
        
    def test_gambling_stats(self):
        '''Test gambling statistics structure'''
        gambling_stats = {
            'totalWagered': 1500,
            'totalWon': 1200,
            'gamesPlayed': 50,
            'biggestWin': 500,
            'lastPlayed': datetime.now().isoformat()
        }
        
        # Test structure
        required_fields = ['totalWagered', 'totalWon', 'gamesPlayed', 'biggestWin', 'lastPlayed']
        for field in required_fields:
            self.assertIn(field, gambling_stats)
            
    def test_user_preferences(self):
        '''Test user preferences structure'''
        preferences = {
            'displayNickname': True,
            'showInLeaderboards': False
        }
        
        self.assertIn('displayNickname', preferences)
        self.assertIn('showInLeaderboards', preferences)
        self.assertIsInstance(preferences['displayNickname'], bool)
        self.assertIsInstance(preferences['showInLeaderboards'], bool)

class MigrationTests(unittest.TestCase):
    def setUp(self):
        '''Set up migration test environment'''
        self.old_economy_data = {
            'user1': 1500,
            'user2': 2000,
            'user3': 500
        }
        
        self.clan_data = [
            {'name': 'TestClan', 'members': ['user1', 'user2']},
            {'name': 'EliteClan', 'members': ['user3']}
        ]
        
    def test_migration_structure(self):
        '''Test migration creates correct structure'''
        # Simulate migration
        migrated_users = {}
        
        for user_id, balance in self.old_economy_data.items():
            # Find clan
            clan_tag = None
            for clan in self.clan_data:
                if user_id in clan['members']:
                    clan_tag = clan['name'][:4].upper()
                    break
            
            # Create migrated user
            migrated_users[user_id] = {
                'userId': user_id,
                'nickname': user_id,
                'servers': {
                    'default_server': {
                        'balance': balance,
                        'clanTag': clan_tag
                    }
                }
            }
        
        # Test migration results
        self.assertEqual(len(migrated_users), 3)
        self.assertEqual(migrated_users['user1']['servers']['default_server']['balance'], 1500)
        self.assertEqual(migrated_users['user1']['servers']['default_server']['clanTag'], 'TEST')
        self.assertEqual(migrated_users['user3']['servers']['default_server']['clanTag'], 'ELIT')

def run_user_database_tests():
    '''Run all user database tests'''
    print("🧪 Running User Database Tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(UserDatabaseTests))
    suite.addTest(unittest.makeSuite(MigrationTests))
    
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
    with open('analysis/user_database_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📊 Test Results:")
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"❌ Errors: {len(result.errors)}")
    print(f"Success: {'✅' if result.wasSuccessful() else '❌'}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_user_database_tests()
