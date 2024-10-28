# Hospital Simulator

## Overview

This project simulates the process of a hospital, managing patient admission, patient intake/ ER treatment, surgery, and nursing. 
The simulation alternates between working hours and non-working hours, processing patient queues and managing resources accordingly.

During non-working hours, only ER patients arrive, and only 1 surgery room available.

During working hours, planned patients and ER patients arrive, 4 surgery rooms available

## Directory Structure

- `simulator.py`: Main script to run the simulation.
- `planner.py`: Use constraints programming for rescheduling patient appointments.
- `db.py`: Module for database operations.
- `diagnosis_helper.py`: Module to assist with patient diagnosis and related operations.
- `instance_generator.py`: Module to help generate patient instances.
- `time_helper.py`: Module to handle time-related operations.
- `main.xml`: Process model

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/Fen-Shi/simulator
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
## Running the Simulation
1. **Start the simulation:**
Run the simulator.py on https://lehre.bpm.in.tum.de/ website. 

   ```
   python simulator.py
   ```
   `simulator.py` is designed to:
- Spawn instances automatically.
- Process these instances through the defined workflow.
- Monitor and log the total duration for each instance. (The duration can be found on the instance link on the CPEE platform)

2. **Endpoints:**

- `POST /patient_init`: Initialize a patient instance.
- `POST /Intake`: Handle patient intake.
- `POST /ER_Resource`: Handle ER treatment.
- `POST /surgery`: Handle surgery.
- `POST /nursing`: Handle nursing.

## How It Works
1. **Initialization:**

- The simulation starts from 00:00 01.01.2018 and runs continuously, 1 h in real world = 1 s in simulator.
- Patients are spawned based on working and non-working hours.
- planned patient with Diagnosis 'A' and 'B' arrive during working hours with rate unif(0,1)
- ER patient arrive throughout the day with rate exp(1)


2. **Patient Admission:**

- Patients are added to queues based on their arrival times.
- ER patients are admitted directly, while others depend on treatment infeasibility.
- Treatment is infeasible either if more than two patients have finished the intake,
but have not yet been processed in the Surgery or Nursing departments, or when all Intake
resources are occupied upon a patient's arrival.
- Patients without ID will be directly sent home.
- Patients sent home will be planned by planner.py using constraints programming to find the next earliest possible appoitment.

3. **Resource Management:**

- Semaphores are used to manage access to shared resources (surgery rooms, beds, ER personnel).
- Resource availability is updated as patients are processed.
- Five operating rooms are available during working hours. This drops to one
operating room outside the working hours

4. **Queue Processing:**

- Patient queues are processed during both working and non-working hours.
- Non-working hours have limited resource availability, while working hours have full resource availability.
- Waiting time in the queue will be added to the duration.

5. **patients replan (`planner.py`)**
- Variable: `reschedule_time` to target optimal time slots.
- Domain: Only working hours (Mon-Fri, 8 AM to 5 PM) within the next 7 days.
- Constraints: 
   - Intake Resources: Rescheduling considers the availability of intake resources, avoiding conflicts where intake capacity would be exceeded.
  - Pending Patients: Monitors the number of patients waiting after intake for the next stage. 


## Detailed Function Descriptions
`simulator.py`
- `simulation()`: Main function that runs the simulation, alternating between working and non-working hours, and processing patient queues.
- `spawn_instances_non_working_hour()`: Schedule patient instances for non-working hours.
- `spawn_instances_working_hour()`: Schedule patient instances for working hours.
- `process_patient_queue_non_working_hour()`: Processes the patient arrivals for non-working hours.
- `process_patient_queue_working_hour()`: Processes the patient arrivals for working hours.

`planner.py`
- Using constraints programming to find the next earliest possible appointment for sent home patients.

`db.py`
- Database operations for managing queues and resources.

`diagnosis_helper.py`
- Helper functions for patient diagnosis and determining if surgery is required.

`instance_generator.py`
- Functions to simulate patient arrivals during working and non-working hours.

`time_helper.py`
- Functions to handle time-related operations, such as checking if the current time is within working hours.