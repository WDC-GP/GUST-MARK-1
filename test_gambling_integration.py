"""
Gambling Integration Test Suite
==============================
Test server-specific gambling functionality
"""

import unittest
import json
import os
from datetime import datetime
import sys

sys.path.append('.')

class GamblingIntegrationTests(unittest.TestCase):
    def setUp(self):
        '''Set up test environment'''
        self.test_user_storage = {
            'gambler1': {
                'userId': 'gambler1',
                'nickname': 'TestGambler1',
                'servers': {
                    'server1': {
                        'balance': 5000,
                        'clanTag': None,
                        'gamblingStats': {
                            'totalWagered': 1000,
                            'totalWon': 800,
                            'gamesPlayed': 20,
                            'biggestWin': 500,
                            'lastPlayed': '2025-06-17T10:00:00Z'
                        }
                    },
                    'server2': {
                        'balance': 3000,
                        'clanTag': 'LUCKY',
                        'gamblingStats': {
                            'totalWagered': 500,
                            'totalWon': 600,
                            'gamesPlayed': 10,
                            'biggestWin': 300,
                            'lastPlayed': '2025-06-17T11:00:00Z'
                        }
                    }
                }
            },
            'gambler2': {
                'userId': 'gambler2',
                'nickname': 'TestGambler2',
                'servers': {
                    'server1': {
                        'balance': 2000,
                        'clanTag': 'RISK',
                        'gamblingStats': {
                            'totalWagered': 2000,
                            'totalWon': 1500,
                            'gamesPlayed': 30,
                            'biggestWin': 250,
                            'lastPlayed': '2025-06-17T09:00:00Z'
                        }
                    }
                }
            }
        }
        
    def test_gambling_stats_retrieval(self):
        '''Test gambling statistics retrieval per server'''
        from routes.gambling import get_user_gambling_stats
        
        # Test gambler1 stats on server1
        stats1 = get_user_gambling_stats('gambler1', 'server1', None, self.test_user_storage)
        self.assertEqual(stats1['totalWagered'], 1000)
        self.assertEqual(stats1['totalWon'], 800)
        self.assertEqual(stats1['gamesPlayed'], 20)
        self.assertEqual(stats1['biggestWin'], 500)
        
        # Test gambler1 stats on server2 (different stats)
        stats2 = get_user_gambling_stats('gambler1', 'server2', None, self.test_user_storage)
        self.assertEqual(stats2['totalWagered'], 500)
        self.assertEqual(stats2['totalWon'], 600)
        self.assertEqual(stats2['gamesPlayed'], 10)
        self.assertEqual(stats2['biggestWin'], 300)
        
        # Verify server isolation
        self.assertNotEqual(stats1['totalWagered'], stats2['totalWagered'])
        self.assertNotEqual(stats1['gamesPlayed'], stats2['gamesPlayed'])

    def test_gambling_leaderboard_server_specific(self):
        '''Test server-specific gambling leaderboards'''
        from routes.gambling import get_server_gambling_leaderboard
        
        # Test server1 leaderboard
        leaderboard1 = get_server_gambling_leaderboard('server1', None, self.test_user_storage, 10)
        
        # Should have 2 users on server1
        self.assertEqual(len(leaderboard1), 2)
        
        # Should be sorted by total winnings (descending)
        self.assertEqual(leaderboard1[0]['userId'], 'gambler2')  # 1500 total won
        self.assertEqual(leaderboard1[1]['userId'], 'gambler1')  # 800 total won
        
        # Verify leaderboard data
        self.assertEqual(leaderboard1[0]['totalWon'], 1500)
        self.assertEqual(leaderboard1[1]['totalWon'], 800)
        self.assertEqual(leaderboard1[0]['rank'], 1)
        self.assertEqual(leaderboard1[1]['rank'], 2)
        
        # Test server2 leaderboard (only gambler1)
        leaderboard2 = get_server_gambling_leaderboard('server2', None, self.test_user_storage, 10)
        self.assertEqual(len(leaderboard2), 1)
        self.assertEqual(leaderboard2[0]['userId'], 'gambler1')
        
    def test_gambling_stats_updates(self):
        '''Test gambling statistics updates'''
        from routes.gambling import update_gambling_stats, get_user_gambling_stats
        
        # Get initial stats
        initial_stats = get_user_gambling_stats('gambler1', 'server1', None, self.test_user_storage)
        initial_wagered = initial_stats['totalWagered']
        initial_won = initial_stats['totalWon']
        initial_games = initial_stats['gamesPlayed']
        initial_biggest = initial_stats['biggestWin']
        
        # Update stats with a big win
        update_gambling_stats('gambler1', 'server1', 100, 800, 'slots', None, self.test_user_storage)
        
        # Get updated stats
        updated_stats = get_user_gambling_stats('gambler1', 'server1', None, self.test_user_storage)
        
        # Verify updates
        self.assertEqual(updated_stats['totalWagered'], initial_wagered + 100)
        self.assertEqual(updated_stats['totalWon'], initial_won + 800)
        self.assertEqual(updated_stats['gamesPlayed'], initial_games + 1)
        self.assertEqual(updated_stats['biggestWin'], 800)  # New biggest win
        
        # Verify other server stats unchanged
        server2_stats = get_user_gambling_stats('gambler1', 'server2', None, self.test_user_storage)
        self.assertEqual(server2_stats['totalWagered'], 500)  # Unchanged
        self.assertEqual(server2_stats['biggestWin'], 300)    # Unchanged

    def test_slot_winnings_calculation(self):
        '''Test slot machine winnings calculation'''
        from routes.gambling import calculate_slot_winnings
        
        # Test three diamonds (jackpot)
        jackpot_result = ['💎', '💎', '💎']
        jackpot_winnings = calculate_slot_winnings(jackpot_result, 100)
        self.assertEqual(jackpot_winnings, 5000)  # 100 * 50
        
        # Test three sevens
        sevens_result = ['7️⃣', '7️⃣', '7️⃣']
        sevens_winnings = calculate_slot_winnings(sevens_result, 100)
        self.assertEqual(sevens_winnings, 2500)  # 100 * 25
        
        # Test three stars
        stars_result = ['⭐', '⭐', '⭐']
        stars_winnings = calculate_slot_winnings(stars_result, 100)
        self.assertEqual(stars_winnings, 1500)  # 100 * 15
        
        # Test regular three of a kind
        cherries_result = ['🍒', '🍒', '🍒']
        cherries_winnings = calculate_slot_winnings(cherries_result, 100)
        self.assertEqual(cherries_winnings, 1000)  # 100 * 10
        
        # Test two of a kind
        pair_result = ['🍒', '🍒', '🍋']
        pair_winnings = calculate_slot_winnings(pair_result, 100)
        self.assertEqual(pair_winnings, 300)  # 100 * 3
        
        # Test no match
        no_match_result = ['🍒', '🍋', '🔔']
        no_winnings = calculate_slot_winnings(no_match_result, 100)
        self.assertEqual(no_winnings, 0)

    def test_gambling_history_isolation(self):
        '''Test gambling history server isolation'''
        from routes.gambling import log_gambling_game, get_user_gambling_history
        
        # Log a game on server1
        log_gambling_game('gambler1', 'server1', 'slots', 100, 200, 
                         {'result': ['🍒', '🍒', '🍒']}, None, self.test_user_storage)
        
        # Log a different game on server2
        log_gambling_game('gambler1', 'server2', 'coinflip', 50, 0,
                         {'choice': 'heads', 'result': 'tails', 'won': False}, None, self.test_user_storage)
        
        # Get history for server1
        history1 = get_user_gambling_history('gambler1', 'server1', None, self.test_user_storage, 10)
        self.assertTrue(len(history1) >= 1)
        self.assertEqual(history1[0]['gameType'], 'slots')
        self.assertEqual(history1[0]['serverId'], 'server1')
        
        # Get history for server2
        history2 = get_user_gambling_history('gambler1', 'server2', None, self.test_user_storage, 10)
        self.assertTrue(len(history2) >= 1)
        self.assertEqual(history2[0]['gameType'], 'coinflip')
        self.assertEqual(history2[0]['serverId'], 'server2')
        
        # Verify server isolation
        self.assertNotEqual(history1[0]['gameType'], history2[0]['gameType'])

