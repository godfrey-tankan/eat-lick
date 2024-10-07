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
from django.db.models import OuterRef, Subquery
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
        check_ticket = Ticket.objects.filter(created_by=inquirer.id,status=PENDING_MODE,ticket_mode='other').first()
        if inquirer.user_status == NEW_TICKET_MODE:
            return handle_inquiry(wa_id, response, name)
    else:
        check_ticket = None
    if 'tnqn' == response.lower():
        return tankan_self
    
    if support_member:
        pending_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member,ticket_mode='other').first()
        if  response.lower() in greeting_messages and not pending_ticket:
            time_of_day = get_greeting()
            try:
                open_inquiries_total= Ticket.objects.filter(status=OPEN_MODE,ticket_mode='other').count()
                open_tasks = f'`current open inquiries` : *{open_inquiries_total}* \n\n'
                if float(open_inquiries_total) > 0:
                    open_tasks += 'Reply with *#open* to view all open tickets.'
            except Ticket.DoesNotExist:
                open_tasks = None
            return f"Golden  {time_of_day} {name.title()}, how can i help you today?\n\n{open_tasks}"
    
        if response.lower() == 'help':
            return support_member_help_menu
        if support_member.user_status==NEW_TICKET_ACCEPT_MODE:
            if response == '1' or response == '1.':
                support_member.user_status = HELPING_MODE
                support_member.save()
                return 'You have skipped the ticket, you can now continue with your current task.'
            return accept_ticket(wa_id,name, response)
        
        if support_member.user_status == RESUME_MODE:
            return resume_assistance(support_member,response)
    
        if '#open' in response.lower() or support_member.user_status == OPEN_TICKETS_MODE:
            return get_all_open_tickets(support_member,response,wa_id,name)
        if '#taken' in response.lower() or support_member.user_status == ATTENDED_TICKETS_MODE:
            return get_attended_tickets(support_member,response)
        if '#relea' in response.lower():
            return release_ticket(support_member)
        if '#hold' in response.lower():
            return hold_ticket(support_member,response)

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
            elif response=='3':
                last_msg = Message.objects.filter(ticket_id=check_ticket,inquirer=inquirer).last()
                data= get_text_message_input(check_ticket.assigned_to.phone_number, last_msg.content, None)
                send_message(data)
                return 'Your message has been sent.'
            
        if response.lower() in ['#menu','#home'] or inquirer.user_mode == MAIN_MENU_MODE:
            time_of_day = get_greeting()
            return main_menu(response,wa_id,time_of_day)
        if inquirer.user_mode==BRANCH_MODE:
            return handle_inquiry(wa_id, response, name)
        if inquirer.user_mode == INQUIRY_STATUS_MODE:
            return inquiry_status(inquirer, response)
        return handle_help(wa_id, response, name,message_type,message_id)
    
    if  response.lower() in greeting_messages or (inquirer and inquirer.user_mode == MAIN_MENU_MODE)or response.lower() in ['menu','#menu']:
        time_of_day = get_greeting()
        if inquirer:
            return main_menu(response,wa_id,time_of_day)
        return f"Golden  {time_of_day} {name.title()}, how can i help you today?\n\n_reply with #menu to view the main menu or #help to view the help menu._"

    if response.lower() in ['help','#help'] or response.lower() == 'usage help':
        return inquirers_help_menu

    if inquirer and inquirer.user_status == SUPPORT_RATING:
        if not '/' in response:
            data = get_text_message_input(inquirer.phone_number, 'Hello', 'rate_support_user',True)
            return send_message(data)
        return inquirer_assistance_response(response, check_ticket, inquirer)
    if not support_member :
        if inquirer and inquirer.user_mode == INQUIRY_STATUS_MODE:
            return inquiry_status(inquirer, response)
        
        for thank_you_message in thank_you_messages:
            if thank_you_message in response.lower():
                return "You are welcome."
        # for help_message in help_messages:
        #     if help_message in response.lower() or len(response) > :
        return handle_inquiry(wa_id, response, name)
    return f"Hello,golden greetings. How can i help you today?"    

