from datetime import datetime, timedelta, timezone

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