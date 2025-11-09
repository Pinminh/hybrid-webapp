# reverse_proxy.py
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
start_proxy
~~~~~~~~~~~~~~~~~

This module serves as the entry point for launching a proxy server using Python's socket framework.
It parses command-line arguments to configure the server's IP address and port, reads virtual host
definitions from a configuration file, and initializes the proxy server with routing information.

Requirements:
--------------
- socket: provide socket networking interface.
- threading: enables concurrent client handling via threads.
- argparse: parses command-line arguments for server configuration.
- re: used for regular expression matching in configuration parsing
- response: response utilities.
- httpadapter: the class for handling HTTP requests.
- urlparse: parses URLs to extract host and port information.
- daemon.create_proxy: initializes and starts the proxy server.

"""

import socket
import threading
import argparse
import re
from urllib.parse import urlparse
from collections import defaultdict

from daemon import create_proxy

PROXY_PORT = 8080


def parse_virtual_hosts(config_file):
    """
    Parses virtual host blocks from a config file.

    :config_file (str): Path to the NGINX config file.
    :rtype list of dict: Each dict contains 'listen'and 'server_name'.
    """

    with open(config_file, 'r') as f:
        config_text = f.read()

    # Match each host block
    host_blocks = re.findall(r'host\s+"([^"]+)"\s*\{(.*?)\}', config_text, re.DOTALL)

    routes = {}
    for host, block in host_blocks:
        # Find all proxy_pass entries
        proxy_passes = re.findall(r'proxy_pass\s+http://([^\s;]+);', block)
        
        # Find dist_policy if present
        policy_match = re.search(r'dist_policy\s+([\w-]+)', block)
        dist_policy = policy_match.group(1) if policy_match else 'round-robin'
        
        # Build the routing configuration
        if len(proxy_passes) == 0:
            # No proxy_pass defined - skip or use default
            print(f"[Config] Warning: No proxy_pass defined for host '{host}'")
            routes[host] = (['127.0.0.1:9000'], 'round-robin')
            
        elif len(proxy_passes) == 1:
            # Single backend - no policy needed
            routes[host] = (proxy_passes[0], dist_policy)
            print(f"[Config] Host '{host}' - Single backend: {proxy_passes[0]}")
            
        else:
            # Multiple backends - policy will be applied
            routes[host] = (proxy_passes, dist_policy)
            print(f"[Config] Host '{host}' - Multiple backends with '{dist_policy}' policy:")
            for i, backend in enumerate(proxy_passes):
                print(f"         [{i}] {backend}")

    return routes


if __name__ == "__main__":
    """
    Entry point for launching the proxy server.

    This block parses command-line arguments to determine the server's IP address
    and port. It then calls `create_backend(ip, port)` to start the RESTful
    application server.

    :arg --server-ip (str): IP address to bind the server (default: 127.0.0.1).
    :arg --server-port (int): Port number to bind the server (default: 9000).
    """

    parser = argparse.ArgumentParser(prog='Proxy', description='', epilog='Proxy daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PROXY_PORT)

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    routes = parse_virtual_hosts("config/proxy.conf")

    create_proxy(ip, port, routes)
