import sys
import re


def read_to_table(path: str) -> list:
    """
    Reads any CSV file and returns the contents as a list of rows.

    Each row is a dictionary where the keys are the column names from the
    header and the values are the data in that row. Everything is kept as
    a string — no conversion happens here.

    Parameters:
        path (str): Path to the CSV file to read.

    Returns:
        list: A list of rows, where each row is a dictionary of string values.
    """
    table = []

    with open(path, 'r') as file_csv:
        headers = file_csv.readline().strip().split(",")

        for line in file_csv:
            values = line.strip().split(",")

            # Build a row dictionary by pairing each header with its matching value
            row = {}
            for i in range(len(headers)):
                row[headers[i].strip()] = values[i].strip()

            table.append(row)

    return table


def valid_id(value: str) -> bool:
    """Returns True if the value matches the ID format — uppercase letters then digits, no leading zero."""
    return re.match(r'^[A-Z]+(0|[1-9][0-9]*)$', value) is not None


def valid_zone(value: str) -> bool:
    """Returns True if the value is a non-empty string of uppercase letters only."""
    return re.match(r'^[A-Z]+$', value) is not None


def valid_int(value: str) -> bool:
    """Returns True if the value is a valid integer string with no leading zeros."""
    return re.match(r'^-?(0|[1-9][0-9]*)$', value) is not None


def valid_float(value: str) -> bool:
    """Returns True if the value is a valid decimal number string with no leading zeros."""
    return re.match(r'^-?(0|[1-9][0-9]*)(\.(0|[0-9]*[1-9]))?$', value) is not None


def read_robots(robots_path: str) -> list:
    """
    Loads and validates all robots from a CSV file.

    Each robot is checked to make sure its ID is in the right format,
    its battery is between 0 and 100, its max load is not negative, and
    its zone is uppercase letters only. Any robot that fails a check is
    skipped and a warning is shown in the error log.

    Parameters:
        robots_path (str): Path to the robots CSV file.

    Returns:
        list: A list of valid robot rows, each as a dictionary.
    """
    raw_table = read_to_table(robots_path)
    robots = []

    for robot in raw_table:
        robot_id = robot["robot_id"]
        battery_str = robot["battery_level"]
        max_load_str = robot["max_load"]
        zone = robot["zone"]

        # IDs must be uppercase letters followed by digits, with no leading zero.
        if not valid_id(robot_id):
            print(f"Warning: Robot {robot_id} has invalid ID format.", file=sys.stderr)
            continue

        # Battery must be a valid integer format before converting
        if not valid_int(battery_str):
            print(f"Warning: Robot {robot_id} has invalid battery level ({battery_str}).", file=sys.stderr)
            continue

        # Max load must be a valid number format before converting
        if not valid_float(max_load_str):
            print(f"Warning: Robot {robot_id} has invalid max load ({max_load_str}).", file=sys.stderr)
            continue

        # Zone must be non-empty and made up of uppercase letters only
        if not valid_zone(zone):
            print(f"Warning: Robot {robot_id} has invalid zone ({zone}).", file=sys.stderr)
            continue

        battery_level = int(battery_str)
        max_load = float(max_load_str)

        if not (0 <= battery_level <= 100):
            print(f"Warning: Robot {robot_id} has invalid battery level ({battery_level}).", file=sys.stderr)
            continue
        if max_load < 0:
            print(f"Warning: Robot {robot_id} has invalid max load ({max_load}).", file=sys.stderr)
            continue

        robot["battery_level"] = battery_level
        robot["max_load"] = max_load
        robots.append(robot)

    return robots


def read_destinations(destinations_path: str) -> list:
    """
    Loads and validates all destinations from a CSV file.

    Each destination is checked to make sure its ID is in the right format
    and its zone is uppercase letters only. Any destination that fails a
    check is skipped and a warning is shown in the error log.

    Parameters:
        destinations_path (str): Path to the destinations CSV file.

    Returns:
        list: A list of valid destination rows, each as a dictionary.
    """
    raw_table = read_to_table(destinations_path)
    destinations = []

    for destination in raw_table:
        destination_id = destination["destination_id"]
        zone = destination["zone"]

        # ID must follow the format: one or more uppercase letters then digits, no leading zero
        if not valid_id(destination_id):
            print(f"Warning: Destination {destination_id} has invalid ID format.", file=sys.stderr)
            continue

        # Zone must be non-empty and made up of uppercase letters only
        if not valid_zone(zone):
            print(f"Warning: Destination {destination_id} has invalid zone ({zone}).", file=sys.stderr)
            continue

        destinations.append(destination)

    return destinations


def read_packages(packages_path: str) -> list:
    """
    Loads and validates all packages from a CSV file.

    Each package is checked to make sure its ID is in the right format and
    its weight is not negative. Any package that fails a check is skipped
    and a warning is shown in the error log.

    Parameters:
        packages_path (str): Path to the packages CSV file.

    Returns:
        list: A list of valid package rows, each as a dictionary.
    """
    raw_table = read_to_table(packages_path)
    packages = []

    for package in raw_table:
        package_id = package["package_id"]
        weight_str = package["weight"]

        # IDs must be uppercase letters followed by digits, with no leading zero.
        if not valid_id(package_id):
            print(f"Warning: Package {package_id} has invalid ID format.", file=sys.stderr)
            continue

        # Weight must be a valid number format before converting
        if not valid_float(weight_str):
            print(f"Warning: Package {package_id} has invalid weight ({weight_str}).", file=sys.stderr)
            continue

        weight = float(weight_str)

        if weight < 0:
            print(f"Warning: Package {package_id} has invalid weight ({weight}).", file=sys.stderr)
            continue

        package["weight"] = weight
        packages.append(package)

    return packages