def get_text_message_input(recipient, text,name=None,template=False):

    if template:
        print('template',name,recipient)
        return json.dumps(
            {
                "messaging_product": "whatsapp",
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
    
def main_menu(response,wa_id,time_of_day):
    inquirer_ob = Inquirer.objects.filter(phone_number=wa_id[0]).first()
    if inquirer_ob:
        if response == '#exit':
            inquirer_ob.user_mode = INQUIRY_MODE
            inquirer_ob.save()
            return f'Hello {inquirer_ob.username.title()}, how can i help you today?'
        elif response =='1' or response == '1.':
            inquirer_ob.user_mode = BRANCH_MODE
            inquirer_ob.save()
            return 'Do you want to change your branch?'
        elif response =='2' or response =='2.':
            check_pending_inquiries = Ticket.objects.filter(created_by=inquirer_ob,status=PENDING_MODE,ticket_mode='other').first()
            if check_pending_inquiries:
                inquirer_ob.user_status = NEW_TICKET_MODE
                inquirer_ob.save()
                return 'What is your inquiry?\n\nReply with exit or q to exit.'
            inquirer_ob.user_mode = INQUIRY_MODE
            inquirer_ob.save()
            return 'What is your inquiry today?'
        elif response =='3' or response =='3.':
            inquirer_ob.user_mode = INQUIRY_STATUS_MODE
            inquirer_ob.save()
            inquirer_tickets = Ticket.objects.filter(created_by=inquirer_ob,status=PENDING_MODE).order_by('-created_at')
            if inquirer_tickets:
                tickets_status= 'Here is your inquiry(s) status:\n\n'
                for i,inquirer_ticket in enumerate(inquirer_tickets,start=1):
                    if inquirer_ticket.ticket_mode == QUEUED_MODE:
                        tickets_status += f'*{i}*. Ticket Number: *{inquirer_ticket.id}*\n- Description: {inquirer_ticket.description}\n- Status: *{inquirer_ticket.status}* - *On Hold*\n\n'
                    else:
                        tickets_status += f'*{i}*. Ticket Number: *{inquirer_ticket.id}*\n- Description: {inquirer_ticket.description}\n- Status: *{inquirer_ticket.status}*\n\n'
                tickets_status += '\nReply with *ticketNo* eg *4* to view more details or *#exit* to exit\n\n'
                return tickets_status
            return 'You have no inquiries at the moment.'
        else:
            menu_option =f'''Golden {time_of_day} *{inquirer_ob.username.title()}*  — `{inquirer_ob.branch.title()}` branch.\nPlease Choose an option: 
            \n1. Update branch from *{inquirer_ob.branch}*
            \n2. ⁠New inquiry 
            \n3. ⁠Your inquiry status'''
            inquirer_ob.user_mode = MAIN_MENU_MODE
            inquirer_ob.save()
            return menu_option
    else:
        return 'Hello, please create a profile first.'

def inquiry_status(inquirer, response):
    if response == '#exit':
        inquirer.user_mode = INQUIRY_MODE
        inquirer.save()
        return f'Hello {inquirer.username.title()}, how can I help you today?'

    try:
        ticket_id = int(response)
    except ValueError:
        return 'Please provide a valid ticket number'

    ticket = Ticket.objects.filter(id=ticket_id).annotate(
        attended_at=Subquery(
            TicketLog.objects.filter(
                ticket=OuterRef('pk'),
                status__icontains='pending'
            ).values('timestamp')[:1]
        )
    ).first()

    if ticket:
        assignee_pending_tickets = Ticket.objects.filter(
            status=PENDING_MODE,
            assigned_to=ticket.assigned_to,
            ticket_mode=QUEUED_MODE
        ).order_by('queued_at')

        ticket_index = None
        for index, pending_ticket in enumerate(assignee_pending_tickets):
            if pending_ticket.id == ticket.id:
                ticket_index = index + 1  
                break
        time_created = timezone.localtime(ticket.created_at).strftime('%Y-%m-%d %H:%M')
        time_attended = timezone.localtime(ticket.attended_at).strftime('%Y-%m-%d %H:%M') if ticket.attended_at else 'Not yet attended'
        ticket_status = f'Ticket Number: *{ticket.id}*\n- Assigned to: *{ticket.assigned_to.username}*\n Time Created: *{time_created}* - attended at: *{time_attended}*\n- Description: {ticket.description}\n- Status: *{ticket.status}*\n\n'

        if ticket.ticket_mode == QUEUED_MODE:
            ticket_status += f'- *On Hold*'

        if ticket_index is not None:
            ticket_status += f'\n- Position in queue: *{ticket_index}*'

        return ticket_status
    return 'Ticket not found, please provide a valid ticket number'

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

def hold_ticket(support_member,response):
    ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member,ticket_mode='other').first()
    if ticket:
        if 'hold' in response.lower():
            reason = response.split('hold')[1]
        else:
            reason = 'no reason provided'
        time_opened = timezone.localtime(ticket.created_at).strftime('%Y-%m-%d %H:%M')
        notifier = f'Hello {ticket.created_by.username.title()},\nYour inquiry *({ticket.description})* is now on hold, `Reason:`\n *{reason}* .'
        data = get_text_message_input(ticket.created_by.phone_number, notifier, None)
        send_message(data)
        message = f'*{support_member.username.title()}* has put the ticket #{ticket.id} on hold.'
        ticket.status = PENDING_MODE
        ticket.ticket_mode = QUEUED_MODE
        ticket.queued_at = timezone.now()
        ticket.save()
        TicketLog.objects.create(ticket=ticket, status='pending', timestamp=timezone.now(),changed_by=f'{support_member.username}- ticket on hold')
        return broadcast_messages('',None,message)

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

def get_all_open_tickets(support_member,response,wa_id,name):
    if '#open' in response.lower():
        open_tickets= Ticket.objects.filter(status=OPEN_MODE).order_by('created_at')
        if not open_tickets:
            support_member.user_status = HELPING_MODE
            support_member.user_mode = HELPING_MODE
            support_member.save()
            return 'There are no open tickets at the moment.'
        support_member.user_status = OPEN_TICKETS_MODE
        support_member.save()
        message = '🟢 Open Tickets:\n\n'
        for i,ticket in enumerate(open_tickets,start=1):
            created = timezone.localtime(ticket.created_at).strftime('%Y-%m-%d %H:%M')
            message += f"*{i}*. Ticket Number: *{ticket.id}*\n- Opened by: *{ticket.created_by.username.title()}* from *{ticket.branch_opened.title()}* branch at {created}\n- Description: {ticket.description}\n\n"
        message += '\nReply with *ticketNo* eg *4* to assign the ticket to yourself or *#exit* to exit'
        return message
    if '#exit' in response.lower() or '#cancel' in response.lower():
        support_member.user_status = HELPING_MODE
        support_member.user_mode = HELPING_MODE
        support_member.save()
        return 'You are now back to your previous mode, you can continue with what you were doing.'
    try:
        ticket_id = int(response)
    except ValueError:
        return 'Please provide a valid ticket number'
    return accept_ticket(wa_id,name, ticket_id)
        
def get_attended_tickets(support_member,response):
    if '#taken' in response.lower():
        attended_tickets= Ticket.objects.filter(status='pending').order_by('updated_at')
        if not attended_tickets:
            support_member.user_status = HELPING_MODE
            support_member.user_mode = HELPING_MODE
            support_member.save()
            return 'There are no tickets being attended to at the moment.'
        message = '🟡 Tickets being attended:\n\n'
        for i,ticket in enumerate(attended_tickets,start=1):
            created =timezone.localtime(ticket.created_at).strftime('%Y-%m-%d %H:%M')
            message += f"*{i}*. Ticket Number: *{ticket.id}*\n- Attended by *{ticket.assigned_to.username}*\n- Opened by: *{ticket.created_by.username.title()}* from *{ticket.branch_opened.title()}* branch at {created}\n- Description: {ticket.description}\n\n"
        message += '\nReply with *#exit* to exit'
        support_member.user_status = ATTENDED_TICKETS_MODE
        support_member.save()
        return message
    if '#exit' in response.lower() or '#cancel' in response.lower():
        support_member.user_status = HELPING_MODE
        support_member.save()
        return 'You are now back to your previous mode, you can continue with what you were doing.'

def release_ticket(support_member):
    ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member,ticket_mode='other').first()
    if ticket:
        time_opened = timezone.localtime(ticket.created_at).strftime('%Y-%m-%d %H:%M')
        notifier = f'Hello {ticket.created_by.username.title()},\nYour inquiry *({ticket.description})* is now now on hold, please wait for your turn to be assisted.'
        data = get_text_message_input(ticket.created_by.phone_number, notifier, None)
        send_message(data)
        message = f'*{support_member.username.title()}* has released the ticket #{ticket.id}\n- Opened by: *{ticket.created_by.username}* - *{ticket.branch_opened}* at *{time_opened}* \n- Description: {ticket.description}\n\nYou can reply with #open to assign this open ticket to yourself.'
        ticket.status = OPEN_MODE
        ticket.assigned_to=None
        ticket.save()
        TicketLog.objects.create(ticket=ticket, status='open', timestamp=timezone.now(),changed_by=f'{support_member.username}- ticket released')
        return broadcast_messages('',None,message)

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
                if response.lower() == 'no':
                    inquirer_obj.user_mode = MAIN_MENU_MODE
                    inquirer_obj.save()
                    return main_menu(response,wa_id,get_greeting())
                try:
                    branch_code = int(response)
                except Exception as e:
                    branch_code = None
                if not branch_code:
                    branches_list = 'Please select a branch:\n\n'
                    all_branches = Branch.objects.all()
                    if all_branches:
                        for branch in all_branches:
                            branches_list += f'Branch number: *{branch.id}*\n- Name : *{branch.name}*\n\n'
                        branches_list += '\n Please reply with your branch number eg *2* .'
                        return branches_list
                    return 'No branches to choose from found!'
                selected_branch = Branch.objects.filter(id=branch_code).first()
                if selected_branch:
                    inquirer_obj.branch = selected_branch.name
                    inquirer_obj.user_mode = INQUIRY_MODE
                    inquirer_obj.save()
                    message = f'You are now inquiring under *{selected_branch.name.title()}* ,to change your branch, send *#menu*'
                    data = get_text_message_input(inquirer_obj.phone_number,message,None)
                    send_message(data)
                    return f'Hello {inquirer_obj.username.split()[0].title()}, What is your inquiry?'
                return 'Invalid branch number, please try again!'
            names = response.split()
            if len(names) < 2:
                return 'Please provide both your first name and last name'
            inquirer_obj.username = response
            inquirer_obj.save()
            if inquirer_obj.branch:
                inquirer_obj.user_mode = INQUIRY_MODE
                inquirer_obj.save()
                return f'Hello {inquirer_obj.username.split()[0].title()}, What is your inquiry?'
            inquirer_obj.user_mode=BRANCH_MODE
            inquirer_obj.save()
            branches_list = 'Please select your branch:\n\n'
            all_branches = Branch.objects.all()
            if all_branches:
                for branch in all_branches:
                    branches_list += f'Branch number: *{branch.id}*\n- Name : *{branch.name}*\n\n'
                branches_list += '\n Please reply with your branch number eg *2* .'
                return branches_list
            return 'No branches to choose from found!'
    try:
        open_inquiries = Ticket.objects.filter(status=OPEN_MODE,created_by=inquirer_obj.id).first()
    except Ticket.DoesNotExist:
        open_inquiries = Ticket.objects.filter(status=PENDING_MODE,created_by=inquirer_obj.id).first()
    if open_inquiries or inquirer_obj.user_status == NEW_TICKET_MODE:
        
        for no_response in deny_open_new_ticket:
            if no_response == response.lower():
                return 'Your inquiry is still being attended to.Please wait for a response.'
        # return "You have an open inquiry, Do you want to open a new inquiry?"
        if not inquirer_obj.user_status == NEW_TICKET_MODE:
            for yes_response in confirm_open_new_ticket:
                if yes_response in response.lower():
                    inquirer_obj.user_status = NEW_TICKET_MODE
                    inquirer_obj.save()
                    # open_inquiries.ticket_mode = QUEUED_MODE
                    # open_inquiries.save()
                    # new_message = f"Hi {open_inquiries.assigned_to.username.split()[0].title()}, {inquirer_obj.username} has opened a new inquiry,Your pending ticket (#{open_inquiries.id})  with them have now been queued.You can resume assisting them anytime by replying with #resume or #continue."
                    # data = get_text_message_input(open_inquiries.assigned_to.phone_number,new_message ,None)
                    # send_message(data)
                    return 'What is your inquiry?.\n\nReply with exit or q to exit.'
            return "You have an open inquiry, Do you want to open a new inquiry?"
        if inquirer_obj.user_status == NEW_TICKET_MODE:
            other_pending_issues = Ticket.objects.filter(status=PENDING_MODE,created_by=inquirer_obj,ticket_mode='other').first()
            if response.lower() == 'exit' or response.lower() == 'q':
                inquirer_obj.user_status = INQUIRY_MODE
                inquirer_obj.user_mode = INQUIRY_MODE
                inquirer_obj.save()
                message_to_send = f'You have exited the inquiry process, now you can continue sending messages on inquiry *({other_pending_issues.description})*' if other_pending_issues else 'You have exited the inquiry process, you can open a new inquiry anytime.'
                return message_to_send
            if other_pending_issues:
                other_pending_issues.ticket_mode = QUEUED_MODE
                other_pending_issues.queued_at = timezone.now()
                other_pending_issues.save()
                TicketLog.objects.create(
                    ticket=other_pending_issues,
                    status=QUEUED_MODE,
                    changed_by=inquirer_obj,
                )
                inquirer_obj.user_status =INQUIRY_MODE
                inquirer_obj.user_mode = INQUIRY_MODE
                inquirer_obj.save()
                assigned_member = SupportMember.objects.filter(phone_number=other_pending_issues.assigned_to.phone_number).first()
                assigned_member.user_status = ACCEPT_TICKET_MODE
                assigned_member.user_mode = ACCEPT_TICKET_MODE
                assigned_member.save()
                message_alert = f'Hello *{other_pending_issues.assigned_to.username.title()}* , {inquirer_obj.username.upper()} has opened a new inquiry,Your pending ticket (#{other_pending_issues.id})  with them have now been queued,This new inquiry might be urgent so you should consider assisting them first before resuming with inquiry *(#{other_pending_issues.id})* .You can resume assisting them anytime by replying with #resume or #continue.'
                data = get_text_message_input(other_pending_issues.assigned_to.phone_number,message_alert ,None)
                send_message(data)
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
            broadcast_messages(name,ticket)
            return new_inquiry_opened_response

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
            if open_inquiries.inquiry_type is None:
                inquiry_type_check = f"Before you start assisting the inquirer, please confirm the type of inquiry you are handling.\n\n1. General Inquiry\n2. Technical Inquiry\n3. Sales Inquiry\n4. Support Inquiry\n5. Other Inquiry\n\nReply with the number that corresponds to the inquiry type."
                if response == '1' or response == '1.':
                    open_inquiries.inquiry_type = 'General Inquiry'
                elif response == '2' or response == '2.':
                    open_inquiries.inquiry_type = 'Technical Inquiry'
                elif response == '3' or response == '3.':
                    open_inquiries.inquiry_type = 'Sales Inquiry'
                elif response == '4' or response == '4.':
                    open_inquiries.inquiry_type = 'Support Inquiry'
                elif response == '5' or response == '5.':
                    open_inquiries.inquiry_type = 'Other Inquiry'
                else:
                    return inquiry_type_check
                open_inquiries.save()
                return "You have successfully confirmed the inquiry type, you can now continue assisting the inquirer."
                
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
        all_queued_tickets = Ticket.objects.filter(ticket_mode=QUEUED_MODE,assigned_to=support_member,status=PENDING_MODE).order_by('queued_at')
        if all_queued_tickets:
            if not '#' in response:
                tickets_info = 'Please select the ticket you want to resume assisting:\n\n'
                for i,queued_ticket in enumerate(all_queued_tickets,start=1):
                    tickets_info +=f"Number in queue: {i}.\n- Ticket Number: # *{queued_ticket.id}*\nInquirer: {queued_ticket.created_by.username.title()} from {queued_ticket.branch_opened.title()}\nDescription: {queued_ticket.description}\n"
                tickets_info += '\nReply with #ticketNo eg *#4* to resume assisting the inquirer.'
                data = get_text_message_input(support_member.phone_number, tickets_info, None)
                return send_message(data)
            else:
                match = re.search(r'#(\d+)', response)
                if match:
                    current_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member,ticket_mode='other').first()
                    if current_ticket:
                        notifier = f'Hello {current_ticket.created_by.username.title()}, your inquiry is now now on hold, please wait for your turn to be assisted.'
                        data = get_text_message_input(current_ticket.created_by.phone_number, notifier, None)
                        send_message(data)
                        current_ticket.ticket_mode = QUEUED_MODE
                        current_ticket.queued_at = timezone.now()
                        current_ticket.save()
                    ticket_obj = Ticket.objects.filter(id=match.group(1)).first()
                    if ticket_obj:
                        ticket_obj.ticket_mode = 'other'
                        ticket_obj.save()
                        message_to_inquirer = f'Hello {ticket_obj.created_by.username.title()}, your inquiry is now being attended to, please wait for a response.'
                        data_to_inquirer = get_text_message_input(ticket_obj.created_by.phone_number,message_to_inquirer , None)
                        send_message(data_to_inquirer)
                        message= f'You are now assisting the inquirer with ticket number *{ticket_obj.id}*'
                        data = get_text_message_input(support_member.phone_number,message , None)
                        return send_message(data)
                    else:
                        return "Ticket not found"
                else:
                    return "Please check the ticket number and try again, use #ticketNo eg *#4*"
        support_member.user_status = HELPING_MODE
        support_member.user_mode=HELPING_MODE
        support_member.save()
    
    if inquirer:
        queued_tickets = Ticket.objects.filter(ticket_mode=QUEUED_MODE,created_by=inquirer,status=PENDING_MODE)
        not_found =True
        if queued_tickets:
            assignee_pending_tickets = Ticket.objects.filter(status=PENDING_MODE,assigned_to=queued_tickets.assigned_to,ticket_mode=QUEUED_MODE).order_by('queued_at')
            message_to_send =f'Hello {inquirer.username.title()}.\nYou have the following inquiries in queue:\n\n'
            for queued_ticket in queued_tickets:
                if assignee_pending_tickets:
                    position_in_queue = list(assignee_pending_tickets).index(queued_ticket) + 1
                    message_to_send += f'Inquiry #{queued_ticket.id} \n- *({queued_ticket.description})* is currently in position # *{position_in_queue}* in the queue.\n\n'
                else:
                    not_found = False
            message_to_send += '\nPlease wait for your turn to be assisted.'
            if not_found:
                data = get_text_message_input(inquirer.phone_number, message_to_send, None)
                return send_message(data)
        return 
        
    return "You have no queued inquiries"

