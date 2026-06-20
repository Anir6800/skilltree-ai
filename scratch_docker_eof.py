import subprocess
import time

start = time.time()
docker_cmd = [
    "docker", "run",
    "--rm",
    "-i",
    "python:3.12-slim-bookworm",
    "python", "-c", "try:\n print('Got:', input())\nexcept EOFError:\n print('EOF')"
]

print("Running docker run -i ...")
result = subprocess.run(
    docker_cmd,
    input="",
    capture_output=True,
    text=True
)
elapsed = time.time() - start

print("STDOUT:", repr(result.stdout))
print("STDERR:", repr(result.stderr))
print(f"Time: {elapsed:.2f}s")
