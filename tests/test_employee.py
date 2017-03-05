"""
Test the Employee object
"""

import unittest

from mobius import Employee, Environment
from mobius.helpers import week_day_range
from mobius.constants import HOURS_PER_DAY
from mobius.shift import Shift
from .helpers import ApiSpoof


class TestEmployee(unittest.TestCase):
    """ Test the worker class """

    def setUp(self):
        self.env_attributes = {
            "organization_id": 7,
            "location_id": 8,
            "role_id": 4,
            "schedule_id": 9,
            "tz_string": "America/Los_Angeles",
            "start": "2015-12-21T08:00:00",
            "stop": "2015-12-28T08:00:00",
            "day_week_starts": "monday",
            "min_minutes_per_workday": 60 * 5,
            "max_minutes_per_workday": 60 * 8,
            "min_minutes_between_shifts": 60 * 12,
            "max_consecutive_workdays": 6,
        }
        self.env = Environment(**self.env_attributes)

        self.employee_attributes = {
            "user_id": 27182818,
            "min_hours_per_workweek": 29.5,
            "max_hours_per_workweek": 40,
            "preceding_day_worked": True,
            "preceding_days_worked_streak": 4,
            "existing_shifts": [],  # TODO - should probably add one fixed
            "time_off_requests": [],
            "preferences": {
                "monday": [0] * 24,
                "tuesday": [1] * 24,
                "wednesday": [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                              1, 1, 1, 1, 1, 1, 0, 0],
                "thursday": [0] * 24,
                "friday": [1] * 24,
                "saturday": [1] * 24,
                "sunday": [0] * 24,
            },
            "working_hours": {
                "monday": [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                           1, 1, 1, 1, 1, 0, 0],
                "tuesday": [1] * 24,
                "wednesday": [1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                              1, 1, 1, 1, 1, 1, 0, 0],
                "thursday": [0] * 24,
                "friday": [1] * 24,
                "saturday": [1] * 24,
                "sunday": [1] * 24,
            },
            "environment": self.env,
        }

    def tearDown(self):
        self.Employee = None
        self.Env = None

    def create_employee(self):
        """ Create a worker object based on the person """
        self.employee = Employee(**self.employee_attributes)

    def test_init(self):
        """ Check whether the class initializes """
        self.create_employee()

        preserved_variables = ["user_id", "min_hours_per_workweek",
                               "max_hours_per_workweek", "preferences",
                               "environment"]

        for variable in preserved_variables:
            assert getattr(self.employee,
                           variable) == self.employee_attributes[variable]

    def test_preferences_filtered_by_availability(self):
        # Overwrite preferences to always be 1
        for day in week_day_range():
            self.employee_attributes["preferences"][day] = [1] * HOURS_PER_DAY

        self.create_employee()

        # And now check that the preferences are filtered
        for day in week_day_range():
            for t in range(HOURS_PER_DAY):
                assert self.employee.preferences[day][
                    t] <= self.employee.availability[day][t]

    def test_available_to_work_working_hours_known_available(self):
        self.create_employee()
        # Hypothetically available to work 1-2am but not 2-3am
        # Wednesday
        shift_src = {
            "id": 2718,
            "start": "2015-12-23T01:00:00-08:00",
            "stop": "2015-12-23T02:00:00-08:00",
            "user_id": 0,  # It's not assigned yeeeeet
        }
        s = Shift(shift_src)
        assert self.employee.available_to_work(s) == True

    def test_available_to_work_working_hours_known_unavailable(self):
        self.create_employee()
        # Hypothetically available to work 1-2am but not 2-3am
        # Wednesday
        shift_src = {
            "id": 2718,
            "start": "2015-12-23T02:00:00-08:00",
            "stop": "2015-12-23T03:00:00-08:00",
            "user_id": 0,  # It's not assigned yeeeeet
        }
        s = Shift(shift_src)
        assert self.employee.available_to_work(s) == False

    def test_available_to_work_working_hours_unavailable_one_minute(self):
        # In this test, we're technically 1 minute into unavailability,
        # which should be overall unavailable
        self.create_employee()
        shift_src = {
            "id": 2718,
            "start": "2015-12-23T01:00:00-08:00",
            "stop": "2015-12-23T02:01:00-08:00",
            "user_id": 0,  # It's not assigned yeeeeet
        }
        s = Shift(shift_src)
        assert self.employee.available_to_work(s) == False

    def test_available_to_work_working_hours_mixed_avail_therefore_unavailable(
            self):
        self.create_employee()
        # Hypothetically available to work 1-2am but not 2-3am
        # Wednesday
        shift_src = {
            "id": 2718,
            "start": "2015-12-23T00:00:00-08:00",
            "stop": "2015-12-23T03:00:00-08:00",
            "user_id": 0,  # It's not assigned yeeeeet
        }
        s = Shift(shift_src)
        assert self.employee.available_to_work(s) == False

    def test_available_to_work_working_hours_mixed_days_available(self):
        self.create_employee()
        # Hypothetically available to work 1-2am but not 2-3am
        # Wednesday
        shift_src = {
            "id": 2718,
            "start": "2015-12-22T07:00:00-08:00",
            "stop": "2015-12-23T02:00:00-08:00",
            "user_id": 0,  # It's not assigned yeeeeet
        }
        s = Shift(shift_src)
        assert self.employee.available_to_work(s) == True

        # Make a quick swap
        self.employee.availability["tuesday"][23] = 0
        assert self.employee.available_to_work(s) == False

    def test_available_to_work_working_hours_mixed_days_unavailable(self):
        self.create_employee()
        # Hypothetically available to work 1-2am but not 2-3am
        # Wednesday
        shift_src = {
            "id": 2718,
            "start": "2015-12-22T07:00:00-08:00",
            "stop": "2015-12-23T02:30:00-08:00",
            "user_id": 0,  # It's not assigned yeeeeet
        }
        s = Shift(shift_src)
        assert self.employee.available_to_work(s) == False

    def test_available_to_work_working_hours_end_midnight_available(self):

        self.employee_attributes["working_hours"]["wednesday"] = [1] * 24
        self.create_employee()
        shift_src = {
            "id": 2718,
            "start": "2015-12-22T07:00:00-08:00",  # Tuesday
            "stop": "2015-12-23T00:00:00-08:00",  # Midnight Wednseady
            "user_id": 0,  # It's not assigned yeeeeet
        }
        s = Shift(shift_src)
        assert self.employee.available_to_work(s) == True

    def test_expected_alpha_beta_values(self):
        # This is with test data
        self.create_employee()
        assert self.employee.alpha > 0
        assert self.employee.alpha < 1
        assert self.employee.beta > 0
        assert self.employee.beta < 1

    def test_no_preference_alpha_beta_values(self):
        """ If we zero out the preferences, alpha and beta should be zero"""
        for day in week_day_range():
            self.employee_attributes["preferences"][day] = [0] * 24

        self.create_employee()
        assert self.employee.alpha == 0
        assert self.employee.beta == 0

    def test_all_preference_alpha_beta_values(self):
        """ If we prefer all the time, alpha and beta should be zero"""
        for day in week_day_range():
            self.employee_attributes["preferences"][day] = [1] * 24

        self.create_employee()
        assert self.employee.alpha == 0
        assert self.employee.beta == 0

    def test_alpha_decreases_beta_increases_with_more_preferences(self):
        self.create_employee()
        start_alpha = self.employee.alpha
        start_beta = self.employee.beta

        # Increase preferneces
        self.employee_attributes["preferences"]["sunday"] = [1] * 24
        self.create_employee()

        # More preference, so upweighting on preferred should go down
        assert self.employee.alpha < start_alpha
        # More preference, so downweight on non-preferred goes up
        assert self.employee.beta > start_beta

    def test_time_off_request_approved_paid(self):
        req = ApiSpoof({
            "approver_user_id": 0,
            "id": 1,
            "minutes_paid": 510,  # 8.5 hours - to detect floating pt err
            "role_id": 3,
            "start": "2015-12-22T08:00:00",  # Tuesday
            "stop": "2015-12-23T08:00:00",  # Tuesday
            "user_id": 4,
            "state": "approved_paid",
        })

        self.employee_attributes["time_off_requests"].append(req)

        # Make sure this bottoms out to zero
        self.employee_attributes["min_hours_per_workweek"] = 1

        self.create_employee()

        # Should subtract minutes paid
        # (should bottom out)
        assert self.employee.min_hours_per_workweek == 0.0
        assert self.employee.max_hours_per_workweek == 31.5
        assert self.employee.availability["tuesday"] == [0] * 24

    def test_time_off_request_approved_unpaid(self):
        req = ApiSpoof({
            "approver_user_id": 0,
            "id": 1,
            "minutes_paid": 0,  # 8.5 hours - to detect floating pt err
            "role_id": 3,
            "start": "2015-12-22T08:00:00",  # Tuesday
            "stop": "2015-12-23T08:00:00",  # Tuesday
            "user_id": 4,
            "state": "approved_unpaid",
        })

        self.employee_attributes["time_off_requests"].append(req)

        self.create_employee()

        assert self.employee.min_hours_per_workweek == self.employee_attributes[
            "min_hours_per_workweek"]
        assert self.employee.max_hours_per_workweek == self.employee_attributes[
            "max_hours_per_workweek"]
        assert self.employee.availability["tuesday"] == [0] * 24

    def test_time_off_request_denied(self):
        req = ApiSpoof({
            "approver_user_id": 0,
            "id": 1,
            "minutes_paid": 0,
            "role_id": 3,
            "start": "2015-12-22T08:00:00",  # Tuesday
            "stop": "2015-12-23T08:00:00",  # Tuesday
            "user_id": 4,
            "state": "denied",
        })

        self.employee_attributes["time_off_requests"].append(req)

        self.create_employee()

        assert self.employee.min_hours_per_workweek == self.employee_attributes[
            "min_hours_per_workweek"]
        assert self.employee.max_hours_per_workweek == self.employee_attributes[
            "max_hours_per_workweek"]
        assert self.employee.availability[
            "tuesday"] == self.employee_attributes["working_hours"]["tuesday"]

    def test_time_off_request_sick(self):
        req = ApiSpoof({
            "approver_user_id": 0,
            "id": 1,
            "minutes_paid": 510,  # 8.5 hours - to detect floating pt err
            "role_id": 3,
            "start": "2015-12-22T08:00:00",  # Tuesday
            "stop": "2015-12-23T08:00:00",  # Tuesday
            "user_id": 4,
            "state": "sick",
        })

        self.employee_attributes["time_off_requests"].append(req)

        self.create_employee()

        # Should subtract minutes paid
        # (should bottom out)
        assert self.employee.min_hours_per_workweek == 21.0
        assert self.employee.max_hours_per_workweek == 31.5
        assert self.employee.availability["tuesday"] == [0] * 24

    def test_time_off_request_no_state(self):
        req = ApiSpoof({
            "approver_user_id": 0,
            "id": 1,
            "minutes_paid": 0,
            "role_id": 3,
            "start": "2015-12-22T08:00:00",  # Tuesday
            "stop": "2015-12-23T08:00:00",  # Tuesday
            "user_id": 4,
            "state": None,
        })

        self.employee_attributes["time_off_requests"].append(req)

        self.create_employee()

        assert self.employee.min_hours_per_workweek == self.employee_attributes[
            "min_hours_per_workweek"]
        assert self.employee.max_hours_per_workweek == self.employee_attributes[
            "max_hours_per_workweek"]
        assert self.employee.availability[
            "tuesday"] == self.employee_attributes["working_hours"]["tuesday"]

    def test_multiple_time_off_requests(self):
        req1 = ApiSpoof({
            "approver_user_id": 0,
            "id": 1,
            "minutes_paid": 0,
            "role_id": 3,
            "start": "2015-12-22T08:00:00",  # Tuesday
            "stop": "2015-12-23T08:00:00",  # Tuesday
            "user_id": 4,
            "state": "approved_unpaid",
        })

        req2 = ApiSpoof({
            "approver_user_id": 0,
            "id": 2,
            "minutes_paid": 60,  # 8.5 hours - to detect floating pt err
            "role_id": 3,
            "start": "2015-12-23T08:00:00",  # Tuesday
            "stop": "2015-12-24T08:00:00",  # Tuesday
            "user_id": 4,
            "state": "approved_paid",
        })

        req3 = ApiSpoof({
            "approver_user_id": 0,
            "id": 2,
            "minutes_paid": 0,  # 8.5 hours - to detect floating pt err
            "role_id": 3,
            "start": "2015-12-24T08:00:00",  # Tuesday
            "stop": "2015-12-25T08:00:00",  # Tuesday
            "user_id": 4,
            "state": "denied",
        })

        self.employee_attributes["time_off_requests"].append(req1)
        self.employee_attributes["time_off_requests"].append(req2)
        self.employee_attributes["time_off_requests"].append(req3)
        self.create_employee()

        assert self.employee.min_hours_per_workweek == 28.5
        assert self.employee.max_hours_per_workweek == 39.0
        # approved
        assert self.employee.availability["tuesday"] == [0] * 24
        assert self.employee.availability["wednesday"] == [0] * 24
        # denied
        assert self.employee.availability[
            "wednesday"] == self.employee_attributes["working_hours"][
                "wednesday"]
