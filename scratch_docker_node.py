import subprocess
import time

start = time.time()
docker_cmd = [
    "docker", "run",
    "--rm",
    "-i",
    "node:20-slim",
    "node", "-e", "const fs = require('fs'); try { console.log('GOT:', fs.readFileSync(0, 'utf-8')); } catch (e) { console.log('Error', e); }"
]

print("Running docker run -i ...")
result = subprocess.run(
    docker_cmd,
    input="node test\n",
    capture_output=True,
    text=True
)
elapsed = time.time() - start

print("STDOUT:", repr(result.stdout))
print("STDERR:", repr(result.stderr))
print(f"Time: {elapsed:.2f}s")
