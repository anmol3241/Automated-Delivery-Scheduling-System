def find_robot(robot_id: str, robots: list) -> dict:
    """Finds and returns a robot by its ID. Returns an empty dict if not found."""
    for robot in robots:
        if robot["robot_id"] == robot_id:
            return robot
    return {}


def find_destination(destination_id: str, destinations: list) -> dict:
    """Finds and returns a destination by its ID. Returns an empty dict if not found."""
    for destination in destinations:
        if destination["destination_id"] == destination_id:
            return destination
    return {}


def find_package(package_id: str, packages: list) -> dict:
    """Finds and returns a package by its ID. Returns an empty dict if not found."""
    for package in packages:
        if package["package_id"] == package_id:
            return package
    return {}


def find_task(task_id: str, tasks: list) -> dict:
    """Finds and returns a task by its ID. Returns an empty dict if not found."""
    for task in tasks:
        if task["task_id"] == task_id:
            return task
    return {}


def get_destination_index(destination_id: str, destinations: list) -> int:
    """
    Finds where a destination sits in the distance matrix.

    The home base takes up position 0, so every destination starts at position 1.
    Returns -1 if the destination cannot be found.

    Parameters:
        destination_id (str): The destination ID to look up.
        destinations (list): All known destinations.

    Returns:
        int: The index in the distance matrix, or -1 if not found.
    """
    for i in range(len(destinations)):
        if destinations[i]["destination_id"] == destination_id:
            return i + 1  
    return -1


def travel(from_index: int, to_index: int, weight: float, carrying_package: bool, battery: float, time: float, total_distance: float, distances: list) -> tuple:
    """
    Moves the robot from one location to another and updates its state.

    The robot always flies at 15 km/h. Battery drains at 1% per km when empty,
    with an extra 0.5% per kg per km added when carrying a package.

    Parameters:
        from_index (int): Starting position in the distance matrix.
        to_index (int): Destination position in the distance matrix.
        weight (float): Weight of the package being carried (0 if empty).
        carrying_package (bool): Whether the robot is carrying a package.
        battery (float): Current battery level as a percentage.
        time (float): Time elapsed so far in hours.
        total_distance (float): Total distance travelled so far in km.
        distances (list): The full distance matrix.

    Returns:
        tuple: Updated (time, total_distance, distance_from_origin, battery).
    """
    distance = distances[from_index][to_index]
    time = time + distance / 15.0
    total_distance = total_distance + distance

    if carrying_package:
        battery_loss = distance * (1.0 + 0.5 * weight)
    else:
        battery_loss = distance * 1.0

    battery = battery - battery_loss
    distance_from_origin = distances[0][to_index]

    return time, total_distance, distance_from_origin, battery


def can_robot_do_task(robot: dict, task: dict, destinations: list, packages: list) -> bool:
    """
    Checks if a robot can carry out a single task.

    The robot must be in the same zone as both locations and be able to
    carry the package weight.

    Parameters:
        robot (dict): The robot to check.
        task (dict): The task to check.
        destinations (list): All known destinations.
        packages (list): All known packages.

    Returns:
        bool: True if the robot can do the task, False otherwise.
    """
    source = find_destination(task["source_id"], destinations)
    target = find_destination(task["target_id"], destinations)
    package = find_package(task["package_id"], packages)

    if robot["zone"] != source["zone"]:
        return False
    if robot["zone"] != target["zone"]:
        return False
    if robot["max_load"] < package["weight"]:
        return False

    return True


def is_task_executable(task: dict, robots: list, destinations: list, packages: list) -> bool:
    """
    Checks whether a task can be carried out by any robot in the fleet.

    A task can be carried out if there is at least one robot that is in the
    same zone as both the pickup and drop-off locations, and can carry the
    weight of the package.

    Parameters:
        task (dict): The task to check.
        robots (list): All available robots.
        destinations (list): All known destinations.
        packages (list): All known packages.

    Returns:
        bool: True if at least one robot can carry out the task, False if none can.
    """
    for robot in robots:
        if can_robot_do_task(robot, task, destinations, packages):
            return True
    return False


