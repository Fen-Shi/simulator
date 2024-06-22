import datetime


# Define working hours start and end times
working_hours_start = datetime.time(8, 0)
working_hours_end = datetime.time(17, 0)

# Define the start and end times for the simulation
start_time = datetime.datetime(2018, 1, 1, 0, 0)
end_time = datetime.datetime(2018, 12, 31, 17, 0)
current_time = start_time


def is_working_hour(current_time):
    """
    Check if the current time is within working hours.
    Working hours are from 8:00 AM to 5:00 PM, Monday to Friday.
    """
    return working_hours_start <= current_time.time() <= working_hours_end and current_time.weekday() < 5


def is_not_working_hour(current_time):
    """
    Check if the current time is outside working hours.
    """
    return not is_working_hour(current_time)


def next_working_hour(current_time):
    """
    Find the next working hour from the current time.
    If the current time is on a weekend, return the next Monday at 8:00 AM.
    If the current time is after 5:00 PM on a weekday, return the next weekday at 8:00 AM.
    If the current time is before 8:00 AM on a weekday, return today at 8:00 AM.
    """
    if current_time.weekday() >= 5:  # It's the weekend
        days_to_monday = 7 - current_time.weekday()
        next_monday_8am = datetime.datetime.combine(
            current_time.date() + datetime.timedelta(days=days_to_monday),
            datetime.time(8, 0)
        )
        return next_monday_8am

    else:  # It's a weekday
        if current_time.hour >= 17:
            next_day_8am = datetime.datetime.combine(
                current_time.date() + datetime.timedelta(days=1),
                datetime.time(8, 0)
            )
            return next_day_8am
        else:
            today_8am = datetime.datetime.combine(
                current_time.date(),
                datetime.time(8, 0)
            )
            return today_8am


def next_non_working_hour(current_time):
    """
    Find the next non-working hour from the current time.
    Return today at 5:01 PM.
    """
    today_17am = datetime.datetime.combine(
        current_time.date(),
        datetime.time(17, 1)
    )
    return today_17am



