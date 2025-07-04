# Broken Pipe Error Fixes for Adakings Backend

## Overview
This document outlines the fixes implemented to resolve broken pipe errors in the Adakings Backend Django application. Broken pipe errors typically occur when clients disconnect abruptly from WebSocket connections or HTTP requests.

## Root Causes of Broken Pipe Errors

1. **WebSocket Connection Drops**: Clients disconnecting from WebSocket connections without proper cleanup
2. **Network Interruptions**: Sudden network disconnections during request processing
3. **Client-Side Connection Termination**: Browsers or mobile apps closing connections abruptly
4. **Server Overload**: Too many concurrent connections causing connection drops
5. **Lack of Connection Management**: Missing heartbeat mechanisms and connection validation

## Implemented Fixes

### 1. Enhanced WebSocket Consumer (`apps/orders/consumers.py`)

**Improvements:**
- Added comprehensive error handling with try-catch blocks
- Implemented heartbeat mechanism to detect broken connections early
- Added graceful connection cleanup in disconnect handlers
- Enhanced logging for better debugging
- Added `safe_send()` method to handle send failures gracefully

**Key Features:**
```python
async def safe_send(self, data):
    """Safely send data over WebSocket with error handling."""
    try:
        await self.send(text_data=json.dumps(data))
    except Exception as e:
        logger.error(f"Error sending WebSocket message: {e}")
        raise StopConsumer()  # Mark connection as broken

async def heartbeat_loop(self):
    """Send periodic heartbeat to detect broken connections."""
    try:
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            await self.safe_send({
                'type': 'heartbeat',
                'timestamp': asyncio.get_event_loop().time()
            })
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        await self.close()
```

### 2. Broken Pipe Middleware (`apps/orders/middleware.py`)

**Purpose:** Catch and handle network-related exceptions at the Django level.

**Features:**
- Handles `BrokenPipeError`, `ConnectionResetError`, `ConnectionAbortedError`
- Logs client disconnections without treating them as server errors
- Returns appropriate HTTP status codes (499 for client disconnections)
- Validates WebSocket upgrade requests

**Example:**
```python
def process_exception(self, request, exception):
    network_exceptions = (
        BrokenPipeError,
        ConnectionResetError,
        ConnectionAbortedError,
        socket.error,
    )
    
    if isinstance(exception, network_exceptions):
        # Log but don't crash the server
        logger.info(f"Client disconnected: {exception}")
        return HttpResponse(status=499)  # Client Closed Request
```

### 3. Improved Gunicorn Configuration (`gunicorn.conf.py`)

**Enhancements:**
- Increased connection limits and timeouts
- Added signal handling to ignore SIGPIPE signals
- Enhanced worker lifecycle management
- Better error handling for worker processes

**Key Settings:**
```python
backlog = 2048  # Increased connection queue
worker_connections = 1000  # More connections per worker
timeout = 120  # Longer timeout for slow requests
graceful_timeout = 30  # Graceful shutdown timeout

# Ignore SIGPIPE in worker processes
def post_fork(server, worker):
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
```

### 4. Enhanced Django Settings

**Connection Management:**
- Added WebSocket timeout settings
- Configured database connection pooling for PostgreSQL
- Enhanced logging configuration for better debugging

**Key Settings:**
```python
WEBSOCKET_TIMEOUT = 300  # 5 minutes
WEBSOCKET_HEARTBEAT_INTERVAL = 30  # 30 seconds
CONNECTION_MAX_AGE = 600  # 10 minutes for DB connections
```

### 5. Startup Scripts with Error Handling

**Files:**
- `start_server.py`: Enhanced Python startup script
- `start_server_robust.bat`: Windows batch file

**Features:**
- Signal handling to prevent broken pipe crashes
- Environment validation and setup
- Multiple server options (Django, Daphne, Gunicorn)
- Error monitoring and logging

## Usage Instructions

### 1. Install Requirements
```bash
# Install Django Channels dependencies
pip install -r requirements-channels.txt

# Or use the automated script
./enable_websockets.bat  # Windows
```

### 2. Start the Server

**Option A: Using the enhanced startup script**
```bash
python start_server.py --server django --port 8000
python start_server.py --server daphne --port 8000  # For WebSockets
python start_server.py --server gunicorn --port 8001  # Production-like
```

