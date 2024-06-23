import random
import numpy as np

class DiagnosisHelper:
    def __init__(self):
        self.diagnosis_type_A = ['A1', 'A2', 'A3', 'A4']
        self.probabilities_A = [1 / 2, 1 / 4, 1 / 8, 1 / 8]

        self.diagnosis_type_B = ['B1', 'B2', 'B3', 'B4']
        self.probabilities_B = [1 / 2, 1 / 4, 1 / 8, 1 / 8]

        self.operation_params = {
            'A2': (1, 1 / 4),
            'A3': (2, 1 / 2),
            'A4': (4, 1 / 2),
            'B3': (4, 1 / 2),
            'B4': (4, 1)
        }
        self.nursing_params = {
            'A1': (4, 1 / 2),
            'A2': (8, 2),
            'A3': (16, 2),
            'A4': (16, 2),
            'B1': (8, 2),
            'B2': (16, 2),
            'B3': (16, 4),
            'B4': (16, 4)
        }
        self.complication_probs = {
            'A1': 0.01,
            'A2': 0.01,
            'A3': 0.02,
            'A4': 0.02,
            'B1': 0.001,
            'B2': 0.01,
            'B3': 0.02,
            'B4': 0.02
        }

    def assign_diagnosis(self, type):
        """
        Assign patient with diagnosis type according to probabilities
        """
        if type == 'A':
            return random.choices(self.diagnosis_type_A, self.probabilities_A, k=1)[0]
        elif type == 'B':
            return random.choices(self.diagnosis_type_B, self.probabilities_B, k=1)[0]
        elif type == 'ER':
            if random.choice([True, False]):
                return random.choices(self.diagnosis_type_A, self.probabilities_A, k=1)[0]
            else:
                return random.choices(self.diagnosis_type_B, self.probabilities_B, k=1)[0]
        else:
            return None

    def requires_surgery(self, diagnosis):
        """
        Check if patient with certain diagnosis need surgery
        """
        non_surgery_diagnoses = {'A1', 'B1', 'B2'}
        return 'false' if diagnosis in non_surgery_diagnoses else 'true'

    def calculate_duration(self, params):
        """
        Choose value from normal distribution
        """
        mean, stddev = params
        return max(0, np.random.normal(loc=mean, scale=stddev))

    def diagnosis_operation_time(self, diagnosis):
        """
        Get the duration for surgery according to diagnosis type
        """
        params = self.operation_params.get(diagnosis)
        return self.calculate_duration(params) if params else None

    def diagnosis_nursing_time(self, diagnosis):
        """
        Get the duration for nursing according to diagnosis type
        """
        params = self.nursing_params.get(diagnosis)
        return self.calculate_duration(params) if params else None

    def no_complication(self, diagnosis):
        """
        Check if the patient with certain diagnosis type could be released (no complication)
        """
        complication_prob = self.complication_probs.get(diagnosis, 0)
        has_complication = random.random() < complication_prob
        if has_complication:
            return 'false'
        else:
            return 'true'

