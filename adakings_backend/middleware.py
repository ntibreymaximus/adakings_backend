"""
Middleware for Adakings Backend
Adds environment information to admin and API pages
Handles JWT token refresh warnings
"""

import os
import logging
from datetime import datetime, timedelta
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

logger = logging.getLogger(__name__)


class EnvironmentTagMiddleware(MiddlewareMixin):
    """
    Middleware that injects environment tag into admin and API pages
    """
    
    def process_response(self, request, response):
        """
        Inject environment tag into HTML responses for admin and API pages
        """
        # Only process HTML responses
        if not isinstance(response, HttpResponse):
            return response
            
        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response
            
        # Only inject on admin and API pages
        path = request.path
        if not (path.startswith('/admin/') or path.startswith('/api/')):
            return response
            
        # Don't inject on AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return response
            
        # Get environment info
        environment_info = self.get_environment_info()
        
        # Only inject if we should show the tag
        if not environment_info['show_tag']:
            return response
            
        # Create the environment tag HTML
        tag_html = f'''
        <div style="
            position: fixed;
            bottom: 10px;
            right: 10px;
            z-index: 9999;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            background-color: {environment_info['bg_color']};
        ">
            {environment_info['ui_tag']}
        </div>
        '''
        
        # Inject the tag into the HTML response
        content = response.content.decode('utf-8')
        
        # Try to inject before closing </body> tag
        if '</body>' in content:
            content = content.replace('</body>', tag_html + '</body>')
        # If no </body> tag, try before closing </html> tag
        elif '</html>' in content:
            content = content.replace('</html>', tag_html + '</html>')
        # If neither, append to the end
        else:
            content += tag_html
            
        # Update the response
        response.content = content.encode('utf-8')
        response['Content-Length'] = len(response.content)
        
        return response
    
    def get_environment_info(self):
        """
        Get environment information for the tag
        """
        # Determine environment
        is_railway = 'RAILWAY_ENVIRONMENT' in os.environ
        django_env = os.environ.get('DJANGO_ENVIRONMENT', 'local')
        railway_env = os.environ.get('RAILWAY_ENVIRONMENT', '')
        
        # Determine UI tag display logic
        if not is_railway:
            # Local development
            return {
                'ui_tag': 'LOCAL',
                'bg_color': '#4CAF50',
                'show_tag': True
            }
        elif django_env == 'development' or railway_env == 'dev':
            # Development server on Railway
            return {
                'ui_tag': 'DEV-SERVER',
                'bg_color': '#FF9800',
                'show_tag': True
            }
        else:
            # Production - don't show tag
            return {
                'ui_tag': None,
                'bg_color': None,
                'show_tag': False
            }


class TokenRefreshMiddleware(MiddlewareMixin):
    """
    Middleware to handle automatic token refresh warnings when tokens are about to expire.
    Adds refresh warnings to response headers when tokens are close to expiring.
    """
    
    def process_request(self, request):
        """Process the request and check token expiration."""
        # Only process API requests
        if not request.path.startswith('/api/'):
            return None
            
        # Skip token endpoints to avoid recursion
        if request.path in ['/api/token/', '/api/token/refresh/', '/api/token/verify/']:
            return None
            
        # Get authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        # Extract token
        token_string = auth_header.split(' ')[1]
        
        try:
            # Validate and decode token
            access_token = AccessToken(token_string)
            
            # Check if token is close to expiring (within 30 minutes)
            exp_timestamp = access_token['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            now = datetime.utcnow()
            time_until_expiry = exp_datetime - now
            
            # If token expires within 30 minutes, add warning header
            if time_until_expiry <= timedelta(minutes=30):
                # Store this info for the response
                request._token_refresh_warning = True
                request._token_expires_in = int(time_until_expiry.total_seconds())
                
                logger.info(f"Token for user {access_token.get('user_id')} expires in {time_until_expiry}")
                
        except (TokenError, InvalidToken) as e:
            # Token is invalid or expired, let the authentication backend handle it
            logger.debug(f"Token validation failed: {str(e)}")
            pass
        except Exception as e:
            # Log unexpected errors but don't block the request
            logger.error(f"Error in TokenRefreshMiddleware: {str(e)}")
            pass
            
        return None
        
    def process_response(self, request, response):
        """Add token refresh headers to the response if needed."""
        
        # Only process API responses
        if not request.path.startswith('/api/'):
            return response
            
        # Add token refresh warning headers if token is close to expiring
        if hasattr(request, '_token_refresh_warning') and request._token_refresh_warning:
            response['X-Token-Refresh-Warning'] = 'true'
            response['X-Token-Expires-In'] = str(request._token_expires_in)
            response['X-Token-Refresh-URL'] = '/api/token/refresh/'
            
        # Add token lifetime information to all authenticated API responses
        if response.status_code == 200 and hasattr(request, 'user') and request.user.is_authenticated:
            response['X-Access-Token-Lifetime'] = str(settings.ACCESS_TOKEN_LIFETIME.total_seconds())
            response['X-Refresh-Token-Lifetime'] = str(settings.REFRESH_TOKEN_LIFETIME.total_seconds())
            
        return response