def resume_assistance(support_member,response):
    all_queued_tickets = Ticket.objects.filter(status=PENDING_MODE,ticket_mode=QUEUED_MODE,assigned_to=support_member).order_by('queued_at')
    if all_queued_tickets:
        if "#exit" in response.lower() or "#cancel" in response.lower():
            support_member.user_status = HELPING_MODE
            support_member.user_mode = HELPING_MODE
            support_member.save()
            return "You have exited the resume mode,you can now take new tickets or reply with #resume to re-take inquiries in queue."
        if '#resume' in response or '#cont' in response:
            tickets_info = 'Please select the ticket you want to resume assisting:\n\n'
            for i,queued_ticket in enumerate(all_queued_tickets,start=1):
                tickets_info +=f"Number in Queue: {i}\n- Ticket Number: # *{queued_ticket.id}*\nOpened By: {queued_ticket.created_by.username} from {queued_ticket.branch_opened} branch.\n- {queued_ticket.description}\n\n"
            tickets_info += '\nReply with #ticketNo eg *#1* to resume assisting the inquirer.'
            data = get_text_message_input(support_member.phone_number, tickets_info, None)
            return send_message(data)
        else:
            match = re.search(r'#(\d+)', response)
            if match:
                ticket_obj = Ticket.objects.filter(id=int(match.group(1)),assigned_to=support_member,ticket_mode=QUEUED_MODE,status=PENDING_MODE).first()
                if ticket_obj:
                    check_other_pending_tickets = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member,ticket_mode='other').first()
                    if check_other_pending_tickets:
                        check_other_pending_tickets.ticket_mode = QUEUED_MODE
                        check_other_pending_tickets.queued_at = timezone.now()
                        check_other_pending_tickets.save()
                        TicketLog.objects.create(ticket=check_other_pending_tickets, status='pending', timestamp=timezone.now(),changed_by=f'{support_member.username}- ticket on hold')
                        notifier = f'Hello {check_other_pending_tickets.created_by.username.title()}.Your inquiry is now on hold, please wait for your turn to be assisted.'
                        data_to_paused_inquirer = get_text_message_input(check_other_pending_tickets.created_by.phone_number, notifier, None)
                        send_message(data_to_paused_inquirer)
                    ticket_obj.ticket_mode = 'other'
                    ticket_obj.save()
                    support_member.user_status = HELPING_MODE
                    support_member.user_mode = HELPING_MODE
                    support_member.save()
                    inquirer_msg = f'Hello {ticket_obj.created_by.username.title()}, your inquiry is now being attended to, please wait for a response.'
                    data_to_inquirer = get_text_message_input(ticket_obj.created_by.phone_number,inquirer_msg , None)
                    send_message(data_to_inquirer)
                    
                    message= f'You are now assisting *{ticket_obj.created_by.username.title()}* - *{ticket_obj.created_by.branch}* \nTicket number *{ticket_obj.id}*\n- Description: {ticket_obj.description} .'
                    data = get_text_message_input(support_member.phone_number,message , None)
                    return send_message(data)
                else:
                    return "No tickets with That ticket number assigned to you found"
            else:
                return "Please check the ticket number and try again, reply with *#resume* to see all your queued tickets. or reply with *#exit* to exit the resume mode."
    support_member.user_status = HELPING_MODE
    support_member.user_mode = HELPING_MODE
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
            elif message_type == "image":
                data = get_image_message(user_mobile, message_id)
                return send_message(data)
            elif message_type == "audio":
                data = get_audio_message_input(user_mobile, message_id)
                return send_message(data)
            else:
                if message:
                    message=message
                else:
                    message=accept_ticket_response.format(ticket.created_by.username,ticket.branch_opened.upper(),ticket.id, ticket.description)
                pending_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=support_member.id,ticket_mode='other').first()
                if not pending_ticket:
                    support_member.user_mode = ACCEPT_TICKET_MODE
                    support_member.save()
                else:
                    support_member.user_status = NEW_TICKET_ACCEPT_MODE
                    support_member.save()
                    message += f'\n\n⚠️ You have a pending inquiry, if you accept this one, inquiry *#{ticket.id}* will be set in queue.\n\n1. Skip this ticket\n2. Reply with this ticket id accept.'
                data = get_text_message_input(support_member.phone_number, message, None)
                send_message(data)


