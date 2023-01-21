import pandas as pd

# Define the preference scheme
preference_scheme = {
    "Prefer": 5,
    "Neutral": 4,
    "Dislike": 3,
    "Minor Conflict": 2,
    "Major Conflict": 0
}

########################################################################################################
############### Populate shift_hours, shift_workers_required from shift_requirements.csv ###############
########################################################################################################

# Initialize shift_hours and shift_workers_required as empty dictionaries
shift_hours = {}
shift_workers_required = {}

# Read shift requirements CSV file
df = pd.read_csv('spring2023/shift_requirements.csv')

# Get the column names of the shifts
shifts = df.columns[1:]

# Iterate through the shifts
for shift in shifts:
    # Get the required number of people and shift length for the shift
    shift_workers_required[shift] = int(df.loc[df['Shift Name'] == 'Required number of people', shift])
    shift_hours[shift] = int(df.loc[df['Shift Name'] == 'Shift Length', shift])

# Print shift_hours and shift_workers_required
# print("Shift hours:", shift_hours)
# print("Shift workers required:", shift_workers_required)

########################################################################################################
############# Populate worker_required_hours, worker_preferences from form_responses.csv ###############
########################################################################################################

# Initialize worker_required_hours and worker_preferences as empty dictionaries
worker_required_hours = {}
worker_preferences = {}

# Read form responses CSV file
df = pd.read_csv('spring2023/form_responses.csv')

# Iterate through rows in the dataframe
for index, row in df.iterrows():
    # Get worker's name, required hours, and preferences
    worker_name = row['Worker Name']
    worker_required_hours[worker_name] = row['Required Hours']
    worker_preferences[worker_name] = {shift: preference_scheme[row[shift]] for shift in shift_hours}

# Print worker_required_hours and worker_preferences
# print("Worker required hours:", worker_required_hours)
# print("Worker preferences:", worker_preferences)

########################################################################################################
################# Populate shift_overlaps from shift_overlaps.csv ######################################
########################################################################################################

df = pd.read_csv("spring2023/shift_overlaps.csv", header=None, skiprows=1)
shift_overlaps = []
for row in df.values:
    shift_overlaps.append([val for val in row if pd.notna(val)])

# Print the shift overlaps
print("Shift overlaps:", shift_overlaps)

#############
# PULP CODE #
#############

from pulp import *

# Create a new LP problem
prob = LpProblem("Shift Scheduling Problem", LpMaximize)

# Create variables for worker-shift assignments
x = {}
for worker in worker_required_hours.keys():
    for shift in shift_hours.keys():
        x[worker, shift] = LpVariable(f'{worker}_{shift}', 0, 1, LpInteger)

# Create variables for worker hours
h = {}
for worker in worker_required_hours.keys():
    h[worker] = LpVariable(f'{worker}_hours', 0, worker_required_hours[worker], LpContinuous)

# Set objective function
prob += sum(worker_preferences[worker][shift]*x[worker, shift] for worker in worker_required_hours.keys() for shift in shift_hours.keys())

################## Add constraints ########################################
# Constraint 1: Shift worker count
for shift in shift_hours.keys():
    prob += sum(x[worker, shift] for worker in worker_required_hours.keys()) == shift_workers_required[shift]

# Constraint 2: Worker hours
for worker in worker_required_hours.keys():
    prob += h[worker] == sum(shift_hours[shift]*x[worker, shift] for shift in shift_hours.keys())

# Constraint 3: Worker preferences
for worker in worker_required_hours.keys():
    for shift in shift_hours.keys():
        if worker_preferences[worker][shift] == 0:
            prob += x[worker, shift] == 0

# Constraint 4: Shift overlaps
for worker in worker_required_hours.keys():
    for overlap_shifts in shift_overlaps:
        prob += sum([x[worker, shift] for shift in overlap_shifts]) <= 1


# (OPTIONAL) Constraint 5: Worker conflicts
# worker_conflicts should be a dictionary where the keys are the names of workers
# and the values are lists of workers that they have conflicts with.
# Example:
# worker_conflicts = {"Bob" : ["Dylan", "Josh"], "Elize" : ["Elvis", "Frank"]} 
# Bob does not want to work with Dylan or Josh. Elize does not want to work with Elvis or Frank.

# NOTE! Names must EXACTLY match the names in the form responses CSV file. Case and spaces matter.

worker_conflicts = {} # NOTE: Need to populate worker_conflicts dictionary manually
for worker in worker_conflicts:
    for conflict_worker in worker_conflicts[worker]:
        for shift in shift_hours.keys():
            prob += x[worker, shift] + x[conflict_worker, shift] <= 1

# Optimize model
prob.solve()


###############
# output code #
###############

import json

# Create a dictionary to store the schedule
schedule = {shift: [] for shift in shift_hours.keys()}

# Iterate through the worker-shift assignments in the solution
for worker, shift in x:
    if value(x[worker, shift]) > 0.5:
        schedule[shift].append(worker)

# Print the schedule in JSON format
print(json.dumps(schedule, indent=2))


# Create a dictionary to store the preference scores
preference_count = {i: 0 for i in range(6)}

# Count the occurrences of each preference score
for worker in worker_preferences.keys():
    for shift in shift_hours.keys():
        if value(x[worker, shift]) > 0.5:
            preference_count[worker_preferences[worker][shift]] += 1

# Print the preference score statistics
print("Preference Scores:")
for i in range(6):
    print(f"{i}: {preference_count[i]}")

# Create a dictionary to store the required and assigned hours for each worker
worker_hours = {worker: {"required": worker_required_hours[worker], "assigned": value(h[worker])} for worker in worker_required_hours.keys()}

# Add the preference score for each worker
for worker in worker_hours.keys():
    assigned_shifts = [shift for shift in shift_hours.keys() if value(x[worker, shift]) > 0.5]
    if len(assigned_shifts) > 0:
        preference_sum = sum(worker_preferences[worker][shift] for shift in assigned_shifts)
        worker_hours[worker]["preference_score"] = preference_sum/len(assigned_shifts)
    else:
        worker_hours[worker]["preference_score"] = 0

# print the schedule
for shift, workers in schedule.items():
    print(shift + ":")
    for worker in workers:
        print(worker)
    print()

# Print total hours required from all shifts
total_hours_required = sum(shift_hours[shift] * shift_workers_required[shift] for shift in shift_hours.keys())
print("Total hours required from all shifts: ", total_hours_required)

# Print total hours available from all workers
total_hours_available = sum(worker_required_hours.values())
print("Total hours available from all workers: ", total_hours_available)

print("{:<20} {:<10} {:<5} {:<5}".format("Name", "Required Hours", "Assigned Hours", "Score"))
total_preference_score = 0
total_hours_assigned = 0
for worker in worker_hours:
    required_hours = worker_hours[worker]['required']
    assigned_hours = worker_hours[worker]['assigned']
    preference_score = worker_hours[worker]['preference_score']
    total_preference_score += preference_score
    total_hours_assigned += assigned_hours
    if assigned_hours == required_hours:
        print("\033[92m{:<30} {:<5} {:<5} {:<5}\033[0m".format(worker, required_hours, assigned_hours, preference_score))
    else:
        print("\033[91m{:<30} {:<5} {:<5} {:<5}\033[0m".format(worker, required_hours, assigned_hours, preference_score))

print("TOTAL PREFERENCE SCORE: ", total_preference_score / len(worker_hours))
print("TOTAL ASSIGNED HOURS: ", total_hours_assigned)



