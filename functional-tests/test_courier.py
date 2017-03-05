from copy import deepcopy

from mobius import Employee, Environment, Assign
from mobius.shift import Shift
from mobius.constants import DAYS_OF_WEEK
from mobius.helpers import week_day_range

# A test derived from some scheduling we did for courier back
# in the day, minus personally-identifiable info :-)
# It's the bike couriers


def test_courier_data():
    env_data = {
        "organization_id": 7,
        "location_id": 8,
        "role_id": 4,
        "schedule_id": 9,
        "tz_string": "America/Los_Angeles",
        "start": "2015-09-14T00:00:00",
        "stop": "2015-09-21T00:00:00",
        "day_week_starts": "monday",
        "min_minutes_per_workday": 60 * 5,
        "max_minutes_per_workday": 60 * 8,
        "min_minutes_between_shifts": 60 * 14,
        "max_consecutive_workdays": 6,
    }

    env = Environment(**env_data)

    # Employee default
    e_default = {
        "user_id": 1,
        "min_hours_per_workweek": 20,
        "max_hours_per_workweek": 29.5,
        "preceding_day_worked": True,
        "preceding_days_worked_streak": 3,
        "existing_shifts": [],  # TODO - should probably add one fixed
        "time_off_requests": [],
        "preferences": {
            "monday": [0] * 24,
            "tuesday": [1] * 24,
            "wednesday": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
                          1, 0, 0],
            "thursday": [0] * 24,
            "friday": [1] * 24,
            "saturday": [1] * 24,
            "sunday": [0] * 24,
        },
        "working_hours": {
            "monday": [1] * 24,
            "tuesday": [1] * 24,
            "wednesday": [1] * 24,
            "thursday": [1] * 24,
            "friday": [1] * 24,
            "saturday": [1] * 24,
            "sunday": [1] * 24,
        },
        "environment": env,
    }

    employees = []

    cameron = deepcopy(e_default)
    cameron["user_id"] = 2
    cameron["preferences"]["thursday"] = [1] * 24
    cameron["preceding_days_worked_streak"] = 5
    employees.append(Employee(**cameron))

    cha = deepcopy(e_default)
    cha["user_id"] = 3
    employees.append(Employee(**cha))

    julian = deepcopy(e_default)
    julian["user_id"] = 4
    julian["min_hours_per_workweek"] = 30
    julian["max_hours_per_workweek"] = 40
    julian["preferences"]["monday"] = julian["preferences"]["wednesday"]
    julian["working_hours"]["sunday"] = julian["preferences"]["wednesday"]
    employees.append(Employee(**julian))

    # Test one person who can't work all hours
    violates_min_hours = deepcopy(e_default)
    violates_min_hours["user_id"] = 188
    violates_min_hours["min_hours_per_workweek"] = 30
    violates_min_hours["max_hours_per_workweek"] = 40
    # We set no availability so it triggers a min hours violation
    for day in week_day_range():
        violates_min_hours["working_hours"][day] = [0] * 24
    employees.append(Employee(**violates_min_hours))

    # and just auto generate 10 more
    for user_id in range(5, 13):
        e = deepcopy(e_default)
        e["user_id"] = user_id
        employees.append(Employee(**e))

    # Start/stop tuples
    start_stops = [
        ("2015-09-14T08:00:00", "2015-09-14T13:00:00"),
        ("2015-09-14T08:00:00", "2015-09-14T12:00:00"),
        ("2015-09-14T08:00:00", "2015-09-14T11:00:00"),
        ("2015-09-14T08:00:00", "2015-09-14T14:00:00"),
        ("2015-09-14T08:00:00", "2015-09-14T13:00:00"),
        ("2015-09-14T11:00:00", "2015-09-14T15:00:00"),
        ("2015-09-14T12:00:00", "2015-09-14T17:00:00"),
        ("2015-09-14T13:00:00", "2015-09-14T21:00:00"),
        ("2015-09-14T13:00:00", "2015-09-14T21:00:00"),
        ("2015-09-14T14:00:00", "2015-09-14T21:00:00"),
        ("2015-09-14T15:00:00", "2015-09-14T21:00:00"),
        ("2015-09-14T17:00:00", "2015-09-14T21:00:00"),
        ("2015-09-15T08:00:00", "2015-09-15T14:00:00"),
        ("2015-09-15T08:00:00", "2015-09-15T12:00:00"),
        ("2015-09-15T08:00:00", "2015-09-15T13:00:00"),
        ("2015-09-15T08:00:00", "2015-09-15T11:00:00"),
        ("2015-09-15T08:00:00", "2015-09-15T16:00:00"),
        ("2015-09-15T11:00:00", "2015-09-15T16:00:00"),
        ("2015-09-15T12:00:00", "2015-09-15T17:00:00"),
        ("2015-09-15T13:00:00", "2015-09-15T21:00:00"),
        ("2015-09-15T14:00:00", "2015-09-15T21:00:00"),
        ("2015-09-15T16:00:00", "2015-09-15T21:00:00"),
        ("2015-09-15T16:00:00", "2015-09-15T21:00:00"),
        ("2015-09-15T17:00:00", "2015-09-15T21:00:00"),
        ("2015-09-16T08:00:00", "2015-09-16T14:00:00"),
        ("2015-09-16T08:00:00", "2015-09-16T13:00:00"),
        ("2015-09-16T08:00:00", "2015-09-16T13:00:00"),
        ("2015-09-16T08:00:00", "2015-09-16T12:00:00"),
        ("2015-09-16T08:00:00", "2015-09-16T14:00:00"),
        ("2015-09-16T12:00:00", "2015-09-16T16:00:00"),
        ("2015-09-16T13:00:00", "2015-09-16T21:00:00"),
        ("2015-09-16T13:00:00", "2015-09-16T17:00:00"),
        ("2015-09-16T14:00:00", "2015-09-16T21:00:00"),
        ("2015-09-16T14:00:00", "2015-09-16T21:00:00"),
        ("2015-09-16T16:00:00", "2015-09-16T21:00:00"),
        ("2015-09-16T17:00:00", "2015-09-16T21:00:00"),
        ("2015-09-17T08:00:00", "2015-09-17T12:00:00"),
        ("2015-09-17T08:00:00", "2015-09-17T13:00:00"),
        ("2015-09-17T08:00:00", "2015-09-17T15:00:00"),
        ("2015-09-17T08:00:00", "2015-09-17T12:00:00"),
        ("2015-09-17T08:00:00", "2015-09-17T15:00:00"),
        ("2015-09-17T11:00:00", "2015-09-17T16:00:00"),
        ("2015-09-17T12:00:00", "2015-09-17T16:00:00"),
        ("2015-09-17T12:00:00", "2015-09-17T17:00:00"),
        ("2015-09-17T15:00:00", "2015-09-17T19:00:00"),
        ("2015-09-17T15:00:00", "2015-09-17T21:00:00"),
        ("2015-09-17T16:00:00", "2015-09-17T21:00:00"),
        ("2015-09-17T16:00:00", "2015-09-17T21:00:00"),
        ("2015-09-17T17:00:00", "2015-09-17T21:00:00"),
        ("2015-09-17T17:00:00", "2015-09-17T21:00:00"),
        ("2015-09-18T08:00:00", "2015-09-18T11:00:00"),
        ("2015-09-18T08:00:00", "2015-09-18T13:00:00"),
        ("2015-09-18T08:00:00", "2015-09-18T13:00:00"),
        ("2015-09-18T08:00:00", "2015-09-18T12:00:00"),
        ("2015-09-18T08:00:00", "2015-09-18T14:00:00"),
        ("2015-09-18T11:00:00", "2015-09-18T16:00:00"),
        ("2015-09-18T12:00:00", "2015-09-18T17:00:00"),
        ("2015-09-18T13:00:00", "2015-09-18T17:00:00"),
        ("2015-09-18T13:00:00", "2015-09-18T21:00:00"),
        ("2015-09-18T14:00:00", "2015-09-18T21:00:00"),
        ("2015-09-18T16:00:00", "2015-09-18T21:00:00"),
        ("2015-09-18T17:00:00", "2015-09-18T21:00:00"),
        ("2015-09-18T17:00:00", "2015-09-18T21:00:00"),
        ("2015-09-19T08:00:00", "2015-09-19T14:00:00"),
        ("2015-09-19T08:00:00", "2015-09-19T12:00:00"),
        ("2015-09-19T08:00:00", "2015-09-19T13:00:00"),
        ("2015-09-19T09:00:00", "2015-09-19T19:00:00"),
        ("2015-09-19T10:00:00", "2015-09-19T16:00:00"),
        ("2015-09-19T12:00:00", "2015-09-19T17:00:00"),
        ("2015-09-19T13:00:00", "2015-09-19T21:00:00"),
        ("2015-09-19T14:00:00", "2015-09-19T21:00:00"),
        ("2015-09-19T16:00:00", "2015-09-19T21:00:00"),
        ("2015-09-19T17:00:00", "2015-09-19T21:00:00"),
        ("2015-09-20T08:00:00", "2015-09-20T13:00:00"),
        ("2015-09-20T08:00:00", "2015-09-20T14:00:00"),
        ("2015-09-20T08:00:00", "2015-09-20T12:00:00"),
        ("2015-09-20T09:00:00", "2015-09-20T14:00:00"),
        ("2015-09-20T10:00:00", "2015-09-20T21:00:00"),
        ("2015-09-20T12:00:00", "2015-09-20T17:00:00"),
        ("2015-09-20T13:00:00", "2015-09-20T19:00:00"),
        ("2015-09-20T14:00:00", "2015-09-20T21:00:00"),
        ("2015-09-20T14:00:00", "2015-09-20T21:00:00"),
        ("2015-09-20T17:00:00", "2015-09-20T21:00:00"),
    ]

    shifts = []
    shift_id = 0
    for (start, stop) in start_stops:
        shift_id += 1
        s = {"id": shift_id, "user_id": 0, "start": start, "stop": stop, }

        shifts.append(Shift(s))

    a = Assign(env, employees, shifts)
    a.calculate()
