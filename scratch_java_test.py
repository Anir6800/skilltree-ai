import subprocess
import os

sandbox_path = "C:\\temp\\skilltree\\test_java"
os.makedirs(sandbox_path, exist_ok=True)
with open(os.path.join(sandbox_path, "Main.java"), "w") as f:
    f.write("""
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        System.out.println("GOT: " + s);
    }
}
""")

cmd = ["docker", "run", "--rm", "-i", "-v", f"{sandbox_path}:/sandbox:ro", "-w", "/sandbox", "openjdk:21-slim", "java", "Main.java"]

print("Running Java...")
r = subprocess.run(cmd, input="no newline", capture_output=True, text=True)
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr)

r2 = subprocess.run(cmd, input="with newline\n", capture_output=True, text=True)
print("STDOUT 2:", r2.stdout)
print("STDERR 2:", r2.stderr)
