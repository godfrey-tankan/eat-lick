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
from django.core.files.base import ContentFile
from django.utils import timezone
import re

def get_greeting():
    current_hour = datetime.now().hour
    if 0 <= current_hour < 10:
        return "morning"
    elif 10 <= current_hour < 16:
        return "afternoon"
    else:
        return "evening"

def generate_response(response, wa_id, name,message_type,message_id):
    try:
        support_member = SupportMember.objects.filter(phone_number=wa_id[0]).first()
        if support_member:
            name = support_member.username.split()[0]
    except SupportMember.DoesNotExist:
        support_member = None
    try:
        inquirer = Inquirer.objects.filter(phone_number=wa_id[0]).first()
    except Inquirer.DoesNotExist:
        inquirer = None
    if inquirer:
        name = inquirer.username.split()[0]
        check_ticket = Ticket.objects.filter(created_by=inquirer.id,status=PENDING_MODE).first()
        if inquirer.user_status == NEW_TICKET_MODE:
            return handle_inquiry(wa_id, response, name)
    else:
        check_ticket = None
        
    if response.lower() in greeting_messages:
        time_of_day = get_greeting()
        return f"Golden  {time_of_day} {name.title()}, how can i help you today?"
    if support_member:
        if support_member.user_status==NEW_TICKET_ACCEPT_MODE:
            if response == '1' or response == '1.':
                support_member.user_status = HELPING_MODE
                support_member.save()
                return 'You have skipped the ticket, you can now continue with your current task.'
        
        if support_member.user_status == RESUME_MODE:
            return resume_assistance(support_member,response)

        if '#resume' in response.lower() or '#conti' in response.lower():
            support_member.user_status = RESUME_MODE
            support_member.save()
            return resume_assistance(support_member,response)
        if response.lower() in support_member_help_requests:
            return request_assistance_support_member(support_member.id)
        if support_member.user_status in [
            SUPPORT_MEMBER_ASSISTING_MODE,
            SUPPORT_MEMBER_ASSISTANCE_MODE,
        ]:
            return assist_support_member(support_member.id,response,message_type,message_id)

        if support_member.user_mode == ACCEPT_TICKET_MODE or support_member.user_status == NEW_TICKET_ACCEPT_MODE:
            return accept_ticket(wa_id,name, response)
        
        if support_member and support_member.user_mode == HELPING_MODE:
            return handle_help(wa_id, response, name,message_type,message_id)

        return 'hello! how can i help you today?'
    
    if check_ticket:
        if inquirer and inquirer.user_mode== CONFIRM_RESPONSE:
            if response == '1' or response == '1.':
                mark_as_resolved(check_ticket.id)
                data = get_text_message_input(inquirer.phone_number, 'Hello', 'rate_support_user',True)
                return send_message(data)
            elif response =='2' or response == '2.':
                mark_as_resolved(check_ticket.id,True)
                data = get_text_message_input(inquirer.phone_number, 'Hello', 'rate_support_user',True)
                return send_message(data)
        return handle_help(wa_id, response, name,message_type,message_id)

    if inquirer and inquirer.user_status == SUPPORT_RATING:
        if not '/' in response:
            data = get_text_message_input(inquirer.phone_number, 'Hello', 'rate_support_user',True)
            return send_message(data)
        return inquirer_assistance_response(response, check_ticket, inquirer)
    
    if not support_member :
        for thank_you_message in thank_you_messages:
            if thank_you_message in response.lower():
                return "You are welcome."
        # for help_message in help_messages:
        #     if help_message in response.lower() or len(response) > :
        return handle_inquiry(wa_id, response, name)
    
    return f"Hello,golden greetings. How can i help you today?"    

def get_text_message_input(recipient, text,name=None,template=False):

    if template:
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": f"{name}",
                    "language": {"code": "en"},
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
        phone_number_id = [contact['wa_id'] for contact in data['entry'][0]['changes'][0]['value']['contacts']]
    except Exception as e:
        phone_number_id = ""

    try:
        profile_name = data['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']
    except Exception as e:
        profile_name = "User"

    try:
        process_message_file_type(
            body, phone_number_id, profile_name
        )
    except Exception as e:
        print(f"Error processing message: {e}")
        ...

