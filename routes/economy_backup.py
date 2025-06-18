"""
GUST Bot Enhanced - Economy System Routes
========================================
Routes for economy management and transactions
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

from routes.auth import require_auth
import logging

logger = logging.getLogger(__name__)

economy_bp = Blueprint('economy', __name__)

def init_economy_routes(app, db, economy_storage):
    """
    Initialize economy routes with dependencies
    
    Args:
        app: Flask app instance
        db: Database connection (optional)
        economy_storage: In-memory economy storage
    """
    
    @economy_bp.route('/api/economy/balance/<user_id>')
    @require_auth
    def get_user_balance(user_id):
        """Get user's economy balance"""
        try:
            if db:
                user = db.economy.find_one({'userId': user_id})
                balance = user.get('balance', 0) if user else 0
            else:
                balance = economy_storage.get(user_id, 0)
            
            logger.info(f"💰 Balance check for {user_id}: {balance}")
            return jsonify({'balance': balance, 'userId': user_id})
            
        except Exception as e:
            logger.error(f"❌ Error getting balance for {user_id}: {e}")
            return jsonify({'error': 'Failed to get balance'}), 500
    
    @economy_bp.route('/api/economy/transfer', methods=['POST'])
    @require_auth
    def transfer_coins():
        """Transfer coins between users"""
        try:
            data = request.json
            from_user = data.get('fromUserId', '').strip()
            to_user = data.get('toUserId', '').strip()
            amount = data.get('amount', 0)
            
            if not from_user or not to_user:
                return jsonify({'success': False, 'error': 'Both user IDs are required'})
            
            if amount <= 0:
                return jsonify({'success': False, 'error': 'Amount must be greater than 0'})
            
            if from_user == to_user:
                return jsonify({'success': False, 'error': 'Cannot transfer to yourself'})
            
            # Perform transfer
            result = transfer_coins_internal(from_user, to_user, amount, db, economy_storage)
            
            if result['success']:
                logger.info(f"💸 Transfer successful: {from_user} -> {to_user}, amount: {amount}")
                
                # Log the transaction
                transaction = {
                    'transactionId': str(uuid.uuid4()),
                    'type': 'transfer',
                    'fromUserId': from_user,
                    'toUserId': to_user,
                    'amount': amount,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'completed'
                }
                
                if db:
                    db.transactions.insert_one(transaction)
                
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Error in coin transfer: {e}")
            return jsonify({'success': False, 'error': 'Transfer failed'}), 500
    
    @economy_bp.route('/api/economy/add-coins', methods=['POST'])
    @require_auth
    def add_coins():
        """Add coins to user account (admin function)"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            amount = data.get('amount', 0)
            reason = data.get('reason', 'Admin addition')
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID is required'})
            
            if amount <= 0:
                return jsonify({'success': False, 'error': 'Amount must be greater than 0'})
            
            # Add coins
            if db:
                db.economy.update_one(
                    {'userId': user_id},
                    {'$inc': {'balance': amount}},
                    upsert=True
                )
                # Get new balance
                user = db.economy.find_one({'userId': user_id})
                new_balance = user.get('balance', 0) if user else 0
            else:
                economy_storage[user_id] = economy_storage.get(user_id, 0) + amount
                new_balance = economy_storage[user_id]
            
            logger.info(f"💰 Added {amount} coins to {user_id}, new balance: {new_balance}")
            
            # Log the transaction
            transaction = {
                'transactionId': str(uuid.uuid4()),
                'type': 'admin_add',
                'userId': user_id,
                'amount': amount,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            if db:
                db.transactions.insert_one(transaction)
            
            return jsonify({
                'success': True,
                'newBalance': new_balance,
                'amountAdded': amount
            })
            
        except Exception as e:
            logger.error(f"❌ Error adding coins: {e}")
            return jsonify({'success': False, 'error': 'Failed to add coins'}), 500
    
    @economy_bp.route('/api/economy/remove-coins', methods=['POST'])
    @require_auth
    def remove_coins():
        """Remove coins from user account (admin function)"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            amount = data.get('amount', 0)
            reason = data.get('reason', 'Admin removal')
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID is required'})
            
            if amount <= 0:
                return jsonify({'success': False, 'error': 'Amount must be greater than 0'})
            
            # Check current balance
            if db:
                user = db.economy.find_one({'userId': user_id})
                current_balance = user.get('balance', 0) if user else 0
            else:
                current_balance = economy_storage.get(user_id, 0)
            
            if current_balance < amount:
                return jsonify({'success': False, 'error': 'Insufficient balance'})
            
            # Remove coins
            if db:
                db.economy.update_one(
                    {'userId': user_id},
                    {'$inc': {'balance': -amount}}
                )
                # Get new balance
                user = db.economy.find_one({'userId': user_id})
                new_balance = user.get('balance', 0) if user else 0
            else:
                economy_storage[user_id] = economy_storage.get(user_id, 0) - amount
                new_balance = economy_storage[user_id]
            
            logger.info(f"💸 Removed {amount} coins from {user_id}, new balance: {new_balance}")
            
            # Log the transaction
            transaction = {
                'transactionId': str(uuid.uuid4()),
                'type': 'admin_remove',
                'userId': user_id,
                'amount': amount,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            if db:
                db.transactions.insert_one(transaction)
            
            return jsonify({
                'success': True,
                'newBalance': new_balance,
                'amountRemoved': amount
            })
            
        except Exception as e:
            logger.error(f"❌ Error removing coins: {e}")
            return jsonify({'success': False, 'error': 'Failed to remove coins'}), 500
    
    @economy_bp.route('/api/economy/transactions/<user_id>')
    @require_auth
    def get_user_transactions(user_id):
        """Get transaction history for a user"""
        try:
            limit = int(request.args.get('limit', 50))
            
            transactions = []
            if db:
                # Get transactions where user is involved
                cursor = db.transactions.find({
                    '$or': [
                        {'userId': user_id},
                        {'fromUserId': user_id},
                        {'toUserId': user_id}
                    ]
                }).sort('timestamp', -1).limit(limit)
                
                transactions = list(cursor)
                # Remove MongoDB _id field
                for tx in transactions:
                    tx.pop('_id', None)
            
            logger.info(f"📊 Retrieved {len(transactions)} transactions for {user_id}")
            return jsonify(transactions)
            
        except Exception as e:
            logger.error(f"❌ Error getting transactions for {user_id}: {e}")
            return jsonify({'error': 'Failed to get transactions'}), 500
    
    @economy_bp.route('/api/economy/leaderboard')
    @require_auth
    def get_leaderboard():
        """Get economy leaderboard"""
        try:
            limit = int(request.args.get('limit', 10))
            
            leaderboard = []
            if db:
                cursor = db.economy.find({}).sort('balance', -1).limit(limit)
                leaderboard = list(cursor)
                # Remove MongoDB _id field
                for user in leaderboard:
                    user.pop('_id', None)
            else:
                # Sort in-memory storage
                sorted_users = sorted(economy_storage.items(), key=lambda x: x[1], reverse=True)
                leaderboard = [{'userId': user_id, 'balance': balance} 
                             for user_id, balance in sorted_users[:limit]]
            
            logger.info(f"🏆 Retrieved leaderboard with {len(leaderboard)} users")
            return jsonify(leaderboard)
            
        except Exception as e:
            logger.error(f"❌ Error getting leaderboard: {e}")
            return jsonify({'error': 'Failed to get leaderboard'}), 500
    
    @economy_bp.route('/api/economy/stats')
    @require_auth
    def get_economy_stats():
        """Get economy system statistics"""
        try:
            stats = {
                'total_users': 0,
                'total_coins': 0,
                'average_balance': 0,
                'richest_user': None,
                'total_transactions': 0
            }
            
            if db:
                # Get user statistics
                pipeline = [
                    {
                        '$group': {
                            '_id': None,
                            'total_users': {'$sum': 1},
                            'total_coins': {'$sum': '$balance'},
                            'average_balance': {'$avg': '$balance'},
                            'max_balance': {'$max': '$balance'}
                        }
                    }
                ]
                
                result = list(db.economy.aggregate(pipeline))
                if result:
                    data = result[0]
                    stats['total_users'] = data.get('total_users', 0)
                    stats['total_coins'] = data.get('total_coins', 0)
                    stats['average_balance'] = round(data.get('average_balance', 0), 2)
                    
                    # Find richest user
                    richest = db.economy.find_one({}, sort=[('balance', -1)])
                    if richest:
                        stats['richest_user'] = {
                            'userId': richest['userId'],
                            'balance': richest['balance']
                        }
                
                # Get transaction count
                stats['total_transactions'] = db.transactions.count_documents({})
                
            else:
                # Calculate from in-memory storage
                if economy_storage:
                    balances = list(economy_storage.values())
                    stats['total_users'] = len(economy_storage)
                    stats['total_coins'] = sum(balances)
                    stats['average_balance'] = round(stats['total_coins'] / stats['total_users'], 2)
                    
                    # Find richest user
                    richest_user_id = max(economy_storage, key=economy_storage.get)
                    stats['richest_user'] = {
                        'userId': richest_user_id,
                        'balance': economy_storage[richest_user_id]
                    }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"❌ Error getting economy stats: {e}")
            return jsonify({'error': 'Failed to get economy statistics'}), 500
    
    return economy_bp

