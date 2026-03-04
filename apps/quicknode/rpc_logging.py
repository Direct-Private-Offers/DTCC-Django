import logging

def log_rpc_call(request, method, params):
    logger = logging.getLogger('quicknode.rpc')
    logger.info({
        'user': str(request.user) if hasattr(request, 'user') else None,
        'ip': request.META.get('REMOTE_ADDR'),
        'method': method,
        'params': params,
        'headers': dict(request.headers),
    })
