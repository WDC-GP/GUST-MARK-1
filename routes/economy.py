"""
GUST Bot Enhanced - Economy Routes (REFACTORED)
==============================================
Server-specific economy system using user database
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

from routes.auth import require_auth
from utils.user_helpers import (
    get_user_profile, get_server_balance, set_server_balance, 
    adjust_server_balance, get_users_on_server, get_server_leaderboard,
    transfer_between_users, ensure_user_on_server, get_user_display_name
)
import logging

logger = logging.getLogger(__name__)

economy_bp = Blueprint('economy', __name__)

def init_economy_routes(app, db, user_storage):
    '''Initialize economy routes with server-specific functionality'''
    
    @economy_bp.route('/api/economy/balance/<user_id>/<server_id>')
    @require_auth
    def get_user_balance_server(user_id, server_id):
        '''Get user's balance for specific server'''
        try:
            # Ensure user exists on server
            ensure_user_on_server(user_id, server_id, db, user_storage)
            
            balance = get_server_balance(user_id, server_id, db, user_storage)
            display_name = get_user_display_name(user_id, db, user_storage)
            
            logger.info(f'💰 Balance check: {user_id} on {server_id}: {balance}')
            return jsonify({
                'success': True,
                'balance': balance,
                'userId': user_id,
                'serverId': server_id,
                'displayName': display_name
            })
            
        except Exception as e:
            logger.error(f'❌ Balance check error: {str(e)}')
            return jsonify({'success': False, 'error': 'Balance check failed'})
    
    @economy_bp.route('/api/economy/set-balance/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def set_user_balance_server(user_id, server_id):
        '''Set user's balance for specific server (admin only)'''
        try:
            data = request.json
            new_balance = data.get('balance', 0)
            
            if new_balance < 0:
                return jsonify({'success': False, 'error': 'Balance cannot be negative'})
            
            # Ensure user exists on server
            ensure_user_on_server(user_id, server_id, db, user_storage)
            
            # Set balance
            if set_server_balance(user_id, server_id, new_balance, db, user_storage):
                logger.info(f'💰 Balance set: {user_id} on {server_id}: {new_balance}')
                return jsonify({
                    'success': True,
                    'message': 'Balance updated successfully',
                    'newBalance': new_balance
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to update balance'})
            
        except Exception as e:
            logger.error(f'❌ Set balance error: {str(e)}')
            return jsonify({'success': False, 'error': 'Balance update failed'})
    
    @economy_bp.route('/api/economy/adjust-balance/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def adjust_user_balance_server(user_id, server_id):
        '''Adjust user's balance for specific server (add/subtract)'''
        try:
            data = request.json
            amount = data.get('amount', 0)
            reason = data.get('reason', 'Manual adjustment')
            
            if amount == 0:
                return jsonify({'success': False, 'error': 'Amount cannot be zero'})
            
            # Ensure user exists on server
            ensure_user_on_server(user_id, server_id, db, user_storage)
            
            # Get current balance
            current_balance = get_server_balance(user_id, server_id, db, user_storage)
            
            # Adjust balance
            if adjust_server_balance(user_id, server_id, amount, db, user_storage):
                new_balance = get_server_balance(user_id, server_id, db, user_storage)
                
                # Log transaction
                log_transaction(user_id, server_id, amount, reason, current_balance, new_balance, db, user_storage)
                
                logger.info(f'💰 Balance adjusted: {user_id} on {server_id}: {current_balance} → {new_balance} ({amount:+})')
                return jsonify({
                    'success': True,
                    'message': 'Balance adjusted successfully',
                    'previousBalance': current_balance,
                    'newBalance': new_balance,
                    'adjustment': amount
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to adjust balance'})
            
        except Exception as e:
            logger.error(f'❌ Adjust balance error: {str(e)}')
            return jsonify({'success': False, 'error': 'Balance adjustment failed'})
    
    @economy_bp.route('/api/economy/transfer/<server_id>', methods=['POST'])
    @require_auth
    def transfer_coins_server(server_id):
        '''Transfer coins between users on same server'''
        try:
            data = request.json
            from_user_id = data.get('fromUserId', '').strip()
            to_user_id = data.get('toUserId', '').strip()
            amount = data.get('amount', 0)
            
            if not from_user_id or not to_user_id:
                return jsonify({'success': False, 'error': 'Both user IDs required'})
            
            if amount <= 0:
                return jsonify({'success': False, 'error': 'Amount must be positive'})
            
            if from_user_id == to_user_id:
                return jsonify({'success': False, 'error': 'Cannot transfer to yourself'})
            
            # Ensure both users exist on server
            ensure_user_on_server(from_user_id, server_id, db, user_storage)
            ensure_user_on_server(to_user_id, server_id, db, user_storage)
            
            # Perform transfer
            success, message = transfer_between_users(from_user_id, to_user_id, amount, server_id, db, user_storage)
            
            if success:
                # Log transfer transactions
                log_transaction(from_user_id, server_id, -amount, f'Transfer to {to_user_id}', 
                              get_server_balance(from_user_id, server_id, db, user_storage) + amount,
                              get_server_balance(from_user_id, server_id, db, user_storage), db, user_storage)
                              
                log_transaction(to_user_id, server_id, amount, f'Transfer from {from_user_id}',
                              get_server_balance(to_user_id, server_id, db, user_storage) - amount,
                              get_server_balance(to_user_id, server_id, db, user_storage), db, user_storage)
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'fromUser': from_user_id,
                    'toUser': to_user_id,
                    'amount': amount,
                    'serverId': server_id
                })
            else:
                return jsonify({'success': False, 'error': message})
            
        except Exception as e:
            logger.error(f'❌ Transfer error: {str(e)}')
            return jsonify({'success': False, 'error': 'Transfer failed'})
    
    @economy_bp.route('/api/economy/leaderboard/<server_id>')
    @require_auth
    def get_economy_leaderboard_server(server_id):
        '''Get economy leaderboard for specific server'''
        try:
            limit = request.args.get('limit', 10, type=int)
            limit = min(max(limit, 1), 50)  # Between 1 and 50
            
            leaderboard = get_server_leaderboard(server_id, db, user_storage, limit)
            
            # Format leaderboard
            formatted_leaderboard = []
            for i, user in enumerate(leaderboard, 1):
                formatted_leaderboard.append({
                    'rank': i,
                    'userId': user['userId'],
                    'nickname': user['nickname'],
                    'balance': user['balance'],
                    'clanTag': user['clanTag']
                })
            
            return jsonify({
                'success': True,
                'leaderboard': formatted_leaderboard,
                'serverId': server_id,
                'totalUsers': len(formatted_leaderboard)
            })
            
        except Exception as e:
            logger.error(f'❌ Leaderboard error: {str(e)}')
            return jsonify({'success': False, 'error': 'Leaderboard retrieval failed'})
    
    @economy_bp.route('/api/economy/transactions/<user_id>/<server_id>')
    @require_auth
    def get_user_transactions_server(user_id, server_id):
        '''Get user's transaction history for specific server'''
        try:
            limit = request.args.get('limit', 20, type=int)
            limit = min(max(limit, 1), 100)  # Between 1 and 100
            
            transactions = get_user_transactions(user_id, server_id, db, user_storage, limit)
            
            return jsonify({
                'success': True,
                'transactions': transactions,
                'userId': user_id,
                'serverId': server_id,
                'totalTransactions': len(transactions)
            })
            
        except Exception as e:
            logger.error(f'❌ Transaction history error: {str(e)}')
            return jsonify({'success': False, 'error': 'Transaction history retrieval failed'})
    
    @economy_bp.route('/api/economy/server-stats/<server_id>')
    @require_auth
    def get_server_economy_stats(server_id):
        '''Get economy statistics for specific server'''
        try:
            users_on_server = get_users_on_server(server_id, db, user_storage)
            
            total_users = len(users_on_server)
            total_balance = sum(user['balance'] for user in users_on_server)
            average_balance = total_balance / total_users if total_users > 0 else 0
            
            # Get highest and lowest balances
            if users_on_server:
                highest_balance = max(user['balance'] for user in users_on_server)
                lowest_balance = min(user['balance'] for user in users_on_server)
                richest_user = next(user for user in users_on_server if user['balance'] == highest_balance)
            else:
                highest_balance = lowest_balance = 0
                richest_user = None
            
            stats = {
                'serverId': server_id,
                'totalUsers': total_users,
                'totalBalance': total_balance,
                'averageBalance': round(average_balance, 2),
                'highestBalance': highest_balance,
                'lowestBalance': lowest_balance,
                'richestUser': richest_user['nickname'] if richest_user else None
            }
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f'❌ Server stats error: {str(e)}')
            return jsonify({'success': False, 'error': 'Server stats retrieval failed'})

# Helper functions
    return economy_bp

def log_transaction(user_id, server_id, amount, reason, old_balance, new_balance, db, user_storage):
    '''Log a transaction for audit trail'''
    try:
        transaction = {
            'transactionId': str(uuid.uuid4()),
            'userId': user_id,
            'serverId': server_id,
            'amount': amount,
            'reason': reason,
            'oldBalance': old_balance,
            'newBalance': new_balance,
            'timestamp': datetime.now().isoformat()
        }
        
        if db:
            db.transactions.insert_one(transaction)
        else:
            # For in-memory storage, append to user data
            user = user_storage.get(user_id)
            if user:
                if 'transactionHistory' not in user:
                    user['transactionHistory'] = []
                user['transactionHistory'].append(transaction)
                # Keep only last 100 transactions
                user['transactionHistory'] = user['transactionHistory'][-100:]
        
        logger.info(f'📝 Transaction logged: {user_id} on {server_id}: {amount} ({reason})')
        
    except Exception as e:
        logger.error(f'❌ Transaction logging error: {str(e)}')

def get_user_transactions(user_id, server_id, db, user_storage, limit=20):
    '''Get user's transaction history'''
    try:
        if db:
            transactions = list(db.transactions.find(
                {'userId': user_id, 'serverId': server_id}
            ).sort('timestamp', -1).limit(limit))
            
            # Remove MongoDB ObjectId for JSON serialization
            for transaction in transactions:
                if '_id' in transaction:
                    del transaction['_id']
        else:
            user = user_storage.get(user_id, {})
            all_transactions = user.get('transactionHistory', [])
            server_transactions = [t for t in all_transactions if t.get('serverId') == server_id]
            server_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
            transactions = server_transactions[:limit]
        
        return transactions
        
    except Exception as e:
        logger.error(f'❌ Get transactions error: {str(e)}')
        return []


    print('🔧 DEBUG: About to return economy_bp from init_economy_routes')

