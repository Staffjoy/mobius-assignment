import os
import json
from copy import deepcopy

from mobius.assign import Assign
from mobius.employee import Employee
from mobius.shift import Shift
from mobius.environment import Environment
from mobius import config, logger


def tune():
    """Take a canonical decomposition model, then tune it using Gurobi"""

    logger.info("Beginning tuning")

    # Creating some employees

    # This must be feasible
    env_attributes = {
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
    env = Environment(**env_attributes)

    employee_attributes = {
        "user_id": 27182818,
        "min_hours_per_workweek": 16,
        "max_hours_per_workweek": 24,
        "preceding_day_worked": False,
        "preceding_days_worked_streak": 4,
        "existing_shifts": [],
        "time_off_requests": [],  # TODO
        "preferences": {
            "monday": [0] * 24,
            "tuesday": [1] * 24,
            "wednesday": [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                          1, 1, 1, 1, 0, 0],
            "thursday": [0] * 24,
            "friday": [1] * 24,
            "saturday": [1] * 24,
            "sunday": [0] * 24,
        },
        "working_hours": {
            "monday": [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                       1, 1, 1, 0, 0],
            "tuesday": [1] * 24,
            "wednesday": [1] * 24,
            "thursday": [0] * 24,
            "friday": [1] * 24,
            "saturday": [1] * 24,
            "sunday": [1] * 24,
        },
        "environment": env,
    }

    employees = []

    e0 = deepcopy(employee_attributes)
    e0["user_id"] = 0
    e0["preferences"]["friday"] = [1] * 24
    employees.append(Employee(**e0))

    e1 = deepcopy(employee_attributes)
    e1["user_id"] = 1
    e1["working_hours"]["tuesday"] = [0] * 24
    e1["preferences"]["monday"] = [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1,
                                   0, 1, 1, 1, 1, 1, 1, 0, 0]
    employees.append(Employee(**e1))

    e2 = deepcopy(employee_attributes)
    e2["user_id"] = 2
    e2["working_hours"]["monday"] = [0] * 24
    e2["preferences"]["friday"] = [1] * 24
    employees.append(Employee(**e2))

    e3 = deepcopy(employee_attributes)
    e3["user_id"] = 3
    employees.append(Employee(**e3))

    e4 = deepcopy(employee_attributes)
    e4["user_id"] = 4
    employees.append(Employee(**e4))

    e5 = deepcopy(employee_attributes)
    e5["user_id"] = 5
    e5["working_hours"]["wednesday"] = [0] * 24
    employees.append(Employee(**e5))

    e6 = deepcopy(employee_attributes)
    e6["user_id"] = 6
    e6["working_hours"]["tuesday"] = [0] * 24
    e6["working_hours"]["monday"] = [0] * 24
    e6["preferences"]["wednesday"] = [0] * 24
    employees.append(Employee(**e6))

    e7 = deepcopy(employee_attributes)
    e7["user_id"] = 7
    e7["working_hours"]["tuesday"] = [0] * 24
    e7["working_hours"]["monday"] = [0] * 24
    e7["preferences"]["wednesday"] = [0] * 24
    employees.append(Employee(**e7))

    e8 = deepcopy(employee_attributes)
    e8["user_id"] = 8
    e8["working_hours"]["tuesday"] = [0] * 24
    e8["working_hours"]["monday"] = [0] * 24
    e8["preferences"]["monday"] = [0] * 24
    e8["preferences"]["tuesday"] = [0] * 24
    e8["preferences"]["wednesday"] = [0] * 24
    employees.append(Employee(**e8))

    e9 = deepcopy(employee_attributes)
    e9["user_id"] = 9
    e9["working_hours"]["tuesday"] = [1] * 24
    e9["working_hours"]["monday"] = [1] * 24
    e9["preferences"]["monday"] = [1] * 24
    e9["preferences"]["tuesday"] = [1] * 24
    e9["preferences"]["wednesday"] = [1] * 24
    employees.append(Employee(**e9))

    e10 = deepcopy(employee_attributes)
    e10["user_id"] = 10
    e10["working_hours"]["tuesday"] = [1] * 24
    e10["working_hours"]["monday"] = [1] * 24
    e10["preferences"]["monday"] = [1] * 24
    e10["preferences"]["tuesday"] = [1] * 24
    e10["preferences"]["wednesday"] = [1] * 24
    employees.append(Employee(**e10))

    e11 = deepcopy(employee_attributes)
    e11["user_id"] = 11
    e11["preferences"]["wednesday"] = [1] * 24
    employees.append(Employee(**e11))

    with open(os.path.dirname(os.path.realpath(__file__)) +
              "/tune_data/shifts.json") as json_data:
        print json_data
        shifts_raw = json.load(json_data)
        json_data.close()

    shifts = []
    for s in shifts_raw:
        shifts.append(Shift(s))

    a = Assign(env, employees, shifts)

    model = a._calculate(return_unsolved_model_for_tuning=True)

    # We're only tuning one model right now
    model.params.tuneResults = 1
    model.params.tuneTimeLimit = config.MAX_TUNING_TIME

    # For tuning - turn this back on for fun
    model.setParam("OutputFlag", True)

    # Tune the model
    model.tune()

    if model.tuneResultCount > 0:
        logger.info("Tuning completed")

        # Load the best tuned parameters into the model
        model.getTuneResult(0)

        # Write tuned parameters to a file
        model.write(config.TUNE_FILE)
        logger.info("Wrote tuning to file %s" % config.TUNE_FILE)

        # Solve the model using the tuned parameters
        model.optimize()
    else:
        logger.warning("No tuning completed")
