from copy import deepcopy
from datetime import timedelta
import iso8601

import staffjoy
from staffjoy.exceptions import NotFoundException

from mobius import config, logger
from mobius.shift import Shift
from mobius.helpers import week_day_range, week_range_all_true, dt_to_query_str, \
    dt_to_day, dt_overlaps
from mobius.constants import MINUTES_PER_HOUR, HOURS_PER_DAY, APPROVED_TIME_OFF_STATES


class Employee:
    """ Extends a person for context within a business """

    def __init__(self,
                 user_id,
                 min_hours_per_workweek,
                 max_hours_per_workweek,
                 preferences=None,
                 working_hours=None,
                 time_off_requests=None,
                 preceding_day_worked=False,
                 preceding_days_worked_streak=None,
                 existing_shifts=None,
                 environment=None):
        """Create a worker based on the person and business info"""

        self.user_id = user_id
        self.min_hours_per_workweek = min_hours_per_workweek
        self.max_hours_per_workweek = max_hours_per_workweek
        self.environment = environment
        self._build_active_days()

        if preferences:
            self.preferences = preferences
        else:
            self._fetch_preferences()

        if working_hours is not None:
            self.availability = working_hours
        else:
            self._fetch_working_hours()

        if time_off_requests is None:
            time_off_requests = self._fetch_time_off_requests()
        self._process_time_off_requests(time_off_requests)

        if preceding_day_worked is not None:
            self.preceding_day_worked = preceding_day_worked
        else:
            self._fetch_preceding_day_worked()

        if preceding_days_worked_streak is not None:
            self.preceding_days_worked_streak = preceding_days_worked_streak
        else:
            self._fetch_preceding_days_worked_streak()

        if existing_shifts is not None:
            self.existing_shifts = existing_shifts
        else:
            self._fetch_existing_shifts()

        self._process_existing_shifts()
        self._filter_preferences()
        self._set_alpha_beta()

    def _build_active_days(self):
        """Build which days the person is *already* working from fixed shifts"""
        self.active_days = {}
        for day in week_day_range():
            self.active_days[day] = False

    def _fetch_preferences(self):
        """Fetch preferences from the api and set on instance"""
        logger.debug("Fetching preferences for user %s" % self.user_id)
        try:
            pref_obj = self._get_role_client().get_schedule(
                self.environment.schedule_id).get_preference(self.user_id)
            self.preferences = pref_obj.data.get("preference")
        except NotFoundException:
            self.preferences = week_range_all_true()

        if not self.preferences:
            self.preferences = week_range_all_true()

    def _fetch_working_hours(self):
        """Fetch working hours from the api and set on instance"""
        logger.debug("Fetching working hours for user %s" % self.user_id)
        role = self._get_role_client()
        worker = role.get_worker(self.user_id)
        self.availability = worker.data.get("working_hours")
        if not self.availability:
            self.availability = week_range_all_true()

    def _fetch_time_off_requests(self):
        """Fetch time off requests from the api and return"""
        logger.debug("Fetching time off requests for user %s" % self.user_id)
        role = self._get_role_client()
        worker = role.get_worker(self.user_id)

        # Get requests from API
        return worker.get_time_off_requests(start=self.environment.start,
                                            end=self.environment.stop)

    def _fetch_preceding_day_worked(self):
        """Fetch from api whether worker worked the day before this week began.
        Used for consecutive days off.
        """
        logger.debug("Fetching preceding day worked for user %s" %
                     self.user_id)
        search_end = self.environment.start
        search_start = search_end - timedelta(days=1)
        shifts_objs = self._get_role_client().get_shifts(
            start=dt_to_query_str(search_start),
            end=dt_to_query_str(search_end),
            user_id=self.user_id, )

        for shift in shifts_objs:
            # Edge case - mark the first day of week as
            # active if the person works past midnight
            if shift.stop > self.environment.start:
                self.active_days[dt_to_day(
                    self.environment.datetime_utc_to_local(shift.stop))] = True

        self.preceding_day_worked = len(shifts_objs) > 0

    def _fetch_preceding_days_worked_streak(self):
        """See how many days in an row the worker has worked prior to the
        beginning of this week.
        """
        logger.debug("Fetching preceding day streak for user %s" %
                     self.user_id)
        # Search up to max_consecutive_workdays - beyond doesn't matter
        streak = 0
        for t in range(self.environment.max_consecutive_workdays):
            # Build search
            search_end = self.environment.start - timedelta(days=t)
            search_start = search_end - timedelta(days=1)

            shifts_obj = self._get_role_client().get_shifts(
                start=dt_to_query_str(search_start - timedelta(
                    hours=config.MAX_HOURS_PER_SHIFT)),
                end=dt_to_query_str(search_end),
                user_id=self.user_id, )
            if len([s for s in shifts_obj
                    if (Shift(s).start >= search_start) > 0]):
                streak += 1
            else:
                # Streak over!
                return streak
        return streak

    def _fetch_existing_shifts(self):
        """Look for fixed shifts and other stuff"""
        logger.debug("Fetching existing shifts for user %s" % self.user_id)
        self.existing_shifts = []
        shifts_obj_raw = self._get_role_client().get_shifts(
            start=dt_to_query_str(self.environment.start - timedelta(
                hours=config.MAX_HOURS_PER_SHIFT)),
            end=dt_to_query_str(self.environment.stop),
            user_id=self.user_id)

        shifts_obj = []
        for s in shifts_obj_raw:
            shifts_obj.append(Shift(s))

        for s in [s for s in shifts_obj if s.start >= self.environment.start]:

            logger.info("Found existing shift %s for user %s" %
                        (s.shift_id, self.user_id))

            self.existing_shifts.append(s)

            # Also decrease hours to be scheduled by that
            self.min_hours_per_workweek -= 1.0 * s.total_minutes(
            ) / MINUTES_PER_HOUR
            if self.min_hours_per_workweek < 0:
                self.min_hours_per_workweek = 0

            self.max_hours_per_workweek -= 1.0 * s.total_minutes(
            ) / MINUTES_PER_HOUR
            if self.max_hours_per_workweek < 0:
                self.min_hours_per_workweek = 0

            self.max_hours_per_workweek -= 1.0 * s.total_minutes(
            ) / MINUTES_PER_HOUR
            if self.max_hours_per_workweek < 0:
                self.max_hours_per_workweek = 0

    def _process_existing_shifts(self):
        """Set self to active during shifts."""
        for s in self.existing_shifts:
            self.active_days[dt_to_day(s.start)] = True
            # only mark end day as active if it's within week (aka not overlap)
            if s.stop < self.environment.stop:
                self.active_days[dt_to_day(s.stop)] = True

    def _process_time_off_requests(self, to_requests):
        """Subtract time off requests from availablity and min/max hours"""
        for r in to_requests:
            if r.data.get("state") not in APPROVED_TIME_OFF_STATES:
                logger.info(
                    "Time off request %s skipped because it is in unapproved state %s"
                    % (r.data.get("time_off_request_id"), r.data.get("state")))
                continue

            logger.debug("Processing time off request for user %s: %s" %
                         (self.user_id, r))

            self.min_hours_per_workweek -= 1.0 * r.data[
                "minutes_paid"] / MINUTES_PER_HOUR
            if self.min_hours_per_workweek < 0:
                self.min_hours_per_workweek = 0

            self.max_hours_per_workweek -= 1.0 * r.data[
                "minutes_paid"] / MINUTES_PER_HOUR
            if self.max_hours_per_workweek < 0:
                self.max_hours_per_workweek = 0

            # Update availability
            # Get day of week for request and update availability
            day_of_week = dt_to_day(self.environment.datetime_utc_to_local(
                iso8601.parse_date(r.data["start"])))
            self.availability[day_of_week] = [0] * HOURS_PER_DAY

            logger.info("Marked user %s as unavailable on %s due to time off" %
                        (self.user_id, day_of_week))

    def available_to_work(self, shift):
        """Check whether the worker can work this shift"""
        # Existing shifts - check whether violates min hours between or overlap
        shift.start = self.environment.datetime_utc_to_local(shift.start)
        shift.stop = self.environment.datetime_utc_to_local(shift.stop)
        for s in self.existing_shifts:
            if dt_overlaps(
                    s.start - timedelta(
                        minutes=self.environment.min_minutes_between_shifts),
                    s.stop + timedelta(
                        minutes=self.environment.min_minutes_between_shifts),
                    shift.start,
                    shift.stop):
                return False

        # todo - compare to self.availability
        s_start_local = self.environment.datetime_utc_to_local(shift.start)
        s_stop_local = self.environment.datetime_utc_to_local(shift.stop)

        s_start_day = dt_to_day(s_start_local)
        s_stop_day = dt_to_day(s_stop_local)

        # What hour to search to - if it's exactly on the hour, then exclude (because search inclusive -> exclusive)
        if s_stop_local.minute + s_stop_local.second + s_stop_local.microsecond > 0:
            search_stop_hour = s_stop_local.hour + 1
        else:
            search_stop_hour = s_stop_local.hour

            # Bug fix - if it's exactly midnight, then roll back day
            if search_stop_hour is 0:
                # Roll back start day
                s_stop_day = s_start_day

        if s_start_day == s_stop_day:
            # Same start and stop day

            for t in range(s_start_local.hour, search_stop_hour):
                if self.availability[s_start_day][t] != 1:
                    return False
        else:
            # Different start and stop days

            # Day 1 (start -> end of day)
            for t in range(s_start_local.hour, HOURS_PER_DAY):
                if self.availability[s_start_day][t] != 1:
                    return False

            # Day 2 (start of day -> stop)
            for t in range(search_stop_hour):
                if self.availability[s_stop_day][t] != 1:
                    return False

        return True

    def _get_role_client(self):
        c = staffjoy.Client(key=config.STAFFJOY_API_KEY, env=config.ENV)
        org = c.get_organization(self.environment.organization_id)
        loc = org.get_location(self.environment.location_id)
        role = loc.get_role(self.environment.role_id)
        return role

    def _filter_preferences(self):
        raw_prefs = deepcopy(self.preferences)
        processed_prefs = {}
        for day in week_day_range():
            # Dot product so that preference is only valid when available
            processed_prefs[day] = [
                a * b for a, b in zip(self.availability[day], raw_prefs[day])
            ]

        self.preferences = processed_prefs

    def _set_alpha_beta(self):
        """ Calculate the alpha and beta values"""
        # (Details in docs)

        # Sum availability and preferences
        sum_availability = 0
        sum_preferences = 0

        for day in week_day_range():
            sum_availability += sum(self.availability[day])
            sum_preferences += sum(self.preferences[day])

        if sum_preferences == sum_availability or sum_preferences == 0 or sum_availability == 0:
            self.alpha = 0
            self.beta = 0
            return

        # Need to force float

        self.alpha = 1.0 * (
            sum_availability - sum_preferences) / sum_availability

        self.beta = 1.0 * sum_preferences / sum_availability

    def shift_happiness_score(self, shift):
        """Return the happiness shift for a given shift"""
        s_start_local = self.environment.datetime_utc_to_local(shift.start)
        s_stop_local = self.environment.datetime_utc_to_local(shift.stop)

        s_start_day = dt_to_day(s_start_local)
        s_stop_day = dt_to_day(s_stop_local)

        score = 0.0

        # Right now we ignore partial hours, though we could do fractions

        if s_start_day == s_stop_day:
            # Same day
            for t in range(s_start_local.hour, s_stop_local.hour):
                if self.preferences[s_start_day] == 1:
                    score += 1 + self.alpha
                else:
                    score += 1 - self.beta
        else:
            # start and end on different days
            for t in range(s_start_local.hour, HOURS_PER_DAY):
                if self.preferences[s_start_day] == 1:
                    score += 1 + self.alpha
                else:
                    score += 1 - self.beta

            for t in range(s_stop_local.hour):
                if self.preferences[s_stop_day] == 1:
                    score += 1 + self.alpha
                else:
                    score += 1 - self.beta
        return score
