from ortools.sat.python import cp_model
import datetime
import random


class Planner:
    def __init__(self, start_date, end_date, working_hours, max_intake):
        self.start_date = start_date
        self.end_date = end_date
        self.working_hours = working_hours
        self.max_intake = max_intake
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.time_slots = self.generate_time_slots()

    def plan_appointments(self, patients, system_state):
        # Define the variables and constraints
        patient_vars = {
            patient['patient_id']: self.model.NewIntVar(0, len(self.time_slots) - 1, f'patient_{patient["patient_id"]}')
            for patient in patients}

        # Constraint: Each time slot cannot exceed max intake
        for slot in range(len(self.time_slots)):
            self.model.Add(sum(patient_vars[patient['patient_id']] == slot for patient in patients) <= self.max_intake)

        # Solve the problem
        status = self.solver.Solve(self.model)

        if status == cp_model.OPTIMAL:
            for patient in patients:
                scheduled_time = self.time_slots[self.solver.Value(patient_vars[patient['patient_id']])]
                print(f'Patient {patient["patient_id"]} scheduled at {scheduled_time}')
                system_state.append({
                    'patient_id': patient['patient_id'],
                    'task': 'Intake',
                    'start': scheduled_time,
                    'wait': False
                })
        else:
            print('No solution found.')

    def generate_time_slots(self):
        time_slots = []
        current_time = self.start_date
        while current_time < self.end_date:
            if self.working_hours[0] <= current_time.time() <= self.working_hours[1]:
                time_slots.append(current_time)
            current_time += datetime.timedelta(minutes=30)
        return time_slots


# Usage example
start_date = datetime.datetime(2018, 1, 1, 8, 0)
end_date = datetime.datetime(2018, 1, 5, 17, 0)
working_hours = (datetime.time(8, 0), datetime.time(17, 0))
max_intake = 4

planner = Planner(start_date, end_date, working_hours, max_intake)
patients = [
    {'patient_id': 'Patient1', 'current_time': start_date, 'diagnosis': 'A1'},
    {'patient_id': 'Patient2', 'current_time': start_date, 'diagnosis': 'B2'}
]
system_state = []
planner.plan_appointments(patients, system_state)