**Option B: Using the Windows batch file**
```cmd
start_server_robust.bat
```

**Option C: Manual Django server**
```bash
python manage.py runserver 0.0.0.0:8000
```

### 3. Test WebSocket Connections

Connect to WebSocket endpoint with authentication:
```javascript
const token = 'your_jwt_token_here';
const ws = new WebSocket(`ws://localhost:8000/ws/orders/?token=${token}`);

ws.onopen = function(event) {
    console.log('WebSocket connected');
    
    // Send heartbeat every 25 seconds (before server timeout)
    setInterval(() => {
        ws.send(JSON.stringify({
            type: 'heartbeat',
            timestamp: Date.now()
        }));
    }, 25000);
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'heartbeat_ack') {
        console.log('Heartbeat acknowledged');
    }
};
```

## Monitoring and Troubleshooting

### 1. Log Files
- `logs/django.log`: General Django application logs
- `logs/websocket.log`: WebSocket-specific logs
- `logs/daphne_access.log`: Daphne server access logs (if using Daphne)

### 2. Common Error Patterns

**Broken Pipe Logs:**
```
INFO Client disconnected (BrokenPipeError): IP: 127.0.0.1, Path: /ws/orders/
WS WARNING Heartbeat error: [Errno 32] Broken pipe
```

**Connection Reset Logs:**
```
INFO Client disconnected (ConnectionResetError): IP: 192.168.1.100
WARNING Connection reset by peer
```

### 3. Debugging Steps

1. **Check WebSocket connections:**
   ```bash
   # Monitor active connections
   netstat -an | grep :8000
   ```

2. **Monitor server logs:**
   ```bash
   tail -f logs/django.log logs/websocket.log
   ```

3. **Test connection stability:**
   ```bash
   # Test HTTP endpoints
   curl -I http://localhost:8000/api/orders/
   
   # Test WebSocket (using wscat if available)
   wscat -c "ws://localhost:8000/ws/orders/?token=YOUR_TOKEN"
   ```

### 4. Performance Tuning

**For High Traffic:**
1. Use Daphne or Gunicorn instead of Django dev server
2. Increase worker processes in Gunicorn config
3. Configure Redis for channel layers in production
4. Monitor connection limits and timeouts

**WebSocket Optimization:**
1. Adjust heartbeat intervals based on client behavior
2. Implement connection pooling for database queries
3. Use Redis for scalable WebSocket message broadcasting

## Environment Variables

Add these to your `.env` file for optimal configuration:

```env
# WebSocket Settings
WEBSOCKET_TIMEOUT=300
WEBSOCKET_HEARTBEAT_INTERVAL=30

# Connection Settings
CONNECTION_MAX_AGE=600

# Logging
LOG_LEVEL=INFO
DJANGO_LOG_LEVEL=INFO

# Performance
MAX_UPLOAD_SIZE=10485760
```

## Production Considerations

1. **Use a reverse proxy** (Nginx) to handle connection management
2. **Configure Redis** for channel layers in production
3. **Monitor connection metrics** using tools like Prometheus
4. **Implement rate limiting** to prevent connection abuse
5. **Use SSL/TLS** for secure WebSocket connections (WSS)

## Testing the Fixes

1. **Manual Testing:**
   - Start the server using the enhanced startup scripts
   - Connect multiple WebSocket clients
   - Abruptly close client connections
   - Monitor logs for graceful handling

2. **Load Testing:**
   - Use tools like `websocket-king` or `artillery` for WebSocket load testing
   - Monitor server behavior under high connection loads

3. **Network Simulation:**
   - Use network simulation tools to test connection drops
   - Verify server stability under various network conditions

## Conclusion

These fixes provide comprehensive handling of broken pipe errors in the Adakings Backend:

- **Graceful Error Handling**: Network errors are caught and logged without crashing the server
- **Proactive Connection Management**: Heartbeat mechanisms detect broken connections early
- **Enhanced Monitoring**: Detailed logging helps with debugging and monitoring
- **Multiple Server Options**: Choose the right server for your deployment scenario
- **Production Ready**: Configurations suitable for both development and production

The server should now handle client disconnections gracefully and maintain stability under various network conditions.
