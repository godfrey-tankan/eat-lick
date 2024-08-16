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
from django.utils import timezone

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
        inquirer = Inquirer.objects.get(phone_number=wa_id[0])
    except Inquirer.DoesNotExist:
        inquirer = None
    if inquirer:
        check_ticket = Ticket.objects.filter(created_by=inquirer.id,status=PENDING_MODE).first()
    else:
        check_ticket = None
    if support_member:
        if response.lower() in support_member_help_requests:
            return request_assistance_support_member(support_member)
        return 'not help request response'
 
    if support_member and support_member.user_status == SUPPORT_MEMBER_ASSISTING_MODE or support_member.user_status == SUPPORT_MEMBER_ASSISTANCE_MODE:
        return assist_support_member(support_member, response)
        
    if response.lower() in greeting_messages:
        time_of_day = get_greeting()
        name = inquirer.username.split()[0] if inquirer else name
        return f"Golden  {time_of_day} {name.title()}, how can i help you today?"
    
    if support_member and support_member.user_mode == HELPING_MODE or check_ticket:
        return handle_help(wa_id, response, name)

    if support_member and support_member.user_mode == ACCEPT_TICKET_MODE:
        return accept_ticket(wa_id,name, response)
    
    if not support_member :
        for thank_you_message in thank_you_messages:
            if thank_you_message in response.lower():
                return "You are welcome."
        for help_message in help_messages:
            if help_message in response.lower() or len(response) > 4:
                return handle_inquiry(wa_id, response, name)
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
    inquirer_obj = Inquirer.objects.filter(phone_number=wa_id[0]).first()
    if not inquirer_obj:
        Inquirer.objects.create(phone_number=wa_id[0],user_mode=NAMES_MODE)
        return f'Hello {name}, please provide your *first name* and *last name*'
    else:
        if inquirer_obj.user_mode == NAMES_MODE or inquirer_obj.user_mode == BRANCH_MODE:
            if inquirer_obj.user_mode == BRANCH_MODE:
                inquirer_obj.branch = response
                inquirer_obj.user_mode = INQUIRY_MODE
                inquirer_obj.save()
                return f'Hello {name.title()}, What is your inquiry?'
            names = response.split()
            if len(names) < 2:
                return 'Please provide your first name and last name'
            inquirer_obj.username = response
            inquirer_obj.save()
            if inquirer_obj.branch:
                inquirer_obj.user_mode = INQUIRY_MODE
                inquirer_obj.save()
                return f'Hello {names[0].title()}, What is your inquiry?'
            inquirer_obj.user_mode=BRANCH_MODE
            inquirer_obj.save()
            return 'Please provide your branch'
    try:
        open_inquiries = Ticket.objects.filter(status=OPEN_MODE,created_by=inquirer_obj.id).first()
    except Ticket.DoesNotExist:
        open_inquiries = Ticket.objects.filter(status=PENDING_MODE,created_by=inquirer_obj.id).first()
    if open_inquiries:
        return "Your inquiry is already being attended to."
    ticket = Ticket.objects.create(
        title=f"Inquiry from {name}",
        description=response,
        created_by=inquirer_obj, 
        branch_opened =inquirer_obj.branch,
        status=OPEN_MODE
    )
    TicketLog.objects.create(
        ticket=ticket,
        status=OPEN_MODE,
        changed_by=inquirer_obj
    )
    with contextlib.suppress(SupportMember.DoesNotExist):
        broadcast_messages(name,ticket)
    return 'Thank you for contacting us. A support member will be assisting you shortly.'