class GamblingMigrationTests(unittest.TestCase):
    def setUp(self):
        '''Set up migration test environment'''
        self.old_gambling_logs = [
            {
                'gameId': 'game1',
                'type': 'slots',
                'userId': 'player1',
                'bet': 100,
                'result': {'symbols': ['🍒', '🍒', '🍒'], 'winnings': 500},
                'timestamp': '2025-06-17T10:00:00Z'
            },
            {
                'gameId': 'game2', 
                'type': 'coinflip',
                'userId': 'player1',
                'bet': 50,
                'result': {'choice': 'heads', 'actual': 'tails', 'won': False},
                'timestamp': '2025-06-17T11:00:00Z'
            }
        ]

    def test_gambling_data_migration(self):
        '''Test migration of gambling data to server-specific format'''
        # This test validates that old gambling logs can be migrated
        # to the new server-specific user database structure
        
        test_user_storage = {}
        default_server = 'migrated_server'
        
        # Simulate migration process
        for log in self.old_gambling_logs:
            user_id = log['userId']
            
            # Ensure user exists
            if user_id not in test_user_storage:
                test_user_storage[user_id] = {
                    'userId': user_id,
                    'nickname': user_id,
                    'servers': {}
                }
            
            # Ensure server exists
            if default_server not in test_user_storage[user_id]['servers']:
                test_user_storage[user_id]['servers'][default_server] = {
                    'balance': 1000,
                    'gamblingStats': {
                        'totalWagered': 0,
                        'totalWon': 0,
                        'gamesPlayed': 0,
                        'biggestWin': 0,
                        'lastPlayed': None
                    }
                }
            
            # Update gambling stats based on old log
            stats = test_user_storage[user_id]['servers'][default_server]['gamblingStats']
            stats['totalWagered'] += log['bet']
            
            winnings = 0
            if log['type'] == 'slots':
                winnings = log['result'].get('winnings', 0)
            elif log['type'] == 'coinflip':
                winnings = log['bet'] * 2 if log['result'].get('won', False) else 0
            
            stats['totalWon'] += winnings
            stats['gamesPlayed'] += 1
            stats['lastPlayed'] = log['timestamp']
            
            if winnings > stats['biggestWin']:
                stats['biggestWin'] = winnings
        
        # Verify migration results
        user = test_user_storage['player1']
        stats = user['servers'][default_server]['gamblingStats']
        
        self.assertEqual(stats['totalWagered'], 150)  # 100 + 50
        self.assertEqual(stats['totalWon'], 500)     # 500 + 0
        self.assertEqual(stats['gamesPlayed'], 2)
        self.assertEqual(stats['biggestWin'], 500)

def run_gambling_tests():
    '''Run all gambling integration tests'''
    print("🎰 Running Gambling Integration Tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(GamblingIntegrationTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(GamblingMigrationTests))
    
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
    with open('analysis/gambling_integration_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📊 Gambling Test Results:")
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"❌ Errors: {len(result.errors)}")
    print(f"Success: {'✅' if result.wasSuccessful() else '❌'}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_gambling_tests()
