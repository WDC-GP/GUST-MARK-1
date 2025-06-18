"""
Clan Integration Test Suite
===========================
Test server-specific clan functionality with user database integration
"""

import unittest
import json
import os
from datetime import datetime
import sys

sys.path.append('.')

class ClanIntegrationTests(unittest.TestCase):
    def setUp(self):
        '''Set up test environment'''
        self.test_user_storage = {
            'leader1': {
                'userId': 'leader1',
                'nickname': 'ClanLeader',
                'servers': {
                    'server1': {
                        'balance': 5000,
                        'clanTag': None,
                        'joinedAt': '2025-06-17T10:00:00Z',
                        'isActive': True
                    }
                }
            },
            'member1': {
                'userId': 'member1',
                'nickname': 'ClanMember1',
                'servers': {
                    'server1': {
                        'balance': 3000,
                        'clanTag': None,
                        'joinedAt': '2025-06-17T11:00:00Z',
                        'isActive': True
                    }
                }
            },
            'member2': {
                'userId': 'member2',
                'nickname': 'ClanMember2',
                'servers': {
                    'server1': {
                        'balance': 2000,
                        'clanTag': 'TEST',
                        'joinedAt': '2025-06-17T12:00:00Z',
                        'isActive': True
                    },
                    'server2': {
                        'balance': 1500,
                        'clanTag': None,
                        'joinedAt': '2025-06-17T13:00:00Z',
                        'isActive': True
                    }
                }
            }
        }
        
        self.test_clans_storage = [
            {
                'clanId': 'clan1',
                'name': 'Test Clan',
                'tag': 'TEST',
                'description': 'A test clan',
                'serverId': 'server1',
                'leader': 'member2',
                'members': ['member2'],
                'memberCount': 1,
                'createdAt': '2025-06-17T12:00:00Z',
                'stats': {
                    'totalMembers': 1,
                    'activeMembers': 1,
                    'totalWealth': 2000,
                    'averageBalance': 2000
                }
            }
        ]

    def test_clan_server_isolation(self):
        '''Test clan server isolation'''
        from routes.clans import get_user_info, set_user_clan_tag
        
        # Set user clan tag on server1
        set_user_clan_tag('member1', 'server1', 'ALPHA', None, self.test_user_storage)
        
        # Set same user different clan tag on server2  
        set_user_clan_tag('member1', 'server2', 'BETA', None, self.test_user_storage)
        
        # Verify isolation
        user_info = get_user_info('member1', None, self.test_user_storage)
        self.assertEqual(user_info['servers']['server1']['clanTag'], 'ALPHA')
        self.assertEqual(user_info['servers']['server2']['clanTag'], 'BETA')
        
        # Verify different servers have different clan tags
        self.assertNotEqual(
            user_info['servers']['server1']['clanTag'],
            user_info['servers']['server2']['clanTag']
        )

    def test_clan_stats_calculation(self):
        '''Test clan statistics calculation'''
        from routes.clans import update_clan_stats
        
        # Create test clan with multiple members
        test_clan = {
            'clanId': 'test_clan',
            'members': ['leader1', 'member1', 'member2'],
            'stats': {}
        }
        
        # Update stats
        update_clan_stats(test_clan, 'server1', None, self.test_user_storage)
        
        # Verify calculations
        stats = test_clan['stats']
        self.assertEqual(stats['totalMembers'], 3)
        self.assertEqual(stats['activeMembers'], 3)
        self.assertEqual(stats['totalWealth'], 10000)  # 5000 + 3000 + 2000
        self.assertEqual(stats['averageBalance'], 3333.33)  # 10000 / 3

    def test_user_clan_synchronization(self):
        '''Test user database and clan synchronization'''
        from routes.clans import set_user_clan_tag, get_user_info
        
        # Initially no clan
        user_info = get_user_info('leader1', None, self.test_user_storage)
        self.assertIsNone(user_info['servers']['server1']['clanTag'])
        
        # Set clan tag
        set_user_clan_tag('leader1', 'server1', 'ELITE', None, self.test_user_storage)
        
        # Verify synchronization
        user_info = get_user_info('leader1', None, self.test_user_storage)
        self.assertEqual(user_info['servers']['server1']['clanTag'], 'ELITE')
        
        # Remove clan tag
        set_user_clan_tag('leader1', 'server1', None, None, self.test_user_storage)
        
        # Verify removal
        user_info = get_user_info('leader1', None, self.test_user_storage)
        self.assertIsNone(user_info['servers']['server1']['clanTag'])

    def test_enhanced_member_info(self):
        '''Test enhanced member information retrieval'''
        from routes.clans import get_user_info
        
        # Get enhanced member info
        member_info = get_user_info('member2', None, self.test_user_storage)
        
        # Verify enhanced data
        self.assertEqual(member_info['userId'], 'member2')
        self.assertEqual(member_info['nickname'], 'ClanMember2')
        self.assertEqual(member_info['servers']['server1']['balance'], 2000)
        self.assertEqual(member_info['servers']['server1']['clanTag'], 'TEST')
        self.assertTrue(member_info['servers']['server1']['isActive'])

    def test_clan_wealth_tracking(self):
        '''Test clan wealth tracking functionality'''
        from routes.clans import update_clan_stats
        
        # Create wealthy clan
        wealthy_clan = {
            'clanId': 'wealthy_clan',
            'members': ['leader1', 'member1'],  # 5000 + 3000 = 8000 total
            'stats': {}
        }
        
        # Update stats
        update_clan_stats(wealthy_clan, 'server1', None, self.test_user_storage)
        
        # Verify wealth calculations
        stats = wealthy_clan['stats']
        self.assertEqual(stats['totalWealth'], 8000)
        self.assertEqual(stats['averageBalance'], 4000.0)
        self.assertEqual(stats['totalMembers'], 2)

