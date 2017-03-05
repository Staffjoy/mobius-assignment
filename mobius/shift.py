import math

from mobius.helpers import str_to_dt
from mobius.constants import SECONDS_PER_MINUTE


class Shift():
    """Converts a shift api object to internal object"""

    def __init__(self, shift_api_obj):
        # If you get a single shift, it's in data,
        # otherwise it's an interator of a dict
        if hasattr(shift_api_obj, "data"):
            self.shift_id = shift_api_obj.data["id"]
            self.user_id = shift_api_obj.data["user_id"]
            self.start = str_to_dt(shift_api_obj.data["start"])
            self.stop = str_to_dt(shift_api_obj.data["stop"])
        else:
            self.shift_id = shift_api_obj["id"]
            self.user_id = shift_api_obj["user_id"]
            self.start = str_to_dt(shift_api_obj["start"])
            self.stop = str_to_dt(shift_api_obj["stop"])

    def total_minutes(self):
        """Return length as minutes, rounded up"""
        return math.ceil(1.0 * (self.stop - self.start).total_seconds() /
                         SECONDS_PER_MINUTE)

    def minutes_overlap(self, start=None, stop=None):
        """Return minutes of overlap with another shift"""
        if start is None or stop is None:
            raise Exception("Need to provide start and stop")

        delta = min(self.stop, stop) - max(self.start, start)
        # Check if delta is negative,
        if delta.total_seconds() < 0:
            return 0
        else:
            return math.ceil(1.0 * delta.total_seconds() / SECONDS_PER_MINUTE)
