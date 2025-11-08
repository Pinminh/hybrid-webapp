
"""
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import json
import datetime
import os
import mimetypes
import socket
from .dictionary import CaseInsensitiveDict
from db import peer_list, history_chat
from urllib.parse import unquote_plus
#from db import *
BASE_DIR = ""
import threading
peer_sockets = {}  # Lưu socket listener của từng peer
connected_peers = {}  # { "ip:port" : ["ip2:port2", ...] }

def handle_peer_message(conn, addr, my_ip, my_port):
    try:
        data = conn.recv(1024).decode()
        if not data:
            return
        print(f"[Peer] Nhận từ {addr}: {data}")

        if data.startswith("CONNECT_REQUEST"):
            src = data.split(" ")[1]
            print(f"🔗 Nhận CONNECT_REQUEST từ {src}, auto-accept luôn!")

            # gửi CONFIRM_CONNECT ngược lại cho peer gửi yêu cầu
            try:
                ip, port = src.split(":")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, int(port)))
                    s.sendall(b"CONFIRM_CONNECT")
                    print(f"✅ Đã CONFIRM_CONNECT với {src}")
            except Exception as e:
                print(f"❌ Lỗi khi gửi CONFIRM_CONNECT: {e}")

        elif data == "CONFIRM_CONNECT":
            print(f"✅ Kết nối được xác nhận từ {addr}")

        elif data.startswith("CHAT_MESSAGE"):
            parts = data.split("|")
            if len(parts) >= 4:
                src_ip, src_port, msg = parts[1], (int)(parts[2]), parts[3]
                print(f"💬 Tin nhắn mới từ {src_ip}:{src_port}: {msg}")
                # key = tuple(sorted([(src_ip, int(src_port)), (my_ip, int(my_port))]))
                # if key not in history_chat:
                #     history_chat[key] = []
                # sender_id = f"{src_ip}:{src_port}"
                # history_chat[key].append({sender_id: msg})

            else:
                print(f"⚠️ CHAT_MESSAGE bị sai format: {data}")

        else:
            print(f"[Peer] Nội dung khác: {data}")

    except Exception as e:
        print(f"❌ Lỗi xử lý peer message: {e}")
    finally:
        conn.close()


def send_to_peer(ip, port, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, int(port)))
            s.sendall(message.encode())
    except Exception as e:
        print(f"[Error] Cannot send to peer {ip}:{port} - {e}")

def start_peer_listener(my_ip, my_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((my_ip, int(my_port)))
        server_socket.listen()
        print(f"[Listener] Đang lắng nghe tại {my_ip}:{my_port}")

        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_peer_message, args=(conn, addr, my_ip, my_port)).start()

def send_to_peer_message(src_ip, src_port, target_ip, target_port, msg):
    try:
        packet = f"CHAT_MESSAGE|{src_ip}|{src_port}|{msg}"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_ip, int(target_port)))
            s.sendall(packet.encode("utf-8"))
        # lưu lịch sử
        key = tuple(sorted([(src_ip, int(src_port)), (target_ip, int(target_port))]))
        if key not in history_chat:
            history_chat[key] = []
        sender_id = f"{src_ip}:{src_port}"
        history_chat[key].append({sender_id: msg})
        print(f"✅ Gửi tin nhắn tới {target_ip}:{target_port} → {msg}")
    except Exception as e:
        print(f"❌ Lỗi gửi tin tới {target_ip}:{target_port}: {e}")

def make_chat_key(peer1, peer2):
    """Tạo key dạng ipA:portA|ipB:portB, đảm bảo thứ tự cố định"""
    peers = sorted([peer1, peer2])
    return f"{peers[0]}|{peers[1]}"

class Response():   

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        
        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        base_dir = ""
        main_type, sub_type = mime_type.split('/', 1)
        self.headers['Content-Type'] = mime_type
        #print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        if main_type == 'text':
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR+"static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR+"www/"
            else:
                raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))
        elif main_type == 'image':
            if sub_type in ['png', 'jpeg', 'vnd.microsoft.icon', 'x-icon']:
                base_dir = BASE_DIR+"static/images/"
            else:
                raise ValueError(f"Unsupported image subtype: {sub_type}")
        elif main_type == 'application':
            if sub_type == 'x-x509-ca-cert':
                base_dir = BASE_DIR+"cert/"
            elif sub_type == 'javascript':
                base_dir = BASE_DIR+"static/js/"
            elif sub_type == 'python':
                base_dir = BASE_DIR+"apps/"
            else:
                raise ValueError(f"Unsupported application subtype: {sub_type}")
        elif main_type == 'video':
            if sub_type == 'mp4':
                base_dir = BASE_DIR + ""
            raise ValueError(f"Unsupported video subtype: {sub_type}")
        else: raise ValueError(f"Unsupported main MIME type: {main_type}")
        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """

        filepath = os.path.join(base_dir, path.lstrip('/'))

        print("[Response] serving the object at location {}".format(filepath))
        # hiện thực lấy dữ liệu trả về (len(content) và content)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().encode('utf-8')
            return (len(content), content)
        except FileNotFoundError:
            print("[Response] File not found: {}".format(filepath))
            self.status_code = 404
            return (len(b"404"),b"404")
        except Exception as e:
            print("[Response] Server error {}: {}".format(filepath, e))
            self.status_code = 500
            return (len(b"500"),b"500")



    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.

        :params request (class:`Request <Request>`): incoming request object.

        :rtypes bytes: encoded HTTP response header.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        # Build dynamic headers
        headers = {
                "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
                "Cache-Control": "no-cache",
                "Content-Type": "{}".format(self.headers['Content-Type']),
                "Content-Length": "{}".format(len(self._content)),
                # "Cookie": "{}".format(reqhdr.get("Cookie", "sessionid=xyz789")), #dummy cooki
        #
        # TODO prepare the request authentication
        #
        # self.auth = ...
                "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
                "Max-Forward": "10",
                "Pragma": "no-cache",
                "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
                "Warning": "199 Miscellaneous warning",
                "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
        }

        # Header text alignment
        #
        #  TODO: implement the header building to create formatted
        #        header from the provided headers
        #  DONE
        lines = ['{}: {}'.format(k, v) for k, v in headers.items()]
        fmt_header = '\r\n'.join(lines)
        
        #
        # TODO prepare the request authentication
        #
        # self.auth = ...
        return str(fmt_header).encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')


    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.

        :params request (class:`Request <Request>`): incoming request object.

        :rtype bytes: complete HTTP response using prepared headers and content.
        """
        #print(f"TAOLAAI:::{request.body}")
        path = request.path
        if not path:
            return self.build_notfound()
        method = request.method

        # ========== TASK 1A: Handle POST /login ==========
        if path == "/login" and method == "POST":
            # Parse form data from request body
            params = request.body or {}            
            username = params.get("username", "")
            password = params.get("password", "")
            
            # Validate credentials
            if username == "admin" and password == "password":
                # LOGIN SUCCESS
                print(f"[Response] '{username}' login SUCCESSFUL - Setting cookie")
                base_dir = self.prepare_content_type("text/html")
                # chuyển hướng
                _, content = self.build_content("/dashboard.html", base_dir)
                
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    "Set-Cookie: auth=true; Path=/; HttpOnly\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                ).encode("utf-8") + content
                return response
            else:
                # LOGIN FAILED
                print(f"[Response] '{username}' login FAILED - Invalid credentials")
                base_dir = self.prepare_content_type("text/html")
                _, content = self.build_content("/login.html", base_dir)
                
                response = (
                    "HTTP/1.1 401 Unauthorized\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                ).encode("utf-8") + content
                return response
    
        # ========== TASK 1B: Handle GET / or /index.html ==========
        elif path in ["/", "/index.html"] and method == "GET":
            cookies = request.cookies or {}
            
            if cookies.get("auth") == "true":
                # Valid cookie found
                print("[Response] Valid auth cookie - Serving dashboard.html")
                base_dir = self.prepare_content_type("text/html")
                _, content = self.build_content("/dashboard.html", base_dir)
                
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                ).encode("utf-8") + content
                return response
            else:
                # No valid cookie
                print("[Response] No auth cookie - Returning 401")
                base_dir = self.prepare_content_type("text/html")
                _, content = self.build_content("/login.html", base_dir)
                
                response = (
                    "HTTP/1.1 401 Unauthorized\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                ).encode("utf-8") + content
                return response
        # ======= START TASK 2 ======= #
        # ========== Handle POST /submit-info ==========
        elif path == "/submit-info" and method == "POST":
            params = request.body or {}
            print(params)
            ip = params.get("ip", "127.0.0.1")
            port = params.get("port", "9001")

            print(f"[Submit] Peer info received: {ip}:{port}")
            if (ip, port) not in peer_list:
                peer_list.append((ip, port))
                print(f"[SubmitInfo] New peer registered: {ip}:{port}")
                # mở luồng nghe request từ peer khác
                t = threading.Thread(target=start_peer_listener, args=(ip, port), daemon=True)
                t.start()
                peer_sockets[(ip, port)] = t
            else:
                print(f"[SubmitInfo] Peer already registered: {ip}:{port}")
            response_body = f"Received peer info: {ip}:{port}".encode("utf-8")

            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode("utf-8") + response_body
            return response
        elif path == "/get-list" and method == "GET":
            if not peer_list:
                content = "No peers registered.".encode("utf-8")
            else:
                content = "\n".join([f"{ip}:{port}" for ip, port in peer_list]).encode("utf-8")
            
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(content)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode("utf-8") + content

            return response
        ## kết nối đến peer / direct peer communicate
        elif path == "/connect-peer" and method == "POST":
            params = request.body or {}
            src_ip = params.get("source_ip")
            src_port = params.get("source_port")
            target_ip = params.get("target_ip", "")
            target_port = params.get("target_port","")

            if not all([src_ip, src_port, target_ip, target_port]):
                msg = "Missing ip or port field".encode("utf-8")
                return (
                    "HTTP/1.1 400 Bad Request\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(msg)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("utf-8") + msg

            try:
                # Gửi yêu cầu kết nối đến peer đích
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((target_ip, int(target_port)))
                s.sendall(f"CONNECT_REQUEST {src_ip}:{src_port}".encode("utf-8"))
                print(f"✅ Gửi CONNECT_REQUEST từ {src_ip}:{src_port} đến {target_ip}:{target_port}")
                s.close()

                msg = f"Kết nối P2P giữa {src_ip}:{src_port} ↔ {target_ip}:{target_port} đã được thiết lập.".encode("utf-8")
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(msg)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("utf-8") + msg
                return response

            except Exception as e:
                err = f"Lỗi khi kết nối tới {target_ip}:{target_port} → {e}".encode("utf-8")
                print(err)
                return self.build_notfound()
        elif path == "/send-peer" and method == "POST":
            params = request.body or {}
            src_ip = params.get("source_ip")
            src_port = params.get("source_port")
            target_ip = params.get("ip")
            target_port = params.get("port")
            message = unquote_plus(params.get("message"))

            if not all([src_ip, src_port, target_ip, target_port, message]):
                msg = "Missing required fields".encode("utf-8")
                return (
                    "HTTP/1.1 400 Bad Request\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(msg)}\r\nConnection: close\r\n\r\n"
                ).encode("utf-8") + msg

            send_to_peer_message(src_ip, src_port, target_ip, target_port, message)

            body = f"Sent from {src_ip}:{src_port} to {target_ip}:{target_port}".encode("utf-8")
            return (
                "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
            ).encode("utf-8") + body
        elif path == "/get-messages" and method == "POST":
            params = request.body or {}
            src_ip = params.get("src_ip","")
            src_port = params.get("src_port","")
            target_ip = params.get("target_ip","")
            target_port = params.get("target_port","")
            if not all([src_ip, src_port, target_ip, target_port]):
                msg = "Missing fields".encode("utf-8")
                return (
                    "HTTP/1.1 400 Bad Request\r\n"
                    f"Content-Length: {len(msg)}\r\n"
                    "Content-Type: text/plain\r\nConnection: close\r\n\r\n"
                ).encode("utf-8") + msg

            key = tuple(sorted([(src_ip, int(src_port)), (target_ip, int(target_port))]))
            chat = history_chat.get(key, [])

            lines = []
            print(f"CHAT NE:{chat}")
            local_id = f"{src_ip}:{int(src_port)}"
            
            for msg_dict in chat:
                for sender, msg in msg_dict.items():
                    if sender == local_id:
                        lines.append(f"{local_id}|{msg}")
            
            resp_body = "\n".join(lines).encode("utf-8")
            print(f"GỬI ĐẾN HTML :{lines}")
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(resp_body)}\r\n"
                "Connection: close\r\n\r\n"
            ).encode("utf-8") + resp_body
            return response

        mime_type = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))


        base_dir = ""

        # If HTML, parse and serve embedded objects
        if path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type='text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type='text/css')
        #
        # TODO: add support objects
        #
        else:
            return self.build_notfound()

        c_len, self._content = self.build_content(path, base_dir)
        self._header = self.build_response_header(request)

        return self._header + self._content