def process_message_file_type(body, phone_number_id, profile_name):
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_type = message["type"]
    message_id = None
    try:
        support_member= SupportMember.objects.get(phone_number=phone_number_id[0])
    except SupportMember.DoesNotExist:
        support_member = None
    try:
        inquirer = Inquirer.objects.get(phone_number=phone_number_id[0])
    except Inquirer.DoesNotExist:
        inquirer = None
    try:
        support_member_pending_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member,ticket_mode='other').first()
    except Ticket.DoesNotExist:
        support_member_pending_ticket = None
    try:
        inquirer_pending_ticket = Ticket.objects.filter(status=PENDING_MODE,created_by=inquirer,ticket_mode='other').first()
    except Ticket.DoesNotExist:
        inquirer_pending_ticket = None
    if support_member and support_member.user_status in  [SUPPORT_MEMBER_ASSISTANCE_MODE ,SUPPORT_MEMBER_ASSISTING]:
        message_body =message_id= None
        if message_type == "audio":
            message_id = message["audio"]["id"]
        if message_type == "video":
            message_id = message["video"]["id"]
            
        if message_type == "document":
            message_id = message["document"]["id"]
            
        if message_type == "image":
            message_id = message["image"]["id"]
        if message_type == "text":
            message_body = message["text"]["body"]
        return assist_support_member(support_member.id, message_body,message_type,message_id)
        
    if message_type == "audio":
        message_id = message["audio"]["id"]
        if support_member and support_member_pending_ticket:
            Message.objects.create(ticket_id=support_member_pending_ticket, support_member=support_member, content='sent audio message')
            data = get_audio_message_input(support_member_pending_ticket.created_by.phone_number, message_id)
        if inquirer and inquirer_pending_ticket:
            Message.objects.create(ticket_id=inquirer_pending_ticket, inquirer=inquirer, content='sent audio message')
            data = get_audio_message_input(inquirer_pending_ticket.assigned_to.phone_number, message_id)
        return send_message(data)
    elif message_type =='button':
        message_body = message["button"]["text"]
    
    elif message_type == "video":
        message_id = message["video"]["id"]
        if support_member and support_member_pending_ticket:
            Message.objects.create(ticket_id=support_member_pending_ticket, support_member=support_member, content='sent video message')
            data = get_video_message(support_member_pending_ticket.created_by.phone_number, message_id)
        if inquirer and inquirer_pending_ticket:
            Message.objects.create(ticket_id=inquirer_pending_ticket, inquirer=inquirer, content='sent video message')
            data = get_video_message(inquirer_pending_ticket.assigned_to.phone_number, message_id)
        return send_message(data)
    
    elif message_type == "document":
        message_id = message["document"]["id"]
        if support_member and support_member_pending_ticket:
            Message.objects.create(ticket_id=support_member_pending_ticket, support_member=support_member, content='sent document message')
            data = get_document_message(support_member_pending_ticket.created_by.phone_number, message_id)
        if inquirer and inquirer_pending_ticket:
            Message.objects.create(ticket_id=inquirer_pending_ticket, inquirer=inquirer, content='sent document message')
            data = get_document_message(inquirer_pending_ticket.assigned_to.phone_number, message_id)
        return send_message(data)

    elif message_type == "image":
        message_id = message["image"]["id"]
        if support_member and support_member_pending_ticket:
            Message.objects.create(ticket_id=support_member_pending_ticket, support_member=support_member, content='sent image message')
            data = get_image_message(support_member_pending_ticket.created_by.phone_number, message_id)
        if inquirer and inquirer_pending_ticket:
            Message.objects.create(ticket_id=inquirer_pending_ticket, inquirer=inquirer, content='sent image message')
            data = get_image_message(inquirer_pending_ticket.assigned_to.phone_number, message_id)
        return send_message(data)
    elif message_type == "text":
        message_body = message["text"]["body"]
        
    response = generate_response(message_body, phone_number_id, profile_name,message_type,message_id)
    data = get_text_message_input(phone_number_id, response, None, False)
    return send_message(data)

def get_audio_message_input(phone_number_id, audio_id):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number_id,
            "type": "audio",
            "audio": {
                'id':audio_id
            },
        }
    )

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
                return f'Hello {inquirer_obj.username.split()[0].title()}, What is your inquiry?'
            names = response.split()
            if len(names) < 2:
                return 'Please provide your first name and last name'
            inquirer_obj.username = response
            inquirer_obj.save()
            if inquirer_obj.branch:
                inquirer_obj.user_mode = INQUIRY_MODE
                inquirer_obj.save()
                return f'Hello {inquirer_obj.username.split()[0].title()}, What is your inquiry?'
            inquirer_obj.user_mode=BRANCH_MODE
            inquirer_obj.save()
            return 'Please provide your branch'
    try:
        open_inquiries = Ticket.objects.filter(status=OPEN_MODE,created_by=inquirer_obj.id).first()
    except Ticket.DoesNotExist:
        open_inquiries = Ticket.objects.filter(status=PENDING_MODE,created_by=inquirer_obj.id).first()
    if open_inquiries:
        for no_response in deny_open_new_ticket:
            if no_response in response.lower():
                return 'Your inquiry is still being attended to.Please wait for a response.'
        # return "You have an open inquiry, Do you want to open a new inquiry?"
        if not inquirer_obj.user_status == NEW_TICKET_MODE:
            return "You have an open inquiry, Do you want to open a new inquiry?"
        if inquirer_obj.user_status == NEW_TICKET_MODE:
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
            inquirer_obj.user_status = INQUIRY_MODE
            inquirer_obj.save()
            with contextlib.suppress(SupportMember.DoesNotExist):
                broadcast_messages(name,ticket)
            return new_inquiry_opened_response
        for yes_response in confirm_open_new_ticket:
            if yes_response in response.lower():
                inquirer_obj.user_status = NEW_TICKET_MODE
                inquirer_obj.save()
                open_inquiries.ticket_mode = QUEUED_MODE
                open_inquiries.save()
                new_message = f"Hi {open_inquiries.assigned_to.username.split()[0].title()}, {inquirer_obj.username} has opened a new inquiry,Your pending ticket (#{open_inquiries.id})  with them have now been queued.You can resume assisting them anytime by replying with #resume or #continue."
                data = get_text_message_input(open_inquiries.assigned_to.phone_number,new_message ,None)
                send_message(data)
                return 'What is your inquiry?'

    if len(response) < 5:
        return 'Please provide a detailed inquiry'
    if response == 'hello i want help':
        return 'Hello what do you need help with?'
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

def handle_help(wa_id, response, name,message_type,message_id):
    support_member = SupportMember.objects.filter(phone_number=wa_id[0]).first()
    inquirer = Inquirer.objects.filter(phone_number=wa_id[0]).first()
    try:
        open_inquiries = Ticket.objects.filter(status=PENDING_MODE,created_by=inquirer,ticket_mode='other').first()
    except Ticket.DoesNotExist:
        open_inquiries = None
    if support_member:
        try:
            open_inquiries = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member,ticket_mode='other').first()
        except Ticket.DoesNotExist:
            open_inquiries = None
   
    if open_inquiries:
        if support_member:
            try:
                Message.objects.create(ticket_id=open_inquiries,inquirer=None, support_member=support_member, content=response)
            except Exception as e:
                ...
            if response in resolve_ticket_responses:
                return mark_as_resolved(open_inquiries.id)
            if response in close_ticket_responses:
                return mark_as_resolved(open_inquiries.id,True)
            data = get_text_message_input(open_inquiries.created_by.phone_number, response, None)
            return send_message(data)
        else:
            if response in resolve_ticket_responses:
                return mark_as_resolved(open_inquiries.id)
            try:
                inquirer = Inquirer.objects.filter(phone_number=wa_id[0]).first()
                Message.objects.create(ticket_id=open_inquiries,inquirer=inquirer, support_member=None, content=response)
            except Exception as e:
                ...
            
            for message in thank_you_messages:
                if message in response.lower():
                    if inquirer:
                        inquirer.user_mode = CONFIRM_RESPONSE
                        inquirer.user_status = SUPPORT_RATING
                        inquirer.save()
                        data = get_text_message_input(inquirer.phone_number, 'Hello', 'customer_helped_template',True)
                        # is_inquirer_helped.format(inquirer.username.split()[0].title(),open_inquiries.description)
                        return send_message(data)

                    data = get_text_message_input(open_inquiries.assigned_to.phone_number, response, None)
                    send_message(data)
                    data = get_text_message_input(open_inquiries.assigned_to.phone_number,inquirer_helped_assumed_messages , None)
                else:
                    data = get_text_message_input(open_inquiries.assigned_to.phone_number, response, None)
                return send_message(data)
    if inquirer:
        return process_queued_tickets(inquirer, None,response)
    else:
        return process_queued_tickets(None,support_member,response)
        
def process_queued_tickets(inquirer=None, support_member=None,response=None):
    if support_member:
        all_queued_tickets = Ticket.objects.filter(ticket_mode=QUEUED_MODE,assigned_to=support_member)
        if all_queued_tickets:
            if not '#' in response:
                tickets_info = 'Please select the ticket you want to resume assisting:\n\n'
                for queued_ticket in all_queued_tickets:
                    tickets_info +=f"- Ticket Number: # *{queued_ticket.id}*\nDescription: {queued_ticket.description}\n"
                tickets_info += '\nReply with #ticketNo eg *#4* to resume assisting the inquirer.'
                data = get_text_message_input(support_member.phone_number, tickets_info, None)
                return send_message(data)
            else:
                match = re.search(r'#(\d+)', response)
                if match:
                    ticket_obj = Ticket.objects.filter(id=match.group(1)).first()
                    if ticket_obj:
                        ticket_obj.ticket_mode = 'other'
                        ticket_obj.save()
                        message= f'You are now assisting the inquirer with ticket number *{ticket_obj.id}*'
                        data = get_text_message_input(support_member.phone_number,message , None)
                        return send_message(data)
                    else:
                        return "Ticket not found"
                else:
                    return "Please check the ticket number and try again, use #ticketNo eg *#4*"
    
    if inquirer:
        queued_tickets = Ticket.objects.filter(ticket_mode=QUEUED_MODE,created_by=inquirer)
        if queued_tickets:
            if not '#' in response:
                tickets_info = 'Please select the ticket you want get help on:\n\n'
                for queued_ticket in queued_tickets:
                    tickets_info +=f"- Ticket Number: # *{queued_ticket.id}*\nDescription: {queued_ticket.description}\n"
                tickets_info += '\nReply with #ticketNo eg *#4* to start asking for help on the ticket.'
                data = get_text_message_input(inquirer.phone_number, tickets_info, None)
                return send_message(data)
            else:
                match = re.search(r'#(\d+)', response)
                if match:
                    support_member_pending_ticket = Ticket.objects.filter(id=match.group(1),ticket_mode=QUEUED_MODE).first()
                    if support_member_pending_ticket:
                        other_tickets_pending = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member_pending_ticket.assigned_to ).exclude(id=support_member_pending_ticket.id).first()
                        if other_tickets_pending:
                            data = get_text_message_input(inquirer.phone_number, 'Please wait, the support member will be in touch shortly.', None)
                            send_message(data)
                            msg =f'*{inquirer.username.title()}* from *{inquirer.branch}* is requesting assistance on ticket #*{support_member_pending_ticket.id}* which is assigned to you,finish or close the current ticket you are on to respond to the inquirer.'
                            data = get_text_message_input(support_member_pending_ticket.assigned_to.phone_number, msg, None)
                            send_message(data)
                    else:
                        return "Ticket not found"
                else:
                    return "Please check the ticket number and try again, use #ticketNo eg *#4*"
    return "You have no queued tickets"

def resume_assistance(support_member,response):
    all_queued_tickets = Ticket.objects.filter(ticket_mode=QUEUED_MODE,assigned_to=support_member)
    if all_queued_tickets:
        if "#exit" in response.lower() or "#cancel" in response.lower():
            support_member.user_status = HELPING_MODE
            support_member.save()
            return "You have exited the resume mode."
        if '#resume' in response or '#cont' in response:
            tickets_info = 'Please select the ticket you want to resume assisting:\n\n'
            for queued_ticket in all_queued_tickets:
                tickets_info +=f"Ticket Number: # *{queued_ticket.id}*\n- {queued_ticket.description}\n"
            tickets_info += '\nReply with #ticketNo eg *#1* to resume assisting the inquirer.'
            data = get_text_message_input(support_member.phone_number, tickets_info, None)
            return send_message(data)
        else:
            match = re.search(r'#(\d+)', response)
            if match:
                ticket_obj = Ticket.objects.filter(id=int(match.group(1)),assigned_to=support_member,ticket_mode=QUEUED_MODE).first()
                if ticket_obj:
                    check_other_pending_tickets = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member).exclude(id=ticket_obj.id).first()
                    if check_other_pending_tickets:
                        check_other_pending_tickets.ticket_mode = QUEUED_MODE
                        check_other_pending_tickets.save()
                    ticket_obj.ticket_mode = 'other'
                    ticket_obj.save()
                    support_member.user_status = HELPING_MODE
                    support_member.save()
                    message= f'You are now assisting {ticket_obj.created_by.username.title()} - *{ticket_obj.created_by.branch}* \nTicket number *{ticket_obj.id}* .'
                    data = get_text_message_input(support_member.phone_number,message , None)
                    return send_message(data)
                else:
                    return "No tickets with That ticket number assigned to you found"
            else:
                return "Please check the ticket number and try again, reply with *#resume* to see all your queued tickets. or reply with *#exit* to exit the resume mode."
    support_member.user_status = HELPING_MODE
    support_member.save()
    return "You have no queued tickets"

def inquirer_assistance_response(response, open_inquiries, inquirer):
    check_ticket = Ticket.objects.filter(created_by=inquirer.id).order_by('-updated_at').first()
    if not check_ticket:
        return 'Thank you for your response.'
    check_ticket.support_level = response
    check_ticket.save()
    data = get_text_message_input(inquirer.phone_number, '✨Thank you for your feedback.', None)
    send_message(data)
    inquirer.user_mode = INQUIRY_MODE
    inquirer.user_status = INQUIRY_MODE
    inquirer.save()
    return ''

def broadcast_messages(name,ticket=None,message=None,phone_number=None,message_type=None,message_id=None):
    support_members = SupportMember.objects.all()
    for support_member in support_members:
        user_mobile = support_member.phone_number
        if user_mobile == phone_number:
            ...
        else:
            if message_type == "document":
                data = get_document_message(user_mobile, message_id)
                return send_message(data)
            if message_type == "image":
                data = get_image_message(user_mobile, message_id)
                return send_message(data)
            if message_type == "audio":
                data = get_audio_message_input(user_mobile, message_id)
                return send_message(data)
            
            if message:
                message=message
            else:
                pending_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member.id).first()
                if not pending_ticket:
                    support_member.user_mode = ACCEPT_TICKET_MODE
                    support_member.save()
                    message=accept_ticket_response.format(ticket.created_by.username,ticket.branch_opened.upper(),ticket.id, ticket.description)
                else:
                    support_member.user_status = NEW_TICKET_ACCEPT_MODE
                    support_member.save()
                    message=accept_ticket_response.format(ticket.created_by.username,ticket.branch_opened.upper(),ticket.id, ticket.description)
                    message += '\n\n⚠️ You have a pending inquiry, if you accept this one, the pending inquiry will be paused.\n\n1. Skip this ticket\n2. Reply with this ticket id accept.'
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
        check_ticket = Ticket.objects.get(id=ticket_id)
        if check_ticket:
            is_ticket_open = check_ticket.status.lower() == OPEN_MODE
        else:
            return "wrong ticket id"
    except Ticket.DoesNotExist:
        return "error ticket not available or already assigned "
    if is_ticket_open:
        try:
            assigned_tickets = Ticket.objects.filter(
                assigned_to=support_member.id, status=PENDING_MODE
            ).first()
            if assigned_tickets:
                assigned_tickets.ticket_mode = QUEUED_MODE
                assigned_tickets.save()
        except Ticket.DoesNotExist:
            assigned_tickets = None
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

def request_assistance_support_member(id):
    request_user = SupportMember.objects.filter(id=id).first()
    support_members = SupportMember.objects.all()
    for member in support_members:
        if member.id != request_user.id:
            member.user_status = SUPPORT_MEMBER_ASSISTING_MODE
            member.save()
        else:
            member.user_status = SUPPORT_MEMBER_ASSISTANCE_MODE
            member.save()
    message = f'🔔 *Support Member {request_user.username.title()}* is requesting assistance.\nPlease select:\n\n1. Assist\n2. Skip \n\n `please choose an option to continue!`'
    broadcast_messages(None,None,message,request_user.phone_number)
    data = get_text_message_input(request_user.phone_number, support_users_interaction, None)
    return send_message(data)

def assist_support_member(support_member_id, response,message_type,message_id):
    support_member = SupportMember.objects.filter(id=support_member_id).first()
    support_members = SupportMember.objects.all().exclude(user_status=HELPING_MODE)
    assisting_member = SupportMember.objects.filter(user_status=SUPPORT_MEMBER_ASSISTING).first()
    if support_member.user_status == SUPPORT_MEMBER_ASSISTING_MODE:
        if '2' == response.lower() or 'skip' in response.lower():
            support_member.user_status = HELPING_MODE
            support_member.save()
            data = get_text_message_input(support_member.phone_number, passed_support_helping, None)
            return send_message(data)
        elif '1' == response.lower() or 'assist' in response.lower():
            support_member.user_status = SUPPORT_MEMBER_ASSISTING
            support_member.save()
            data = get_text_message_input(support_member.phone_number, support_user_helper, None)
            return send_message(data)
        else:
            support_member.user_status = HELPING_MODE
            support_member.save()
            message ='you skipped assisting the support member who was requesting assistance.You can now continue with your current task.'
            data = get_text_message_input(support_member.phone_number, message, None)
            return send_message(data)
    elif support_member.user_status == SUPPORT_MEMBER_ASSISTANCE_MODE:
        for thank_you_message in thank_you_messages:
            if thank_you_message in response.lower():
                for member in support_members:
                    if member.user_status == SUPPORT_MEMBER_ASSISTING:
                        message = '*Support Member is now helped,You can now proceed with your previous tasks*'
                        data = get_text_message_input(member.phone_number, message, None)
                        send_message(data)
                    member.user_status = HELPING_MODE
                    member.save()
                data = get_text_message_input(support_member.phone_number, back_to_helping_mode, None)
                return send_message(data)
        if assisting_member:
            if message_type == "document":
                data = get_document_message(assisting_member.phone_number, message_id)
                return send_message(data)
            elif message_type == "image":
                data = get_image_message(assisting_member.phone_number, message_id)
                return send_message(data)
            elif message_type == "audio":
                data = get_audio_message_input(assisting_member.phone_number, message_id)
                return send_message(data)
            elif message_type == "video":
                data = get_video_message(assisting_member.phone_number, message_id)
                return send_message(data)
            data = get_text_message_input(assisting_member.phone_number, response, None)
            return send_message(data)
        return 'wait for the support member to accept  assisting you first or reply with *#exit* to quit.'
    elif support_member.user_status == SUPPORT_MEMBER_ASSISTING:
        member_to_assist = SupportMember.objects.filter(user_status=SUPPORT_MEMBER_ASSISTANCE_MODE).first()
        if member_to_assist:
            if message_type == "document":
                data = get_document_message(member_to_assist.phone_number, message_id)
                return send_message(data)
            elif message_type == "image":
                data = get_image_message(member_to_assist.phone_number, message_id)
                return send_message(data)
            elif message_type == "audio":
                data = get_audio_message_input(member_to_assist.phone_number, message_id)
                return send_message(data)
            elif message_type == "video":
                data = get_video_message(member_to_assist.phone_number, message_id)
                return send_message(data)
            data = get_text_message_input(member_to_assist.phone_number, response, None)
            return send_message(data)
        support_member.user_status = HELPING_MODE
        support_member.save()
        return 'There is no support member requesting assistance at the moment, you can continue with your current task.'
    
