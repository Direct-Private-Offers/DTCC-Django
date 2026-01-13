import os
import sys
import traceback
from io import BytesIO

# Add project root to path
sys.path. insert(0, os.path. dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django with error catching
try:
    import django
    django.setup()
    from django.core.handlers.wsgi import WSGIHandler
    application = WSGIHandler()
    DJANGO_LOADED = True
except Exception as e: 
    DJANGO_LOADED = False
    DJANGO_ERROR = traceback.format_exc()

def handler(event, context):
    """Vercel serverless function handler for Django"""
    
    # If Django failed to load, return the error
    if not DJANGO_LOADED:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': f'{{"error": "Django failed to initialize", "traceback": {repr(DJANGO_ERROR)}}}'
        }
    
    # Extract request details
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    body = event.get('body', '')
    query = event.get('rawQuery', '')
    
    # Build WSGI environ
    environ = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query,
        'CONTENT_TYPE':  headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(body)) if body else '0',
        'SERVER_NAME': headers.get('host', 'localhost').split(':')[0],
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi. version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(body. encode('utf-8') if isinstance(body, str) else body),
        'wsgi.errors':  sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add HTTP headers to environ
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # Response container
    response = {'statusCode': 200, 'headers': {}, 'body': ''}
    
    def start_response(status, response_headers, exc_info=None):
        response['statusCode'] = int(status.split(' ')[0])
        for header, value in response_headers:
            response['headers'][header] = value
        return lambda s: None
    
    # Execute Django WSGI app
    try:
        result = application(environ, start_response)
        response['body'] = b''.join(result).decode('utf-8')
    except Exception as e:
        response['statusCode'] = 500
        response['headers'] = {'Content-Type': 'application/json'}
        error_detail = traceback.format_exc()
        response['body'] = f'{{"error": "Request failed", "traceback": {repr(error_detail)}}}'
    
    return response