@csrf_exempt
def testing(request):
    name ='tankan'
    wa_id = ['263779586059']
    ticket_id =90
    # x = get_text_message_input(wa_id[0], 'hello', 'rate_support_user',True)
    x = get_text_message_input(wa_id[0], 'hello', 'customer_helped_template',True)
    
    e=send_message(x)
    print('response',e)
    # x=accept_ticket(wa_id,name, ticket_id)
    return JsonResponse({'data':'y'})
    
    
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
    support_msg= 'hello'
    message_to_send = 'hello'
    try:
        check_ticket = Ticket.objects.get(id=ticket_id)
        if check_ticket:
            is_ticket_open = check_ticket.status.lower() == OPEN_MODE
        else:
            return "wrong ticket id"
    except Ticket.DoesNotExist:
        pending_ticket= Ticket.objects.filter(assigned_to=support_member.id,status=PENDING_MODE,ticket_mode='other').first()
        if pending_ticket:
            support_member.user_mode =HELPING_MODE
            support_member.user_status=HELPING_MODE
            support_member.save()
            return f'inquiry not available or already assigned\n\nplease continue assisting *{pending_ticket.created_by.username}* , ticket number *{pending_ticket.id}* by sending them messages now!.'
        return "error ticket not available or already assigned "
    if is_ticket_open:
        try:
            # Get the first assigned ticket that is pending
            assigned_tickets = Ticket.objects.filter(
                assigned_to=support_member.id, status=PENDING_MODE,ticket_mode='other'
            ).first()
            if assigned_tickets:
                # If there are any assigned pending tickets, set their ticket_mode
                ticket_mode = QUEUED_MODE
                queued_at_time = timezone.now()
            else:
                ticket_mode = 'other'
                queued_at_time = None

        except Ticket.DoesNotExist:
            assigned_tickets = None
            ticket_mode = 'other'
            queued_at_time = None
        creator_pending_tickets = Ticket.objects.filter(status=PENDING_MODE,created_by=check_ticket.created_by,ticket_mode='other').first()
        if creator_pending_tickets:
            if queued_at_time:
                ...
            else:
                queued_at_time = timezone.now()
                ticket_mode = QUEUED_MODE
            message = f'Inquirer : {check_ticket.created_by.username.title()} is being attended to by *{creator_pending_tickets.assigned_to.username.title()}* on inquiry *#{creator_pending_tickets.id}*\n ({creator_pending_tickets.description}).Your inquiry with them is now in the queue.'
            data = get_text_message_input(wa_id[0], message, None)
            send_message(data)

        ticket = Ticket.objects.get(id=ticket_id)
        ticket.assigned_to = support_member
        ticket.status = PENDING_MODE
        ticket.ticket_mode = ticket_mode
        ticket.queued_at = queued_at_time
        ticket.save()

        # Retrieve all other pending tickets in the queue, ordered by queued_at
        other_tickets_pending = Ticket.objects.filter(
            status=PENDING_MODE,
            assigned_to=support_member,
            ticket_mode=QUEUED_MODE
        ).order_by('queued_at')

        if other_tickets_pending:
            try:
                position_in_queue = list(other_tickets_pending).index(ticket) + 1
            except ValueError:
                position_in_queue = 'N/A'
            if ticket.ticket_mode == QUEUED_MODE:
                message_to_send = (
                    f'Your inquiry is now in the queue, please wait for your turn to be assisted.\n\n'
                    f'Queue Number: *{position_in_queue}*\n'
                    f'Your Inquiry: {ticket.description}'
                )
                support_msg = f'You have accepted the ticket number #{ticket_id},it is now in the queue, please continue with your current task first or reply with #resume to take it from the queued list.'
            else:
                message_to_send = (
                    f'Hey {ticket.created_by.username.title()}, your inquiry *({ticket.description})* is now being attended to by *{ticket.assigned_to.username}*.'
                )
                support_msg = f'You have accepted the ticket number #{ticket_id}\n\nBut before you start assisting the inquirer, please confirm the type of inquiry you are handling.\n\n1. General Inquiry\n2. Technical Inquiry\n3. Sales Inquiry\n4. Support Inquiry\n5. Other Inquiry\n\nReply with the number that corresponds to the inquiry type.'
            
        else:
            message_to_send = (
                f'Hey {ticket.created_by.username.title()}, your inquiry *({ticket.description})* is now being attended to by *{ticket.assigned_to.username}*.'
            )
            support_msg = f'You have accepted the ticket number #{ticket_id}\n\nBut before you start assisting the inquirer, please confirm the type of inquiry you are handling.\n\n1. General Inquiry\n2. Technical Inquiry\n3. Sales Inquiry\n4. Support Inquiry\n5. Other Inquiry\n\nReply with the number that corresponds to the inquiry type.'
            
        data = get_text_message_input(ticket.created_by.phone_number, message_to_send, None)
        send_message(data)        
        TicketLog.objects.create(
            ticket=ticket,
            status=PENDING_MODE,
            changed_by=support_member
        )
        support_member.user_mode=HELPING_MODE
        support_member.user_status = HELPING_MODE
        support_member.save()
        data2 = get_text_message_input(support_member.phone_number,support_msg, None)
        send_message(data2)
        message=f"🟡ticket *#{ticket.id}* is now assigned to *{support_member.username if support_member.username.lower() != 'support' else support_member.phone_number}*"
        return broadcast_messages(name,None,message,support_member.phone_number)
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
        if '#exit' in response.lower() or '#cancel' in response.lower():
            support_member.user_status = HELPING_MODE
            support_member.save()
            return 'You have exited the Support member assistance mode, you can now continue interacting with the inquirer.'
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
                'id':f'{image_id}'
            },
        }
    )

