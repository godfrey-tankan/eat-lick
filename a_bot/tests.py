from datetime import datetime
# Create your tests here.
def get_greeting():
    current_hour = datetime.now().hour

    if 5 <= current_hour < 12:
        return "good morning"
    elif 12 <= current_hour < 18:
        return "good afternoon"
    else:
        return "good evening"
    
x=get_greeting()
print(x.title())