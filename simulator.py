#!/usr/bin/env python3
import datetime
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue
from gevent import monkey

monkey.patch_all()

import json
import gevent
from gevent.pywsgi import WSGIServer
from gevent.lock import Semaphore
from bottle import Bottle, request, response, HTTPResponse
from numpy import random
import requests
import db
import diagnosis_helper as dh
from instance_generator import simulate_er_patients, simulate_planned_patients_a, simulate_planned_patients_b
from time_helper import start_time, end_time, is_not_working_hour, next_working_hour, next_non_working_hour

app = Bottle()
diagnosis_helper = dh.DiagnosisHelper()

# Semaphores for resource management
surgery_semaphore = Semaphore()
bed_a_semaphore = Semaphore()
bed_b_semaphore = Semaphore()
er_semaphore = Semaphore()

# Priority queues for simulation
patient_queue_non_working_hour = PriorityQueue()
patient_queue_working_hour = PriorityQueue()

# Counters for tracking spawned instances and deciding time to start simulation
patients_count_non_working_hour = 0
patients_added_non_working_hour = 0
patients_count_working_hour = 0
patients_added_working_hour = 0

# Events to signal when the instances queues are ready
patient_queue_ready_event_working_hour = threading.Event()
patient_queue_ready_event_non_working_hour = threading.Event()


# Function to signal when the instances queues are ready
def set_patient_queue_ready():
    patient_queue_ready_event_non_working_hour.set()


def set_patient_queue_ready_working():
    patient_queue_ready_event_working_hour.set()


def callback(callback_response, callback_url):
    """
    Callback the instance.
    """
    headers = {
        'content-type': 'application/json',
        'CPEE-CALLBACK': 'true'
    }
    requests.put(callback_url, headers=headers, json=callback_response)
    print(f"callback: {callback_url}")


def callback_http_response():
    """
    HTTP response for callback
    """
    return HTTPResponse(
        json.dumps({'Ack.:': 'Response later'}),
        status=202,
        headers={'content-type': 'application/json', 'CPEE-CALLBACK': 'true'}
    )


def process_queue_er():
    """
    Process ER Queue: This function continuously monitors and processes the ER queue.
    It checks if there are any patients in the ER queue and if there are available ER personnel to attend to them.
    If both conditions are met, it processes the first patient in the queue.
    """
    while True:
        # Get the current ER queue and the count of available ER personnel
        queue_er = db.get_queue_er()
        er_count = db.get_resource('ER')

        # Check if there are patients in the queue and available ER personnel
        if len(queue_er) > 0 and er_count > 0:
            # Use the semaphore to control access to the ER resource
            with er_semaphore:
                # Occupy 1 ER personnel for the first patient in the queue
                db.update_resource('ER', er_count - 1)
                callback_url = db.get_queue_er()[0]
                print(callback_url, 'First patient in the queue go to ER')

                # Simulate the duration of ER treatment using a normal distribution
                duration = max(0, random.normal(loc=2, scale=1 / 2, size=None))
                gevent.sleep(duration)

                # Remove the patient from the queue after treatment
                db.delete_from_queue_er(callback_url)
                # Release the occupied ER personnel after treatment
                db.update_resource('ER', db.get_resource('ER') + 1)

                # Determine if the ER patient has phantom pain or needs further treatment
                phantom_pain = random.choice(['true', 'false'])
                if phantom_pain == 'false':
                    diagnosis = diagnosis_helper.assign_diagnosis('ER')
                    require_surgery = diagnosis_helper.requires_surgery(diagnosis)
                else:
                    diagnosis = ""
                    require_surgery = ""

                callback_response = {'status': 'ER Treatment finished', 'duration': round(duration, 2),
                                     'phantom_pain': phantom_pain,
                                     'diagnosis': diagnosis,
                                     'require_surgery': require_surgery}

                callback(callback_response, callback_url)

        # Sleep for a short duration to avoid busy-waiting
        gevent.sleep(0.01)


