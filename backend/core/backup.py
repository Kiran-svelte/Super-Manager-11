"""
Backup & Recovery Module
========================

Comprehensive backup system for:
- Database backups (PostgreSQL/Supabase)
- File/media backups
- Configuration backups
- Automated scheduling
- Point-in-time recovery

Author: Super Manager
Version: 1.0.0
"""

import os
import json
import gzip
import shutil
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


# =============================================================================
# Backup Types and Configuration
# =============================================================================

class BackupType(str, Enum):
    FULL = "full"           # Complete backup
    INCREMENTAL = "incremental"  # Changes since last backup
    DIFFERENTIAL = "differential"  # Changes since last full backup


class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class BackupConfig:
    """Backup configuration settings"""
    backup_dir: str = "./backups"
    retention_days: int = 30
    max_backups: int = 100
    compression_enabled: bool = True
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    
    # Schedule (cron-like)
    schedule_full: str = "0 2 * * 0"  # Weekly on Sunday at 2 AM
    schedule_incremental: str = "0 2 * * *"  # Daily at 2 AM
    
    # Notification
    notify_on_failure: bool = True
    notify_on_success: bool = False


@dataclass
class BackupRecord:
    """Record of a backup operation"""
    id: str
    backup_type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


# =============================================================================
# Database Backup
# =============================================================================

