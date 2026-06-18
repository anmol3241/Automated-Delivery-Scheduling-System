import pandas as pd
import matplotlib.pyplot as plt

from reader import read_robots, read_destinations, read_packages, read_tasks, read_schedules, read_distances
from tasker import get_task_results, get_schedule_report


def write_feasability_report(report_path: str, tasks: list, task_results: list, schedules: list, schedule_report: list) -> None:
    """
    Saves a feasibility report to a text file.

    Lists each task and whether it can be carried out, then shows totals.
    Also includes a schedule section showing time, distance and battery
    remaining for each feasible schedule.

    Parameters:
        report_path (str): Path to save the report to.
        tasks (list): All tasks that were checked.
        task_results (list): True/False for each task, in the same order as tasks.
        schedules (list): All schedules that were checked.
        schedule_report (list): Result of check_schedule for each schedule —
                                either a list of tuples or None if infeasible.

    Returns:
        None
    """
    executable_count = 0

    with open(report_path, 'w') as report_file:
        report_file.write("Task Feasibility Report\n\n")

        for i in range(len(tasks)):
            task_id = tasks[i]["task_id"]

            if task_results[i]:
                report_file.write(f"{task_id}: executable\n")
                executable_count += 1
            else:
                report_file.write(f"{task_id}: not executable\n")

        # Write the total summary at the bottom of the task section
        report_file.write("\n")
        report_file.write(f"Executable tasks: {executable_count}\n")
        report_file.write(f"Non-executable tasks: {len(tasks) - executable_count}\n")

        # Write the schedule feasibility section
        report_file.write("\nSchedule feasibility\n\n")

        for i in range(len(schedules)):
            schedule = schedules[i]
            result = schedule_report[i]

            if result is None:
                report_file.write(f"{schedule['schedule_id']}: Infeasible\n")
            else:
                # The last tuple holds the final state — total time, distance and battery
                final_state = result[-1]
                final_time = final_state[0]
                final_distance = final_state[1]
                final_battery = final_state[3]

                report_file.write(
                    f"{schedule['schedule_id']}: Robot {schedule['robot_id']} "
                    f"completed schedule in {final_time:.2f} hours and covered "
                    f"{final_distance:.2f} km. Battery remaining {final_battery:.2f}%.\n"
                )

def plot_schedule_positions(schedules: list, schedule_report: list, plot_file: str) -> None:
    """
    Plots each feasible schedule's distance from the origin over time.

    Only feasible schedules are plotted. Each schedule is shown as a separate
    line labelled by robot ID. The plot is saved to a file.

    Parameters:
        schedules (list): All schedule rows.
        schedule_report (list): Result of check_schedule for each schedule.
        plot_file (str): The file path to save the plot to.

    Returns:
        None
    """
    plt.figure()

    for i in range(len(schedules)):
        schedule = schedules[i]
        result = schedule_report[i]

        # Infeasible schedules have no position data so they are skipped
        if result is not None:
            data = pd.DataFrame(
                result,
                columns=["time", "distance_travelled", "distance_from_origin", "battery"]
            )

            label = schedule["robot_id"]

            plt.plot(data["time"], data["distance_from_origin"], marker="o", label=label)

    plt.title("Robot Distance from Origin Over Time")
    plt.xlabel("Time (hours)")
    plt.ylabel("Distance from Origin (km)")
    plt.grid(True)
    plt.legend()
    plt.savefig(plot_file)
    plt.close()


def main(
    robots_path: str,
    destinations_path: str,
    packages_path: str,
    tasks_path: str,
    schedules_path: str,
    distances_path: str,
    report_path: str,
    plot_file: str
) -> None:
    """
    Runs the full delivery scheduling process from start to finish.

    Loads all CSV files, checks task and schedule feasibility, writes a
    report and saves a plot of feasible schedule paths.

    Parameters:
        robots_path (str): Path to the robots CSV file.
        destinations_path (str): Path to the destinations CSV file.
        packages_path (str): Path to the packages CSV file.
        tasks_path (str): Path to the tasks CSV file.
        schedules_path (str): Path to the schedules CSV file.
        distances_path (str): Path to the distances CSV file.
        report_path (str): Path to save the feasibility report to.
        plot_file (str): Path to save the schedule plot to.

    Returns:
        None
    """
    robots = read_robots(robots_path)
    destinations = read_destinations(destinations_path)
    packages = read_packages(packages_path)

    # Extract IDs from the loaded tables to validate tasks 
    destination_ids = []
    for destination in destinations:
        destination_ids.append(destination["destination_id"])

    package_ids = []
    for package in packages:
        package_ids.append(package["package_id"])

    tasks = read_tasks(tasks_path, destination_ids, package_ids)

    # Extract IDs to validate schedules 
    robot_ids = []
    for robot in robots:
        robot_ids.append(robot["robot_id"])

    task_ids = []
    for task in tasks:
        task_ids.append(task["task_id"])

    schedules = read_schedules(schedules_path, robot_ids, task_ids)
    distances = read_distances(distances_path)

    # Check every task and record whether it can be carried out
    task_results = get_task_results(robots, destinations, packages, tasks)

    # Check every schedule and record the result
    schedule_report = get_schedule_report(schedules, distances, robots, destinations, packages, tasks)

    write_feasability_report(report_path, tasks, task_results, schedules, schedule_report)
    plot_schedule_positions(schedules, schedule_report, plot_file)


if __name__ == "__main__":
    main(
        "robots.csv",
        "destinations.csv",
        "packages.csv",
        "tasks.csv",
        "schedules.csv",
        "distances.csv",
        "feasibility_report.txt",
        "schedule_plot.png"
    )