def process_queue_surgery():
    """
    Process Surgery Queue: This function continuously monitors and processes the Surgery queue.
    It checks if there are any patients in the Surgery queue and if there are available surgery rooms.
    If both conditions are met, it processes the first patient in the queue.
    """
    while True:
        queue_surgery = db.get_queue('Queue_Surgery')
        surgery_room_count = db.get_resource('Surgery')
        if len(queue_surgery) > 0 and surgery_room_count > 0:
            with surgery_semaphore:
                db.update_resource('Surgery', surgery_room_count - 1)
                print(callback_url, 'First patient in the queue go to surgery')

                patient_id, diagnosis, status, callback_url = db.get_queue('Queue_Surgery')[0]
                duration = diagnosis_helper.diagnosis_operation_time(diagnosis)
                gevent.sleep(duration)
                db.delete_from_queue('Queue_Surgery', callback_url)
                print(db.get_queue('Queue_Surgery'))
                db.update_resource('Surgery', db.get_resource('Surgery') + 1)

                callback_response = {
                    'status': 'Surgery finished',
                    'duration': round(duration, 2)
                }

                callback(callback_response, callback_url)
        gevent.sleep(0.01)


def process_queue_nursing_a():
    """
    Process Queue for Nursing Bed A: This function continuously monitors and processes the Nursing Bed A queue.
    It checks if there are any patients in the Nursing Bed A queue and if there are available bed A.
    If both conditions are met, it processes the first patient in the queue.
    """
    while True:
        queue_nursing_a = db.get_queue('Queue_Nursing_A')
        bed_a_count = db.get_resource('Bed_A')
        if len(queue_nursing_a) > 0 and bed_a_count > 0:
            with bed_a_semaphore:
                db.update_resource('Bed_A', bed_a_count - 1)
                print(callback_url, 'First patient in the queue go to bed A')
                patient_id, diagnosis, status, callback_url = db.get_queue('Queue_Nursing_A')[0]
                duration = diagnosis_helper.diagnosis_nursing_time(diagnosis)
                gevent.sleep(duration)
                db.delete_from_queue('Queue_Nursing_A', callback_url)
                db.update_resource('Bed_A', db.get_resource('Bed_A') + 1)
                release = diagnosis_helper.no_complication(diagnosis)

                callback_response = {
                    'status': 'Nursing finished',
                    'duration': round(duration, 2),
                    'release': release
                }
                callback(callback_response, callback_url)
        gevent.sleep(0.01)


def process_queue_nursing_b():
    """
    Process Queue for Nursing Bed B: This function continuously monitors and processes the Nursing Bed B queue.
    It checks if there are any patients in the Nursing Bed B queue and if there are available bed B.
    If both conditions are met, it processes the first patient in the queue.
    """
    while True:
        queue_nursing_b = db.get_queue('Queue_Nursing_B')
        bed_b_count = db.get_resource('Bed_B')
        if len(queue_nursing_b) > 0 and bed_b_count > 0:
            with bed_b_semaphore:
                db.update_resource('Bed_B', bed_b_count - 1)
                print(callback_url, 'First patient in the queue go to bed B')
                patient_id, diagnosis, status, callback_url = db.get_queue('Queue_Nursing_B')[0]
                duration = diagnosis_helper.diagnosis_nursing_time(diagnosis)
                gevent.sleep(duration)
                db.delete_from_queue('Queue_Nursing_B', callback_url)
                db.update_resource('Bed_B', db.get_resource('Bed_B') + 1)
                release = diagnosis_helper.no_complication(diagnosis)

                callback_response = {
                    'status': 'Nursing finished',
                    'duration': round(duration, 2),
                    'release': release
                }
                callback(callback_response, callback_url)
        gevent.sleep(0.01)


# start of the process
@app.post('/patient_init')
def patient_init():
    """
    Initialize the patient instance, waiting for callback while patient arrives.
    This endpoint handles the initialization of patient instances, placing them in the appropriate queue based on their arrival time.
    """
    global patients_added_non_working_hour
    global patients_added_working_hour
    patient_id = request.forms.get('patientID')
    patient_type = request.forms.get('patientType')
    arrival_time = request.forms.get('arrival_time')
    callback_url = request.headers['CPEE-CALLBACK']

    # Check if the arrival time is during non-working hours
    if is_not_working_hour(datetime.datetime.fromisoformat(arrival_time)):
        # Add the patient to the non-working hour queue
        patient_queue_non_working_hour.put((arrival_time, callback_url, patient_id, patient_type))
        patients_added_non_working_hour += 1
    else:
        # Add the patient to the working hour queue
        patient_queue_working_hour.put((arrival_time, callback_url, patient_id, patient_type))
        patients_added_working_hour += 1

    # Check if all non-working hour patients have been added
    if patients_added_non_working_hour == patients_count_non_working_hour:
        set_patient_queue_ready()

    # Check if all working hour patients have been added
    if patients_added_working_hour == patients_count_working_hour:
        set_patient_queue_ready_working()
    return callback_http_response()


