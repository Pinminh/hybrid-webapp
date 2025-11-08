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



@app.route("/submit-info", methods=["POST"])
def submit_info(headers=None, body=None):

    print(f"[Submit] Received peer info: ")


peer_list = []  # simple in-memory tracker

@app.route("/add-list", methods=["POST"])
def add_list(headers=None, body=None):
    """
    Add a peer to active list
    Example body: ip=127.0.0.1&port=9002
    """
    params = dict(pair.split("=", 1) for pair in body.split("&") if "=" in pair)
    ip = params.get("ip", "")
    port = params.get("port", "")
    if ip and port:
        peer_list.append((ip, port))
        print(f"[SampleApp] Peer added to list: {ip}:{port}")
    else:
        print("[SampleApp] Failed to added peer to list")


@app.route("/get-list", methods=["GET"])
def get_list(headers=None, body=None):
    """
    Return list of all active peers
    """
    print("[SampleApp] Get-List in {} to {}".format(headers, body))



@app.route("/connect-peer", methods=["POST"])
def connect_peer(headers=None, body=None):
    """
    Initiate connection to another peer
    """
    params = dict(pair.split("=", 1) for pair in body.split("&") if "=" in pair)
    target = params.get("target", "")
    print(f"[SampleApp] Connecting to peer {target}")


@app.route("/broadcast-peer", methods=["POST"])
def broadcast_peer(headers=None, body=None):
    """
    Broadcast message to all peers
    """
    params = dict(pair.split("=", 1) for pair in body.split("&") if "=" in pair)
    message = params.get("message", "")
    print(f"[SampleApp] Broadcasting message: {message}")
    print(f"   → Sent to {len(peer_list)} peers")
    print(f"Broadcasted message to {len(peer_list)} peers.")



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

@app.route("/get-messages", methods=["POST"])
def get_messages(headers=None, body=None):
    # trả lịch sử giữa current peer và target
    pass

@app.route("/get-connected", methods=["GET"])
def get_connected(headers=None, body=None):
    # trả danh sách các peer đã connect
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