class ClanMigrationTests(unittest.TestCase):
    def setUp(self):
        '''Set up migration test environment'''
        self.old_clan_data = [
            {
                'clanId': 'old_clan1',
                'name': 'Legacy Clan',
                'tag': 'LEGACY',
                'members': ['user1', 'user2', 'user3'],
                'leader': 'user1'
                # Note: No serverId in old format
            }
        ]
        
        self.test_user_storage = {
            'user1': {
                'userId': 'user1',
                'nickname': 'User1',
                'servers': {
                    'default_server': {
                        'balance': 1000,
                        'clanTag': None,
                        'isActive': True
                    }
                }
            },
            'user2': {
                'userId': 'user2', 
                'nickname': 'User2',
                'servers': {
                    'default_server': {
                        'balance': 2000,
                        'clanTag': None,
                        'isActive': True
                    }
                }
            }
        }

    def test_clan_migration_to_server_specific(self):
        '''Test migration of clans to server-specific format'''
        from routes.clans import set_user_clan_tag, update_clan_stats
        
        # Simulate migration process
        default_server = 'migrated_server'
        migrated_clans = []
        
        for old_clan in self.old_clan_data:
            # Migrate clan to server-specific format
            migrated_clan = {
                'clanId': old_clan['clanId'],
                'name': old_clan['name'],
                'tag': old_clan['tag'],
                'serverId': default_server,  # Add server context
                'leader': old_clan['leader'],
                'members': old_clan['members'],
                'memberCount': len(old_clan['members']),
                'description': old_clan.get('description', 'Migrated clan'),
                'createdAt': old_clan.get('createdAt', '2025-06-17T00:00:00Z'),
                'lastUpdated': '2025-06-17T00:00:00Z'
            }
            
            # Update clan stats
            update_clan_stats(migrated_clan, default_server, None, self.test_user_storage)
            
            # Set clan tags for all members
            for member_id in migrated_clan['members']:
                if member_id in self.test_user_storage:
                    set_user_clan_tag(member_id, default_server, migrated_clan['tag'], None, self.test_user_storage)
            
            migrated_clans.append(migrated_clan)
        
        # Verify migration results
        migrated_clan = migrated_clans[0]
        self.assertEqual(migrated_clan['serverId'], default_server)
        self.assertEqual(migrated_clan['memberCount'], 3)
        self.assertIn('stats', migrated_clan)
        
        # Verify user clan tags were set
        user1_info = self.test_user_storage['user1']
        self.assertEqual(user1_info['servers'][default_server]['clanTag'], 'LEGACY')

def run_clan_tests():
    '''Run all clan integration tests'''
    print("⚔️ Running Clan Integration Tests...")

    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ClanIntegrationTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ClanMigrationTests))

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
    with open('analysis/clan_integration_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)

    print(f"\n📊 Clan Test Results:")
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"❌ Errors: {len(result.errors)}")
    print(f"Success: {'✅' if result.wasSuccessful() else '❌'}")

    return result.wasSuccessful()

if __name__ == "__main__":
    run_clan_tests()