def forward_message(message,number):
    data =get_text_message_input(number, message, None)
    return send_message(number)
    
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
    if is_closed:
        ticket = Ticket.objects.get(id=ticket_id)
        ticket.status = CLOSED_MODE
        ticket.closed_at = timezone.now()
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
        other_pending_tickets = Ticket.objects.filter(
            status=PENDING_MODE,
            assigned_to=ticket.assigned_to,
            ticket_mode=QUEUED_MODE
        ).order_by('queued_at')

        if other_pending_tickets.exists():
            message = f'Hello {ticket.assigned_to.username.title()},\nYou still have pending tickets in the queue, pick one to resume assisting the inquirer now.\n\n'
            
            for i, pending_ticket in enumerate(other_pending_tickets, start=1):
                alert_message = f'Your inquiry *({pending_ticket.description})* is now number # *{i}* in the queue, please wait for your turn to be assisted.'
                data = get_text_message_input(pending_ticket.created_by.phone_number, alert_message, None)
                send_message(data)
                created_time = timezone.localtime(pending_ticket.created_at).strftime('%Y-%m-%d %H:%M')
                
                message += (f'{i}. Ticket Number: *#{pending_ticket.id}*'
                            f'\n- Opened by *{pending_ticket.created_by.username.title()}* from *{pending_ticket.created_by.branch.upper()}* branch '
                            f'at {created_time}\n- Description: {pending_ticket.description}\n\n')

            message += 'Reply with #ticketNo eg *#4* to resume assisting the inquirer.'
            support_member.user_status = RESUME_MODE
            support_member.save()

            data = get_text_message_input(support_member.phone_number, message, None)
            send_message(data)
        message=f"ticket *#{ticket.id}* has been closed ❌."
        reply = f'Your inquiry has been closed.'
        data = get_text_message_input(ticket.created_by.phone_number, reply, None)
        send_message(data)
        return broadcast_messages(None,ticket,message)
    
    ticket = Ticket.objects.get(id=ticket_id)
    ticket.status = RESOLVED_MODE
    ticket.resolved_at = timezone.now()
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
    other_pending_tickets = Ticket.objects.filter(
            status=PENDING_MODE,
            assigned_to=ticket.assigned_to,
            ticket_mode=QUEUED_MODE
        ).order_by('queued_at')

    if other_pending_tickets.exists():
        message=f'Hello {ticket.assigned_to.username.title()},\nThe ticket you were working on has been resolved but you still have pending tickets in the queue, pick one to resume assisting the inquirer now.\n\n'
        
        for i, pending_ticket in enumerate(other_pending_tickets, start=1):
            alert_message = f'Your inquiry is now number # *{i}* in the queue, please wait for the support member to assist you.'
            data = get_text_message_input(pending_ticket.created_by.phone_number, alert_message, None)
            send_message(data)
            created_time = timezone.localtime(pending_ticket.created_at).strftime('%Y-%m-%d %H:%M')
            message += (f'{i}. Ticket Number: *#{pending_ticket.id}*'
                        f'\n- Opened by *{pending_ticket.created_by.username.title()}* from *{pending_ticket.created_by.branch.upper()}* branch'
                        f'at {created_time}\n- Description {pending_ticket.description}\n\n')

        message += 'Reply with #ticketNo eg *#4* to resume assisting the inquirer.'
        support_member.user_status = RESUME_MODE
        support_member.save()

        data = get_text_message_input(support_member.phone_number, message, None)
        send_message(data)
    
    message=f"ticket *#{ticket.id}* is now resolved ✅ by {ticket.assigned_to.username}."
    ticket_description = ticket.description.split('Web:')[1] if 'Web:' in ticket.description else ticket.description
    reply = f'Your inquiry (*{ticket_description}*) has been marked as resolved'
    data = get_text_message_input(ticket.created_by.phone_number, reply, None)
    send_message(data)
    return broadcast_messages(None,ticket,message)

