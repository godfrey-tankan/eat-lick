import logging
import json
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .views import *
from .signatures import signature_required

logger = logging.getLogger(__name__)

@csrf_exempt
# @signature_required
def webhook(request):
    if request.method == "GET":
        return verify(request)
    elif request.method == "POST":
        return handle_message(request)

def handle_message(request):
    try:
        body = json.loads(request.body.decode("utf-8"))

        if (
            body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("statuses")
        ):
            # logger.info("Received a WhatsApp status update.")
            return JsonResponse({"status": "ok"}, status=200)

        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
        else:
            send_message_template(body)
        return JsonResponse({"status": "ok"}, status=200)

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON")
        return JsonResponse({"status": "error", "message": "Invalid JSON provided"}, status=400)

def verify(request):
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == settings.VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            return HttpResponse(challenge, status=200)
        else:
            logger.info("VERIFICATION_FAILED")
            return JsonResponse({"status": "error", "message": "Verification failed"}, status=403)
    else:
        logger.info("MISSING_PARAMETER")
        return JsonResponse({"status": "error", "message": "Missing parameters"}, status=400)
