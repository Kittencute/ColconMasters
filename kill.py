import subprocess

processes = [
    "gz sim",
    "parameter_bridge",
    "robot_state_publisher",
    "cartographer",
    "nav2",
    "rviz2",
]

for process in processes:
    subprocess.run(
        ["pkill", "-f", process],
        check=False
    )

print("Simulation processes stopped.")