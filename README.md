# Hybrid Web Application - P2P Chat System

A lightweight peer-to-peer chat application built with a custom HTTP server framework in Python. This project implements session management, reverse proxy with load balancing, and P2P messaging capabilities without external dependencies.

## Overview

This is an educational project demonstrating fundamental web technologies including:
- Custom HTTP server implementation using raw sockets
- Session-based authentication with SQLite persistence
- Reverse proxy with multiple distribution policies
- Peer-to-peer direct messaging and broadcasting
- RESTful API routing framework

## Requirements

- **Python**: 3.8+ (no external packages required)
- Standard library modules only: `socket`, `threading`, `sqlite3`, `json`, `uuid`, `mimetypes`

## Project Architecture

### Core Components

```
hybrid-webapp/
├── daemon/              # HTTP server framework
│   ├── backend.py       # Backend server implementation
│   ├── proxy.py         # Reverse proxy with load balancing
│   ├── weaprous.py      # RESTful routing framework
│   ├── request.py       # HTTP request parser
│   ├── response.py      # HTTP response builder & P2P logic
│   ├── httpadapter.py   # HTTP adapter for request handling
│   ├── cookie.py        # Cookie management utilities
│   └── dictionary.py    # Case-insensitive dictionary
├── db/                  # Data persistence
│   ├── __init__.py      # Peer list and connection tracking
│   └── session.py       # SQLite-based session manager
├── www/                 # HTML pages
├── static/              # CSS, JS, images
├── config/              # Proxy configuration
└── apps/                # Sample applications
```

### Architecture Flow

1. **Proxy Layer** (`start_proxy.py`)
   - Listens on port 8080
   - Routes requests based on hostname
   - Supports round-robin and random load balancing

2. **Backend Layer** (`start_backend.py`)
   - Multiple backend instances (ports 9000-9002)
   - Handles HTTP requests
   - Serves static files and dynamic content

3. **Session Management**
   - SQLite-based persistent sessions
   - Cookie-based authentication
   - Automatic session cleanup

4. **P2P Communication**
   - Direct peer-to-peer socket connections
   - Real-time message broadcasting
   - Connection state management

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Pinminh/hybrid-webapp.git
cd hybrid-webapp
```

### 2. Verify Python Version

```bash
python --version  # Should be 3.8 or higher
```

No additional packages need to be installed.

## Running the Application

### Option 1: Run Backend Only (Simple Mode)

Start a single backend server:

```bash
python start_backend.py --server-ip 0.0.0.0 --server-port 9000
```

Access the application at: `http://localhost:9000`

### Option 2: Run with Proxy (Full Mode)

1. **Start multiple backend instances** (in separate terminals):

```bash
# Terminal 1
python start_backend.py --server-ip 127.0.0.1 --server-port 9000

# Terminal 2
python start_backend.py --server-ip 127.0.0.1 --server-port 9001

# Terminal 3
python start_backend.py --server-ip 127.0.0.1 --server-port 9002
```

2. **Start the proxy server**:

```bash
python start_proxy.py --server-ip 0.0.0.0 --server-port 8080
```

3. **Access via proxy**: `http://localhost:8080`

### Option 3: Run Sample RESTful App

```bash
python start_sampleapp.py --server-ip 0.0.0.0 --server-port 8000
```

## Configuration

### Proxy Configuration (`config/proxy.conf`)

```
host "127.0.0.1:8080" {
    proxy_pass http://127.0.0.1:9000;
    proxy_pass http://127.0.0.1:9001;
    proxy_pass http://127.0.0.1:9002;
    dist_policy round-robin;  # or 'random'
}
```

Supported policies:
- `round-robin`: Distributes requests evenly across backends
- `random`: Randomly selects a backend for each request

## Usage Guide

### 1. Authentication

**Default credentials:**
- Username: `admin`
- Password: `password`

**Session timeout:** 120 seconds (configurable in `db/session.py`)

