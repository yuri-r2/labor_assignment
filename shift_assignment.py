import pandas as pd
from pulp import *

# Define the preference scheme
preference_scheme = {
    "Prefer": 5,
    "Neutral": 4,
    "Dislike": 3,
    "Minor Conflict": 1,
    "Major Conflict": 0
}

########################################################################################################
############### Populate shift_hours, shift_workers_required from shift_requirements.csv ###############
########################################################################################################

def read_shift_requirements(file_path):
    df = pd.read_csv(file_path)
    shifts = df.columns[1:]

    shift_hours = {}
    shift_workers_required = {}

    for shift in shifts:
        shift_workers_required[shift] = int(df.loc[df['Shift Name'] == 'Required number of people', shift])
        shift_hours[shift] = int(df.loc[df['Shift Name'] == 'Shift Length', shift])

    return shift_hours, shift_workers_required

def read_form_responses(file_path, shift_hours):
    df = pd.read_csv(file_path)

    worker_required_hours = {}
    worker_preferences = {}

    for index, row in df.iterrows():
        worker_name = row['What is your first and last name?']
        worker_required_hours[worker_name] = row['Required hours of labor']
        worker_preferences[worker_name] = {
            shift: preference_scheme[row[shift]] if not pd.isna(row[shift]) else 0
            for shift in shift_hours
        }

    return worker_required_hours, worker_preferences


def read_shift_overlaps(file_path):
    df = pd.read_csv(file_path, header=None, skiprows=1)
    shift_overlaps = []
    for row in df.values:
        shift_overlaps.append([val for val in row if pd.notna(val)])

    return shift_overlaps


# Read shift requirements CSV file
shift_hours, shift_workers_required = read_shift_requirements('spring2023/shift_requirements.csv')

# Read form responses CSV file
worker_required_hours, worker_preferences = read_form_responses('spring2023/form_responses.csv', shift_hours)

# Read shift overlaps CSV file
shift_overlaps = read_shift_overlaps("spring2023/shift_overlaps.csv")


#############
# PULP CODE #
#############


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

# Create a dictionary to store the schedule
schedule = {shift: [] for shift in shift_hours.keys()}

# Iterate through the worker-shift assignments in the solution
for worker, shift in x:
    if value(x[worker, shift]) > 0.5:
        schedule[shift].append(worker)

# Print the schedule in JSON format
# print(json.dumps(schedule, indent=2))


# Create a dictionary to store the preference scores
preference_count = {i: 0 for i in range(6)}

# Count the occurrences of each preference score
for worker in worker_preferences.keys():
    for shift in shift_hours.keys():
        if value(x[worker, shift]) > 0.5:
            preference_count[worker_preferences[worker][shift]] += 1

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
print("SCHEDULE:\n")
for shift, workers in schedule.items():
    print("    " + shift)
    for worker in workers:
        print(worker)

print("END OF SCHEDULE\n")


print("{:<20} {:<5} {:<5} {:<5}".format("Name", "|Required Hours|", "Assigned Hours|", "Score"))
total_preference_score = 0
total_hours_assigned = 0
for worker in worker_hours:
    required_hours = worker_hours[worker]['required']
    assigned_hours = worker_hours[worker]['assigned']
    preference_score = worker_hours[worker]['preference_score']
    total_preference_score += preference_score
    total_hours_assigned += assigned_hours
    if assigned_hours == required_hours:
        print("\033[92m{:<30} {:<10} {:<10} {:<10}\033[0m".format(worker, required_hours, assigned_hours, preference_score))
    else:
        print("\033[91m{:<30} {:<10} {:<10} {:<10}\033[0m".format(worker, required_hours, assigned_hours, preference_score))


# Print total hours required from all shifts
total_hours_required = sum(shift_hours[shift] * shift_workers_required[shift] for shift in shift_hours.keys())
print("Total hours required from all shifts: ", total_hours_required)

# Print total hours available from all workers
total_hours_available = sum(worker_required_hours.values())
print("Total hours available from all workers: ", total_hours_available)

print("TOTAL ASSIGNED HOURS: ", total_hours_assigned)

print("TOTAL PREFERENCE SCORE: ", total_preference_score / len(worker_hours))

# Print the preference score statistics
print("Preference Score Count:")
for i in range(6):
    print(f"{i}: {preference_count[i]}")