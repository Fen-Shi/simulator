import datetime
from constraint import Problem
import diagnosis_helper as dh
from numpy import random

operating_capacity = 5
surgery_duration = 2  # Assuming each surgery takes 2 hours
INTAKE_RESOURCES = 4
MAX_PENDING_PATIENTS = 2
nursing_a_capacity = 30
nursing_b_capacity = 40


diagnosis_helper = dh.DiagnosisHelper()

def get_working_hours(start_time, days=7):
    start_time = datetime.datetime.fromisoformat(start_time)
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

def planner(cid, time, info, resources):
    problem = Problem()
    current_time = time
    working_hours = get_working_hours(current_time)
    diagnosis = info.get('diagnosis', '')

    require_surgery = diagnosis_helper.requires_surgery(diagnosis=diagnosis)

    # Add variable and its domain
    problem.addVariable('reschedule_time', working_hours)

    # Constraint for intake resources
    def intake_resource_constraint(time):
        ongoing_intake = [state for state in resources if state['task'] == 'intake' and state['start'] <= time]
        ongoing_count = sum(1 for state in ongoing_intake if datetime.datetime.fromisoformat(state['start']) <= time < calculate_end_time(datetime.datetime.fromisoformat(state['start']), max(0, random.normal(loc=1, scale=1 / 8))))
        return ongoing_count < INTAKE_RESOURCES

    problem.addConstraint(intake_resource_constraint, ['reschedule_time'])


    def surgery_capacity_constraint(time):
        surgery_pending_patients = sorted([state for state in resources if 
                                   state['task'] == 'surgery' and state['wait']], 
                                  key=lambda x: x['start'])
        
        pending_count = len(surgery_pending_patients)
        if pending_count >=2:
            ongoing_surgeries = [state for state in resources if state['task'] == 'surgery' and not state['wait']]
            ongoing_count = sum(1 for state in ongoing_surgeries if
                                datetime.datetime.fromisoformat(state['start']) <= time < calculate_end_time(datetime.datetime.fromisoformat(state['start']), diagnosis_helper.diagnosis_operation_time(diagnosis=state['info']['diagnosis'])))
            if ongoing_count < operating_capacity:
                pending_count-=1

        return pending_count
        # if pending_count <2:
        #     return True
        
    # problem.addConstraint(surgery_capacity_constraint, ['reschedule_time'])
            


    # Constraint for nursing capacity
    def nursing_a_capacity_constraint(time):
        nursing_a_pending_patients = sorted([state for state in resources if 
                                            state['task'] == 'nursing' and state['wait'] and 
                                            state['info']['diagnosis'] in ['A1']], 
                                            key=lambda x: x['start'])

        
        pending_a_count = len(nursing_a_pending_patients)
        if pending_a_count > 2:
            ongoing_a_nursing = [state for state in resources if state['task'] == 'nursing' and not state['wait'] and 
                                            state['info']['diagnosis'] in ['A1', 'A2', 'A3', 'A4']]
            ongoing_a_count = sum(1 for state in ongoing_a_nursing if
                                datetime.datetime.fromisoformat(state['start']) <= time < calculate_end_time(datetime.datetime.fromisoformat(state['start']), diagnosis_helper.diagnosis_nursing_time(diagnosis=state['info']['diagnosis'])))
            if ongoing_a_count < nursing_a_capacity:
                pending_a_count -= 1
        
        return pending_a_count
        # if pending_a_count <=2:
        #     return True
        
    # problem.addConstraint(nursing_a_capacity_constraint, ['reschedule_time'])


    def nursing_b_capacity_constraint(time):
        nursing_b_pending_patients = sorted([state for state in resources if 
                                        state['task'] == 'nursing' and state['wait'] and 
                                        state['info']['diagnosis'] in ['B1', 'B2']], 
                                        key=lambda x: x['start'])
        pending_b_count =  len(nursing_b_pending_patients)
        if pending_b_count > 2:
            ongoing_b_nursing = [state for state in resources if state['task'] == 'nursing' and not state['wait'] and 
                                            state['info']['diagnosis'] in ['B1', 'B2', 'B3', 'B4']]
            ongoing_b_count = sum(1 for state in ongoing_b_nursing if
                                datetime.datetime.fromisoformat(state['start']) <= time < calculate_end_time(datetime.datetime.fromisoformat(state['start']), diagnosis_helper.diagnosis_nursing_time(diagnosis=state['info']['diagnosis'])))
            if ongoing_b_count < nursing_b_capacity:
                pending_b_count -= 1   

        return pending_b_count
        # if pending_b_count <= 2:
        #     return True
    
    # problem.addConstraint(nursing_b_capacity_constraint, ['reschedule_time'])

    def pending_constraint(time):
        pending_surgery_count = surgery_capacity_constraint(time)
        pending_nursing_a_count = nursing_a_capacity_constraint(time)
        pending_nursing_b_count = nursing_b_capacity_constraint(time)
        return pending_surgery_count + pending_nursing_a_count + pending_nursing_b_count <= 2

    problem.addConstraint(pending_constraint, ['reschedule_time'])



    # Solve the problem
    solutions = problem.getSolutions()

    # Sort solutions by the reschedule_time
    solutions = sorted(solutions, key=lambda x: x['reschedule_time'])

    # Choose the earliest solution if available
    if solutions:
        rescheduled_time = solutions[0]['reschedule_time']
        return {
            'cid': cid,
            'reschedule_time': rescheduled_time.isoformat(),
            'info': info
        }
    else:
        return None


