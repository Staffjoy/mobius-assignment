import pytz

from mobius.helpers import str_to_dt
from mobius import config


class Environment:
    """Role, Location, and Organization data used in the calculation"""

    def __init__(self,
                 organization_id=None,
                 location_id=None,
                 role_id=None,
                 schedule_id=None,
                 tz_string=None,
                 start=None,
                 stop=None,
                 day_week_starts=None,
                 min_minutes_per_workday=None,
                 max_minutes_per_workday=None,
                 min_minutes_between_shifts=None,
                 max_consecutive_workdays=None):

        self.organization_id = organization_id
        self.location_id = location_id
        self.role_id = role_id
        self.schedule_id = schedule_id
        self.tz = pytz.timezone(tz_string)
        self.start = self.datetime_utc_to_local(str_to_dt(start))
        self.stop = self.datetime_utc_to_local(str_to_dt(stop))

        self.day_week_starts = day_week_starts

        self.min_minutes_per_workday = min_minutes_per_workday
        self.max_minutes_per_workday = max_minutes_per_workday
        self.min_minutes_between_shifts = min_minutes_between_shifts
        self.max_consecutive_workdays = max_consecutive_workdays

    def datetime_utc_to_local(self, dt):
        """Take a datetime that is naive or in utc and convert to local tz"""
        if not hasattr(dt, "tzinfo"):
            dt.replace(tzinfo=pytz.timezone(config.DEFAULT_TZ))

        return dt.astimezone(self.tz)
