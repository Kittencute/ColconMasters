import subprocess
import os

workspace = os.path.expanduser("~/turtlebot3_ws_mx")

subprocess.run(
    ["colcon", "build", "--symlink-install"],
    cwd=workspace,
    check=True
)

print("Build complete.")