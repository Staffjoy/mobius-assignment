from datetime import timedelta
from copy import deepcopy
import os

import staffjoy

from mobius.helpers import dt_overlaps, week_day_range, dt_to_day
from mobius.constants import MINUTES_PER_HOUR
from mobius import logger, config

tune_file = os.path.dirname(os.path.realpath(
    __file__)) + "/../" + config.TUNE_FILE


class Assign():
    """Assigns workers to shifts"""

    # core math

    def __init__(self, environment, employees, shifts):
        self.environment = environment
        self.employees = employees
        self.shifts = shifts
        self.shifts.sort(key=lambda s: s.start)

        logger.info(
            "Initialized assignment problem of %s employees and %s shifts" %
            (len(self.employees), len(self.shifts)))

    def set_shift_user_ids(self):
        """Patch request the user ids in for all of the assigned shifts!"""
        c = staffjoy.Client(key=config.STAFFJOY_API_KEY, env=config.ENV)
        org = c.get_organization(self.environment.organization_id)
        loc = org.get_location(self.environment.location_id)
        role = loc.get_role(self.environment.role_id)

        for shift in self.shifts:
            if shift.user_id is 0:
                logger.info("Shift %s not assigned" % shift.shift_id)
            else:
                logger.info("Setting shift %s to user %s" %
                            (shift.shift_id, shift.user_id))
                shift_api = role.get_shift(shift.shift_id)
                shift_api.patch(user_id=shift.user_id)

    def calculate(self):
        success = False
        # Step 1: Try consecutive days off, happy
        try:
            logger.info("Trying consecutive days off with happiness")
            self._calculate(consecutive_days_off=True, happiness_scoring=True)
            success = True
        except Exception as e:
            success = False
            logger.info("Consecutive days off failed: %s" % e)

        if success:
            return

        # Step 2: Try no happy, yes consecutive days off
        try:
            logger.info("Trying consecutive days off without happiness")
            self._calculate(consecutive_days_off=True, happiness_scoring=False)
            success = True
        except Exception as e:
            success = False
            logger.info("Consecutive days off without happiness failed: %s" %
                        e)

        if success:
            return

        # Step 3: Try no happy, no consecutive days off
        # Don't catch error
        logger.info("Trying consecutive days off without happiness")
        self._calculate(consecutive_days_off=False, happiness_scoring=False)

    def _calculate(self,
                   consecutive_days_off=False,
                   return_unsolved_model_for_tuning=False,
                   happiness_scoring=False):
        """Run the calculation"""

        # Import Guorbi now so server connection doesn't go stale
        # (importing triggers a server connection)
        import gurobipy as grb
        GRB = grb.GRB  # For easier constant access

        m = grb.Model("mobius-%s-role-%s" %
                      (config.ENV, self.environment.role_id))
        m.setParam("OutputFlag", False)  # Don't print gurobi logs
        m.setParam("Threads", config.THREADS)

        # Add Timeout on happiness scoring.
        if happiness_scoring:
            m.setParam("TimeLimit", config.HAPPY_CALCULATION_TIMEOUT)

        # Try loading a tuning file if we're not tuning
        if not return_unsolved_model_for_tuning:
            try:
                m.read(tune_file)
                logger.info("Loaded tuned model")
            except:
                logger.info("No tune file found")

        # Create objective - which is basically happiness minus penalties
        obj = grb.LinExpr()

        # Whether worker is assigned to shift
        assignments = {}
        unassigned = {}
        for e in self.employees:
            logger.debug("Building shifts for user %s" % e.user_id)
            for s in self.shifts:
                assignments[e.user_id, s.shift_id] = m.addVar(
                    vtype=GRB.BINARY,
                    name="user-%s-assigned-shift-%s" % (e.user_id, s.shift_id))

                # Only add happiness if we're scoring happiness
                if happiness_scoring:
                    obj += assignments[e.user_id,
                                       s.shift_id] * e.shift_happiness_score(s)

                # Also add an unassigned shift - and penalize it!
                unassigned[s.shift_id] = m.addVar(vtype=GRB.BINARY,
                                                  name="unassigned-shift-%s" %
                                                  s.shift_id)
                obj += unassigned[s.shift_id] * config.UNASSIGNED_PENALTY

        # Helper variables
        min_week_hours_violation = {}
        week_minutes_sum = {}
        day_shifts_sum = {}
        day_active = {}
        for e in self.employees:
            min_week_hours_violation[e.user_id] = m.addVar(
                vtype=GRB.BINARY,
                name="user-%s-min-week-hours-violation" % (e.user_id))

            week_minutes_sum[e.user_id] = m.addVar(
                name="user-%s-hours-per-week" % e.user_id)

            for day in week_day_range():
                day_shifts_sum[e.user_id, day] = m.addVar(
                    vtype=GRB.INTEGER,
                    name="user-%s-day-%s-shift-sum" % (e.user_id, day))

                day_active[e.user_id, day] = m.addVar(
                    vtype=GRB.BINARY,
                    name="user-%s-day-%s-shift-sum" % (e.user_id, day))

            obj += min_week_hours_violation[
                e.user_id] * config.MIN_HOURS_VIOLATION_PENALTY

        m.update()

        for s in self.shifts:
            m.addConstr(
                grb.quicksum(assignments[e.user_id, s.shift_id]
                             for e in self.employees) + unassigned[s.shift_id],
                GRB.EQUAL, 1)

        # Allowed shift state transitions
        for test in self.shifts:
            # Use index because shifts are sorted!
            # Iterate through "other" (o) shifts
            for o in self.shifts:
                if o.shift_id == test.shift_id:
                    continue

                # Add min minutes between shifts for allowed overlaps
                if dt_overlaps(
                        o.start,
                        o.stop,
                        test.start,
                        test.stop + timedelta(minutes=self.environment.
                                              min_minutes_between_shifts)):

                    # Add constraint that shift transitions not allowed
                    for e in self.employees:
                        m.addConstr(assignments[e.user_id, test.shift_id] +
                                    assignments[e.user_id, o.shift_id],
                                    GRB.LESS_EQUAL, 1)

        # Add consecutive days off constraint
        # so that workers have a "weekend" - at least 2 consecutive
        # days off in a week where possible
        # 
        # The current  implementation has us run the model a second
        # time if this is infeasible, however we should revise it
        # to be a weighted variable.
        if consecutive_days_off:
            for e in self.employees:
                day_off_sum = grb.LinExpr()
                previous_day_name = None
                for day in week_day_range(self.environment.day_week_starts):
                    if not previous_day_name:
                        # It's the first loop
                        if not e.preceding_day_worked:
                            # if they didn't work the day before, then not
                            # working the first day is consec days off
                            day_off_sum += (1 - day_active[e.user_id, day])
                    else:
                        # We're in the loop not on first day
                        day_off_sum += (1 - day_active[e.user_id, day]) * (
                            1 - day_active[e.user_id, previous_day_name])

                    previous_day_name = day

                # We now have built the LinExpr. It needs to be >= 1
                # (for at least 1 set of consec days off)
                m.addConstr(day_off_sum, GRB.GREATER_EQUAL, 1)

        # Availability constraints
        for e in self.employees:
            for s in self.shifts:
                if not e.available_to_work(s):
                    logger.debug("User %s unavailable to work shift %s" %
                                 (e.user_id, s.shift_id))
                    m.addConstr(assignments[e.user_id, s.shift_id], GRB.EQUAL,
                                0)

        # Limit employee hours per workweek
        for e in self.employees:

            # The running total of shifts is equal to the helper variable
            m.addConstr(
                sum([s.total_minutes() * assignments[e.user_id, s.shift_id]
                     for s in self.shifts]), GRB.EQUAL,
                week_minutes_sum[e.user_id])

            # The total minutes an employee works in a week is less than or equal to their max
            m.addConstr(week_minutes_sum[e.user_id], GRB.LESS_EQUAL,
                        e.max_hours_per_workweek * MINUTES_PER_HOUR)

            # A worker must work at least their min hours per week. 
            # Violation causes a penalty.
            # NOTE - once the min is violated, we don't say "try to get as close as possible" - 
            # we stop unassigned shifts, but if you violate min then you're not guaranteed anything
            m.addConstr(week_minutes_sum[e.user_id], GRB.GREATER_EQUAL,
                        e.min_hours_per_workweek * MINUTES_PER_HOUR *
                        (1 - min_week_hours_violation[e.user_id]))

            for day in week_day_range():
                m.addSOS(GRB.SOS_TYPE1, [day_shifts_sum[e.user_id, day],
                                         day_active[e.user_id, day]])
                m.addConstr(day_shifts_sum[e.user_id, day], GRB.EQUAL,
                            grb.quicksum([assignments[e.user_id, s.shift_id]
                                          for s in self.shifts
                                          if ((dt_to_day(s.start) == day) or (
                                              dt_to_day(s.stop) == day and
                                              s.stop <= self.environment.stop))
                                          ]))

                m.addConstr(day_shifts_sum[e.user_id, day] +
                            day_active[e.user_id, day], GRB.GREATER_EQUAL, 1)

        # Limit employee hours per workday
        workday_start = deepcopy(self.environment.start)
        while workday_start < self.environment.stop:
            for e in self.employees:
                # Look for minutes of overlap
                workday_stop = workday_start + timedelta(days=1)
                m.addConstr(
                    sum([s.minutes_overlap(start=workday_start,
                                           stop=workday_stop) * assignments[
                                               e.user_id, s.shift_id]
                         for s in self.shifts
                         if dt_overlaps(s.start, s.stop, workday_start,
                                        workday_stop)]),
                    GRB.LESS_EQUAL,
                    self.environment.max_minutes_per_workday)

            workday_start += timedelta(days=1)

        m.update()
        m.setObjective(obj)
        m.modelSense = GRB.MAXIMIZE  # Make something people love!

        if return_unsolved_model_for_tuning:
            return m

        m.optimize()
        if m.status != GRB.status.OPTIMAL:
            logger.info("Calculation failed - gurobi status code %s" %
                        m.status)
            raise Exception("Calculation failed")

        logger.info("Optimized! objective: %s" % m.objVal)

        for e in self.employees:
            if min_week_hours_violation[e.user_id].x > .5:
                logger.info(
                    "User %s unable to meet min hours for week (hours: %s, min: %s)"
                    % (e.user_id, 1.0 * week_minutes_sum[e.user_id].x /
                       MINUTES_PER_HOUR, e.min_hours_per_workweek))

            for s in self.shifts:
                if assignments[e.user_id, s.shift_id].x > .5:
                    logger.info("User %s assigned shift %s" %
                                (e.user_id, s.shift_id))
                    s.user_id = e.user_id

        logger.info("%s shifts of %s still unsassigned" %
                    (len([s for s in self.shifts if s.user_id == 0]),
                     len(self.shifts)))