def web_messaging(ticket_id,message=None,is_broadcasting=False,prev_assignee=None):
    if message in resolve_ticket_responses:
        return mark_as_resolved(ticket_id)
    if message in close_ticket_responses:
        return mark_as_resolved(ticket_id,True)
    if is_broadcasting:
        ticket = Ticket.objects.filter(id=ticket_id).first()
        check_other_pending_tickets = Ticket.objects.filter(status=PENDING_MODE,assigned_to=ticket.assigned_to,ticket_mode='other').exclude(id=ticket.id).first()
        if check_other_pending_tickets:
            check_other_pending_tickets.ticket_mode = QUEUED_MODE
            check_other_pending_tickets.queued_at = timezone.now()
            check_other_pending_tickets.save()
            notifier = f'Hello {check_other_pending_tickets.created_by.username.title()}, your inquiry is now on hold, please wait for your turn to be assisted.'
            data_to_paused_inquirer = get_text_message_input(check_other_pending_tickets.created_by.phone_number, notifier, None)
            send_message(data_to_paused_inquirer)
            created =timezone.localtime(ticket.created_at).strftime('%Y-%m-%d %H:%M')
            message =f'Hello {ticket.assigned_to.username}\nInquiry *#{ticket.id}*:\nOpened by: *{ticket.created_by.username.title()} - {ticket.branch_opened.title()}* branch at {created}\n- {ticket.description}\n\nhas been escalated to you and your current inquiry with *{check_other_pending_tickets.created_by.username.title()}* has been placed on hold,start helping the new inquirer now!'
        else:
            created =timezone.localtime(ticket.created_at).strftime('%Y-%m-%d %H:%M')
            message =f'Hello {ticket.assigned_to.username}\nInquiry *#{ticket.id}*:\nOpened by: *{ticket.created_by.username.title()} - {ticket.branch_opened.title()}* branch at {created}\n- {ticket.description}\n\nhas been escalated to you, start helping the inquirer now!'
        if prev_assignee:
            previous_supporter = SupportMember.objects.filter(id=prev_assignee).first()
            if previous_supporter:
                current_ticket = Ticket.objects.filter(status=PENDING_MODE,assigned_to=previous_supporter,ticket_mode='other').exclude(id=ticket.id).first()
                if current_ticket:
                    created =timezone.localtime(current_ticket.created_at).strftime('%Y-%m-%d %H:%M')
                    message_ob = f'Hello {previous_supporter.username},\nInquiry *#{current_ticket.id}*:\nOpened by: *{current_ticket.created_by.username.title()} - {current_ticket.branch_opened.title()}* branch at {created}\n- {current_ticket.description}\n\nhas been taken from you and escalated to *{ticket.assigned_to.username}* ,please continue assisting {current_ticket.created_by.username.title()} inquiry No *#{current_ticket.id}*'
                    data_ob = get_text_message_input(previous_supporter.phone_number, message_ob, None)
                    send_message(data_ob)
                else:
                    created =timezone.localtime(ticket.created_at).strftime('%Y-%m-%d %H:%M')
                    message_ob = f'Hello {previous_supporter.username},\nInquiry *#{ticket.id}*:\nOpened by: *{ticket.created_by.username.title()} - {ticket.branch_opened.title()}* branch at {created}\n- {ticket.description}\n\nhas been taken from you and escalated to *{ticket.assigned_to.username}* ,please reply with #resume to check your other queued tickets!.'
                    data_ob = get_text_message_input(previous_supporter.phone_number, message_ob, None)
                    send_message(data_ob)
                
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
    if message:
        data = get_text_message_input(ticket.assigned_to.phone_number, message, None)
        return send_message(data)
    if resolved:
        return mark_as_resolved(ticket.id)
    return broadcast_messages(name,ticket)
    