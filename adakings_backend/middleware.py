"""
Middleware for Adakings Backend
Adds environment information to admin and API pages
"""

import os
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.template.loader import render_to_string


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
            top: 10px;
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
