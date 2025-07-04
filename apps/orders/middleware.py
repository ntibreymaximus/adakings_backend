"""
Middleware for handling connection errors and broken pipes gracefully.
"""
import logging
import socket
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class BrokenPipeMiddleware(MiddlewareMixin):
    """
    Middleware to handle broken pipe errors and connection issues gracefully.
    
    This middleware catches BrokenPipeError, ConnectionResetError, and similar
    network-related exceptions that occur when clients disconnect abruptly.
    """
    
    def process_exception(self, request, exception):
        """
        Handle broken pipe and connection reset errors.
        
        Args:
            request: The Django request object
            exception: The exception that was raised
            
        Returns:
            None to let Django handle the exception normally,
            or an HttpResponse to handle it gracefully
        """
        # List of network-related exceptions to handle gracefully
        network_exceptions = (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionAbortedError,
            socket.error,
            OSError,  # Can include broken pipe on some systems
        )
        
        # Check for broken pipe in exception message as well
        exception_str = str(exception).lower()
        broken_pipe_keywords = [
            'broken pipe',
            'connection reset',
            'connection aborted',
            'errno 32',  # Broken pipe errno
            'errno 104', # Connection reset by peer
        ]
        
        is_broken_pipe = (
            isinstance(exception, network_exceptions) or
            any(keyword in exception_str for keyword in broken_pipe_keywords)
        )
        
        if is_broken_pipe:
            # Don't log these common client disconnections unless in debug mode
            if logger.isEnabledFor(logging.DEBUG):
                client_info = self._get_client_info(request)
                logger.debug(
                    f"Client disconnected ({exception.__class__.__name__}): {client_info}"
                )
            
            # Return an empty response since the client is gone
            # This prevents the exception from propagating up the stack
            return HttpResponse(status=499)  # 499 Client Closed Request
        
        # For WebSocket-related errors during HTTP requests
        if 'websocket' in exception_str or 'ws' in exception_str:
            logger.warning(f"WebSocket-related error during HTTP request: {exception}")
            return HttpResponse(status=400)  # Bad Request
        
        # Let other exceptions be handled normally
        return None
    
    def _get_client_info(self, request):
        """Get basic client information for logging."""
        try:
            remote_addr = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            path = request.get_full_path()
            
            return f"IP: {remote_addr}, Path: {path}, User-Agent: {user_agent[:100]}"
        except Exception:
            return "Unknown client"
    
    def _get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip


class WebSocketConnectionMiddleware(MiddlewareMixin):
    """
    Middleware to handle WebSocket upgrade requests and connection issues.
    """
    
    def process_request(self, request):
        """
        Process WebSocket upgrade requests.
        
        Args:
            request: The Django request object
            
        Returns:
            None to continue processing, or an HttpResponse to handle immediately
        """
        # Check if this is a WebSocket upgrade request
        if self._is_websocket_request(request):
            # Add custom headers for WebSocket handling
            request.META['WEBSOCKET_REQUEST'] = True
            
            # Validate the WebSocket request
            if not self._validate_websocket_request(request):
                logger.warning(f"Invalid WebSocket request from {self._get_client_ip(request)}")
                return HttpResponse(status=400, content="Invalid WebSocket request")
        
        return None
    
    def _is_websocket_request(self, request):
        """Check if this is a WebSocket upgrade request."""
        connection = request.META.get('HTTP_CONNECTION', '').lower()
        upgrade = request.META.get('HTTP_UPGRADE', '').lower()
        
        return 'upgrade' in connection and upgrade == 'websocket'
    
    def _validate_websocket_request(self, request):
        """Basic validation for WebSocket requests."""
        required_headers = [
            'HTTP_SEC_WEBSOCKET_KEY',
            'HTTP_SEC_WEBSOCKET_VERSION',
        ]
        
        for header in required_headers:
            if header not in request.META:
                return False
        
        # Check WebSocket version
        ws_version = request.META.get('HTTP_SEC_WEBSOCKET_VERSION')
        if ws_version != '13':
            return False
        
        return True
    
    def _get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip
