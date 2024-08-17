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
            return request_assistance_support_member(support_member.id)
        if support_member.user_status == SUPPORT_MEMBER_ASSISTING_MODE or support_member.user_status == SUPPORT_MEMBER_ASSISTANCE_MODE:
            return assist_support_member(support_member.id,response)

        if support_member.user_mode == HELPING_MODE or check_ticket:
            return handle_help(wa_id, response, name)

        if support_member.user_mode == ACCEPT_TICKET_MODE:
            return accept_ticket(wa_id,name, response)

        return 'hello! how can i help you today?'

    if response.lower() in greeting_messages:
        time_of_day = get_greeting()
        name = inquirer.username.split()[0] if inquirer else name
        return f"Golden  {time_of_day} {name.title()}, how can i help you today?"


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
    print(data)
    
    try:
        phone_number_id = [contact['wa_id'] for contact in data['entry'][0]['changes'][0]['value']['contacts']]
    except Exception as e:
        phone_number_id = ""

    try:
        profile_name = data['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']
    except Exception as e:
        profile_name = "User"
    
    try:
        message = body["entry"][0]["changes"][0]["value"]["messages"][0]
        message_type = message["type"]

        if message_type == "text":
            message_body = message["text"]["body"]
            response = generate_response(message_body, phone_number_id, profile_name)
            data = get_text_message_input(phone_number_id, response, None, False)
            send_message(data)
        
        elif message_type == "image":
            image_id = message["image"]["id"]
            # Download the image using its ID
            image_data = download_image(image_id)
            # Resend the image back to the requester
            data = get_image_message_input(phone_number_id, image_data)
            return send_message(data)
        elif message_type == "audio":
            # audio_id = message["audio"]["id"]
            # audio_data = download_media(audio_id, "audio")
            # data = get_audio_message_input(phone_number_id, audio_data)
            data = get_text_message_input(phone_number_id, "I am sorry, I cannot process audio messages at the moment.", None)
            return send_message(data)
        
        elif message_type == "document":
            document_id = message["document"]["id"]
            document_filename = message["document"]["filename"]
            # document_data = download_media(document_id, "document")
            data = get_document_message_input(phone_number_id, document_filename, None)
            return send_message(data)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        ...

def download_media(media_id, media_type):
    access_token = 'YOUR_ACCESS_TOKEN'
    url = f"https://graph.facebook.com/v12.0/{media_id}"

    params = {
        'access_token': access_token
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.content  # This is the media content
    else:
        print(f"Error downloading {media_type}: {response.status_code} - {response.text}")
        return None

def get_document_message_input(phone_number_id, document_filename, document_data):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number_id,
            "type": "document",
            "document": {
                "link": "https://github.com/godfrey-tankan/My_projects/raw/main/Agatha%20Agatha%20Christie%20-%20Cards%20on%20the%20Table_%20A%20Hercule%20Poirot%20Mystery.pdf",  # Host the document or find a way to re-upload it
                "filename": document_filename,
                "caption": f"Here is the document you sent: {document_filename}"
            },
        }
    )

def get_audio_message_input(phone_number_id, audio_data):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number_id,
            "type": "audio",
            "audio": {
                "link": "https://path_to_your_audio_hosting_service",  # Host the audio or find a way to re-upload it
                "caption": "Here is the audio you sent!"
            },
        }
    )

def download_image(image_id):
    # Define your access token and the URL to download the image
    access_token = settings.ACCESS_TOKEN
    url = f"https://graph.facebook.com/v12.0/{image_id}"

    params = {
        'access_token': access_token
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.content  # This is the image content
    else:
        print(f"Error downloading image: {response.status_code} - {response.text}")
        return None

def get_image_message_input(phone_number_id, image_data):
    # Create the message payload to send the image back to the user
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number_id,
            "type": "image",
            "image": {
                "link": "https://clava.co.zw/assets/images/ai.png",  # Host the image or find a way to re-upload it
                "caption": "Here is the image you sent!"
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
    message = f'🔔 *{request_user.username}* is requesting assistance,please reply to assist. or type pass to skip this request.'
    broadcast_messages(None,None,message,request_user.phone_number)
    data = get_text_message_input(request_user.phone_number, support_users_interaction, None)
    return send_message(data)

def assist_support_member(support_member_id, response):
    support_member = SupportMember.objects.filter(id=support_member_id).first()
    support_members = SupportMember.objects.all()
    if support_member.user_status == SUPPORT_MEMBER_ASSISTING_MODE:
        if 'pass' in response.lower():
            support_member.user_status = HELPING_MODE
            support_member.save()
            data = get_text_message_input(support_member.phone_number, passed_support_helping, None)
            return send_message(data)
        broadcast_messages(None,None,response,support_member.phone_number)
    elif support_member.user_status == SUPPORT_MEMBER_ASSISTANCE_MODE:
        for thank_you_message in thank_you_messages:
            if thank_you_message in response.lower():
                for member in support_members:
                    member.user_status = HELPING_MODE
                    member.save()
                data = get_text_message_input(support_member.phone_number, back_to_helping_mode, None)
                return send_message(data)
        broadcast_messages(None,None,response,support_member.phone_number)
    
def send_image_message(recipient, image_url):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": '263779586059',
            "type": "image",
            "image": {
                "link": 'https://clava.co.zw/assets/images/ai.png',
            },
        }
    )
def forward_message(request):
    print('forwarding message.........>>>>>>')
    # data = send_image_message('263779586059','https://clava.co.zw/assets/images/ai.png')
    data = get_text_message_input('263779586059','https://clava.co.zw/assets/images/ai.png',None)
    return send_message(data)
def send_document_message(recipient, document_url):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": "example.pdf",
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