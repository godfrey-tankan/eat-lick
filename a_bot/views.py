from django.shortcuts import render
import logging
from datetime import datetime
import json
import time
import random
from django.conf import settings
import requests as requests
import contextlib
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from home.models import *
from .responses import *

def get_greeting():
    current_hour = datetime.now().hour
    if 0 <= current_hour < 10:
        return "morning"
    elif 10 <= current_hour < 16:
        return "afternoon"
    else:
        return "evening"

def generate_response(response, wa_id, name):
    try:
        support_member = SupportMember.objects.get(phone_number=wa_id[0])
        
    except SupportMember.DoesNotExist:
        support_member = None
    try:
        check_ticket = Ticket.objects.filter(created_by=wa_id[0],status=PENDING_MODE).last()
    except Ticket.DoesNotExist:
        check_ticket = None
        
    if response.lower() in greeting_messages:
        time_of_day = get_greeting()
        return f"Golden  {time_of_day} {name.title()}, how can i help you today?"
    
    if support_member and support_member.user_mode == HELPING_MODE or check_ticket:
        response = handle_help(wa_id, response, name)
        return response

    if support_member and support_member.user_mode == ACCEPT_TICKET_MODE:
        response=accept_ticket(wa_id,name, response)
        return response
    
    if response:#not support_member or wa_id[0]=="263779586059":
        for help_message in help_messages:
            if help_message in response.lower() or len(response) > 5:
                response = handle_inquiry(wa_id, response, name)
                return response
            else:
                response = 'how can i help you today?'
        return response
    return "Hello,golden greetings."    

def get_text_message_input(recipient, text,media,template=False):
    if media:
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "document",
                # "type": "document",
                "document": {
                    "link": media,
                    "filename": text
                },
            }
        )
    if template:
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": "clava_welcome",
                    "language": {"code": "en-GB"},
                },
            }
        )
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )
    
def send_message(data,template=False):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {settings.ACCESS_TOKEN}",
    }
    url = f"https://graph.facebook.com/{settings.VERSION}/{settings.PHONE_NUMBER_ID}/messages"
    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=30
        )  
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        pass
        # logging.error("Timeout occurred while sending message")
        # return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (    
        requests.RequestException
    ) as e:  # This will catch any general request exception
        pass
        # logging.error(f"Request failed due to: {e}")
        # return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        return response

def process_whatsapp_message(body):
    data = body
    try:
        # phone_number_id = data['entry'][0]['changes'][0]['value']['metadata']['phone_number_id']
        phone_number_id =  [contact['wa_id'] for contact in data['entry'][0]['changes'][0]['value']['contacts']]
    except Exception as e:
        phone_number_id = ""

    try:
        profile_name = data['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']
    except Exception as e:
        profile_name = "User"
    try:
        message = body["entry"][0]["changes"][0]["value"]["messages"][0]
        message_body = message["text"]["body"]
    except Exception as e:
        message_body = "hello there, how can i help you today?"
    try:
        response = generate_response(message_body, phone_number_id, profile_name)
        data = get_text_message_input(phone_number_id, response,None,False)
        send_message(data)
    except Exception as e:
        ...

def send_message_template(recepient):
    return json.dumps(
    {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{recepient}",
        "type": "template",
        "template": {
            "namespace": "7a757027_47cc_4bb8_997e_e1fdb0600675",
            "name": "clava_home2",
            "language": {
                "code": "en",
            }
        }
    }
)

def is_valid_whatsapp_message(body):
    
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
def handle_inquiry(wa_id, response, name):
    ticket = Ticket.objects.create(
        title=f"Inquiry from {name}",
        description=response,
        created_by=wa_id[0], 
        status=OPEN_MODE
    )
    TicketLog.objects.create(
        ticket=ticket,
        status=OPEN_MODE,
        changed_by=wa_id[0]
    )
    with contextlib.suppress(SupportMember.DoesNotExist):
        broadcast_messages(name,ticket)

    return 'Thank you for contacting us. A support member will be assisting you shortly.'

def handle_help(wa_id, response, name):
    support_member = SupportMember.objects.filter(phone_number=wa_id[0]).first()
        
    if open_inquiries:= Ticket.objects.filter(status=PENDING_MODE,created_by=wa_id[0]).last() :
        for message in thank_you_messages:
            if message in response.lower():
                data = get_text_message_input(open_inquiries.assigned_to.phone_number, message, None)
                send_message(data)
                response = mark_as_resolved(open_inquiries.id)
                return response
        message = f"*Hello {open_inquiries.created_by},* \n{response}"
    if support_member:
        data = get_text_message_input(support_member.phone_number, response, None)
    else:
        data = get_text_message_input(open_inquiries.created_by, message, None)
    response = send_message(data)
    return response

def broadcast_messages(name,ticket=None,message=None):
    support_members = SupportMember.objects.all()
    for support_member in support_members:
        user_mobile = support_member.phone_number
        if message:
            support_member.user_status = HELPING_MODE
            message=message
        else:
            support_member.user_mode = ACCEPT_TICKET_MODE
            message=accept_ticket_response.format(support_member.username,name,ticket.id, ticket.description)
        support_member.save()
        try:
            data = get_text_message_input(user_mobile, message, None)
            response = send_message(data)
        except Exception as e:
            response = "error sending messages"
    return response
@csrf_exempt
def accept_ticket(wa_id,name, ticket_id):
    
    try:
        ticket_id = int(ticket_id)
    except Exception as e:
        return "Invalid ticket id"
    
    support_team_mobiles =[support_member.phone_number for support_member in SupportMember.objects.all()]
    if wa_id[0] not in support_team_mobiles:
        return "You are not authorized to accept tickets"
    support_member = SupportMember.objects.filter(phone_number=wa_id[0]).first()
    is_ticket_open = False
    try:
        if check_ticket := Ticket.objects.get(id=ticket_id):
            is_ticket_open = check_ticket.status.lower() == OPEN_MODE
        else:
            return "wrong ticket id"
    except Ticket.DoesNotExist:
        return "error ticket not available or already assigned "
    if is_ticket_open:
        ticket = Ticket.objects.get(id=ticket_id)
        ticket.assigned_to = support_member
        ticket.status = PENDING_MODE
        ticket.save()
        TicketLog.objects.create(
            ticket=ticket,
            status=PENDING_MODE,
            changed_by=support_member
        )
        support_member.user_mode=HELPING_MODE
        support_member.save()
        message=f"🟡ticket *#{ticket.id}* is now assigned to *{support_member.username if support_member.username.lower() != 'support' else support_member.phone_number}*"
        return broadcast_messages(name,None,message)
    else:
        return "Ticket not available or already assigned"

def mark_as_resolved( ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    ticket.status = RESOLVED_MODE
    ticket.closed_at = datetime.now()
    ticket.save()
    TicketLog.objects.create(
        ticket=ticket,
        status=RESOLVED_MODE,
        changed_by=ticket.assigned_to
    )
    support_member = SupportMember.objects.filter(phone_number=ticket.assigned_to).first()
    support_member.user_mode = WAITING_MODE
    support_member.save()
    message=f"ticket *#{ticket.id}* is now resolved ✅."
    return broadcast_messages(None,ticket,message)