resources = [
    {'cid': '1', 'task': 'nursing', 'start': "2018-01-01T10:00:00", 'info': {'diagnosis': 'A1'}, 'wait': False},
    {'cid': '2', 'task': 'nursing', 'start': "2018-01-01T10:00:00", 'info': {'diagnosis': 'A1'}, 'wait': False},
    {'cid': '3', 'task': 'nursing', 'start': "2018-01-01T10:00:00", 'info': {'diagnosis': 'A1'}, 'wait': False},
    {'cid': '4', 'task': 'nursing', 'start': "2018-01-01T10:00:00", 'info': {'diagnosis': 'A1'}, 'wait': False},
    {'cid': '5', 'task': 'nursing', 'start': "2018-01-01T10:00:00", 'info': {'diagnosis': 'A1'}, 'wait': False},
    {'cid': '6', 'task': 'nursing', 'start': "2018-01-01T10:00:00", 'info': {'diagnosis': 'A1'}, 'wait': True},
    {'cid': '7', 'task': 'nursing', 'start': "2018-01-01T10:00:00", 'info': {'diagnosis': 'A1'}, 'wait': True},
    {'cid': '8', 'task': 'nursing', 'start': "2018-01-01T10:00:00", 'info': {'diagnosis': 'A1'}, 'wait': True},


    # Intake tasks
    # {'cid': '5', 'task': 'intake', 'start': datetime.datetime(2018, 1, 1, 10, 0), 'info': {'diagnosis': 'B1'}, 'wait': False},
    # {'cid': '6', 'task': 'intake', 'start': datetime.datetime(2018, 1, 1, 10, 0), 'info': {'diagnosis': 'B2'}, 'wait': False},
    # {'cid': '7', 'task': 'intake', 'start': datetime.datetime(2018, 1, 1, 10, 0), 'info': {'diagnosis': 'A1'}, 'wait': False},
    # {'cid': '8', 'task': 'intake', 'start': datetime.datetime(2018, 1, 1, 10, 0), 'info': {'diagnosis': 'B4'}, 'wait': False},
]

# Example usage
current_time = datetime.datetime(2018, 1, 1, 10, 0).isoformat()  # Example current time
result = planner('6', current_time, {'diagnosis': 'A2'}, resources)
print(result)
