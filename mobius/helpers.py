import pytz
import iso8601

from mobius.constants import HOURS_PER_DAY, DAYS_OF_WEEK
from mobius import config


def week_day_range(start_day="monday"):
    """ Return list of days of week in order from start day """
    start_index = DAYS_OF_WEEK.index(start_day)
    return DAYS_OF_WEEK[start_index:] + DAYS_OF_WEEK[:start_index]


def week_range_all_true():
    """Return a week range with all true"""
    output = {}
    for day in week_day_range():
        output[day] = [1] * HOURS_PER_DAY

    return output


def week_sum(week_range_obj):
    """Return the sum of the contents of a week object"""
    sigma = 0
    for day in week_day_range():
        sigma += sum(week_range_obj[day])
    return sigma


def normalize_to_midnight(dt_obj):
    """Take a datetime and round it to midnight"""
    return dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)


def str_to_dt(dt_str):
    """Convert timestamp to datetime object that is *not* naive."""
    dt = iso8601.parse_date(dt_str)
    return dt.astimezone(pytz.timezone(config.DEFAULT_TZ))


def dt_to_query_str(dt_obj):
    """Convert a datetime object to UTC time then a naive string"""
    return dt_obj.astimezone(pytz.timezone(config.DEFAULT_TZ)).isoformat()


def dt_to_day(dt_obj):
    """Return day of week for datetime"""
    return dt_obj.strftime("%A").lower()


def dt_overlaps(start1, stop1, start2, stop2):
    """Return whether the start and end times of these datetime overlap"""

    # Filter to utc just for safety
    tz = pytz.timezone(config.DEFAULT_TZ)
    start1 = start1.astimezone(tz)
    stop1 = stop1.astimezone(tz)
    start2 = start2.astimezone(tz)
    stop2 = stop2.astimezone(tz)

    # case 1: 1 completely within 2
    if (start1 >= start2) and (stop1 <= stop2):
        return True

    # case 2:  1 overlaps beginning of 2
    if (start1 <= start2) and (stop1 > start2):
        return True

    # case 3: 1 overlaps end of 2
    if (start1 < stop2) and (stop1 >= stop2):
        return True

    return False