def transfer_coins_internal(from_user, to_user, amount, db, economy_storage):
    """
    Internal function to transfer coins between users
    
    Args:
        from_user (str): Source user ID
        to_user (str): Destination user ID
        amount (int): Amount to transfer
        db: Database connection
        economy_storage: In-memory storage
        
    Returns:
        dict: Transfer result
    """
    try:
        if db:
            # Check sender balance
            sender = db.economy.find_one({'userId': from_user})
            sender_balance = sender.get('balance', 0) if sender else 0
            
            if sender_balance < amount:
                return {'success': False, 'error': 'Insufficient balance'}
            
            # Perform transfer
            db.economy.update_one(
                {'userId': from_user},
                {'$inc': {'balance': -amount}},
                upsert=True
            )
            
            db.economy.update_one(
                {'userId': to_user},
                {'$inc': {'balance': amount}},
                upsert=True
            )
            
            # Get new balances
            sender = db.economy.find_one({'userId': from_user})
            receiver = db.economy.find_one({'userId': to_user})
            
            return {
                'success': True,
                'senderNewBalance': sender.get('balance', 0) if sender else 0,
                'receiverNewBalance': receiver.get('balance', 0) if receiver else 0
            }
            
        else:
            # In-memory demo mode
            sender_balance = economy_storage.get(from_user, 0)
            if sender_balance < amount:
                return {'success': False, 'error': 'Insufficient balance'}
            
            economy_storage[from_user] = sender_balance - amount
            economy_storage[to_user] = economy_storage.get(to_user, 0) + amount
            
            return {
                'success': True,
                'senderNewBalance': economy_storage[from_user],
                'receiverNewBalance': economy_storage[to_user]
            }
            
    except Exception as e:
        logger.error(f"❌ Internal transfer error: {e}")
        return {'success': False, 'error': 'Transfer failed'}
