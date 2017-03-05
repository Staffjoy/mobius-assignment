from time import sleep
import traceback
import os

import pytz
import iso8601
from staffjoy import Client, NotFoundException

from mobius import config, logger
from mobius.employee import Employee
from mobius.environment import Environment
from mobius.assign import Assign
from mobius.constants import MINUTES_PER_HOUR, UNASSIGNED_USER_ID
from mobius.helpers import week_sum, dt_to_query_str
from mobius.shift import Shift


class Tasking():
    """Get tasks and process them"""

    REQUEUE_STATE = "mobius-queue"

    def __init__(self):
        self.client = Client(key=config.STAFFJOY_API_KEY, env=config.ENV)
        self.default_tz = pytz.timezone(config.DEFAULT_TZ)

    def server(self):
        previous_request_failed = False  # Have some built-in retries

        while True:
            # Get task
            try:
                task = self.client.claim_mobius_task()
                logger.info("Task received: %s" % task.data)
                previous_request_failed = False
            except NotFoundException:
                logger.debug("No task found. Sleeping.")
                previous_request_failed = False
                sleep(config.TASKING_FETCH_INTERVAL_SECONDS)
                continue
            except Exception as e:
                if not previous_request_failed:
                    # retry, but info log it
                    logger.info("Unable to fetch mobius task - retrying")
                    previous_request_failed = True
                else:
                    logger.error(
                        "Unable to fetch mobius task after previous failure: %s"
                        % e)

                # Still sleep so we avoid thundering herd
                sleep(config.TASKING_FETCH_INTERVAL_SECONDS)
                continue

            try:
                self._process_task(task)
                task.delete()
                logger.info("Task completed %s" % task.data)
            except Exception as e:
                logger.error("Failed schedule %s:  %s %s" %
                             (task.data.get("schedule_id"), e,
                              traceback.format_exc()))

                logger.info("Requeuing schedule %s" %
                            task.data.get("schedule_id"))

                # self.sched set in process_task
                self.sched.patch(state=self.REQUEUE_STATE)

                # Sometimes rebooting Mobius helps with errors. For example, if
                # a Gurobi connection is drained then it helps to reboot.
                if config.KILL_ON_ERROR:
                    sleep(config.KILL_DELAY)
                    logger.info("Rebooting to kill container")
                    os.system("shutdown -r now")

    def _process_task(self, task):

        # 1. Fetch schedule
        self.org = self.client.get_organization(task.data.get(
            "organization_id"))
        self.loc = self.org.get_location(task.data.get("location_id"))
        self.role = self.loc.get_role(task.data.get("role_id"))
        self.sched = self.role.get_schedule(task.data.get("schedule_id"))

        env = Environment(
            organization_id=task.data.get("organization_id"),
            location_id=task.data.get("location_id"),
            role_id=task.data.get("role_id"),
            schedule_id=task.data.get("schedule_id"),
            tz_string=self.loc.data.get("timezone"),
            start=self.sched.data.get("start"),
            stop=self.sched.data.get("stop"),
            day_week_starts=self.org.data.get("day_week_starts"),
            min_minutes_per_workday=self.role.data.get("min_hours_per_workday")
            * MINUTES_PER_HOUR,
            max_minutes_per_workday=self.role.data.get("max_hours_per_workday")
            * MINUTES_PER_HOUR,
            min_minutes_between_shifts=self.role.data.get(
                "min_hours_between_shifts") * MINUTES_PER_HOUR,
            max_consecutive_workdays=self.role.data.get(
                "max_consecutive_workdays"))

        user_objs = self.role.get_workers(archived=False)
        employees = []
        for e in user_objs:
            new_e = Employee(
                user_id=e.data["id"],
                min_hours_per_workweek=e.data["min_hours_per_workweek"],
                max_hours_per_workweek=e.data["max_hours_per_workweek"],
                environment=env, )

            # check whether employee even has availability to work
            if week_sum(new_e.availability) > new_e.min_hours_per_workweek:
                employees.append(new_e)

        if len(employees) is 0:
            logger.info("No employees")
            return

        # Get the shifts
        shift_api_objs = self.role.get_shifts(start=dt_to_query_str(env.start),
                                              end=dt_to_query_str(env.stop),
                                              user_id=UNASSIGNED_USER_ID)

        # Convert api objs to something more manageable
        shifts = []
        for s in shift_api_objs:
            shifts.append(Shift(s))

        if len(shifts) is 0:
            logger.info("No unassigned shifts")
            return

        # Run the  calculation
        a = Assign(env, employees, shifts)
        a.calculate()
        a.set_shift_user_ids()

    def _get_local_start_time(self):
        # Create the datetimes
        local_tz = pytz.timezone(self.loc.data.get("timezone"))
        utc_start_time = iso8601.parse_date(self.sched.data.get(
            "start")).replace(tzinfo=self.default_tz)
        local_start_time = utc_start_time.astimezone(local_tz)
        return local_start_time
