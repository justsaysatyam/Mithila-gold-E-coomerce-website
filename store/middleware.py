import os
import psutil
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class MemoryUsageMiddleware(MiddlewareMixin):
    """
    Middleware to log memory usage at the end of every request.
    Helps monitor if specific views are causing memory spikes.
    """
    def process_response(self, request, response):
        # Get process info
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024 * 1024) # Resident Set Size in MB
        
        # Log if usage is getting high (threshold 400MB)
        log_level = logging.INFO
        if mem_mb > 400:
            log_level = logging.WARNING
        
        logger.log(log_level, f"Memory Usage after {request.path}: {mem_mb:.2f} MB")
        
        # Optionally add a header for debugging in development
        if os.environ.get('DEBUG') == 'True':
            response['X-Memory-Usage-MB'] = f"{mem_mb:.2f}"
            
        return response
