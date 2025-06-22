"""
Routes/Logs Storage & File Management Module for GUST-MARK-1
============================================================
✅ MODULARIZED: File operations, storage management, and data organization
✅ PRESERVED: All file handling logic and directory structure from original
✅ OPTIMIZED: Enhanced file operations with better error handling
✅ MAINTAINED: Compatible with both MongoDB and in-memory storage
"""

import os
import json
import time
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class LogsStorage:
    """
    ✅ PRESERVED: File storage and management system with dual storage support
    """
    
    def __init__(self, db=None, logs_storage=None):
        """
        Initialize storage system with database and in-memory fallback
        
        Args:
            db: MongoDB database instance (optional)
            logs_storage: In-memory storage list (fallback)
        """
        self.db = db
        self.logs_storage = logs_storage if logs_storage is not None else []
        
        # Storage configuration
        self.logs_dir = 'logs'  # Relative path as per config
        self.ensure_directories()
        
        logger.info("✅ Logs storage system initialized")
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        try:
            os.makedirs(self.logs_dir, exist_ok=True)
            logger.debug(f"📁 Ensured logs directory exists: {self.logs_dir}")
        except Exception as e:
            logger.error(f"❌ Error creating logs directory: {e}")
    
    def get_log_file_path(self, filename):
        """Get full path for log file"""
        return os.path.join(self.logs_dir, filename)
    
    def save_log_data(self, server_id, server_name, region, formatted_logs, metadata=None):
        """
        ✅ PRESERVED: Save log data with atomic file operations
        
        Args:
            server_id: Server identifier
            server_name: Human-readable server name
            region: Server region
            formatted_logs: Parsed log entries
            metadata: Additional metadata
            
        Returns:
            dict: Log entry metadata
        """
        try:
            # Create output file with timestamp
            timestamp = int(time.time())
            output_file = f"parsed_logs_{server_id}_{timestamp}.json"
            output_path = self.get_log_file_path(output_file)
            
            # Save formatted logs atomically
            temp_path = output_path + '.tmp'
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(formatted_logs, f, indent=2, ensure_ascii=False)
                
                # Atomic move
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(temp_path, output_path)
                
                logger.info(f"💾 Saved {len(formatted_logs)} log entries to {output_file}")
                
            except Exception as save_error:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise save_error
            
            # Create log entry metadata
            log_entry = {
                'id': f"log_{timestamp}",
                'server_id': server_id,
                'server_name': server_name,
                'region': region,
                'timestamp': datetime.now().isoformat(),
                'entries_count': len(formatted_logs),
                'file_path': output_path,
                'download_file': output_file,
                'file_size': os.path.getsize(output_path),
                'recent_entries': formatted_logs[-10:] if formatted_logs else [],
                'download_attempt': metadata.get('attempt', 1) if metadata else 1,
                'content_length': metadata.get('content_length', 0) if metadata else 0,
                'cached': metadata.get('cached', False) if metadata else False
            }
            
            # Store log entry in database or memory
            try:
                if self.db and hasattr(self.db, 'logs'):
                    self.db.logs.insert_one(log_entry.copy())
                    logger.debug("💾 Stored log entry in MongoDB")
                else:
                    if self.logs_storage is not None:
                        self.logs_storage.append(log_entry)
                        logger.debug("💾 Stored log entry in memory")
            except Exception as storage_error:
                logger.warning(f"⚠️ Failed to store log entry metadata: {storage_error}")
            
            return log_entry
            
        except Exception as e:
            logger.error(f"❌ Error saving log data: {e}")
            raise
    
    def get_all_logs(self):
        """
        ✅ PRESERVED: Get list of all stored logs with metadata
        
        Returns:
            list: List of log entries with metadata
        """
        try:
            # Try to get from database first
            if self.db and hasattr(self.db, 'logs'):
                logs = list(self.db.logs.find({}, {'_id': 0}).sort('timestamp', -1))
                logger.debug(f"📋 Retrieved {len(logs)} logs from MongoDB")
                return logs
            
            # Fallback to in-memory storage
            if self.logs_storage:
                logs = list(self.logs_storage)
                logger.debug(f"📋 Retrieved {len(logs)} logs from memory")
                return logs
            
            logger.debug("📋 No logs found in any storage")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting logs list: {e}")
            return []
    
    def get_log_metadata(self, log_id):
        """
        ✅ PRESERVED: Get metadata for specific log entry
        
        Args:
            log_id: Log identifier
            
        Returns:
            dict: Log metadata or None if not found
        """
        try:
            # Try database first
            if self.db and hasattr(self.db, 'logs'):
                log_entry = self.db.logs.find_one({'id': log_id}, {'_id': 0})
                if log_entry:
                    logger.debug(f"📋 Found log metadata in MongoDB: {log_id}")
                    return log_entry
            
            # Fallback to in-memory storage
            if self.logs_storage:
                log_entry = next((log for log in self.logs_storage if log.get('id') == log_id), None)
                if log_entry:
                    logger.debug(f"📋 Found log metadata in memory: {log_id}")
                    return log_entry
            
            logger.debug(f"📋 Log metadata not found: {log_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting log metadata for {log_id}: {e}")
            return None
    
    def get_log_entries(self, log_id, page=1, per_page=50):
        """
        ✅ PRESERVED: Get log entries with pagination
        
        Args:
            log_id: Log identifier
            page: Page number (1-based)
            per_page: Entries per page
            
        Returns:
            dict: Paginated log data or None if not found
        """
        try:
            # Get log metadata
            log_entry = self.get_log_metadata(log_id)
            if not log_entry:
                return None
            
            # Load log entries from file
            file_path = log_entry.get('file_path')
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"⚠️ Log file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                all_entries = json.load(f)
            
            # Calculate pagination
            total_entries = len(all_entries)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            
            entries = all_entries[start_idx:end_idx]
            
            # Calculate pagination info
            total_pages = (total_entries + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1
            
            result = {
                'log_id': log_id,
                'entries': entries,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_entries,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                },
                'server_info': {
                    'server_id': log_entry.get('server_id'),
                    'server_name': log_entry.get('server_name'),
                    'region': log_entry.get('region'),
                    'timestamp': log_entry.get('timestamp')
                }
            }
            
            logger.debug(f"📄 Retrieved page {page} ({len(entries)} entries) for log {log_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting log entries for {log_id}: {e}")
            return None
    
    def cleanup_old_logs(self, retention_days=7):
        """
        ✅ PRESERVED: Clean up old log files and database entries
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            int: Number of files cleaned up
        """
        try:
            cleanup_count = 0
            
            if not os.path.exists(self.logs_dir):
                return cleanup_count
            
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
            
            # Clean up files
            for filename in os.listdir(self.logs_dir):
                file_path = os.path.join(self.logs_dir, filename)
                
                if (os.path.isfile(file_path) and 
                    os.path.getmtime(file_path) < cutoff_time):
                    try:
                        os.remove(file_path)
                        cleanup_count += 1
                        logger.debug(f"🗑️ Removed old log file: {filename}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not remove file {filename}: {e}")
            
            # Clean up database entries
            if self.db and hasattr(self.db, 'logs'):
                try:
                    cutoff_datetime = datetime.now() - timedelta(days=retention_days)
                    result = self.db.logs.delete_many({
                        'timestamp': {'$lt': cutoff_datetime.isoformat()}
                    })
                    if result.deleted_count > 0:
                        logger.info(f"🗑️ Removed {result.deleted_count} old log entries from database")
                except Exception as e:
                    logger.warning(f"⚠️ Could not clean up database entries: {e}")
            
            # Clean up in-memory storage
            if self.logs_storage:
                try:
                    cutoff_datetime = datetime.now() - timedelta(days=retention_days)
                    original_count = len(self.logs_storage)
                    
                    self.logs_storage[:] = [
                        log for log in self.logs_storage 
                        if log.get('timestamp', '') >= cutoff_datetime.isoformat()
                    ]
                    
                    removed_count = original_count - len(self.logs_storage)
                    if removed_count > 0:
                        logger.info(f"🗑️ Removed {removed_count} old log entries from memory")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not clean up memory storage: {e}")
            
            if cleanup_count > 0:
                logger.info(f"🧹 Cleaned up {cleanup_count} old log files")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            return 0
    
    def get_storage_info(self):
        """
        ✅ NEW: Get storage system information and statistics
        
        Returns:
            dict: Storage information and statistics
        """
        try:
            info = {
                'logs_directory': self.logs_dir,
                'directory_exists': os.path.exists(self.logs_dir),
                'database_available': bool(self.db and hasattr(self.db, 'logs')),
                'memory_storage_available': bool(self.logs_storage is not None),
                'total_logs': len(self.get_all_logs())
            }
            
            # File system info
            if os.path.exists(self.logs_dir):
                files = os.listdir(self.logs_dir)
                info['files_count'] = len(files)
                
                total_size = 0
                for filename in files:
                    file_path = os.path.join(self.logs_dir, filename)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                
                info['total_size_bytes'] = total_size
                info['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            else:
                info.update({
                    'files_count': 0,
                    'total_size_bytes': 0,
                    'total_size_mb': 0
                })
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Error getting storage info: {e}")
            return {
                'error': str(e),
                'logs_directory': self.logs_dir,
                'directory_exists': False,
                'database_available': False,
                'memory_storage_available': False,
                'total_logs': 0,
                'files_count': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0
            }
    
    def backup_logs(self, backup_dir='logs_backup'):
        """
        ✅ NEW: Create backup of all log files
        
        Args:
            backup_dir: Directory to store backup
            
        Returns:
            dict: Backup operation result
        """
        try:
            if not os.path.exists(self.logs_dir):
                return {
                    'success': False,
                    'error': 'Logs directory does not exist'
                }
            
            # Create backup directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{backup_dir}_{timestamp}"
            
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            
            # Copy logs directory
            shutil.copytree(self.logs_dir, backup_path)
            
            # Get backup info
            files_count = len(os.listdir(backup_path))
            
            logger.info(f"💾 Created logs backup: {backup_path} ({files_count} files)")
            
            return {
                'success': True,
                'backup_path': backup_path,
                'files_count': files_count,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating logs backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_log_file(self, log_id):
        """
        ✅ NEW: Validate log file integrity
        
        Args:
            log_id: Log identifier
            
        Returns:
            dict: Validation result
        """
        try:
            log_entry = self.get_log_metadata(log_id)
            if not log_entry:
                return {
                    'valid': False,
                    'error': 'Log metadata not found'
                }
            
            file_path = log_entry.get('file_path')
            if not file_path:
                return {
                    'valid': False,
                    'error': 'File path not specified in metadata'
                }
            
            if not os.path.exists(file_path):
                return {
                    'valid': False,
                    'error': 'Log file does not exist on disk'
                }
            
            # Validate JSON format
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    return {
                        'valid': False,
                        'error': 'Log file does not contain valid log entries array'
                    }
                
                # Check entry count consistency
                expected_count = log_entry.get('entries_count', 0)
                actual_count = len(data)
                
                if expected_count != actual_count:
                    return {
                        'valid': False,
                        'error': f'Entry count mismatch: expected {expected_count}, found {actual_count}'
                    }
                
                return {
                    'valid': True,
                    'entries_count': actual_count,
                    'file_size': os.path.getsize(file_path)
                }
                
            except json.JSONDecodeError as e:
                return {
                    'valid': False,
                    'error': f'Invalid JSON format: {str(e)}'
                }
            
        except Exception as e:
            logger.error(f"❌ Error validating log file {log_id}: {e}")
            return {
                'valid': False,
                'error': str(e)
            }

# Export the main class
__all__ = ['LogsStorage']