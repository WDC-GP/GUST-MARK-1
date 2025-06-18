# GUST_BOT Development Environment Setup
# Run this after the project analysis

Write-Host "🚀 Setting up GUST_BOT development environment..." -ForegroundColor Green

# 1. CREATE DEVELOPMENT BRANCH
Write-Host "`n📂 Creating development branch..." -ForegroundColor Yellow
git init
git add .
git commit -m "Initial commit - backup before refactoring"
git branch -M main
git checkout -b feature/user-database-refactor

Write-Host "✅ Development branch created: feature/user-database-refactor" -ForegroundColor Green

# 2. CREATE DEVELOPMENT DIRECTORIES
Write-Host "`n📁 Creating development directories..." -ForegroundColor Yellow

$devDirs = @(
    "dev_tools",
    "migration_scripts", 
    "tests/unit",
    "tests/integration",
    "docs/architecture",
    "backup/schemas"
)

$devDirs | ForEach-Object {
    if (!(Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force
        Write-Host "  ✅ Created: $_"
    }
}

# 3. CREATE TESTING CONFIGURATION
Write-Host "`n⚙️ Creating testing configuration..." -ForegroundColor Yellow

$testConfig = @"
# Test Configuration for GUST_BOT Refactoring
# Copy this to your .env.test file

# Test Database Settings
MONGODB_TEST_URI=mongodb://localhost:27017/gust_bot_test
DEMO_MODE=True
DEBUG=True

# Test Server Settings
FLASK_ENV=testing
SECRET_KEY=test_secret_key_change_in_production

# Test Redis (if used)
REDIS_TEST_URL=redis://localhost:6379/1

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=tests/test.log
"@

$testConfig | Out-File "dev_tools/test.env" -Encoding UTF8
Write-Host "✅ Test configuration created: dev_tools/test.env" -ForegroundColor Green

# 4. CREATE DEVELOPMENT DATABASE SCHEMA
Write-Host "`n💾 Creating development database schema..." -ForegroundColor Yellow

$devSchema = @"
# Development Database Schema for User-Centric Architecture
# This is a prototype schema for testing

from datetime import datetime
from typing import Dict, List, Optional
import pymongo

class UserDatabaseSchema:
    '''
    Prototype schema for the new user-centric database
    Each user document contains all their server-specific data
    '''
    
    @staticmethod
    def create_user_document(user_id: str, nickname: str, internal_id: int) -> Dict:
        '''Create a new user document with default structure'''
        return {
            "userId": user_id,                    # G-Portal username (primary key)
            "nickname": nickname,                 # User-chosen display name
            "internalId": internal_id,            # Hidden admin ID (1-9 digits)
            "registeredAt": datetime.utcnow(),
            "lastSeen": datetime.utcnow(),
            "servers": {},                        # Server-specific data
            "preferences": {
                "displayNickname": True,
                "showInLeaderboards": True
            },
            "totalServers": 0
        }
    
    @staticmethod
    def create_server_entry(server_id: str, initial_balance: int = 1000) -> Dict:
        '''Create server-specific entry for a user'''
        return {
            "balance": initial_balance,
            "clanTag": None,
            "joinedAt": datetime.utcnow(),
            "gamblingStats": {
                "totalWagered": 0,
                "totalWon": 0,
                "gamesPlayed": 0,
                "biggestWin": 0
            },
            "isActive": True
        }
    
    @staticmethod
    def get_user_balance(user_doc: Dict, server_id: str) -> int:
        '''Get user balance for specific server'''
        if server_id not in user_doc.get("servers", {}):
            return 0
        return user_doc["servers"][server_id].get("balance", 0)
    
    @staticmethod
    def update_user_balance(user_doc: Dict, server_id: str, new_balance: int) -> Dict:
        '''Update user balance for specific server'''
        if "servers" not in user_doc:
            user_doc["servers"] = {}
        
        if server_id not in user_doc["servers"]:
            user_doc["servers"][server_id] = UserDatabaseSchema.create_server_entry(server_id, 0)
        
        user_doc["servers"][server_id]["balance"] = new_balance
        user_doc["lastSeen"] = datetime.utcnow()
        return user_doc

# Example usage and testing
if __name__ == "__main__":
    # Create sample user
    user = UserDatabaseSchema.create_user_document("test_user", "TestPlayer", 123456)
    
    # Add server data
    user["servers"]["server_001"] = UserDatabaseSchema.create_server_entry("server_001", 1500)
    user["servers"]["server_002"] = UserDatabaseSchema.create_server_entry("server_002", 800)
    user["totalServers"] = 2
    
    print("Sample User Document:")
    import json
    print(json.dumps(user, indent=2, default=str))
"@

$devSchema | Out-File "dev_tools/user_schema.py" -Encoding UTF8
Write-Host "✅ Development schema created: dev_tools/user_schema.py" -ForegroundColor Green

# 5. CREATE MIGRATION PLANNING SCRIPT
Write-Host "`n🔄 Creating migration planning tools..." -ForegroundColor Yellow

$migrationPlanner = @"
# GUST_BOT Migration Planning Script
# Analyzes current data and plans migration strategy

import json
from datetime import datetime
from typing import Dict, List

class MigrationPlanner:
    '''Plans the migration from global to server-specific data'''
    
    def __init__(self):
        self.current_collections = [
            "economy",      # Global balances - NEEDS MIGRATION
            "gambling_logs", # Global logs - NEEDS SERVER_ID
            "clans",        # Server-specific - NEEDS USER INTEGRATION
            "transactions"  # Global - NEEDS SERVER CONTEXT
        ]
    
    def analyze_economy_collection(self, economy_data: List[Dict]) -> Dict:
        '''Analyze current economy data for migration'''
        analysis = {
            "total_users": len(economy_data),
            "total_balance": sum(user.get("balance", 0) for user in economy_data),
            "users_with_balance": len([u for u in economy_data if u.get("balance", 0) > 0]),
            "max_balance": max((u.get("balance", 0) for u in economy_data), default=0),
            "migration_strategy": "CREATE_DEFAULT_SERVER_ENTRIES"
        }
        return analysis
    
    def plan_user_migration(self, user_id: str, current_balance: int, default_server: str = "server_001") -> Dict:
        '''Plan migration for a single user'''
        return {
            "userId": user_id,
            "currentBalance": current_balance,
            "migrationPlan": {
                "createUserDocument": True,
                "assignToServer": default_server,
                "preserveBalance": True,
                "generateInternalId": True
            }
        }
    
    def generate_migration_report(self) -> str:
        '''Generate migration planning report'''
        report = f'''
# GUST_BOT Migration Plan
Generated: {datetime.now()}

## Migration Strategy
1. Create new 'users' collection with server-specific structure
2. Migrate existing economy data to default server (server_001)
3. Add serverId field to gambling_logs
4. Integrate clan membership with user documents
5. Preserve all existing balances and transaction history

## Data Preservation
- All existing balances will be preserved
- Transaction history will be maintained with server context
- Gambling logs will be updated with server association
- Clan memberships will be integrated into user profiles

## Rollback Plan
- Complete backup of all collections before migration
- Migration script with rollback functionality
- Validation checks at each step
- Ability to restore from backup if needed

## Testing Strategy
- Test migration on copy of production data
- Validate all balances match after migration
- Test API endpoints with new structure
- Performance testing with new queries

## Timeline
- Phase 1: Schema design and testing (2-3 hours)
- Phase 2: Migration script development (3-4 hours)
- Phase 3: Testing and validation (2-3 hours)
- Phase 4: Production migration (1-2 hours)
'''
        return report

# Example usage
if __name__ == "__main__":
    planner = MigrationPlanner()
    report = planner.generate_migration_report()
    print(report)
"@

$migrationPlanner | Out-File "migration_scripts/migration_planner.py" -Encoding UTF8
Write-Host "✅ Migration planner created: migration_scripts/migration_planner.py" -ForegroundColor Green

# 6. CREATE TESTING FRAMEWORK
Write-Host "`n🧪 Creating testing framework..." -ForegroundColor Yellow

$testFramework = @"
# Basic testing framework for GUST_BOT refactoring
import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class TestUserDatabase(unittest.TestCase):
    '''Test cases for new user database functionality'''
    
    def setUp(self):
        '''Set up test environment'''
        self.test_user_id = "test_user"
        self.test_server_id = "server_001"
        self.test_balance = 1500
    
    def test_user_creation(self):
        '''Test user document creation'''
        # TODO: Implement user creation tests
        self.assertTrue(True, "User creation test placeholder")
    
    def test_server_balance(self):
        '''Test server-specific balance operations'''
        # TODO: Implement balance tests
        self.assertTrue(True, "Balance test placeholder")
    
    def test_clan_integration(self):
        '''Test clan tag integration with user database'''
        # TODO: Implement clan integration tests
        self.assertTrue(True, "Clan integration test placeholder")

class TestAPIEndpoints(unittest.TestCase):
    '''Test cases for refactored API endpoints'''
    
    def setUp(self):
        '''Set up test Flask app'''
        # TODO: Set up test Flask app
        pass
    
    def test_economy_endpoints(self):
        '''Test new economy API endpoints'''
        # TODO: Test /api/economy/balance/{userId}/{serverId}
        self.assertTrue(True, "Economy API test placeholder")
    
    def test_gambling_endpoints(self):
        '''Test new gambling API endpoints'''
        # TODO: Test /api/gambling/slots/{serverId}
        self.assertTrue(True, "Gambling API test placeholder")

if __name__ == '__main__':
    unittest.main()
"@

$testFramework | Out-File "tests/test_user_database.py" -Encoding UTF8
Write-Host "✅ Testing framework created: tests/test_user_database.py" -ForegroundColor Green

# 7. CREATE DOCUMENTATION TEMPLATE
Write-Host "`n📚 Creating documentation templates..." -ForegroundColor Yellow

$docTemplate = @"
# GUST_BOT Architecture Documentation

## Current Architecture Analysis

### Route Structure
- **Hybrid Approach**: Mix of blueprints and inline routes in app.py
- **Database Access**: Direct MongoDB access throughout codebase
- **WebSocket Integration**: Live console connections without server context

### Identified Issues
1. **Global Economy**: Balances shared across all servers
2. **Performance**: Multiple database queries per operation
3. **Scalability**: No server isolation framework
4. **Security**: Potential cross-server data access vulnerabilities

## Proposed Architecture

### New User Database Structure
```json
{
  "userId": "gportal_username",
  "nickname": "PlayerChoice", 
  "internalId": 123456789,
  "servers": {
    "server_001": {
      "balance": 1500,
      "clanTag": "CLAN",
      "gamblingStats": {...}
    }
  }
}
```

### API Changes
- Add server context to all endpoints
- Implement proper error handling
- Add request validation
- Implement rate limiting per server

## Implementation Timeline
- **Phase 1**: Analysis and Setup (Current)
- **Phase 2**: Database Schema Migration
- **Phase 3**: API Refactoring  
- **Phase 4**: Frontend Updates
- **Phase 5**: Testing and Deployment

## Risks and Mitigations
- **Data Loss**: Complete backup before migration
- **Downtime**: Blue-green deployment strategy
- **Performance**: Load testing with new architecture
- **Security**: Server isolation validation

## Success Metrics
- 75% reduction in database queries
- Sub-100ms API response times
- Zero cross-server data leakage
- 99.9% uptime during migration
"@

$docTemplate | Out-File "docs/architecture/ARCHITECTURE.md" -Encoding UTF8
Write-Host "✅ Documentation template created: docs/architecture/ARCHITECTURE.md" -ForegroundColor Green

Write-Host "`n🎉 Development environment setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Run the project analysis script" -ForegroundColor White
Write-Host "2. Review the generated reports" -ForegroundColor White  
Write-Host "3. Test the development schema" -ForegroundColor White
Write-Host "4. Plan your migration strategy" -ForegroundColor White