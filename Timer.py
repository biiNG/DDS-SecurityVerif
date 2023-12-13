import re

def analyze_task_file(file_name, time_threshold):
    task_times = {}
    prefixes = ["MAC-MaliciousParticipant","ENC-MaliciousParticipant","ENC-Base","MAC-Base"]
    with open(file_name, 'r') as file:
        for line in file:
            match = re.search(r'Task (\S+).*runs (\d+(\.\d+)?) seconds', line)
            if match:
                task_name = match.group(1)
                task_time = float(match.group(2))
                if any(task_name.startswith(prefix) for prefix in prefixes):
                    task_times[task_name] = task_time

    max_time_task = max(task_times, key=task_times.get)
    min_time_task = min(task_times, key=task_times.get)

    print(f'Task with max time {max_time_task}: {task_times[max_time_task]}')
    print(f'Task with min time {min_time_task}: {task_times[min_time_task]}')

    tasks_within_threshold = [task for task, time in task_times.items() if time <= time_threshold]
    print(f'Number of tasks completed within {time_threshold} seconds: {len(tasks_within_threshold)}')

analyze_task_file('result-timeout.txt', 10)
