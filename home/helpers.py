from datetime import datetime, timedelta
from django.utils.timezone import now
import re


def get_current_month_dates(today):
    try:
        today = datetime.strptime(today, '%Y-%m-%d')
    except ValueError:
        today = datetime.strptime(now().date(), '%Y-%m-%d ')
    year = today.year
    month = today.month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    return start_date, end_date


def format_phone_number(phone_number):
    match = re.search(r'7', phone_number)
    if match:
        formatted_number = '263' + phone_number[match.start():]
        return formatted_number
    else:
        return phone_number