def patient_admission(callback_url, patient_id, patient_type, arrival_time):
    """
    Task "Patient Admission"
    This function handles the admission process for a patient based on their type and available resources.
    """
    if patient_type == "ER":
        # Directly admit the patient if they are an ER patient
        status = 'patient admitted'
    elif not patient_id:
        # Send the patient home if no patient ID is provided
        status = 'sent home'
    else:
        # Get the count of available intake personnel
        intake_personnel_count = db.get_resource('Intake')
        # Calculate the number of patients finished Intake but not proceeded to next step yet.
        waiting_in_queue = db.get_count_queue('Queue_Surgery', 'Intake finished') \
                           + db.get_count_queue('Queue_Nursing_A', 'Intake finished') \
                           + db.get_count_queue('Queue_Nursing_B', 'Intake finished')

        # no intake resources available or no more than 2 patients finished intake but not processed with next step yet.
        if intake_personnel_count <= 0 or waiting_in_queue >= 2:
            status = 'sent home'
        else:
            # Admit the patient and reserve 1 intake personnel
            db.update_resource('Intake', intake_personnel_count - 1)
            status = 'patient admitted'

    callback_response = {'status': status, 'arrival_time': arrival_time}
    callback(callback_response, callback_url)


@app.post('/Intake')
def intake():
    """
    Task "Intake"
    """
    try:
        diagnosis = request.forms.get('diagnosis')

        # Simulate the duration of the intake process using a normal distribution
        duration = max(0, random.normal(loc=1, scale=1 / 8, size=None))
        gevent.sleep(duration)

        # Release the occupied intake resource
        db.update_resource('Intake', db.get_resource('Intake') + 1)

        # Determine if surgery is required based on the diagnosis
        require_surgery = diagnosis_helper.requires_surgery(diagnosis)

        response.content_type = 'application/json'
        data = {'status': 'Intake finished', 'duration': round(duration, 2), 'require_surgery': require_surgery}
        return json.dumps(data)

    except Exception as e:
        response.status = 500
        return json.dumps({"error": str(e)})


@app.post('/ER_Resource')
def handle_er_resource():
    """
    Task "ER Treatment"
    """
    try:
        callback_url = request.headers['CPEE-CALLBACK']
        er_personnel_count = db.get_resource('ER')

        # Check if there are already patients in the ER queue or if no ER personnel are available
        if len(db.get_queue_er()) > 0 or er_personnel_count <= 0:
            # Add the patient to the ER queue if the ER is busy or no personnel are available
            db.add_to_queue_er(callback_url)
            print('ER is busy', callback_url,'added to ER queue')
            return callback_http_response()

        else:
            db.update_resource('ER', er_personnel_count - 1)
            duration = max(0, random.normal(loc=2, scale=1 / 2, size=None))

            gevent.sleep(duration)
            db.update_resource('ER', db.get_resource('ER') + 1)

            # Determine if the ER patient has phantom pain or needs further treatment
            phantom_pain = random.choice(['true', 'false'])
            if phantom_pain == 'false':
                diagnosis = diagnosis_helper.assign_diagnosis('ER')
                require_surgery = diagnosis_helper.requires_surgery(diagnosis)
            else:
                diagnosis = ""
                require_surgery = ""

            data = {'status': 'ER Treatment finished', 'duration': round(duration, 2), 'phantom_pain': phantom_pain,
                    'diagnosis': diagnosis,
                    'require_surgery': require_surgery}
            response.content_type = 'application/json'
            return json.dumps(data)

    except Exception as e:
        response.status = 500
        return json.dumps({"error": str(e)})


