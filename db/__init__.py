# đường dẫn db/__init__.py
# Khởi tạo danh sách lưu các peer kết nối
peer_list = []
active_peers = []
connections = {}
chat_history = {}  # ánh xạ cặp peer -> list message
pending_requests = []  # chứa các yêu cầu chờ xác nhận
history_chat = {}     # { "ipA:portA|ipB:portB" : [ { "sender": "...", "msg": "..." }, ..
