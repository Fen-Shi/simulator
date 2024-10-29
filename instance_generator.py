#!/usr/bin/env python3
import datetime
import json
import random
import uuid
from queue import PriorityQueue
import requests
from diagnosis_helper import DiagnosisHelper


diagnosis_helper = DiagnosisHelper()

queue = PriorityQueue()


def create_patient_instance(patient_type, patient_id, diagnosis, current_time_str):
    """
    Create a new instance.
    """
    instance_response = requests.post("https://cpee.org/flow/start/url/",
                                      data={"behavior": "fork_running",
                                            "url": "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Fen_Shi.dir/main.xml",
                                            "init": json.dumps({
                                                "patientType": patient_type,
                                                "patientID": patient_id,
                                                "diagnosis": diagnosis,
                                                "arrival_time": current_time_str,

                                            })
                                            })

    return (
        f"Response content:, {instance_response.text}, Patient Type: {patient_type}, Patient ID: {patient_id}, diagnosis: {diagnosis}")


def simulate_planned_patients_a(current_time, end_time):
    """
    Generate instances of planned patients with diagnosis type A arriving within a specified time window.
    """
    count = 0
    while current_time < end_time:
        # Randomly assign a patient ID or leave it empty
        patient_id = random.choice(["", str(uuid.uuid4())])
        # Assign diagnosis type 'A'
        diagnosis = diagnosis_helper.assign_diagnosis('A')
        current_time, create_patient_instance('Planned', patient_id, diagnosis, current_time.isoformat())
        # Increment the time interval by a uniform random value between 0 and 1 hour
        time_delta = random.uniform(0, 1)
        current_time += datetime.timedelta(hours=time_delta)
        count += 1

    return count


def simulate_planned_patients_b(current_time, end_time):
    """
    Generate instances of planned patients with diagnosis type B arriving within a specified time window.
    """
    count = 0
    while current_time < end_time:
        patient_id = random.choice(["", str(uuid.uuid4())])
        # Assign diagnosis type 'B'
        diagnosis = diagnosis_helper.assign_diagnosis('B')
        # Create patient instance and update the current time
        current_time, create_patient_instance('Planned', patient_id, diagnosis, current_time.isoformat())
        time_delta = random.uniform(0, 1)
        current_time += datetime.timedelta(hours=time_delta)
        count += 1

    return count


def simulate_er_patients(current_time, end_time):
    """
    Generate instances of ER patients arriving based on an exponential inter-arrival time distribution.
    """
    count = 0
    while current_time < end_time:
        patient_id = random.choice(["", str(uuid.uuid4())])
        # ER patients do not have a predefined diagnosis
        diagnosis = ""
        create_patient_instance('ER', patient_id, diagnosis, current_time.isoformat())
        # Increment the time interval by an exponentially distributed random value
        time_delta = random.expovariate(1)
        current_time += datetime.timedelta(hours=time_delta)
        count+=1

    return count








