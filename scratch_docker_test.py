import subprocess

docker_cmd = [
    "docker", "run",
    "--rm",
    "-i",
    "python:3.12-slim-bookworm",
    "python", "-c", "import sys; print('GOT:', sys.stdin.read())"
]

result = subprocess.run(
    docker_cmd,
    input="hello world\n123",
    capture_output=True,
    text=True
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)

docker_cmd2 = [
    "docker", "run",
    "--rm",
    "-i",
    "python:3.12-slim-bookworm",
    "python", "-c", "print('GOT:', input())"
]

result2 = subprocess.run(
    docker_cmd2,
    input="hello world",
    capture_output=True,
    text=True
)

print("STDOUT2:", result2.stdout)
print("STDERR2:", result2.stderr)
