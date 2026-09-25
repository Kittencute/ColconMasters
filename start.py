import subprocess
import os
import signal
import time

workspace = os.path.expanduser("~/turtlebot3_ws_mx")

command = f"""
source /opt/ros/jazzy/setup.bash
source {workspace}/install/setup.bash

export TURTLEBOT3_MODEL=burger_cam
export GZ_SIM_RESOURCE_PATH={workspace}/install/turtlebot3_gazebo/share/turtlebot3_gazebo/models${{GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}}

ros2 launch my_turtlebot3 mapping_cam.launch.py
"""

process = subprocess.Popen(
    ["bash", "-c", command],
    cwd=workspace,
    start_new_session=True
)

try:
    # time.sleep(5)

    # subprocess.Popen([
    #     "gnome-terminal",
    #     "--",
    #     "bash",
    #     "-c",
    #     f"""
    #     source /opt/ros/jazzy/setup.bash
    #     source {workspace}/install/setup.bash
    #     export TURTLEBOT3_MODEL=burger_cam
    #     ros2 run turtlebot3_teleop teleop_keyboard
    #     exec bash
    #     """
    # ])

    process.wait()

except KeyboardInterrupt:
    print("\nStopping simulation...")

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGINT)
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print("ROS did not stop cleanly, sending SIGTERM...")
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Force killing remaining processes...")
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)

    print("Simulation stopped.")