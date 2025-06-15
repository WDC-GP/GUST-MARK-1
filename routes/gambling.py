"""
GUST Bot Enhanced - Gambling System Routes
==========================================
Routes for gambling games (slots, coinflip, etc.)
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import secrets
import uuid

from routes.auth import require_auth
import logging

logger = logging.getLogger(__name__)

gambling_bp = Blueprint('gambling', __name__)

def init_gambling_routes(app, db, economy_storage):
    """
    Initialize gambling routes with dependencies
    
    Args:
        app: Flask app instance
        db: Database connection (optional)
        economy_storage: In-memory economy storage
    """
    
    @gambling_bp.route('/api/gambling/slots', methods=['POST'])
    @require_auth
    def play_slots():
        """Play slot machine"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            bet_amount = data.get('bet', 0)
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID is required'})
            
            if bet_amount <= 0:
                return jsonify({'success': False, 'error': 'Bet amount must be greater than 0'})
            
            # Check user balance
            if db:
                user = db.economy.find_one({'userId': user_id})
                current_balance = user.get('balance', 0) if user else 0
            else:
                current_balance = economy_storage.get(user_id, 0)
            
            if current_balance < bet_amount:
                return jsonify({'success': False, 'error': 'Insufficient balance'})
            
            # Generate slot results
            symbols = ['🍒', '🍋', '🔔', '⭐', '💎']
            result = [secrets.choice(symbols) for _ in range(3)]
            
            # Calculate winnings
            winnings = calculate_slot_winnings(result, bet_amount)
            
            # Update balance
            net_change = winnings - bet_amount
            new_balance = current_balance + net_change
            
            if db:
                db.economy.update_one(
                    {'userId': user_id},
                    {'$set': {'balance': new_balance}},
                    upsert=True
                )
            else:
                economy_storage[user_id] = new_balance
            
            # Log the game
            game_log = {
                'gameId': str(uuid.uuid4()),
                'type': 'slots',
                'userId': user_id,
                'bet': bet_amount,
                'result': result,
                'winnings': winnings,
                'net_change': net_change,
                'timestamp': datetime.now().isoformat()
            }
            
            if db:
                db.gambling_logs.insert_one(game_log)
            
            logger.info(f"🎰 Slots: {user_id} bet {bet_amount}, result {result}, winnings {winnings}")
            
            return jsonify({
                'success': True,
                'result': result,
                'winnings': winnings,
                'net_change': net_change,
                'new_balance': new_balance,
                'bet_amount': bet_amount
            })
            
        except Exception as e:
            logger.error(f"❌ Error in slots game: {e}")
            return jsonify({'success': False, 'error': 'Slots game failed'}), 500
    
    @gambling_bp.route('/api/gambling/coinflip', methods=['POST'])
    @require_auth
    def play_coinflip():
        """Play coinflip game"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            bet_amount = data.get('amount', 0)
            choice = data.get('choice', 'heads').lower()
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID is required'})
            
            if bet_amount <= 0:
                return jsonify({'success': False, 'error': 'Bet amount must be greater than 0'})
            
            if choice not in ['heads', 'tails']:
                return jsonify({'success': False, 'error': 'Choice must be heads or tails'})
            
            # Check user balance
            if db:
                user = db.economy.find_one({'userId': user_id})
                current_balance = user.get('balance', 0) if user else 0
            else:
                current_balance = economy_storage.get(user_id, 0)
            
            if current_balance < bet_amount:
                return jsonify({'success': False, 'error': 'Insufficient balance'})
            
            # Flip the coin
            result = secrets.choice(['heads', 'tails'])
            won = result == choice
            
            # Calculate net change
            net_change = bet_amount if won else -bet_amount
            new_balance = current_balance + net_change
            
            # Update balance
            if db:
                db.economy.update_one(
                    {'userId': user_id},
                    {'$set': {'balance': new_balance}},
                    upsert=True
                )
            else:
                economy_storage[user_id] = new_balance
            
            # Log the game
            game_log = {
                'gameId': str(uuid.uuid4()),
                'type': 'coinflip',
                'userId': user_id,
                'bet': bet_amount,
                'choice': choice,
                'result': result,
                'won': won,
                'net_change': net_change,
                'timestamp': datetime.now().isoformat()
            }
            
            if db:
                db.gambling_logs.insert_one(game_log)
            
            logger.info(f"🪙 Coinflip: {user_id} bet {bet_amount} on {choice}, result {result}, won: {won}")
            
            return jsonify({
                'success': True,
                'result': result,
                'choice': choice,
                'won': won,
                'net_change': net_change,
                'new_balance': new_balance,
                'bet_amount': bet_amount
            })
            
        except Exception as e:
            logger.error(f"❌ Error in coinflip game: {e}")
            return jsonify({'success': False, 'error': 'Coinflip game failed'}), 500
    
    @gambling_bp.route('/api/gambling/dice', methods=['POST'])
    @require_auth
    def play_dice():
        """Play dice game"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            bet_amount = data.get('amount', 0)
            prediction = data.get('prediction', 0)
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID is required'})
            
            if bet_amount <= 0:
                return jsonify({'success': False, 'error': 'Bet amount must be greater than 0'})
            
            if prediction < 1 or prediction > 6:
                return jsonify({'success': False, 'error': 'Prediction must be between 1 and 6'})
            
            # Check user balance
            if db:
                user = db.economy.find_one({'userId': user_id})
                current_balance = user.get('balance', 0) if user else 0
            else:
                current_balance = economy_storage.get(user_id, 0)
            
            if current_balance < bet_amount:
                return jsonify({'success': False, 'error': 'Insufficient balance'})
            
            # Roll the dice
            result = secrets.randbelow(6) + 1
            won = result == prediction
            
            # Calculate winnings (5x multiplier for exact prediction)
            if won:
                winnings = bet_amount * 5
                net_change = winnings - bet_amount
            else:
                winnings = 0
                net_change = -bet_amount
            
            new_balance = current_balance + net_change
            
            # Update balance
            if db:
                db.economy.update_one(
                    {'userId': user_id},
                    {'$set': {'balance': new_balance}},
                    upsert=True
                )
            else:
                economy_storage[user_id] = new_balance
            
            # Log the game
            game_log = {
                'gameId': str(uuid.uuid4()),
                'type': 'dice',
                'userId': user_id,
                'bet': bet_amount,
                'prediction': prediction,
                'result': result,
                'won': won,
                'winnings': winnings,
                'net_change': net_change,
                'timestamp': datetime.now().isoformat()
            }
            
            if db:
                db.gambling_logs.insert_one(game_log)
            
            logger.info(f"🎲 Dice: {user_id} bet {bet_amount}, predicted {prediction}, rolled {result}, won: {won}")
            
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
            
        except Exception as e:
            logger.error(f"❌ Error in dice game: {e}")
            return jsonify({'success': False, 'error': 'Dice game failed'}), 500
    
    @gambling_bp.route('/api/gambling/history/<user_id>')
    @require_auth
    def get_gambling_history(user_id):
        """Get gambling history for a user"""
        try:
            limit = int(request.args.get('limit', 20))
            game_type = request.args.get('type', 'all')
            
            history = []
            if db:
                query = {'userId': user_id}
                if game_type != 'all':
                    query['type'] = game_type
                
                cursor = db.gambling_logs.find(query).sort('timestamp', -1).limit(limit)
                history = list(cursor)
                
                # Remove MongoDB _id field
                for game in history:
                    game.pop('_id', None)
            
            logger.info(f"📊 Retrieved {len(history)} gambling records for {user_id}")
            return jsonify(history)
            
        except Exception as e:
            logger.error(f"❌ Error getting gambling history for {user_id}: {e}")
            return jsonify({'error': 'Failed to get gambling history'}), 500
    
    @gambling_bp.route('/api/gambling/stats/<user_id>')
    @require_auth
    def get_user_gambling_stats(user_id):
        """Get gambling statistics for a user"""
        try:
            stats = {
                'total_games': 0,
                'total_bet': 0,
                'total_winnings': 0,
                'net_profit': 0,
                'games_won': 0,
                'games_lost': 0,
                'win_rate': 0,
                'favorite_game': None,
                'biggest_win': 0,
                'biggest_loss': 0
            }
            
            if db:
                # Get all games for user
                games = list(db.gambling_logs.find({'userId': user_id}))
                
                if games:
                    stats['total_games'] = len(games)
                    stats['total_bet'] = sum(game.get('bet', 0) for game in games)
                    stats['total_winnings'] = sum(game.get('winnings', 0) for game in games)
                    stats['net_profit'] = sum(game.get('net_change', 0) for game in games)
                    
                    # Count wins/losses
                    for game in games:
                        if game.get('won', False) or game.get('net_change', 0) > 0:
                            stats['games_won'] += 1
                        else:
                            stats['games_lost'] += 1
                    
                    # Calculate win rate
                    if stats['total_games'] > 0:
                        stats['win_rate'] = round((stats['games_won'] / stats['total_games']) * 100, 2)
                    
                    # Find favorite game
                    game_counts = {}
                    for game in games:
                        game_type = game.get('type', 'unknown')
                        game_counts[game_type] = game_counts.get(game_type, 0) + 1
                    
                    if game_counts:
                        stats['favorite_game'] = max(game_counts, key=game_counts.get)
                    
                    # Find biggest win/loss
                    net_changes = [game.get('net_change', 0) for game in games]
                    if net_changes:
                        stats['biggest_win'] = max(net_changes)
                        stats['biggest_loss'] = min(net_changes)
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"❌ Error getting gambling stats for {user_id}: {e}")
            return jsonify({'error': 'Failed to get gambling statistics'}), 500
    
    @gambling_bp.route('/api/gambling/leaderboard')
    @require_auth
    def get_gambling_leaderboard():
        """Get gambling leaderboard"""
        try:
            limit = int(request.args.get('limit', 10))
            period = request.args.get('period', 'all')  # all, week, month
            
            leaderboard = []
            if db:
                # Build date filter if needed
                match_filter = {}
                if period != 'all':
                    from datetime import timedelta
                    if period == 'week':
                        cutoff = datetime.now() - timedelta(days=7)
                    elif period == 'month':
                        cutoff = datetime.now() - timedelta(days=30)
                    else:
                        cutoff = None
                    
                    if cutoff:
                        match_filter['timestamp'] = {'$gte': cutoff.isoformat()}
                
                # Aggregate gambling stats by user
                pipeline = [
                    {'$match': match_filter},
                    {
                        '$group': {
                            '_id': '$userId',
                            'total_profit': {'$sum': '$net_change'},
                            'total_games': {'$sum': 1},
                            'total_bet': {'$sum': '$bet'},
                            'games_won': {
                                '$sum': {
                                    '$cond': [{'$gt': ['$net_change', 0]}, 1, 0]
                                }
                            }
                        }
                    },
                    {
                        '$project': {
                            'userId': '$_id',
                            'total_profit': 1,
                            'total_games': 1,
                            'total_bet': 1,
                            'games_won': 1,
                            'win_rate': {
                                '$cond': [
                                    {'$gt': ['$total_games', 0]},
                                    {'$multiply': [{'$divide': ['$games_won', '$total_games']}, 100]},
                                    0
                                ]
                            }
                        }
                    },
                    {'$sort': {'total_profit': -1}},
                    {'$limit': limit}
                ]
                
                leaderboard = list(db.gambling_logs.aggregate(pipeline))
                
                # Clean up the data
                for entry in leaderboard:
                    entry.pop('_id', None)
                    entry['win_rate'] = round(entry.get('win_rate', 0), 2)
            
            logger.info(f"🏆 Retrieved gambling leaderboard with {len(leaderboard)} users")
            return jsonify(leaderboard)
            
        except Exception as e:
            logger.error(f"❌ Error getting gambling leaderboard: {e}")
            return jsonify({'error': 'Failed to get gambling leaderboard'}), 500
    
    return gambling_bp

def calculate_slot_winnings(result, bet_amount):
    """
    Calculate slot machine winnings based on result
    
    Args:
        result (list): List of 3 slot symbols
        bet_amount (int): Amount bet
        
    Returns:
        int: Winnings amount
    """
    # Check for three of a kind
    if result[0] == result[1] == result[2]:
        symbol = result[0]
        if symbol == '💎':
            return bet_amount * 10  # Diamond jackpot
        elif symbol == '⭐':
            return bet_amount * 5   # Star
        else:
            return bet_amount * 3   # Other symbols
    
    # Check for two of a kind
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        return bet_amount * 2
    
    # No match
    return 0