def handle_help(wa_id, response, name):
    support_member = SupportMember.objects.filter(phone_number=wa_id[0]).first()
    inquirer = Inquirer.objects.filter(phone_number=wa_id[0]).first()
    try:
        open_inquiries = Ticket.objects.filter(status=PENDING_MODE,created_by=inquirer).first()
    except Ticket.DoesNotExist:
        open_inquiries = None
    if support_member:
        try:
            open_inquiries = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member).first()
        except Ticket.DoesNotExist:
            open_inquiries = None

    if open_inquiries:
        if support_member:
            print('support member')
            try:
                Message.objects.create(ticket_id=open_inquiries,inquirer=None, support_member=support_member, content=response)
            except Exception as e:
                print('error saving message')
            if response in resolve_ticket_responses:
                return mark_as_resolved(open_inquiries.id)
            if response in close_ticket_responses:
                return mark_as_resolved(open_inquiries.id,True)
            data = get_text_message_input(open_inquiries.created_by.phone_number, response, None)
            return send_message(data)
        else:
            print('not support member')
            try:
                inquirer = Inquirer.objects.filter(phone_number=wa_id[0]).first()
                # save_messages(open_inquiries.id,inquirer,None,response)
                Message.objects.create(ticket_id=open_inquiries,inquirer=inquirer, support_member=None, content=response)
            except Exception as e:
                print('error saving message')
            if inquirer and inquirer.user_mode == CONFIRM_RESPONSE:
                if '1' in response:
                    return mark_as_resolved(open_inquiries.id)
                elif '2' in response:
                    return mark_as_resolved(open_inquiries.id,True)
                
            for message in thank_you_messages:
                if message in response.lower():
                    print('matched')
                    if inquirer:
                        inquirer.user_mode = CONFIRM_RESPONSE
                        inquirer.save()
                        return is_inquirer_helped.format(inquirer.username.split()[0].title(),open_inquiries.description)
                        
                    data = get_text_message_input(open_inquiries.assigned_to.phone_number, response, None)
                    send_message(data)
                    data = get_text_message_input(open_inquiries.assigned_to.phone_number,inquirer_helped_assumed_messages , None)
                    return send_message(data)
                else:
                    print('replying to support member')
                    data = get_text_message_input(open_inquiries.assigned_to.phone_number, response, None)
                    return send_message(data)
    return "You have no open inquiries"
def broadcast_messages(name,ticket=None,message=None,phone_number=None):
    support_members = SupportMember.objects.all()
    for support_member in support_members:
        user_mobile = support_member.phone_number
        if user_mobile == phone_number:
            ...
        else:
            if message:
                message=message
            else:
                pending_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member.id).first()
                if not pending_ticket:
                    support_member.user_mode = ACCEPT_TICKET_MODE
                    message=accept_ticket_response.format(name,ticket.id, ticket.description)
                    support_member.save()
            try:
                data = get_text_message_input(user_mobile, message, None)
                response = send_message(data)
            except Exception as e:
                response = "error sending messages"
    return response
def save_messages(ticket_id,inquirer=None, support_member=None, content=None):
    Message.objects.create(ticket_id=ticket_id,inquirer=inquirer, support_member=support_member, content=content)
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
    try:
        assigned_tickets = Ticket.objects.filter(
            assigned_to=support_member.id, status=PENDING_MODE
        ).first()
        if assigned_tickets:
            return "You already have an open ticket"
    except Ticket.DoesNotExist:
        assigned_tickets = None
    is_ticket_open = False
    try:
        check_ticket = Ticket.objects.get(id=ticket_id)
        if check_ticket:
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
        support_member.user_status = HELPING_MODE

        support_member.save()
        message=f"🟡ticket *#{ticket.id}* is now assigned to *{support_member.username if support_member.username.lower() != 'support' else support_member.phone_number}*"
        return broadcast_messages(name,None,message)
    else:
        return "Ticket not available or already assigned"

def request_assistance_support_member(support_member):
    support_members = SupportMember.objects.all()
    for member in support_members:
        if member.id != support_member.id:
            member.user_status = SUPPORT_MEMBER_ASSISTING_MODE
        else:
            member.user_mode = SUPPORT_MEMBER_ASSISTANCE_MODE
        member.save()
    message = f'🔔 *{support_member.username}* is requesting assistance,please reply to assist. or type pass to skip this request.'
    broadcast_messages(None,None,message,support_member.phone_number)
    return "You are now interacting with other support members,What do you need help with?"

