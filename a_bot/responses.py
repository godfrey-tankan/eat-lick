accept_ticket_response = "🟢There is a ticket opened just now by *{} - {}*.\n\n*Ticket ID:* {}\n*Description:* \n- {}\n\nPlease reply with this ticket id to assign it to yourself."
greeting_messages = ["hi","hy", "hello", "hey", "good day", "good morning", "good afternoon", "good evening"]
thank_you_messages = ["thank",'zvaita','yaita','now working','#cancel','#exit']
help_messages = ["help", "help me", "i need help", "can you help me", "can you help me with this",'please','assist','support','can you ','is not','a problem','an issue','error','fault','mistake','wrong','fail','trouble']
inquirer_helped_assumed_messages = 'This inquirer seem to have been helped, Reply with #helped or #done to mark this inquirer as helped'
resolve_ticket_responses = ['#done','#resolved','##done','##resolved']
inquirers_help_menu='📋 *INQUIRY HELP MENU!*\n`Guidance to get assistance quickly`:\n\n*Fill in Your Details*\n- Please start by providing your First Name, Surname, and Branch. This helps us serve you better.\n\n*1. OPEN AN INQUIRY:*\n- Once your details are submitted, you can open an inquiry anytime. Just describe your issue, and a support member will start assisting you right away.\n\n*2. MANAGE YOUR INQUIRIES*\n- You can open different inquiries by replying with `yes` when asked or `no` accordingly.\n\n*3. TRACK YOUR INQUIRIES*\n- Your inquiries will be tracked throughout the conversation. Once you seem like your issue is resolved, you’ll be prompted to mark it as resolved or not.\n\n*4. Rate Our Support*\n- If you feel helped, select 1 to mark the inquiry as Resolved. \n- If helped but your issue was not fully resolved, select 2.\n- If you need more help, simply continue chatting with the support member\n.*NB*: If you select 1 (Resolved), you’ll be asked to rate the level of support you received from 0-5. Please give your honest feedback.\n\n*5. MANUAL  RESOLUTION*\n- If you are helped but don’t receive a prompt asking if you’re satisfied, simply reply with #done.\n\n*6. SEND MEDIA FILES*\n- You can send screenshots, voice notes, videos, or documents to help us understand your issue better. Feel free to share any necessary files with the support member.\n\nYou can always refer to this help menu by sending word *help*.'
close_ticket_responses = ['#close','#closed','##close']
is_inquirer_helped = 'Hi {}!\n*Please confirm if your inquiry has been resolved*\n`INQUIRY`:\n- *"{}"*\n\n*1*.yes resolved\n*2*.completed but unresolved \n\nReply with the number of your choice.'
ACCEPT_TICKET_MODE = "ticket_acceptance"
NEW_TICKET_ACCEPT_MODE = "new_ticket_acceptance"
confirm_open_new_ticket = ['yes','yeah','sure','yea']
deny_open_new_ticket = ['no','nah','nope','not']
new_inquiry_opened_response='Your inquiry has been created.A support member will be assisting you shortly.\n\nYou can *mark this inquiry as helped* by replying with #done.'
HELPING_MODE = "helping"
RESUME_MODE = "resuming"
INQUIRY_MODE = "inquiry"
RESOLVED_MODE = "resolved"
PENDING_MODE = "pending"
CLOSED_MODE = "closed"
NEW_TICKET_MODE = "new_ticket"
MAIN_MENU_MODE='main-menu'
INQUIRY_STATUS_MODE='inquiry-status'
OPEN_MODE = "open"
QUEUED_MODE = "queued"
SUPPORT_RATING='support_rating'
WAITING_MODE = "waiting"
NAMES_MODE = "providing_names"
BRANCH_MODE = "providing_branch"
OPEN_TICKETS_MODE="open_tickets"
ATTENDED_TICKETS_MODE="attended_tickets"
CONFIRM_RESPONSE ='confirming_response'
SUPPORT_MEMBER_ASSISTANCE_MODE = "support_assistance"
SUPPORT_MEMBER_ASSISTING_MODE="support_assisting"
SUPPORT_MEMBER_ASSISTING='support_member_assisting'
support_member_help_requests = ["#help","#assist","#support","#trouble"]
back_to_helping_mode = "You are now back to helping mode, you're now chatting with the inquirer."
tankan_self='This bot was created by tnqn @ clava.co.zw'
passed_support_helping ="You have passed the request,you can now continue with your current task."
support_users_interaction = "You are now interacting with other support members,What do you need help with?"
support_user_helper = "You are now helping a support member,send a message to start assisting."
support_member_help_menu = '''*👨‍💻 SUPPORT MEMBER GUIDE*\n\n
1. *ASSIGNING TICKETS*
   \n- When a new ticket is opened, reply with the *provided Ticket ID* to assign it to yourself.
   \n- Once you see a message confirming the assignment, you can immediately start assisting the inquirer by sending a message.\n\n
2. *HANDLING MULTIPLE TICKETS*
   \n- If you have pending tickets, you’ll still be prompted to assign any newly opened ticket to yourself.
   \n- *Top Priority:* If you choose to take the new ticket, it will be set in queue and the current assigned ticket will be given top priority. The conversation will remain between you and the previous inquirer.
   \n- *Skipping Tickets:* If you decide to skip the new ticket, you can continue working on your current tasks.\n\n
3. *RESUMING TICKETS*
   \n- If you have multiple tickets assigned and some are in the queue, send *#resume* to choose a ticket and resume providing assistance.\n\n
4. *CLOSING AND RESOLVING TICKETS*
   \n- To close a ticket, send *#close*.
   \n- If the inquiry is resolved, send *#done*. This will mark the ticket as resolved.
5. *REQUESTING ASSISTANCE*
   \n- If you need help with a ticket, send *#help* or *#assist*.
   \n- All support members will be notified of your request, and those who choose to assist will follow the prompts.\n\n
6. *Exiting Assistance Mode*
   \n- If you decide to exit the support member assistance mode, send *#exit* or *#cancel*. This will allow you to continue interacting with inquirers directly.\n\n
7. *Open Tickets*
   \n- To view all open tickets, send *#open*.
   \n- You can view all the tickets that are currently open and not assigned to anyone.\n\n
8. *Attended Tickets*
   \n- To view all attended tickets, send *#taken*.
   \n- You can view all the tickets that have been assigned and are currently being assisted.\n\n
9. *RELEASING TICKETS*
   \n- If you are unable to assist an inquirer, you can release the ticket by sending *#release*.\n\n
*Remember:* Your role is crucial in providing timely and effective support. Keep track of your tickets, prioritize as needed, and don’t hesitate to ask for help when necessary. You can always refer to this by sending word *help*.
'''