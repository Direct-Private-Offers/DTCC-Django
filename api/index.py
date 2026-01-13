import json

def handler(event, context):
    """Vercel serverless handler"""
    
    path = event. get('path', '/')
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json. dumps({
            'status': 'success',
            'message': 'Django API is running!',
            'path': path,
        })
    }
