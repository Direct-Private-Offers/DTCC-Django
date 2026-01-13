from http.server import BaseHTTPRequestHandler
import os
import sys
import json
from io import BytesIO

# Add project root to path
sys.path. insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
try:
    import django
    django.setup()
    from django.core.handlers.wsgi import WSGIHandler
    application = WSGIHandler()
    DJANGO_LOADED = True
except Exception as e:
    DJANGO_LOADED = False
    DJANGO_ERROR = str(e)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request()
    
    def do_POST(self):
        self._handle_request()
    
    def do_PUT(self):
        self._handle_request()
    
    def do_DELETE(self):
        self._handle_request()
    
    def do_PATCH(self):
        self._handle_request()
    
    def _handle_request(self):
        # Check if Django loaded
        if not DJANGO_LOADED:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                'error': 'Django failed to initialize',
                'details':  DJANGO_ERROR
            }
            self.wfile.write(json.dumps(error_response).encode())
            return
        
        # Get request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        
        # Build WSGI environ
        environ = {
            'REQUEST_METHOD': self.command,
            'SCRIPT_NAME': '',
            'PATH_INFO': self.path. split('? ')[0],
            'QUERY_STRING':  self.path.split('?')[1] if '?' in self. path else '',
            'CONTENT_TYPE': self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH': str(content_length),
            'SERVER_NAME': self.headers.get('Host', 'localhost').split(':')[0],
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL':  'HTTP/1.1',
            'wsgi.version':  (1, 0),
            'wsgi.url_scheme':  'https',
            'wsgi.input': BytesIO(body),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }
        
        # Add HTTP headers
        for key, value in self.headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key}'] = value
        
        # Response container
        response_status = [200]
        response_headers = []
        
        def start_response(status, headers, exc_info=None):
            response_status[0] = int(status.split(' ')[0])
            response_headers.extend(headers)
            return lambda s: None
        
        # Call Django
        try:
            result = application(environ, start_response)
            response_body = b''.join(result)
            
            # Send response
            self.send_response(response_status[0])
            for header, value in response_headers:
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(response_body)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                'error': 'Request failed',
                'details': str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())