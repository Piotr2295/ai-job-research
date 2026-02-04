"""
Database service - handles all database operations.
"""

import hashlib
import logging
import sqlite3
from pathlib import Path

from app.database import DatabaseManager

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_manager.db_path)

    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create job_analyses table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS job_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                job_title TEXT NOT NULL,
                company TEXT NOT NULL,
                skills_required TEXT NOT NULL,
                skill_gaps TEXT NOT NULL,
                learning_plan TEXT NOT NULL,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, job_title, company)
            )
            """
        )

        # Create learning_progress table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                skill TEXT NOT NULL,
                progress_percentage INTEGER DEFAULT 0,
                completed_modules TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, skill)
            )
            """
        )

        # Create parsed_resumes table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS parsed_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                full_text TEXT NOT NULL,
                sections TEXT,
                extracted_experiences TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT
            )
            """
        )

        # Add file_path column if it doesn't exist (migration for existing databases)
        cursor.execute("PRAGMA table_info(parsed_resumes)")
        columns = [column[1] for column in cursor.fetchall()]
        if "file_path" not in columns:
            cursor.execute("ALTER TABLE parsed_resumes ADD COLUMN file_path TEXT")
            logger.info("Added file_path column to parsed_resumes table")

        # Create cv_metadata table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cv_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (resume_id) REFERENCES parsed_resumes(id),
                UNIQUE(user_id, file_hash)
            )
            """
        )

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    @staticmethod
    def compute_file_hash(file_content: bytes) -> str:
        """Compute SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def save_cv_file(
        user_id: str, file_content: bytes, original_filename: str, storage_path: Path
    ) -> str:
        """Save CV file to local storage and return the path"""
        from datetime import datetime

        # Create user-specific directory
        user_cv_dir = storage_path / user_id
        user_cv_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{original_filename}"
        file_path = user_cv_dir / safe_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)