def read_tasks(tasks_path: str, destination_ids: list, package_ids: list) -> list:
    """
    Loads and validates all tasks from a CSV file.

    Each task is checked to make sure its ID is in the right format, its
    pickup and drop-off locations exist, its package exists, and its status
    is either 'pending' or 'complete'. Any task that fails a check is
    skipped and a warning is shown in the error log.

    Parameters:
        tasks_path (str): Path to the tasks CSV file.
        destination_ids (list): The known destination IDs to check against.
        package_ids (list): The known package IDs to check against.

    Returns:
        list: A list of valid task rows, each as a dictionary.
    """
    raw_table = read_to_table(tasks_path)
    tasks = []

    for task in raw_table:
        task_id = task["task_id"]
        source_id = task["source_id"]
        target_id = task["target_id"]
        package_id = task["package_id"]

        # Convert to lowercase so 'Pending' and 'PENDING' are treated the same as 'pending'
        status = task["status"].lower()

        # ID must follow the format: one or more uppercase letters then digits, no leading zero
        if not valid_id(task_id):
            print(f"Warning: Task {task_id} has invalid ID format.", file=sys.stderr)
            continue

        # Check that the pickup and drop-off locations exist in our loaded destinations
        if source_id not in destination_ids:
            print(f"Warning: Task {task_id} has unknown source destination ({source_id}).", file=sys.stderr)
            continue
        if target_id not in destination_ids:
            print(f"Warning: Task {task_id} has unknown target destination ({target_id}).", file=sys.stderr)
            continue

        # Check that the package this task references actually exists
        if package_id not in package_ids:
            print(f"Warning: Task {task_id} references unknown package ({package_id}).", file=sys.stderr)
            continue

        # Status must be either pending or complete
        if status not in ["pending", "complete"]:
            print(f"Warning: Task {task_id} has invalid status ({status}).", file=sys.stderr)
            continue

        task["status"] = status
        tasks.append(task)

    return tasks


def read_schedules(schedules_path: str, robot_ids: list, task_ids: list) -> list:
    """
    Loads and validates all schedules from a CSV file.

    Each schedule contains a schedule ID, a robot ID, and one or more task IDs.
    The file has no header row, so read_to_table cannot be used here.
    Any schedule that references an unknown robot or task is skipped and a
    warning is shown in the error log.

    Parameters:
        schedules_path (str): Path to the schedules CSV file.
        robot_ids (list): The known robot IDs to check against.
        task_ids (list): The known task IDs to check against.

    Returns:
        list: A list of valid schedule rows, each as a dictionary with
              schedule_id, robot_id, and task_ids.
    """
    schedules = []

    with open(schedules_path, 'r') as file_schedule:
        for line in file_schedule:
            values = line.strip().split(",")

            schedule_id = values[0].strip()
            robot_id = values[1].strip()

            # Collect all task IDs from the remaining columns
            schedule_task_ids = []
            for i in range(2, len(values)):
                schedule_task_ids.append(values[i].strip())

            if not valid_id(schedule_id):
                print(f"Warning: Schedule {schedule_id} has invalid ID format.", file=sys.stderr)
                continue

            if not valid_id(robot_id):
                print(f"Warning: Schedule {schedule_id} has invalid robot ID ({robot_id}).", file=sys.stderr)
                continue

            # Check the robot exists in our loaded data
            if robot_id not in robot_ids:
                print(f"Warning: Schedule {schedule_id} references unknown robot ({robot_id}).", file=sys.stderr)
                continue

            # Each schedule must have at least one task
            if len(schedule_task_ids) == 0:
                print(f"Warning: Schedule {schedule_id} has no tasks.", file=sys.stderr)
                continue

            # Check every task in the schedule exists in our loaded data
            all_tasks_valid = True
            for task_id in schedule_task_ids:
                if not valid_id(task_id):
                    print(f"Warning: Schedule {schedule_id} has invalid task ID ({task_id}).", file=sys.stderr)
                    all_tasks_valid = False
                    break
                if task_id not in task_ids:
                    print(f"Warning: Schedule {schedule_id} references unknown task ({task_id}).", file=sys.stderr)
                    all_tasks_valid = False
                    break

            if not all_tasks_valid:
                continue

            schedules.append({
                "schedule_id": schedule_id,
                "robot_id": robot_id,
                "task_ids": schedule_task_ids
            })

    return schedules


def read_distances(distances_path: str) -> list:
    """
    Reads a distances CSV file and returns it as a list of lists.

    The file contains an adjacency matrix where row 0 and column 0 represent
    the home base. Each remaining row and column corresponds to a destination.
    No validation is performed on this file.

    Parameters:
        distances_path (str): Path to the distances CSV file.

    Returns:
        list: A list of lists containing distances as floats.
    """
    distances = []

    with open(distances_path, 'r') as file_distances:
        for line in file_distances:
            values = line.strip().split(",")
            row = []

            for value in values:
                row.append(float(value.strip()))

            distances.append(row)

    return distances
