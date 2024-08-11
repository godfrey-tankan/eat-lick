from functools import wraps
import logging
import hashlib
import hmac
from django.conf import settings
from django.http import JsonResponse

def validate_signature(payload, signature):
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(settings.APP_SECRET, "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)

def signature_required(view_func):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Extract the signature from headers
        signature = request.headers.get("X-Hub-Signature-256", "")[7:]  # Removing 'sha256='
        
        # Validate the signature
        if not validate_signature(request.body.decode("utf-8"), signature):
            logging.info("Signature verification failed!")
            return JsonResponse({"status": "error", "message": "Invalid signature"}, status=403)
        
        return view_func(request, *args, **kwargs)

    return _wrapped_view
