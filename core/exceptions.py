from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError

def custom_exception_handler(exc, context):
    """
    Custom exception handler to match the API Conventions (S1-15).
    Format:
    {
        "error": {
            "code": "validation_error",
            "message": "Please correct the highlighted fields.",
            "fields": { ... }
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Restructure the response data
        if isinstance(exc, ValidationError):
            # DRF returns a dict of lists for field errors
            response.data = {
                "error": {
                    "code": "validation_error",
                    "message": "Please correct the highlighted fields.",
                    "fields": response.data
                }
            }
        else:
            # For other errors (404, 403, etc.)
            response.data = {
                "error": {
                    "code": response.status_code,
                    "message": response.data.get('detail', 'An error occurred.')
                }
            }
            
    return response