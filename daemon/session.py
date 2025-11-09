#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#

"""
This module provides session management for HTTP server with cookie-based authentication.
"""

import uuid
import time
from datetime import datetime, timedelta, timezone


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
    """Manages all active sessions for the HTTP server."""
    
    def __init__(self, default_timeout=3600):
        self.sessions = {}
        self.default_timeout = default_timeout
    
    def create_session(self, username):
        """Create a new session for a user."""
        session_id = str(uuid.uuid4())
        session = Session(session_id, username, self.default_timeout)
        self.sessions[session_id] = session
        print("[Session] Created session {} for user '{}'".format(session_id, username))
        return session
    
    def get_session(self, session_id):
        """Retrieve a session by ID."""
        if not session_id:
            return None
        
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        if session.is_expired():
            print("[Session] Session {} expired".format(session_id))
            self.destroy_session(session_id)
            return None
        
        session.touch(self.default_timeout)
        return session
    
    def destroy_session(self, session_id):
        """Destroy a session and remove it from storage."""
        if session_id in self.sessions:
            username = self.sessions[session_id].username
            del self.sessions[session_id]
            print("[Session] Destroyed session {} for user '{}'".format(session_id, username))
            return True
        return False
    
    def validate_session(self, session_id):
        """Validate if a session exists and is not expired."""
        session = self.get_session(session_id)
        return session is not None
    
    def cleanup_expired_sessions(self):
        """Remove all expired sessions from storage."""
        expired = [sid for sid, session in self.sessions.items() if session.is_expired()]
        
        for session_id in expired:
            self.destroy_session(session_id)
        
        if expired:
            print("[Session] Cleaned up {} expired sessions".format(len(expired)))
        
        return len(expired)
    
    def get_active_sessions_count(self):
        """Get count of currently active sessions."""
        self.cleanup_expired_sessions()
        return len(self.sessions)


# Global session manager instance
session_manager = SessionManager(default_timeout=120)


def parse_session_cookie(cookie_header):
    """Parse session information from Cookie header."""
    session_info = {
        'session_id': None,
        'auth': None
    }
    
    if not cookie_header:
        return session_info
    
    cookies = {}
    for item in cookie_header.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    
    session_info['session_id'] = cookies.get('sessionId')
    session_info['auth'] = cookies.get('auth')
    
    return session_info


def create_session_cookie(session_id, max_age=3600):
    """Create a Set-Cookie header for session."""
    expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)
    expires_str = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    cookie = "sessionId={}; Path=/; HttpOnly; Max-Age={}; Expires={}".format(
        session_id, max_age, expires_str
    )
    
    return cookie


def create_logout_cookie():
    """Create a Set-Cookie header to clear session cookie."""
    expires_str = 'Thu, 01 Jan 1970 00:00:00 GMT'
    cookie = "sessionId=; Path=/; HttpOnly; Max-Age=0; Expires={}".format(expires_str)
    
    return cookie