def assist_support_member(support_member, response):
    if support_member.user_status == SUPPORT_MEMBER_ASSISTING_MODE:
        if 'pass' in response.lower():
            support_member.user_status = HELPING_MODE
            support_member.save()
            return "You have passed the request,you can now continue with your current task."
        broadcast_messages(None,None,response,support_member.phone_number)
    elif support_member.user_status == SUPPORT_MEMBER_ASSISTANCE_MODE:
        if response.lower() in thank_you_messages:
            support_members = SupportMember.objects.all()
            for member in support_members:
                member.user_status = HELPING_MODE
                member.save()
            return "You are now back to helping mode, you're now chatting with the inquirer."
        broadcast_messages(None,None,response,support_member.phone_number)
    
def mark_as_resolved( ticket_id,is_closed=False):
    naive_datetime = datetime.now()
    aware_datetime = timezone.make_aware(naive_datetime)
    if is_closed:
        ticket = Ticket.objects.get(id=ticket_id)
        ticket.status = CLOSED_MODE
        ticket.closed_at = aware_datetime
        ticket.save()
        TicketLog.objects.create(
            ticket=ticket,
            status=CLOSED_MODE,
            changed_by=ticket.assigned_to
        )
        support_member = SupportMember.objects.filter(id=ticket.assigned_to.id).first()
        support_member.user_mode = ACCEPT_TICKET_MODE
        support_member.user_status = ACCEPT_TICKET_MODE
        support_member.save()
        message=f"ticket *#{ticket.id}* has been closed ❌."
        reply = f'Your inquiry has been closed.'
        data = get_text_message_input(ticket.created_by.phone_number, reply, None)
        send_message(data)
        return broadcast_messages(None,ticket,message)
    
    ticket = Ticket.objects.get(id=ticket_id)
    ticket.status = RESOLVED_MODE
    ticket.resolved_at = aware_datetime
    ticket.save()
    TicketLog.objects.create(
        ticket=ticket,
        status=RESOLVED_MODE,
        changed_by=ticket.assigned_to
    )
    support_member = SupportMember.objects.filter(id=ticket.assigned_to.id).first()
    support_member.user_mode = ACCEPT_TICKET_MODE
    support_member.user_status = ACCEPT_TICKET_MODE
    support_member.save()
    message=f"ticket *#{ticket.id}* is now resolved ✅ by {ticket.assigned_to.username}."
    reply = f'Your inquiry *{ticket.description}* has been marked as resolved'
    data = get_text_message_input(ticket.created_by.phone_number, reply, None)
    send_message(data)
    return broadcast_messages(None,ticket,message)
def web_messaging(ticket_id,message=None,is_broadcasting=False):
    if message in resolve_ticket_responses:
        return mark_as_resolved(ticket_id)
    if message in close_ticket_responses:
        return mark_as_resolved(ticket_id,True)
    if is_broadcasting:
        ticket = Ticket.objects.filter(id=ticket_id).first()
        message =f'Hello {ticket.assigned_to.username}\nInquiry *#{ticket.id}*:\n- {ticket.description}\n\nhas been escalated to you,you can start helping the inquirer now.'
        support_member = SupportMember.objects.filter(id=ticket.assigned_to.id).first()
        support_member.user_mode = HELPING_MODE
        support_member.user_status = HELPING_MODE
        support_member.save()
        data = get_text_message_input(ticket.assigned_to.phone_number, message, None)
        return send_message(data)
    ticket = Ticket.objects.filter(id=ticket_id).first()
    data =get_text_message_input(ticket.created_by.phone_number, message, None)
    return send_message(data)