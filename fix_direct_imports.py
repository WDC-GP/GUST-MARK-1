#!/usr/bin/env python3
"""
Fix Direct Import Statements in GUST Bot
========================================
Finds and fixes files that are importing from old utils paths.
"""

import os
import re
import glob

class ImportFixer:
    def __init__(self):
        self.import_fixes = {
            # Old import -> New import
            'from utils.core.rate_limiter import': 'from utils.core.rate_limiter import',
            'import utils.core.rate_limiter': 'import utils.core.rate_limiter',
            'utils.core.rate_limiter.': 'utils.core.rate_limiter.',
            
            'from utils.health.graphql_sensors import': 'from utils.health.graphql_sensors import',
            'import utils.health.graphql_sensors': 'import utils.health.graphql_sensors',
            'utils.health.graphql_sensors.': 'utils.health.graphql_sensors.',
            
            'from utils.core.error_handlers import': 'from utils.core.error_handlers import',
            'import utils.core.error_handlers': 'import utils.core.error_handlers',
            'utils.core.error_handlers.': 'utils.core.error_handlers.',
            
            'from utils.core.common_imports import': 'from utils.core.common_imports import',
            'import utils.core.common_imports': 'import utils.core.common_imports',
            'utils.core.common_imports.': 'utils.core.common_imports.',
            
            'from utils.health.server_health_storage import': 'from utils.health.server_health_storage import',
            'import utils.health.server_health_storage': 'import utils.health.server_health_storage',
            'utils.health.server_health_storage.': 'utils.health.server_health_storage.',
            
            'from utils.health.server_monitor import': 'from utils.health.server_monitor import',
            'import utils.health.server_monitor': 'import utils.health.server_monitor',
            'utils.health.server_monitor.': 'utils.health.server_monitor.',
            
            'from utils.auth.auth_decorators import': 'from utils.auth.auth_decorators import',
            'import utils.auth.auth_decorators': 'import utils.auth.auth_decorators',
            'utils.auth.auth_decorators.': 'utils.auth.auth_decorators.',
            
            'from utils.database.user_migration import': 'from utils.database.user_migration import',
            'import utils.database.user_migration': 'import utils.database.user_migration',
            'utils.database.user_migration.': 'utils.database.user_migration.',
            
            'from utils.database.gust_db_optimization import': 'from utils.database.gust_db_optimization import',
            'import utils.database.gust_db_optimization': 'import utils.database.gust_db_optimization',
            'utils.database.gust_db_optimization.': 'utils.database.gust_db_optimization.',
        }
        
        self.files_to_fix = []
        self.changes_made = []

    def find_problematic_files(self):
        """Find files with problematic imports"""
        
        print("🔍 Scanning for files with old import paths...")
        print("=" * 60)
        
        # Get all Python files
        python_files = []
        for root, dirs, files in os.walk('.'):
            # Skip certain directories
            if any(skip in root for skip in ['__pycache__', '.git', 'node_modules', 'venv']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        problematic_files = {}
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                found_issues = []
                for old_import in self.import_fixes.keys():
                    if old_import in content:
                        found_issues.append(old_import)
                
                if found_issues:
                    problematic_files[file_path] = found_issues
                    
            except Exception as e:
                print(f"⚠️ Could not read {file_path}: {e}")
        
        return problematic_files

    def show_required_fixes(self, problematic_files):
        """Show what needs to be fixed"""
        
        print(f"📋 Found {len(problematic_files)} files with old import paths:")
        print("=" * 60)
        
        for file_path, issues in problematic_files.items():
            print(f"\n📄 {file_path}:")
            for issue in issues:
                new_import = self.import_fixes[issue]
                print(f"   🔄 {issue}")
                print(f"   ➜  {new_import}")
        
        return len(problematic_files) > 0

    def fix_file(self, file_path, issues):
        """Fix imports in a single file"""
        
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes_in_file = []
            
            # Apply all fixes
            for old_import in issues:
                if old_import in content:
                    new_import = self.import_fixes[old_import]
                    content = content.replace(old_import, new_import)
                    changes_in_file.append(f"{old_import} → {new_import}")
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Fixed {file_path}:")
                for change in changes_in_file:
                    print(f"   🔄 {change}")
                
                self.changes_made.extend(changes_in_file)
                return True
            else:
                print(f"ℹ️ No changes needed in {file_path}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to fix {file_path}: {e}")
            return False

    def fix_all_files(self, problematic_files):
        """Fix all problematic files"""
        
        print(f"\n🔧 Fixing {len(problematic_files)} files...")
        print("=" * 60)
        
        fixed_count = 0
        
        for file_path, issues in problematic_files.items():
            if self.fix_file(file_path, issues):
                fixed_count += 1
        
        return fixed_count

    def run(self, fix_automatically=False):
        """Run the import fixer"""
        
        print("🚀 GUST Bot - Direct Import Statement Fixer")
        print("=" * 60)
        
        # Find problematic files
        problematic_files = self.find_problematic_files()
        
        if not problematic_files:
            print("✅ No files found with old import paths!")
            return
        
        # Show what needs to be fixed
        has_issues = self.show_required_fixes(problematic_files)
        
        if not has_issues:
            return
        
        # Ask user if they want to fix automatically
        if not fix_automatically:
            print(f"\n🎯 Found {len(problematic_files)} files that need fixing.")
            choice = input("Fix all files automatically? (y/N): ").lower().strip()
            fix_automatically = choice == 'y'
        
        if fix_automatically:
            # Fix all files
            fixed_count = self.fix_all_files(problematic_files)
            
            print(f"\n🎯 IMPORT FIXING COMPLETE!")
            print("=" * 60)
            print(f"✅ Fixed {fixed_count} files")
            print(f"📊 Made {len(self.changes_made)} import changes")
            print("\n🧪 Next steps:")
            print("1. Restart your GUST Bot")
            print("2. Test login functionality")
            print("3. No more import errors!")
        else:
            print("\n📋 Manual fixes needed:")
            print("Update the import statements shown above in each file.")

def main():
    fixer = ImportFixer()
    fixer.run()

if __name__ == "__main__":
    main()
