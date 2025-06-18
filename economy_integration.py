"""
Economy Integration Script
=========================
Integrate refactored economy with user database
"""

import sys
import os
sys.path.append('.')

from routes.economy import init_economy_routes, economy_bp
from routes.user_database import init_user_database_routes, user_database_bp
from utils.user_migration import UserDatabaseMigration
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def integrate_economy_with_user_database(app, db, user_storage, economy_storage):
    '''Integrate economy system with new user database'''
    
    logger.info('🔧 Starting economy integration...')
    
    # Initialize user database routes
    init_user_database_routes(app, db, user_storage)
    app.register_blueprint(user_database_bp)
    logger.info('✅ User database routes registered')
    
    # Initialize refactored economy routes
    init_economy_routes(app, db, user_storage)
    app.register_blueprint(economy_bp)
    logger.info('✅ Economy routes registered')
    
    logger.info('🎉 Economy integration completed successfully!')

def migrate_economy_data(db, user_storage, economy_storage, default_server_id='default_server'):
    '''Migrate existing economy data to user database'''
    
    logger.info('🔄 Starting economy data migration...')
    
    # Create migration instance
    migrator = UserDatabaseMigration(db, user_storage, economy_storage)
    
    # Create backup before migration
    backup_file = migrator.create_migration_backup()
    if backup_file:
        logger.info(f'✅ Migration backup created: {backup_file}')
    
    # Perform migration
    migration_report = migrator.migrate_existing_data(default_server_id)
    
    # Validate migration
    validation_report = migrator.validate_migration()
    
    logger.info('📊 Migration Report:')
    logger.info(f'  Users migrated: {migration_report["users_migrated"]}')
    logger.info(f'  Users failed: {migration_report["users_failed"]}')
    logger.info(f'  Clans processed: {migration_report["clans_processed"]}')
    
    if migration_report['errors']:
        logger.warning('⚠️ Migration errors:')
        for error in migration_report['errors']:
            logger.warning(f'  - {error}')
    
    logger.info('🧪 Validation Report:')
    logger.info(f'  New users: {validation_report.get("new_users", 0)}')
    logger.info(f'  Old economy records: {validation_report.get("old_economy_records", 0)}')
    logger.info(f'  Match: {"✅" if validation_report.get("match", False) else "❌"}')
    
    return migration_report, validation_report

def test_economy_integration():
    '''Test the economy integration'''
    
    logger.info('🧪 Testing economy integration...')
    
    # Test in-memory storage
    test_user_storage = {}
    test_economy_storage = {
        'test_user_1': 1500,
        'test_user_2': 2000,
        'test_user_3': 500
    }
    
    # Test migration
    migration_report, validation_report = migrate_economy_data(
        None, test_user_storage, test_economy_storage, 'test_server'
    )
    
    # Verify results
    success = (
        migration_report['users_migrated'] == 3 and
        migration_report['users_failed'] == 0 and
        len(test_user_storage) == 3
    )
    
    if success:
        logger.info('✅ Economy integration test passed!')
        
        # Test server-specific balance functions
        from utils.user_helpers import get_server_balance, set_server_balance
        
        # Test balance operations
        balance = get_server_balance('test_user_1', 'test_server', None, test_user_storage)
        logger.info(f'  Test balance retrieval: {balance} (expected: 1500)')
        
        set_result = set_server_balance('test_user_1', 'test_server', 2500, None, test_user_storage)
        new_balance = get_server_balance('test_user_1', 'test_server', None, test_user_storage)
        logger.info(f'  Test balance update: {new_balance} (expected: 2500)')
        
        if balance == 1500 and new_balance == 2500 and set_result:
            logger.info('✅ All integration tests passed!')
            return True
        else:
            logger.error('❌ Balance operation tests failed!')
            return False
    else:
        logger.error('❌ Economy integration test failed!')
        return False

if __name__ == "__main__":
    test_economy_integration()