def get_task_results(robots: list, destinations: list, packages: list, tasks: list) -> list:
    """
    Checks every task and returns whether each one can be carried out.

    True means at least one robot can do the task. False means none can.

    Parameters:
        robots (list): All available robots.
        destinations (list): All known destinations.
        packages (list): All known packages.
        tasks (list): All tasks to check.

    Returns:
        list: A list of booleans in the same order as tasks.
    """
    results = []
    for task in tasks:
        results.append(is_task_executable(task, robots, destinations, packages))
    return results


def check_schedule(schedule: dict, distances: list, robots: list, destinations: list, packages: list, tasks: list) -> list:
    """
    Checks whether a schedule can be completed and returns the robot's state after each move.

    A schedule is feasible if the robot can carry every package, stays in the
    right zone for all destinations, and never runs out of battery before
    returning home.

    Parameters:
        schedule (dict): The schedule to check, containing robot_id and task_ids.
        distances (list): The distance matrix — row/col 0 is home base.
        robots (list): All available robots.
        destinations (list): All known destinations.
        packages (list): All known packages.
        tasks (list): All known tasks.

    Returns:
        list: A list of tuples showing the robot's state after each move —
              (time in hours, total distance in km, distance from home in km, battery %).
              Returns None if the schedule cannot be completed.
    """
    robot = find_robot(schedule["robot_id"], robots)

    battery = float(robot["battery_level"])
    time = 0.0
    total_distance = 0.0
    current_index = 0  

    # Record the robot's starting state
    states = [(time, total_distance, 0.0, battery)]

    for task_id in schedule["task_ids"]:
        task = find_task(task_id, tasks)
        package = find_package(task["package_id"], packages)
        source = find_destination(task["source_id"], destinations)
        target = find_destination(task["target_id"], destinations)

        # All destinations must be in the same zone as the robot
        if robot["zone"] != source["zone"] or robot["zone"] != target["zone"]:
            return None

        # Robot must be able to carry the package
        if robot["max_load"] < package["weight"]:
            return None

        source_index = get_destination_index(task["source_id"], destinations)
        target_index = get_destination_index(task["target_id"], destinations)

        # Travel from the current location to the source with no load
        time, total_distance, dist_from_origin, battery = travel(
            current_index, source_index, 0.0, False,
            battery, time, total_distance, distances
        )

        # Battery cannot reach 0 mid journey
        if battery <= 0:
            return None

        states.append((time, total_distance, dist_from_origin, battery))
        current_index = source_index

        # Moving from source to target while the robot carries the package
        time, total_distance, dist_from_origin, battery = travel(
            current_index, target_index, package["weight"], True,
            battery, time, total_distance, distances
        )

        # Battery cannot reach 0 mid journey
        if battery <= 0:
            return None

        states.append((time, total_distance, dist_from_origin, battery))
        current_index = target_index

    # Return to the home base once all tasks are done
    time, total_distance, dist_from_origin, battery = travel(
        current_index, 0, 0.0, False,
        battery, time, total_distance, distances
    )

    # Battery can reach exactly 0 at home but not go below
    if battery < 0:
        return None

    states.append((time, total_distance, 0.0, battery))

    return states


def get_schedule_report(schedules: list, distances: list, robots: list, destinations: list, packages: list, tasks: list) -> list:
    """
    Runs check_schedule on every schedule and collects the results.

    Each result is either a list of robot state tuples if the schedule is
    feasible, or None if it cannot be completed.

    Parameters:
        schedules (list): All schedules to check.
        distances (list): The full distance matrix.
        robots (list): All available robots.
        destinations (list): All known destinations.
        packages (list): All known packages.
        tasks (list): All known tasks.

    Returns:
        list: A list where each item is either a list of state tuples or None.
    """
    schedule_report = []
    for schedule in schedules:
        schedule_report.append(
            check_schedule(schedule, distances, robots, destinations, packages, tasks)
        )
    return schedule_report