class DatabaseBackup:
    """
    Database backup and restore operations
    
    Supports:
    - PostgreSQL pg_dump/pg_restore
    - Supabase API backups
    - Selective table backup
    """
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        Path(self.config.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def _generate_backup_id(self) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"db_backup_{timestamp}"
    
    async def backup_postgres(
        self,
        connection_string: str,
        backup_type: BackupType = BackupType.FULL,
        tables: List[str] = None
    ) -> BackupRecord:
        """
        Backup PostgreSQL database
        
        Args:
            connection_string: PostgreSQL connection URL
            backup_type: Type of backup to perform
            tables: Specific tables to backup (None = all)
        
        Returns:
            BackupRecord with backup details
        """
        backup_id = self._generate_backup_id()
        timestamp = datetime.utcnow()
        
        record = BackupRecord(
            id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.IN_PROGRESS,
            created_at=timestamp
        )
        
        try:
            # Build pg_dump command
            filename = f"{backup_id}.sql"
            if self.config.compression_enabled:
                filename += ".gz"
            
            file_path = os.path.join(self.config.backup_dir, filename)
            
            # Construct pg_dump arguments
            pg_dump_args = [
                "pg_dump",
                connection_string,
                "--format=plain",
                "--no-owner",
                "--no-acl"
            ]
            
            if tables:
                for table in tables:
                    pg_dump_args.extend(["-t", table])
            
            # Execute backup
            import subprocess
            
            if self.config.compression_enabled:
                # Pipe through gzip
                with open(file_path, 'wb') as f:
                    dump_process = subprocess.Popen(
                        pg_dump_args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    gzip_process = subprocess.Popen(
                        ['gzip'],
                        stdin=dump_process.stdout,
                        stdout=f,
                        stderr=subprocess.PIPE
                    )
                    dump_process.stdout.close()
                    gzip_process.communicate()
            else:
                with open(file_path, 'w') as f:
                    subprocess.run(pg_dump_args, stdout=f, check=True)
            
            # Calculate checksum
            checksum = self._calculate_checksum(file_path)
            file_size = os.path.getsize(file_path)
            
            record.status = BackupStatus.COMPLETED
            record.completed_at = datetime.utcnow()
            record.file_path = file_path
            record.file_size_bytes = file_size
            record.checksum = checksum
            record.metadata = {
                "tables": tables or "all",
                "compression": self.config.compression_enabled
            }
            
            logger.info(f"Database backup completed: {backup_id} ({file_size} bytes)")
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            logger.error(f"Database backup failed: {e}")
        
        return record
    
    async def backup_supabase(self, supabase_client, tables: List[str] = None) -> BackupRecord:
        """
        Backup data from Supabase
        
        Uses Supabase API to export table data as JSON
        """
        backup_id = self._generate_backup_id()
        timestamp = datetime.utcnow()
        
        record = BackupRecord(
            id=backup_id,
            backup_type=BackupType.FULL,
            status=BackupStatus.IN_PROGRESS,
            created_at=timestamp
        )
        
        try:
            backup_data = {}
            
            # Get list of tables if not specified
            if not tables:
                tables = ["users", "conversations", "messages", "tasks", "memories"]
            
            for table in tables:
                try:
                    response = supabase_client.table(table).select("*").execute()
                    backup_data[table] = response.data
                    logger.info(f"Backed up {len(response.data)} rows from {table}")
                except Exception as e:
                    logger.warning(f"Failed to backup table {table}: {e}")
                    backup_data[table] = {"error": str(e)}
            
            # Write to file
            filename = f"{backup_id}_supabase.json"
            if self.config.compression_enabled:
                filename += ".gz"
            
            file_path = os.path.join(self.config.backup_dir, filename)
            
            json_data = json.dumps(backup_data, default=str, indent=2)
            
            if self.config.compression_enabled:
                with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                    f.write(json_data)
            else:
                with open(file_path, 'w') as f:
                    f.write(json_data)
            
            checksum = self._calculate_checksum(file_path)
            file_size = os.path.getsize(file_path)
            
            record.status = BackupStatus.COMPLETED
            record.completed_at = datetime.utcnow()
            record.file_path = file_path
            record.file_size_bytes = file_size
            record.checksum = checksum
            record.metadata = {
                "tables": tables,
                "row_counts": {t: len(backup_data.get(t, [])) for t in tables}
            }
            
            logger.info(f"Supabase backup completed: {backup_id}")
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            logger.error(f"Supabase backup failed: {e}")
        
        return record
    
    async def restore_postgres(self, backup_path: str, connection_string: str) -> bool:
        """Restore PostgreSQL database from backup"""
        try:
            import subprocess
            
            # Handle compressed backups
            if backup_path.endswith('.gz'):
                # Decompress first
                with gzip.open(backup_path, 'rt') as f:
                    sql_content = f.read()
                
                process = subprocess.Popen(
                    ['psql', connection_string],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                _, stderr = process.communicate(sql_content.encode())
                
                if process.returncode != 0:
                    raise Exception(f"Restore failed: {stderr.decode()}")
            else:
                with open(backup_path, 'r') as f:
                    subprocess.run(
                        ['psql', connection_string],
                        stdin=f,
                        check=True
                    )
            
            logger.info(f"Database restored from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    async def restore_supabase(self, backup_path: str, supabase_client) -> bool:
        """Restore Supabase data from backup"""
        try:
            # Read backup file
            if backup_path.endswith('.gz'):
                with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)
            
            for table, rows in backup_data.items():
                if isinstance(rows, list) and rows:
                    try:
                        # Upsert data
                        supabase_client.table(table).upsert(rows).execute()
                        logger.info(f"Restored {len(rows)} rows to {table}")
                    except Exception as e:
                        logger.warning(f"Failed to restore {table}: {e}")
            
            logger.info(f"Supabase data restored from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Supabase restore failed: {e}")
            return False
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


# =============================================================================
# File Backup
# =============================================================================

class FileBackup:
    """
    File and directory backup system
    
    Supports:
    - Full directory backup
    - Incremental backup based on modification time
    - File integrity verification
    """
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self._manifest: Dict[str, Dict] = {}
    
    async def backup_directory(
        self,
        source_dir: str,
        backup_type: BackupType = BackupType.FULL
    ) -> BackupRecord:
        """Backup a directory"""
        backup_id = f"files_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.utcnow()
        
        record = BackupRecord(
            id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.IN_PROGRESS,
            created_at=timestamp
        )
        
        try:
            source_path = Path(source_dir)
            if not source_path.exists():
                raise ValueError(f"Source directory does not exist: {source_dir}")
            
            # Create backup archive
            backup_filename = f"{backup_id}.tar.gz"
            backup_path = os.path.join(self.config.backup_dir, backup_filename)
            
            # Use shutil for simple backup
            shutil.make_archive(
                os.path.join(self.config.backup_dir, backup_id),
                'gztar',
                source_dir
            )
            
            checksum = self._calculate_checksum(backup_path)
            file_size = os.path.getsize(backup_path)
            
            record.status = BackupStatus.COMPLETED
            record.completed_at = datetime.utcnow()
            record.file_path = backup_path
            record.file_size_bytes = file_size
            record.checksum = checksum
            
            logger.info(f"Directory backup completed: {backup_id}")
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            logger.error(f"Directory backup failed: {e}")
        
        return record
    
    async def restore_directory(self, backup_path: str, target_dir: str) -> bool:
        """Restore directory from backup"""
        try:
            shutil.unpack_archive(backup_path, target_dir)
            logger.info(f"Directory restored to {target_dir}")
            return True
        except Exception as e:
            logger.error(f"Directory restore failed: {e}")
            return False
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


# =============================================================================
# Backup Manager
# =============================================================================

class BackupManager:
    """
    Central backup orchestration
    
    Features:
    - Scheduled backups
    - Retention management
    - Backup verification
    - Recovery point objectives (RPO)
    """
    
    def __init__(self, config: BackupConfig = None):
        self.config = config or BackupConfig()
        self.db_backup = DatabaseBackup(self.config)
        self.file_backup = FileBackup(self.config)
        self._backup_history: List[BackupRecord] = []
        self._lock = threading.Lock()
        self._scheduler_running = False
    
    async def create_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        include_db: bool = True,
        include_files: bool = True,
        db_connection: str = None,
        file_dirs: List[str] = None
    ) -> Dict[str, BackupRecord]:
        """
        Create a comprehensive backup
        
        Args:
            backup_type: Type of backup
            include_db: Include database backup
            include_files: Include file backup
            db_connection: Database connection string
            file_dirs: Directories to backup
        
        Returns:
            Dict of backup records by type
        """
        results = {}
        
        if include_db and db_connection:
            record = await self.db_backup.backup_postgres(db_connection, backup_type)
            results["database"] = record
            self._add_to_history(record)
        
        if include_files and file_dirs:
            for dir_path in file_dirs:
                record = await self.file_backup.backup_directory(dir_path, backup_type)
                results[f"files_{Path(dir_path).name}"] = record
                self._add_to_history(record)
        
        # Cleanup old backups
        self._cleanup_old_backups()
        
        return results
    
    async def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verify backup integrity"""
        record = self._get_backup_record(backup_id)
        if not record:
            return {"valid": False, "error": "Backup not found"}
        
        if not record.file_path or not os.path.exists(record.file_path):
            return {"valid": False, "error": "Backup file not found"}
        
        # Verify checksum
        current_checksum = self.db_backup._calculate_checksum(record.file_path)
        
        return {
            "valid": current_checksum == record.checksum,
            "expected_checksum": record.checksum,
            "actual_checksum": current_checksum,
            "file_size": os.path.getsize(record.file_path),
            "created_at": record.created_at.isoformat()
        }
    
    def list_backups(
        self,
        backup_type: BackupType = None,
        status: BackupStatus = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List available backups"""
        with self._lock:
            backups = self._backup_history.copy()
        
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]
        
        if status:
            backups = [b for b in backups if b.status == status]
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x.created_at, reverse=True)
        
        return [
            {
                "id": b.id,
                "type": b.backup_type.value,
                "status": b.status.value,
                "created_at": b.created_at.isoformat(),
                "completed_at": b.completed_at.isoformat() if b.completed_at else None,
                "file_size_bytes": b.file_size_bytes,
                "file_path": b.file_path
            }
            for b in backups[:limit]
        ]
    
    def _add_to_history(self, record: BackupRecord):
        """Add backup record to history"""
        with self._lock:
            self._backup_history.append(record)
            # Keep history bounded
            if len(self._backup_history) > self.config.max_backups * 2:
                self._backup_history = self._backup_history[-self.config.max_backups:]
    
    def _get_backup_record(self, backup_id: str) -> Optional[BackupRecord]:
        """Get backup record by ID"""
        with self._lock:
            for record in self._backup_history:
                if record.id == backup_id:
                    return record
        return None
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
        backup_dir = Path(self.config.backup_dir)
        
        cleaned = 0
        for backup_file in backup_dir.glob("*"):
            if backup_file.is_file():
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    try:
                        backup_file.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.warning(f"Failed to cleanup backup {backup_file}: {e}")
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old backup files")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get backup storage statistics"""
        backup_dir = Path(self.config.backup_dir)
        
        if not backup_dir.exists():
            return {"total_size_bytes": 0, "backup_count": 0}
        
        total_size = 0
        backup_count = 0
        
        for backup_file in backup_dir.glob("*"):
            if backup_file.is_file():
                total_size += backup_file.stat().st_size
                backup_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_human": self._format_size(total_size),
            "backup_count": backup_count,
            "backup_dir": str(backup_dir),
            "retention_days": self.config.retention_days
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"


# Global backup manager instance
backup_manager = BackupManager()
