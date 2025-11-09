#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse
peer_list = []
from daemon.weaprous import WeApRous
from db import peer_list
from db import active_peers
PORT = 8000  # Default port

app = WeApRous()

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    print("[SampleApp] Logging in {} to {}".format(headers, body))


@app.route('/logout', methods=['POST'])
def logout(headers=None, body=None):
    print("[SampleApp] Logging out {}".format(headers))

@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))


# đăng kí ip và port đến server trung tâm
@app.route("/submit-info", methods=["POST"])
def submit_info(headers=None, body=None):

    print(f"[Submit] Received peer info: ")


# thêm 1 peer trong danh sách peer vào danh sách peer-connected với peer hiện tại
@app.route("/add-list", methods=["POST"])
def add_list(headers=None, body=None):
    """
    Add a peer to active list
    Example body: ip=127.0.0.1&port=9002
    """
    print("[SampleApp] add-List")

# Lấy danh sách những peer đã kết nối với peer hiện tại, chọn POST do cần đính kém vài thông tin
@app.route("/get-list", methods=["POST"])
def get_list(headers=None, body=None):
    """
    Return list of all active peers
    """
    print("[SampleApp] Get-List")

# Kết nối với 1 peer trong danh sách connected để chat đơn bằng /send-peer
@app.route("/connect-peer", methods=["POST"])
def connect_peer(headers=None, body=None):
    """
    Initiate connection to another peer
    """
    params = dict(pair.split("=", 1) for pair in body.split("&") if "=" in pair)
    target = params.get("target", "")
    print(f"[SampleApp] Connecting to peer {target}")

# Nhắn với tất cả connected peer
@app.route("/broadcast-peer", methods=["POST"])
def broadcast_peer(headers=None, body=None):
    """
    Broadcast message to all peers
    """
    print(f"Broadcasted message to peers.")

# Nhắn với peer nào đó
@app.route("/send-peer", methods=["POST"])
def send_peer(headers=None, body=None):
    """
    Send message directly to one peer
    Example body: target=127.0.0.1:9002&message=Hello
    """
    params = dict(pair.split("=", 1) for pair in body.split("&") if "=" in pair)
    target = params.get("target", "")
    message = params.get("message", "")
    print(f"[SampleApp] Send to {target}: {message}")
# đồng bộ để hiển thị lên frontend
@app.route("/get-messages", methods=["POST"])
def get_messages(headers=None, body=None):
    # trả lịch sử giữa current peer và target
    pass
# Lấy danh sách những peer đã kết nối với peer hiện tại
@app.route("/get-total-peer", methods=["GET"])
def get_list(headers=None, body=None):
    """
    Return list of all active peers
    """
    print("[SampleApp] Get-total-List")
@app.route("/get-connected", methods=["GET"])
def get_connected(headers=None, body=None):
    # trả danh sách các peer đã connect
    pass
# cái này để cập nhật peer_list khi có peer rời
@app.route('/remove-peer', methods=['POST'])
def remove_peer(headers=None, body=None):
    pass

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()
