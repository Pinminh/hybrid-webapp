

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::
        >>> import deamon.request
        >>> req = request.Request()
        ## Incoming message obtain aka. incoming_msg
        >>> r = req.prepare(incoming_msg)
        >>> r
        <Request>
    """
    
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None, None

        return method, path, version

    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        print(f"{request}")
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO: manage the webapp hook in this mounting point
        #
        
        if not routes == {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))

        self.headers = self.prepare_headers(request)
        cookies = self.headers.get('Cookie', '')
        for item in cookies.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                if self.cookies is None:
                    self.cookies = {}
                self.cookies[key] = value

        # Body (bytes) — sliced by Content-Length if present
        _, body_bytes = self.split_head_body(request)
        try:
            cl = int(self.headers.get('Content-Length', '0') or 0)
        except Exception:
            cl = 0
        if cl > 0 and len(body_bytes) >= cl:
            body_bytes = body_bytes[:cl]
        self.body = body_bytes
        self.prepare_body(self.body, files=None)

    def prepare_body(self, data, files, json=None):
        self.prepare_content_length(self.body)
        
        if not isinstance(data, str):
            data = data.decode('utf-8', 'ignore')
        
        self.body = {}
        for item in data.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                self.body[key.strip()] = value.strip()
        #
        # TODO prepare the request authentication
        #
        # self.auth = ...
        
        return


    def prepare_content_length(self, body):
        self.headers["Content-Length"] = "0"
        #
        # TODO prepare the request authentication
        #
        # self.auth = ...
        if self.headers is None:
            self.headers = {}
        self.headers["Content-Length"] = str(len(body) if body else 0)
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
        # DONE partially

        if auth is None:
                return
            
        if self.headers is None:
            self.headers = {}
            
        if isinstance(auth, tuple) and len(auth) == 2:
            # Basic Authentication
            import base64
            username, password = auth
            credentials = f"{username}:{password}"
            encoded = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
            self.headers["Authorization"] = f"Basic {encoded}"
            self.auth = auth
        elif isinstance(auth, str):
            # Bearer Token Authentication
            self.headers["Authorization"] = f"Bearer {auth}"
            self.auth = auth
        else:
            self.auth = auth

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies

    def split_head_body(self, request: str):
        """
        Split raw HTTP message into (head:str, body:bytes).
        - Accepts either str or bytes as input.
        - Returns the header section as UTF-8 text (best-effort) and the raw body bytes.
        """
        if isinstance(request, bytes):
            raw = request
        else:
            # Best-effort encode so we can safely partition on CRLFCRLF
            raw = request.encode("utf-8", "ignore")

        # Split on the first empty line (CRLFCRLF)
        head_bytes, sep, body_bytes = raw.partition(b"\r\n\r\n")

        # Decode headers to str for easier parsing; keep body as bytes
        head_str = head_bytes.decode("utf-8", "ignore")
        return head_str, body_bytes