"""
Test the Employee object
"""

import unittest

from mobius import Environment
"""
Note: We let you modify the self.env_attributes for
any tests you want to run before the env object
gets created.

idea:

self.env_attributes["foo"] = "new_value"
self.create_env
assert self.env.foo == "new_value"
"""


class TestEnvironment(unittest.TestCase):
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

    def create_env(self):
        """ Create an environment object based on the attributes """
        self.env = Environment(**self.env_attributes)

    def test_init(self):
        """ Check whether the class initializes """
        self.create_env()

        preserved_variables = ["organization_id", "location_id", "role_id",
                               "schedule_id", "day_week_starts",
                               "min_minutes_per_workday",
                               "max_minutes_per_workday",
                               "min_minutes_between_shifts",
                               "max_consecutive_workdays"]
        for variable in preserved_variables:
            assert getattr(self.env, variable) == self.env_attributes[variable]

    # TODO - better testing of this class