@app.post('/surgery')
def surgery():
    """
    Task "Surgery"
    """
    callback_url = request.headers['CPEE-CALLBACK']
    patient_id = request.forms.get('patientID')
    status = request.forms.get('status')
    diagnosis = request.forms.get('diagnosis')

    surgery_room_count = db.get_resource('Surgery')
    # Check if there are already patients in the Surgery queue or if no Surgery room are available
    if len(db.get_queue('Queue_Surgery')) > 0 or surgery_room_count <= 0:
        # Add the patient to the Surgery queue if it is busy
        db.add_to_queue('Queue_Surgery', patient_id, diagnosis, status, callback_url)
        print('Surgery room not available', callback_url, 'added to surgery queue')
        return callback_http_response()
    else:
        db.update_resource('Surgery', surgery_room_count - 1)
        duration = diagnosis_helper.diagnosis_operation_time(diagnosis)
        gevent.sleep(duration)
        db.update_resource('Surgery', db.get_resource('Surgery') + 1)

        data = {'status': 'Surgery finished', 'duration': round(duration, 2)}
        response.content_type = 'application/json'
        return json.dumps(data)


@app.post('/nursing')
def nursing():
    """
    Task "Nursing"
    """
    callback_url = request.headers['CPEE-CALLBACK']
    patient_id = request.forms.get('patientID')
    status = request.forms.get('status')
    diagnosis = request.forms.get('diagnosis')

    if diagnosis.startswith('A'):
        Bed_A_count = db.get_resource('Bed_A')
        # Check if there are already patients in the nursing bed A queue or if no bed A are available
        if len(db.get_queue('Queue_Nursing_A')) > 0 or Bed_A_count <= 0:
            print('Bed A not available', callback_url, 'added to Nursing Bed A queue')
            # Add the patient to the nursing bed A queue if it is busy
            db.add_to_queue('Queue_Nursing_A', patient_id, diagnosis, status, callback_url)
            return callback_http_response()
        else:
            db.update_resource('Bed_A', Bed_A_count - 1)
            duration = diagnosis_helper.diagnosis_nursing_time(diagnosis)
            gevent.sleep(duration)
            db.update_resource('Bed_A', db.get_resource('Bed_A') + 1)

            release = diagnosis_helper.no_complication(diagnosis)

            data = {'status': 'Nursing finished', 'duration': round(duration, 2), 'release': release}
            response.content_type = 'application/json'
            return json.dumps(data)
    else:
        Bed_B_count = db.get_resource('Bed_B')
        # Check if there are already patients in the nursing bed B queue or if no bed B are available
        if len(db.get_queue('Queue_Nursing_B')) > 0 or Bed_B_count <= 0:
            print('Bed B not available', callback_url, 'added to Nursing Bed B queue')
            # Add the patient to the nursing bed B queue if it is busy
            db.add_to_queue('Queue_Nursing_B', patient_id, diagnosis, status, callback_url)
            return callback_http_response()
        else:
            db.update_resource('Bed_B', Bed_B_count - 1)
            duration = diagnosis_helper.diagnosis_nursing_time(diagnosis)
            gevent.sleep(duration)
            db.update_resource('Bed_B', db.get_resource('Bed_B') + 1)

            release = diagnosis_helper.no_complication(diagnosis)

            data = {'status': 'Nursing finished', 'duration': round(duration, 2), 'release': release}
            response.content_type = 'application/json'
            return json.dumps(data)
# end of the process


def process_patient_queue_non_working_hour():
    """
    Spawned patient instances arrive during non-working hours, start the process.
    This function processes the queue of patient instances that arrive during non-working hours.
    """
    previous_time = None
    while not patient_queue_non_working_hour.empty():
        # Get the next patient instance from the queue
        arrival_time_str, callback_url, patient_id, patient_type = patient_queue_non_working_hour.get()
        arrival_time = datetime.datetime.fromisoformat(arrival_time_str)
        if previous_time is not None:
            time_difference = round((arrival_time - previous_time).total_seconds() / 3600, 2)
            # Sleep for the time difference to simulate the actual arrival time of patients
            time.sleep(time_difference)
        previous_time = arrival_time
        print(arrival_time, callback_url, "arrives")
        # Proceed the patient to the first task in the process
        patient_admission(callback_url, patient_id, patient_type, arrival_time_str)


