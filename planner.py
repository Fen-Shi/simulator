from constraint import Problem, AllDifferentConstraint
import datetime


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


def planner(patient_id, current_time, diagnosis, system_state):
    problem = Problem()
    working_hours = get_working_hours(current_time)

    # Add variables and their domains
    problem.addVariable('reschedule_time', working_hours)

    # directly go to surgery, 要反向实现，现在无意义
    def immediate_appointment_constraint(time):
        if time != current_time:
            return True

        surgery_count = sum(1 for state in system_state if state['task'] == 'surgery' and not state['wait'])
        if surgery_count <= 5 and diagnosis in ['A2', 'A3', 'A4', 'B3', 'B4']:
            return True
        return False

    problem.addConstraint(immediate_appointment_constraint, ['reschedule_time'])

    # directly go to nursing, 要反向实现，现在无意义
    def nursing_constraint(time):
        if time != current_time:
            return True

        nursing_wait_count = sum(1 for state in system_state if state['task'] == 'nursing' and state['wait'])
        if diagnosis in ["A1", "B1", "B2"] and nursing_wait_count == 0:
            return True
        return False

    problem.addConstraint(nursing_constraint, ['reschedule_time'])

    # Solve the problem
    solutions = problem.getSolutions()

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


# Example usage
current_time = datetime.datetime(2018, 1, 1, 10, 0)  # Example current time
system_state = [
    {'patient_id': '1', 'task': 'surgery', 'start': current_time, 'wait': False},
    {'patient_id': '2', 'task': 'nursing', 'start': current_time - datetime.timedelta(hours=1), 'wait': False}
]

result = planner('3', current_time, 'A1', system_state)
print(result)
print(get_working_hours(current_time))
