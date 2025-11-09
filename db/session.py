"""
Database-backed session storage using SQLite.
Thread-safe and supports multiple backend processes.
"""

import uuid
import time
import sqlite3
import threading
from contextlib import contextmanager

DB_PATH = "db/sessions.db"

class Session:
    """Represents a user session with authentication state and metadata."""
    
    def __init__(self, session_id, username, timeout=3600):
        self.session_id = session_id
        self.username = username
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.expires_at = self.created_at + timeout
        self.data = {}
    
    def is_expired(self):
        return time.time() > self.expires_at
    
    def touch(self, timeout=3600):
        """Update last accessed time and extend expiration."""
        self.last_accessed = time.time()
        self.expires_at = self.last_accessed + timeout
    
    def get(self, key, default=None):
        """Retrieve data from session storage."""
        return self.data.get(key, default)
    
    def set(self, key, value):
        """Store data in session."""
        self.data[key] = value
    
    def __repr__(self):
        return f"Session(id={self.session_id}, username={self.username}, created_at={self.created_at}, last_accessed={self.last_accessed}, expires_at={self.expires_at}, data={self.data})"

class SessionManager:
    """Session manager with SQLite persistence."""
    
    def __init__(self, default_timeout=3600, db_path=DB_PATH):
        self.default_timeout = default_timeout
        self.db_path = db_path
        self.local = threading.local()
        
        # Initialize database
        self._init_db()
        print(f"[SessionManager] Using database: {self.db_path}")
    
    def _init_db(self):
        """Create sessions table if it doesn't exist."""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    data TEXT
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires 
                ON sessions(expires_at)
            ''')
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection."""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10.0
            )
            self.local.conn.row_factory = sqlite3.Row
        
        try:
            yield self.local.conn
        except Exception as e:
            self.local.conn.rollback()
            raise e
    
    def create_session(self, username):
        """Create a new session in database."""
        session_id = str(uuid.uuid4())
        now = time.time()
        expires_at = now + self.default_timeout
        
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO sessions 
                (session_id, username, created_at, last_accessed, expires_at, data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, username, now, now, expires_at, '{}'))
            conn.commit()
        
        session = Session(session_id, username, self.default_timeout)
        session.created_at = now
        session.last_accessed = now
        session.expires_at = expires_at
        
        print(f"[Session] Created session {session_id} for user '{username}'")
        return session
    
    def get_session(self, session_id):
        """Retrieve session from database."""
        if not session_id:
            return None
        
        with self._get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM sessions WHERE session_id = ?
            ''', (session_id,)).fetchone()
            
            if not row:
                return None
            
            # Check expiration
            if row['expires_at'] < time.time():
                print(f"[Session] Session {session_id} expired")
                self.destroy_session(session_id)
                return None
            
            # Create session object
            session = Session(
                session_id=row['session_id'],
                username=row['username'],
                timeout=self.default_timeout
            )
            session.created_at = row['created_at']
            session.last_accessed = row['last_accessed']
            session.expires_at = row['expires_at']
            
            # Update last accessed time
            session.touch(self.default_timeout)
            conn.execute('''
                UPDATE sessions 
                SET last_accessed = ?, expires_at = ?
                WHERE session_id = ?
            ''', (session.last_accessed, session.expires_at, session_id))
            conn.commit()
            
            return session
    
    def destroy_session(self, session_id):
        """Delete session from database."""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            print(f"[Session] Destroyed session {session_id}")
            return True
    
    def validate_session(self, session_id):
        """Validate session exists and not expired."""
        return self.get_session(session_id) is not None
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from database."""
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM sessions WHERE expires_at < ?
            ''', (now,))
            count = cursor.rowcount
            conn.commit()
            
            if count > 0:
                print(f"[Session] Cleaned up {count} expired sessions")
            
            return count


# Global database session manager
session_manager = SessionManager(default_timeout=120)