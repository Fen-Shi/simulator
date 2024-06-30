import datetime
from constraint import Problem

operating_capacity = 5
surgery_duration = 2  # Assuming each surgery takes 2 hours


def get_working_hours(start_time, days=7):
    working_hours = []
    end_time = start_time + datetime.timedelta(days=days)
    current_day = start_time.date()

    while current_day < end_time.date():
        for hour in range(8, 17):  # Working hours from 8 AM to 5 PM
            working_time = datetime.datetime.combine(current_day, datetime.time(hour))
            if start_time <= working_time < end_time and working_time.weekday() < 5:  # Within the next 7 days and Monday to Friday
                working_hours.append(working_time)
        current_day += datetime.timedelta(days=1)
    return working_hours


def calculate_end_time(start, duration):
    return start + datetime.timedelta(hours=duration)


def planner(patient_id, current_time, diagnosis, system_state):
    problem = Problem()
    working_hours = get_working_hours(current_time)

    # Add variable and its domain
    problem.addVariable('reschedule_time', working_hours)

    # Constraint for surgery capacity
    def surgery_capacity_constraint(time):
        last_waiting_end_time = max((state['start'] for state in system_state if state['wait']), default=time)
        if time < last_waiting_end_time:
            return False

        ongoing_surgeries = [state for state in system_state if state['task'] == 'surgery' and state['start'] <= time]
        # ongoing in the rescheduled time?
        ongoing_count = sum(1 for state in ongoing_surgeries if
                            state['start'] <= time < calculate_end_time(state['start'], surgery_duration))
        return ongoing_count < operating_capacity

    problem.addConstraint(surgery_capacity_constraint, ['reschedule_time'])




    # Solve the problem
    solutions = problem.getSolutions()

    # Sort solutions by the reschedule_time
    solutions = sorted(solutions, key=lambda x: x['reschedule_time'])

    # Choose the earliest solution if available
    if solutions:
        rescheduled_time = solutions[0]['reschedule_time']
        return {
            'patient_id': patient_id,
            'reschedule_time': rescheduled_time,
            'diagnosis': diagnosis
        }
    else:
        return None


def get_system_state():
    return [
        {'patient_id': '1', 'task': 'surgery', 'start': datetime.datetime(2018, 1, 1, 10, 0), 'wait': False},
        {'patient_id': '2', 'task': 'surgery', 'start': datetime.datetime(2018, 1, 1, 10, 0), 'wait': False},
        {'patient_id': '3', 'task': 'surgery', 'start': datetime.datetime(2018, 1, 1, 9, 30), 'wait': False},
        {'patient_id': '4', 'task': 'surgery', 'start': datetime.datetime(2018, 1, 1, 9, 30), 'wait': False},
        {'patient_id': '5', 'task': 'surgery', 'start': datetime.datetime(2018, 1, 1, 8, 0), 'wait': False},
    ]


# Example usage
current_time = datetime.datetime(2018, 1, 1, 10, 0)  # Example current time
system_state = get_system_state()

result = planner('6', current_time, 'A2', system_state)
print(result)
print(get_working_hours(current_time))
