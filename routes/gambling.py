"""
GUST Bot Enhanced - Gambling Routes (REFACTORED)
===============================================
Server-specific gambling system using user database
"""


from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import secrets
import random

from routes.auth import require_auth
from utils.user_helpers import (
    get_user_profile, get_server_balance, set_server_balance,
    adjust_server_balance, ensure_user_on_server, get_user_display_name,
    get_users_on_server
)
import logging


# GUST database optimization imports
from utils.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor
)
logger = logging.getLogger(__name__)

gambling_bp = Blueprint('gambling', __name__)

def init_gambling_routes(app, db, user_storage):
    '''Initialize gambling routes with server-specific functionality'''
    
    @gambling_bp.route('/api/gambling/slots/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def play_slots_server(user_id, server_id):
        '''Play slot machine on specific server'''
        try:
            data = request.json
            bet_amount = data.get('bet', 0)
            
            if not user_id or not server_id:
                return jsonify({'success': False, 'error': 'User ID and Server ID required'})
            
            if bet_amount <= 0:
                return jsonify({'success': False, 'error': 'Bet must be positive'})
            
            # Ensure user exists on server
            ensure_user_on_server(user_id, server_id, db, user_storage)
            
            # Check user balance on this server
            current_balance = get_server_balance(user_id, server_id, db, user_storage)
            if current_balance < bet_amount:
                return jsonify({'success': False, 'error': 'Insufficient balance'})
            
            # Generate slot results
            symbols = ['🍒', '🍋', '🔔', '⭐', '💎', '7️⃣']
            result = [secrets.choice(symbols) for _ in range(3)]
            
            # Calculate winnings based on slot combination
            winnings = calculate_slot_winnings(result, bet_amount)
            net_change = winnings - bet_amount
            
            # Update balance
            if adjust_server_balance(user_id, server_id, net_change, db, user_storage):
                new_balance = get_server_balance(user_id, server_id, db, user_storage)
                
                # Update gambling stats
                update_gambling_stats(user_id, server_id, bet_amount, winnings, 'slots', db, user_storage)
                
                # Log game
                log_gambling_game(user_id, server_id, 'slots', bet_amount, winnings, {'result': result}, db, user_storage)
                
                logger.info(f'🎰 Slots: {user_id} on {server_id}, bet: {bet_amount}, won: {winnings}')
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'winnings': winnings,
                    'net_change': net_change,
                    'new_balance': new_balance,
                    'bet_amount': bet_amount
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to update balance'})
            
        except Exception as e:
            logger.error(f'❌ Error in slots: {e}')
            return jsonify({'success': False, 'error': 'Slots game failed'})
    
    @gambling_bp.route('/api/gambling/coinflip/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def play_coinflip_server(user_id, server_id):
        '''Play coinflip on specific server'''
        try:
            data = request.json
            bet_amount = data.get('amount', 0)
            choice = data.get('choice', '').lower()
            
            if choice not in ['heads', 'tails']:
                return jsonify({'success': False, 'error': 'Choice must be heads or tails'})
            
            if bet_amount <= 0:
                return jsonify({'success': False, 'error': 'Bet must be positive'})
            
            # Ensure user exists on server
            ensure_user_on_server(user_id, server_id, db, user_storage)
            
            # Check balance
            current_balance = get_server_balance(user_id, server_id, db, user_storage)
            if current_balance < bet_amount:
                return jsonify({'success': False, 'error': 'Insufficient balance'})
            
            # Flip coin
            result = secrets.choice(['heads', 'tails'])
            won = result == choice
            winnings = bet_amount * 2 if won else 0
            net_change = winnings - bet_amount
            
            # Update balance
            if adjust_server_balance(user_id, server_id, net_change, db, user_storage):
                new_balance = get_server_balance(user_id, server_id, db, user_storage)
                
                # Update gambling stats
                update_gambling_stats(user_id, server_id, bet_amount, winnings, 'coinflip', db, user_storage)
                
                # Log game
                log_gambling_game(user_id, server_id, 'coinflip', bet_amount, winnings, 
                                {'choice': choice, 'result': result, 'won': won}, db, user_storage)
                
                logger.info(f'🪙 Coinflip: {user_id} on {server_id}, {choice} → {result}, won: {won}')
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'choice': choice,
                    'won': won,
                    'winnings': winnings,
                    'net_change': net_change,
                    'new_balance': new_balance,
                    'bet_amount': bet_amount
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to update balance'})
                
        except Exception as e:
            logger.error(f'❌ Error in coinflip: {e}')
            return jsonify({'success': False, 'error': 'Coinflip failed'})
    
    @gambling_bp.route('/api/gambling/dice/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def play_dice_server(user_id, server_id):
        '''Play dice game on specific server'''
        try:
            data = request.json
            bet_amount = data.get('amount', 0)
            prediction = data.get('prediction', 0)
            
            if not (1 <= prediction <= 6):
                return jsonify({'success': False, 'error': 'Prediction must be between 1 and 6'})
            
            if bet_amount <= 0:
                return jsonify({'success': False, 'error': 'Bet must be positive'})
            
            # Ensure user exists on server
            ensure_user_on_server(user_id, server_id, db, user_storage)
            
            # Check balance
            current_balance = get_server_balance(user_id, server_id, db, user_storage)
            if current_balance < bet_amount:
                return jsonify({'success': False, 'error': 'Insufficient balance'})
            
            # Roll dice
            result = secrets.randbelow(6) + 1
            won = result == prediction
            winnings = bet_amount * 6 if won else 0  # 6x payout for exact prediction
            net_change = winnings - bet_amount
            
            # Update balance
            if adjust_server_balance(user_id, server_id, net_change, db, user_storage):
                new_balance = get_server_balance(user_id, server_id, db, user_storage)
                
                # Update gambling stats
                update_gambling_stats(user_id, server_id, bet_amount, winnings, 'dice', db, user_storage)
                
                # Log game
                log_gambling_game(user_id, server_id, 'dice', bet_amount, winnings,
                                {'prediction': prediction, 'result': result, 'won': won}, db, user_storage)
                
                logger.info(f'🎲 Dice: {user_id} on {server_id}, predicted: {prediction}, rolled: {result}, won: {won}')
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'prediction': prediction,
                    'won': won,
                    'winnings': winnings,
                    'net_change': net_change,
                    'new_balance': new_balance,
                    'bet_amount': bet_amount
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to update balance'})
                
        except Exception as e:
            logger.error(f'❌ Error in dice: {e}')
            return jsonify({'success': False, 'error': 'Dice game failed'})
    
    @gambling_bp.route('/api/gambling/history/<user_id>/<server_id>')
    @require_auth
    def get_gambling_history_server(user_id, server_id):
        '''Get user's gambling history for specific server'''
        try:
            limit = request.args.get('limit', 20, type=int)
            game_type = request.args.get('type', 'all')
            limit = min(max(limit, 1), 100)  # Between 1 and 100
            
            history = get_user_gambling_history(user_id, server_id, db, user_storage, limit, game_type)
            
            return jsonify({
                'success': True,
                'history': history,
                'userId': user_id,
                'serverId': server_id,
                'totalGames': len(history)
            })
            
        except Exception as e:
            logger.error(f'❌ Error getting gambling history: {e}')
            return jsonify({'success': False, 'error': 'Failed to get gambling history'})
    
    @gambling_bp.route('/api/gambling/stats/<user_id>/<server_id>')
    @require_auth
    def get_gambling_stats_server(user_id, server_id):
        '''Get user's gambling statistics for specific server'''
        try:
            stats = get_user_gambling_stats(user_id, server_id, db, user_storage)
            
            # Calculate additional statistics
            if stats['gamesPlayed'] > 0:
                stats['winRate'] = round((stats['totalWon'] / stats['totalWagered']) * 100, 2) if stats['totalWagered'] > 0 else 0
                stats['averageBet'] = round(stats['totalWagered'] / stats['gamesPlayed'], 2)
                stats['netProfit'] = stats['totalWon'] - stats['totalWagered']
            else:
                stats['winRate'] = 0
                stats['averageBet'] = 0
                stats['netProfit'] = 0
            
            return jsonify({
                'success': True,
                'stats': stats,
                'userId': user_id,
                'serverId': server_id
            })
            
        except Exception as e:
            logger.error(f'❌ Error getting gambling stats: {e}')
            return jsonify({'success': False, 'error': 'Failed to get gambling stats'})
    
    @gambling_bp.route('/api/gambling/leaderboard/<server_id>')
    @require_auth
    def get_gambling_leaderboard_server(server_id):
        '''Get gambling leaderboard for specific server'''
        try:
            limit = request.args.get('limit', 10, type=int)
            period = request.args.get('period', 'all')  # all, today, week, month
            limit = min(max(limit, 1), 50)  # Between 1 and 50
            
            leaderboard = get_server_gambling_leaderboard(server_id, db, user_storage, limit, period)
            
            return jsonify({
                'success': True,
                'leaderboard': leaderboard,
                'serverId': server_id,
                'period': period,
                'totalUsers': len(leaderboard)
            })
            
        except Exception as e:
            logger.error(f'❌ Error getting gambling leaderboard: {e}')
            return jsonify({'success': False, 'error': 'Failed to get gambling leaderboard'})

    # ============================================
    # LEGACY ROUTES FOR FRONTEND COMPATIBILITY
    # ============================================
    @gambling_bp.route('/api/gambling/slots', methods=['POST'])
    @require_auth
    def play_slots_legacy():
        """Legacy slots route"""
        try:
            data = request.json or {}
            user_id = data.get('userId', 'bradf')  # Default from your frontend
            server_id = data.get('serverId', 'default_server')
            bet_amount = data.get('bet', 1)
            
            # Call the server-specific function
            return play_slots_server(user_id, server_id)
        except Exception as e:
            logger.error(f'❌ Legacy slots error: {str(e)}')
            return jsonify({'success': False, 'error': 'Slots game failed'})

    @gambling_bp.route('/api/gambling/coinflip', methods=['POST'])
    @require_auth
    def play_coinflip_legacy():
        """Legacy coinflip route"""
        try:
            data = request.json or {}
            user_id = data.get('userId', 'bradf')  # Default from your frontend
            server_id = data.get('serverId', 'default_server')
            
            # Call the server-specific function
            return play_coinflip_server(user_id, server_id)
        except Exception as e:
            logger.error(f'❌ Legacy coinflip error: {str(e)}')
            return jsonify({'success': False, 'error': 'Coinflip failed'})

    @gambling_bp.route('/api/gambling/dice', methods=['POST'])
    @require_auth
    def play_dice_legacy():
        """Legacy dice route"""
        try:
            data = request.json or {}
            user_id = data.get('userId', 'bradf')  # Default from your frontend
            server_id = data.get('serverId', 'default_server')
            
            # Call the server-specific function
            return play_dice_server(user_id, server_id)
        except Exception as e:
            logger.error(f'❌ Legacy dice error: {str(e)}')
            return jsonify({'success': False, 'error': 'Dice game failed'})

    return gambling_bp

# Helper functions for gambling system
def calculate_slot_winnings(result, bet_amount):
    '''Calculate slot machine winnings based on result'''
    # Count matching symbols
    symbol_counts = {}
    for symbol in result:
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
    
    max_count = max(symbol_counts.values())
    
    # Payout multipliers
    if max_count == 3:  # Three of a kind
        if '💎' in result:
            return bet_amount * 50  # Diamond jackpot
        elif '7️⃣' in result:
            return bet_amount * 25  # Lucky seven
        elif '⭐' in result:
            return bet_amount * 15  # Star bonus
        else:
            return bet_amount * 10  # Regular three of a kind
    elif max_count == 2:  # Two of a kind
        return bet_amount * 3
    else:
        return 0  # No win

def update_gambling_stats(user_id, server_id, bet_amount, winnings, game_type, db, user_storage):
    '''Update gambling statistics for user on server'''
    try:
        timestamp = datetime.now().isoformat()
        
        if db:
            # Update gambling stats in database
            update_data = {
                f'servers.{server_id}.gamblingStats.totalWagered': bet_amount,
                f'servers.{server_id}.gamblingStats.totalWon': winnings,
                f'servers.{server_id}.gamblingStats.gamesPlayed': 1,
                f'servers.{server_id}.gamblingStats.lastPlayed': timestamp
            }
            
            # Update biggest win if applicable
            if winnings > 0:
                user = db.users.find_one({'userId': user_id})
                if user and server_id in user.get('servers', {}):
                    current_biggest = user['servers'][server_id]['gamblingStats'].get('biggestWin', 0)
                    if winnings > current_biggest:
                        update_data[f'servers.{server_id}.gamblingStats.biggestWin'] = winnings
            
            db.users.update_one(
                {'userId': user_id},
                {'$inc': {k: v for k, v in update_data.items() if k != f'servers.{server_id}.gamblingStats.lastPlayed' and k != f'servers.{server_id}.gamblingStats.biggestWin'},
                 '$set': {k: v for k, v in update_data.items() if k == f'servers.{server_id}.gamblingStats.lastPlayed' or k == f'servers.{server_id}.gamblingStats.biggestWin'}}
            )
        else:
            # Update in-memory storage
            user = user_storage.get(user_id)
            if user and server_id in user.get('servers', {}):
                stats = user['servers'][server_id]['gamblingStats']
                stats['totalWagered'] += bet_amount
                stats['totalWon'] += winnings
                stats['gamesPlayed'] += 1
                stats['lastPlayed'] = timestamp
                
                if winnings > stats.get('biggestWin', 0):
                    stats['biggestWin'] = winnings
        
        logger.info(f'📊 Updated gambling stats for {user_id} on {server_id}')
        
    except Exception as e:
        logger.error(f'❌ Error updating gambling stats: {e}')

def log_gambling_game(user_id, server_id, game_type, bet_amount, winnings, game_data, db, user_storage):
    '''Log gambling game for audit trail'''
    try:
        game_log = {
            'gameId': str(uuid.uuid4()),
            'userId': user_id,
            'serverId': server_id,
            'gameType': game_type,
            'betAmount': bet_amount,
            'winnings': winnings,
            'netChange': winnings - bet_amount,
            'gameData': game_data,
            'timestamp': datetime.now().isoformat()
        }
        
        if db:
            db.gambling_logs.insert_one(game_log)
        else:
            # For in-memory storage, append to user data
            user = user_storage.get(user_id)
            if user:
                if 'gamblingHistory' not in user:
                    user['gamblingHistory'] = []
                user['gamblingHistory'].append(game_log)
                # Keep only last 100 games
                user['gamblingHistory'] = user['gamblingHistory'][-100:]
        
        logger.info(f'📝 Logged gambling game: {game_type} for {user_id} on {server_id}')
        
    except Exception as e:
        logger.error(f'❌ Error logging gambling game: {e}')

def get_user_gambling_history(user_id, server_id, db, user_storage, limit=20, game_type='all'):
    '''Get user's gambling history for specific server'''
    try:
        if db:
            query = {'userId': user_id, 'serverId': server_id}
            if game_type != 'all':
                query['gameType'] = game_type
            
            games = list(db.gambling_logs.find(query).sort('timestamp', -1).limit(limit))
            
            # Remove MongoDB ObjectId for JSON serialization
            for game in games:
                if '_id' in game:
                    del game['_id']
        else:
            user = user_storage.get(user_id, {})
            all_games = user.get('gamblingHistory', [])
            server_games = [g for g in all_games if g.get('serverId') == server_id]
            
            if game_type != 'all':
                server_games = [g for g in server_games if g.get('gameType') == game_type]
            
            server_games.sort(key=lambda x: x['timestamp'], reverse=True)
            games = server_games[:limit]
        
        return games
        
    except Exception as e:
        logger.error(f'❌ Error getting gambling history: {e}')
        return []

def get_user_gambling_stats(user_id, server_id, db, user_storage):
    '''Get gambling statistics for user on server'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and 'servers' in user and server_id in user['servers']:
            return user['servers'][server_id].get('gamblingStats', {
                'totalWagered': 0,
                'totalWon': 0,
                'gamesPlayed': 0,
                'biggestWin': 0,
                'lastPlayed': None
            })
        
        return {
            'totalWagered': 0,
            'totalWon': 0,
            'gamesPlayed': 0,
            'biggestWin': 0,
            'lastPlayed': None
        }
        
    except Exception as e:
        logger.error(f'❌ Error getting gambling stats: {e}')
        return {
            'totalWagered': 0,
            'totalWon': 0,
            'gamesPlayed': 0,
            'biggestWin': 0,
            'lastPlayed': None
        }

def get_server_gambling_leaderboard(server_id, db, user_storage, limit=10, period='all'):
    '''Get gambling leaderboard for specific server'''
    try:
        users = get_users_on_server(server_id, db, user_storage)
        
        # Add gambling stats to each user
        leaderboard_users = []
        for user in users:
            stats = get_user_gambling_stats(user['userId'], server_id, db, user_storage)
            if stats['gamesPlayed'] > 0:  # Only include users who have gambled
                leaderboard_users.append({
                    'userId': user['userId'],
                    'nickname': user['nickname'],
                    'totalWagered': stats['totalWagered'],
                    'totalWon': stats['totalWon'],
                    'gamesPlayed': stats['gamesPlayed'],
                    'biggestWin': stats['biggestWin'],
                    'netProfit': stats['totalWon'] - stats['totalWagered'],
                    'winRate': round((stats['totalWon'] / stats['totalWagered']) * 100, 2) if stats['totalWagered'] > 0 else 0
                })
        
        # Sort by total winnings (descending)
        leaderboard_users.sort(key=lambda x: x['totalWon'], reverse=True)
        
        # Add rank
        for i, user in enumerate(leaderboard_users[:limit], 1):
            user['rank'] = i
        
        return leaderboard_users[:limit]
        
    except Exception as e:
        logger.error(f'❌ Error getting gambling leaderboard: {e}')
        return []