def process_patient_queue_working_hour():
    """
    Spawned patient instances arrive during working hours, start the process.
    This function processes the queue of patient instances that arrive during working hours.
    """
    previous_time = None
    while not patient_queue_working_hour.empty():
        arrival_time_str, callback_url, patient_id, patient_type = patient_queue_working_hour.get()
        arrival_time = datetime.datetime.fromisoformat(arrival_time_str)
        if previous_time is not None:
            time_difference = round((arrival_time - previous_time).total_seconds() / 3600, 2)
            time.sleep(time_difference)
        previous_time = arrival_time
        print(arrival_time, callback_url, "arrives")
        patient_admission(callback_url, patient_id, patient_type, arrival_time_str)


def spawn_instances_non_working_hour():
    """
    Spawn patient instances for non-working hours.
    This function schedules the arrival of patient instances during non-working hours.
    """
    global patients_count_non_working_hour
    # start time is 00:00 01.01.2018
    current_time = start_time
    while current_time < end_time:
        # Wait until patient instances in the last round processed and cleared
        while patients_count_non_working_hour == 0 and patients_added_non_working_hour == 0:
            if is_not_working_hour(current_time):
                next_timestamp = next_working_hour(current_time)
                # only ER patients arrived during non_working hours
                patients_count_non_working_hour += simulate_er_patients(current_time, next_timestamp)
                current_time = next_timestamp

            else:  # is working hour
                next_timestamp = next_non_working_hour(current_time)
                current_time = next_timestamp
        time.sleep(1)


def spawn_instances_working_hour():
    """
    Spawn patient instances for working hours.
    This function schedules the arrival of patient instances during working hours.
    """
    global patients_count_working_hour
    current_time = start_time
    while current_time < end_time:
        # Wait until patient instances in the last round processed and cleared
        while patients_count_working_hour == 0 and patients_added_working_hour == 0:
            if is_not_working_hour(current_time):
                current_time = next_working_hour(current_time)

            else:
                next_timestamp = next_non_working_hour(current_time)
                # type A, type B, ER patients arrive during working hours
                with ThreadPoolExecutor() as executor:
                    future_a = executor.submit(simulate_planned_patients_a, current_time, next_timestamp)
                    future_b = executor.submit(simulate_planned_patients_b, current_time, next_timestamp)
                    future_er = executor.submit(simulate_er_patients, current_time, next_timestamp)

                    planned_a_count = future_a.result()
                    planned_b_count = future_b.result()
                    er_count = future_er.result()

                patients_count_working_hour += planned_a_count + planned_b_count + er_count
                current_time = next_timestamp
        time.sleep(1)


def simulation():
    """
    Simulate from 00:00 01.01.2018
    """
    global patients_count_non_working_hour
    global patients_added_non_working_hour
    global patients_count_working_hour
    global patients_added_working_hour
    while True:
        # Non-working hours
        # Wait for the patient queue to be ready for non-working hours
        patient_queue_ready_event_non_working_hour.wait()
        print('non-working hour started, surgery room 1 available')
        # Update the Surgery resource to reflect non-working hour availability (1 Surgery room available)
        db.update_resource('Surgery', db.get_resource('Surgery') - 4)
        process_patient_queue_non_working_hour()
        patients_count_non_working_hour = 0
        patients_added_non_working_hour = 0
        patient_queue_ready_event_non_working_hour.clear()  # Clear the event to reset to not ready state
        patient_queue_ready_event_working_hour.clear()

        # Working hours
        # Wait for the patient queue to be ready for working hours
        patient_queue_ready_event_working_hour.wait()
        print('working hour started, surgery room 5 available')
        # Update the Surgery resource to reflect non-working hour availability (5 Surgery rooms available)
        db.update_resource('Surgery', db.get_resource('Surgery') + 4)
        process_patient_queue_working_hour()
        patients_count_working_hour = 0
        patients_added_working_hour = 0
        patient_queue_ready_event_working_hour.clear()
        patient_queue_ready_event_non_working_hour.clear()


if __name__ == '__main__':
    gevent.spawn(process_queue_surgery)
    gevent.spawn(process_queue_nursing_a)
    gevent.spawn(process_queue_nursing_b)
    gevent.spawn(process_queue_er)
    gevent.spawn(spawn_instances_non_working_hour)
    gevent.spawn(spawn_instances_working_hour)
    gevent.spawn(simulation)

    try:
        server = WSGIServer(('::1', 23462), app)
        server.serve_forever()
    except OSError as e:
        print(f"Error: {e}")
        if "Address already in use" in str(e):
            print("Address already in use. Please free the port or use a different one.")
