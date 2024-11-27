import yaml
from collections import defaultdict

with open('my_schedule.yaml', 'r') as file:
    data = yaml.safe_load(file)

def parse_time_slots(data):
    return [(slot['day'], slot['time']) for slot in data['schedule']['time_slots']]

def parse_subjects(data):
    return {subject['name']: subject['hours'] for subject in data['schedule']['subjects']}

def parse_groups(data):
    groups = {}
    for group in data['schedule']['groups']:
        name = group['name']
        capacity = group['capacity']
        subject_names = group['subject_names']
        groups[name] = {'capacity': capacity, 'subjects': subject_names}
    return groups

def parse_lecturers(data):
    lecturers = defaultdict(list)
    for lecturer in data['schedule']['lecturers']:
        name = lecturer['name']
        for subject in lecturer['can_teach_subjects']:
            lecturers[subject].append(name)
    return lecturers

def parse_halls(data):
    return {hall['name']: hall['capacity'] for hall in data['schedule']['halls']}

time_slots = parse_time_slots(data)
subjects = parse_subjects(data)
groups = parse_groups(data)
lecturers = parse_lecturers(data)
halls = parse_halls(data)

# Множина змінних Xi
variables = []
for group_name, group_info in groups.items():
    for subject_name in group_info['subjects']:
        hours = subjects[subject_name]
        for i in range(hours):
            variables.append((group_name, subject_name, i))

# Непорожня область визначення Dі можливих значень для кожної змінної
domains = {
    (group_name, subject_name, idx): [
        (day, time, hall, lecturer)
        for day, time in time_slots
        for hall, hall_capacity in halls.items() if hall_capacity >= groups[group_name]['capacity']
        for lecturer in lecturers.get(subject_name, [])
    ]
    for group_name, group_info in groups.items()
    for subject_name in group_info['subjects']
    for idx in range(subjects[subject_name])
}

# print(domains)

# Множиною обмежень Сі, що визначають допустимі комбінації значень для підмножин змінних.  Сі=(var,lim)
def constraints(var1, lim1, var2, lim2, assignment):
    if var1 == var2 and lim1 == lim2:
        return True

    group1, subject1, idx1 = var1
    group2, subject2, idx2 = var2
    day1, time1, hall1, lecturer1 = lim1
    day2, time2, hall2, lecturer2 = lim2

    # Різні дні, різний час - проблем немає
    if day1 != day2 or time1 != time2:
        return True

    # Якщо в одного лектора більше 2 занять в день - проблема
    if lecturer1 == lecturer2 and day1 == day2:
        unique_lectures = set()

        for v, val in assignment.items():
            if val[0] == day1 and val[3] == lecturer1:
                unique_lectures.add((val[1], val[0], val[1]))  # (предмет, день, час)


        # Підраховуємо кількість унікальних лекцій
        lectures_on_day = len(unique_lectures)
        print(f"{lectures_on_day} unique lectures for {lecturer1} at {day1}")
        if lectures_on_day > 2:
            return False

    # Якщо в один день, в один час, в 1 аудиторії більше людей, ніж вона вміщає - проблема
    if hall1 == hall2 and day1 == day2 and time1 == time2:
        total_capacity = halls[hall1]
        total_students = groups[group1]['capacity'] + groups[group2]['capacity']
        if total_students <= total_capacity:
            return True

    # Якщо 1 лектор веде в 1 день в 1 час лекцію - проблема
    if lecturer1 == lecturer2 and day1 == day2 and time1 == time2:
        return False

    return True

def is_consistent(assignment, variable, value, constraints):
    for other_variable, other_value in assignment.items():
        if not constraints(variable, value, other_variable, other_value, assignment):
            return False
    return True

# Пошук з поверненням - це метод розв'язання задачі за допомогою пошук в глибину,
# в якому пошук починається з початкового стану, на кожному кроці вибирається значення для однієї змінної та присвоюється,
# і виконується повернення, якщо більше не залишається допустимих значень, які можна було б присвоїти змінній.
# Якщо мету досягнуто - розв'язок знайдено.
def backtracking(variables, domains, constraints, assignment={}):
    if len(assignment) == len(variables):
        return assignment

    # Minimum Remaining Values - MRV
    unassigned = [v for v in variables if v not in assignment]
    variable = min(unassigned, key=lambda var: len(domains[var]))

    for value in domains[variable]:
        if is_consistent(assignment, variable, value, constraints):
            assignment[variable] = value
            result = backtracking(variables, domains, constraints, assignment)
            if result:
                return result
            del assignment[variable]

    return None

assignment = backtracking(variables, domains, constraints)

if assignment:
    sorted_schedule = sorted(
        ((group, subject, idx, day, time, hall, lecturer) for (group, subject, idx), (day, time, hall, lecturer) in assignment.items()),
        key=lambda x: (x[3], x[4])
    )
    print("\nSchedule:")
    for group, subject, idx, day, time, hall, lecturer in sorted_schedule:
        print(f"Group: {group}, Subject: {subject}, Lesson {idx}, Day: {day}, Time: {time}, Hall: {hall}, Lecturer: {lecturer}")
else:
    print("No solution found.")
