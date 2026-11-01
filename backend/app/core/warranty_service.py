import calendar
from datetime import date


def add_calendar_months(start_date: date, months: int) -> date:
    total_months = start_date.month + months - 1
    year = start_date.year + total_months // 12
    month = total_months % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