### 2. P2P Chat Features

Once logged in, the dashboard provides:

#### Submit Peer Info
- Register your IP and port with the central server
- Example: `127.0.0.1:9001`

#### View Available Peers
- Click "Refresh List" to see all registered peers
- Add peers to your connection list

#### Connect to Peers
- Select a peer from "My Connections"
- Establishes direct P2P socket connection
- Opens 1-on-1 chat interface

#### Send Messages
- **Direct Message**: Select a peer and type your message
- **Broadcast**: Click "Broadcast Mode" to send to all connected peers

#### Message History
- Automatically syncs every second
- Messages persist in server memory (stored in `history_chat`)

## API Endpoints

### Authentication
- `POST /login` - User login (returns session cookie)
- `POST /logout` - Destroy session
- `GET /` or `/index.html` - Main page (requires valid session)

### Peer Management
- `POST /submit-info` - Register peer IP and port
- `GET /get-total-peer` - Get list of all registered peers
- `POST /get-list` - Get connected peers for a specific peer
- `POST /add-list` - Add peer to connection list

### P2P Communication
- `POST /connect-peer` - Establish P2P connection between two peers
- `POST /send-peer` - Send direct message to a peer
- `POST /broadcast-peer` - Broadcast message to all connected peers
- `POST /get-messages` - Retrieve chat history between two peers
- `POST /remove-peer` - Remove peer from active list

## Key Features

### 1. Custom HTTP Server
- Built from scratch using Python sockets
- Multi-threaded request handling
- MIME type detection and content serving
- HTTP header parsing and formatting

### 2. Session Management
- SQLite-based persistent storage
- Thread-safe operations
- Automatic expiration handling
- Secure cookie implementation

### 3. Reverse Proxy
- Virtual host routing
- Multiple load balancing strategies
- Dynamic backend selection
- Request forwarding with full headers

### 4. P2P Architecture
- Direct peer-to-peer connections
- Real-time message delivery
- Connection state tracking
- Broadcast capabilities

### 5. RESTful Framework (WeApRous)
- Decorator-based routing
- Method-specific handlers
- Easy endpoint registration
- Request/response abstraction

## Data Storage

### In-Memory Storage
- `peer_list`: All registered peers `[(ip, port), ...]`
- `connections`: Peer connection graph `{"ip:port": {"peer1", "peer2"}}`
- `history_chat`: Message history `{(peer1, peer2): [messages]}`

### Persistent Storage (SQLite)
- `db/sessions.db`: User sessions with expiration tracking

## Security Notes

⚠️ **This is an educational project**. Security considerations:

- No password hashing (plain text comparison)
- No HTTPS/TLS encryption
- Basic session management without advanced security
- No input validation or sanitization
- Suitable for learning purposes only

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process using the port
lsof -ti:9000 | xargs kill -9
```

### Session Database Locked
```bash
# Remove existing database
rm db/sessions.db
# Restart the backend
```

### Peer Connection Fails
- Ensure both peers have submitted their info
- Check firewall settings
- Verify IP addresses are correct
- Ensure listener threads are running

## Development

### Adding New Routes

```python
from daemon.weaprous import WeApRous

app = WeApRous()

@app.route('/your-endpoint', methods=['GET', 'POST'])
def your_handler(headers, body):
    # Your logic here
    return {'status': 'success'}

app.prepare_address('0.0.0.0', 8000)
app.run()
```

### Extending Response Handler

Edit `daemon/response.py` to add custom endpoints in the `build_response()` method.

## License

Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.

This project is part of the CO3093/CO3094 course and is released under the MIT License Agreement. Personal permission is granted to use and modify the source code for educational purposes while attending the course.

## Contributors

Project developed as part of the Computer Networks course at HCMC University of Technology.

## Acknowledgments

- Custom HTTP server framework inspired by traditional web server architecture
- Session management patterns from industry best practices
- P2P messaging concepts from distributed systems design
