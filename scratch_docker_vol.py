import subprocess
import os

sandbox_path = "C:\\temp\\skilltree\\test"
os.makedirs(sandbox_path, exist_ok=True)
with open(os.path.join(sandbox_path, "test.py"), "w") as f:
    f.write("print('Hello from volume')")

# Method 1: /c/temp/...
vol1 = "/c/temp/skilltree/test"
cmd1 = ["docker", "run", "--rm", "-v", f"{vol1}:/sandbox:ro", "python:3.12-slim-bookworm", "python", "/sandbox/test.py"]

print("Running Method 1...")
r1 = subprocess.run(cmd1, capture_output=True, text=True)
print("STDOUT 1:", r1.stdout)
print("STDERR 1:", r1.stderr)

# Method 2: C:\temp\...
vol2 = sandbox_path
cmd2 = ["docker", "run", "--rm", "-v", f"{vol2}:/sandbox:ro", "python:3.12-slim-bookworm", "python", "/sandbox/test.py"]

print("Running Method 2...")
r2 = subprocess.run(cmd2, capture_output=True, text=True)
print("STDOUT 2:", r2.stdout)
print("STDERR 2:", r2.stderr)