def get_image_message(recipient, image_id):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "image",
            "image": {
                # "link": f'{image_name}',
                'id':f'{image_id}'
            },
        }
    )

def forward_message(request):
    data =get_text_message_input('263779586059', 'Hello', 'customer_helped_template',True)
    return send_message(data)
    
def get_document_message(recipient, document_id, caption='New document'):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "document",
            "document": {
                "id": document_id,
                "filename": f"{caption}",
            },
        }
    )

def get_video_message(recipient, video_id):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "video",
            "video": {
                "id": video_id,
            },
        }
    )

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
        support_member_pending_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member).exclude(id=ticket_id).first()
        if not support_member_pending_ticket:
            support_member.user_mode = ACCEPT_TICKET_MODE
            support_member.user_status = ACCEPT_TICKET_MODE
            support_member.save()
        try:
            inquirer = Inquirer.objects.get(id=ticket.created_by.id)
            if not inquirer.user_status == SUPPORT_RATING and inquirer.user_mode == CONFIRM_RESPONSE:
                inquirer.user_status = INQUIRY_MODE
                inquirer.user_mode = INQUIRY_MODE
                inquirer.save()
        except Inquirer.DoesNotExist:
            ...
        other_pending_tickets = Ticket.objects.filter(status=PENDING_MODE,assigned_to=ticket.assigned_to,ticket_mode=QUEUED_MODE)
        if other_pending_tickets:
            message=f'Hello {ticket.assigned_to.username.title()},\nYou still have pending tickets in the queue, pick one to resume assisting the inquirer now.\n\n'
            for pending_ticket in other_pending_tickets:
                message += f'Ticket Number: *#{pending_ticket.id}*\nOpened by *{pending_ticket.created_by.username.title()}* from *{pending_ticket.created_by.branch.upper()}*\n- {pending_ticket.description}\n\n'
            message += 'Reply with #ticketNo eg *#4* to resume assisting the inquirer.'
            support_member.user_status = RESUME_MODE
            support_member.save()
            data = get_text_message_input(ticket.assigned_to.phone_number, message, None)
            send_message(data)
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
    support_member_pending_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member).exclude(id=ticket_id).first()
    if not support_member_pending_ticket:
        support_member.user_mode = ACCEPT_TICKET_MODE
        support_member.user_status = ACCEPT_TICKET_MODE
        support_member.save()
    try:
        inquirer = Inquirer.objects.get(id=ticket.created_by.id)
        if not inquirer.user_status == SUPPORT_RATING and inquirer.user_mode == CONFIRM_RESPONSE:
            inquirer.user_status = INQUIRY_MODE
            inquirer.user_mode = INQUIRY_MODE
            inquirer.save()
    except Inquirer.DoesNotExist:
        ...
    other_pending_tickets = Ticket.objects.filter(status=PENDING_MODE,assigned_to=ticket.assigned_to,ticket_mode=QUEUED_MODE)
    if other_pending_tickets:
        message=f'Hello {ticket.assigned_to.username.title()},\nThe ticket you were working on has been resolved but you still have pending tickets in the queue, pick one to resume assisting the inquirer now.\n\n'
        for pending_ticket in other_pending_tickets:
            message += f'Ticket Number: *#{pending_ticket.id}*\nOpened by *{pending_ticket.created_by.username.title()}* from *{pending_ticket.created_by.branch.upper()}*\n- {pending_ticket.description}\n\n'
        message += 'Reply with #ticketNo eg *#4* to resume assisting the inquirer.'
        support_member.user_status = RESUME_MODE
        support_member.save()
        data = get_text_message_input(ticket.assigned_to.phone_number, message, None)
        send_message(data)
    message=f"ticket *#{ticket.id}* is now resolved ✅ by {ticket.assigned_to.username}."
    reply = f'Your inquiry (*{ticket.description}*) has been marked as resolved'
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

def alert_support_members(name,ticket, message,resolved=False):
    if resolved:
        return mark_as_resolved(ticket.id)
    return broadcast_messages(name,ticket)
    