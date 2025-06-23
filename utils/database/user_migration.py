"""
"""
"""
User Database Migration Utilities
================================
Tools for migrating existing data to new user database structure
"""

# Standard library imports
from datetime import datetime
import logging
import random


# GUST database optimization imports
from utils.database.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor
)


logger = logging.getLogger(__name__)

def generate_internal_id():
    '''Generate unique 9-digit internal ID'''
    return random.randint(100000000, 999999999)

class UserDatabaseMigration:
    def __init__(self, db, user_storage, economy_storage):
        self.db = db
        self.user_storage = user_storage
        self.economy_storage = economy_storage
        self.migration_report = {
            'users_migrated': 0,
            'users_failed': 0,
            'clans_processed': 0,
            'errors': []
        }
    
    def migrate_existing_data(self, default_server_id='default_server'):
        '''Migrate all existing economy/gambling data to new user structure'''
        try:
            logger.info('ðŸ”„ Starting comprehensive data migration...')
            
            # Get existing economy data
            if self.db:
                economy_users = list(self.db.economy.find())
                existing_clans = list(self.db.clans.find())
                gambling_logs = list(self.db.gambling_logs.find()) if hasattr(self.db, 'gambling_logs') else []
            else:
                economy_users = [{'userId': uid, 'balance': bal} for uid, bal in self.economy_storage.items()]
                existing_clans = []
                gambling_logs = []
            
            logger.info(f'ðŸ“Š Found {len(economy_users)} economy users, {len(existing_clans)} clans')
            
            # Process each user
            for economy_record in economy_users:
                try:
                    user_id = economy_record['userId']
                    balance = economy_record.get('balance', 1000)
                    
                    # Find user's clan tag
                    clan_tag = self._find_user_clan_tag(user_id, existing_clans)
                    
                    # Calculate gambling stats
                    gambling_stats = self._calculate_gambling_stats(user_id, gambling_logs)
                    
                    # Create user document
                    user_data = {
                        'userId': user_id,
                        'nickname': user_id,  # Default to userId
                        'internalId': generate_internal_id(),
                        'registeredAt': datetime.now().isoformat(),
                        'lastSeen': datetime.now().isoformat(),
                        'servers': {
                            default_server_id: {
                                'balance': balance,
                                'clanTag': clan_tag,
                                'joinedAt': datetime.now().isoformat(),
                                'gamblingStats': gambling_stats,
                                'isActive': True
                            }
                        },
                        'preferences': {
                            'displayNickname': True,
                            'showInLeaderboards': True
                        },
                        'totalServers': 1
                    }
                    
                    # Save user
                    if self.db:
                        # Check if user already exists in new format
                        existing = self.db.users.find_one({'userId': user_id})
                        if existing:
                            logger.warning(f'âš ï¸ User {user_id} already exists in new format, skipping')
                            continue
                        
                        self.db.users.insert_one(user_data)
                    else:
                        self.user_storage[user_id] = user_data
                    
                    self.migration_report['users_migrated'] += 1
                    logger.info(f'âœ… Migrated user: {user_id} (balance: {balance}, clan: {clan_tag})')
                    
                except Exception as e:
                    self.migration_report['users_failed'] += 1
                    self.migration_report['errors'].append(f'User {user_id}: {str(e)}')
                    logger.error(f'âŒ Failed to migrate user {user_id}: {str(e)}')
            
            # Process clans for reporting
            self.migration_report['clans_processed'] = len(existing_clans)
            
            logger.info('âœ… Migration completed successfully')
            return self.migration_report
            
        except Exception as e:
            logger.error(f'âŒ Migration failed: {str(e)}')
            self.migration_report['errors'].append(f'Migration failed: {str(e)}')
            return self.migration_report
    
    def _find_user_clan_tag(self, user_id, clans):
        '''Find clan tag for user'''
        for clan in clans:
            if user_id in clan.get('members', []):
                clan_name = clan.get('name', '')
                # Create tag from clan name (first 4 chars, uppercase)
                if clan_name:
                    return clan_name[:4].upper()
        return None
    
    def _calculate_gambling_stats(self, user_id, gambling_logs):
        '''Calculate gambling statistics for user'''
        stats = {
            'totalWagered': 0,
            'totalWon': 0,
            'gamesPlayed': 0,
            'biggestWin': 0,
            'lastPlayed': None
        }
        
        user_logs = [log for log in gambling_logs if log.get('userId') == user_id]
        
        for log in user_logs:
            bet = log.get('bet', 0)
            winnings = log.get('winnings', 0)
            timestamp = log.get('timestamp')
            
            stats['totalWagered'] += bet
            stats['totalWon'] += winnings
            stats['gamesPlayed'] += 1
            
            if winnings > stats['biggestWin']:
                stats['biggestWin'] = winnings
            
            if timestamp and (not stats['lastPlayed'] or timestamp > stats['lastPlayed']):
                stats['lastPlayed'] = timestamp
        
        return stats
    
    def validate_migration(self):
        '''Validate that migration was successful'''
        try:
            logger.info('ðŸ§ª Validating migration...')
            
            if self.db:
                new_user_count = self.db.users.count_documents({})
                old_economy_count = self.db.economy.count_documents({})
            else:
                new_user_count = len(self.user_storage)
                old_economy_count = len(self.economy_storage)
            
            validation_report = {
                'new_users': new_user_count,
                'old_economy_records': old_economy_count,
                'match': new_user_count >= old_economy_count,
                'sample_users': []
            }
            
            # Sample a few users for validation
            if self.db:
                sample_users = list(self.db.users.find().limit(3))
            else:
                sample_users = list(self.user_storage.values())[:3]
            
            for user in sample_users:
                validation_report['sample_users'].append({
                    'userId': user['userId'],
                    'hasServers': bool(user.get('servers')),
                    'serverCount': len(user.get('servers', {})),
                    'hasBalance': any(server.get('balance', 0) > 0 for server in user.get('servers', {}).values())
                })
            
            logger.info(f'âœ… Validation complete: {new_user_count} users migrated')
            return validation_report
            
        except Exception as e:
            logger.error(f'âŒ Validation failed: {str(e)}')
            return {'error': str(e)}
    
    def create_migration_backup(self):
        '''Create backup of current data before migration'''
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'economy_data': [],
                'clan_data': [],
                'gambling_data': []
            }
            
            if self.db:
                backup_data['economy_data'] = list(self.db.economy.find())
                backup_data['clan_data'] = list(self.db.clans.find())
                if hasattr(self.db, 'gambling_logs'):
                    backup_data['gambling_data'] = list(self.db.gambling_logs.find())
            else:
                backup_data['economy_data'] = [{'userId': k, 'balance': v} for k, v in self.economy_storage.items()]
            
            # Save backup
            import json
            import os
            os.makedirs('migration_backups', exist_ok=True)
            backup_file = f'migration_backups/pre_migration_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f'âœ… Migration backup created: {backup_file}')
            return backup_file
            
        except Exception as e:
            logger.error(f'âŒ Backup creation failed: {str(e)}')
            return None

