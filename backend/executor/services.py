"""
Code Execution Service
Handles secure, sandboxed code execution using Docker containers.
"""

import os
import sys
import uuid
import shutil
import subprocess
import time
from typing import Dict, List, Optional, Any
from pathlib import Path


# Language configuration with Docker images and commands
LANGUAGE_CONFIG = {
    "python": {
        "image": "python:3.12-slim-bookworm",
        "run_cmd": ["python", "{file}"],
        "extension": "py"
    },
    "javascript": {
        "image": "node:20-slim",
        "run_cmd": ["node", "{file}"],
        "extension": "js"
    },
    "cpp": {
        "image": "gcc:13",
        "compile_cmd": ["g++", "-O2", "-o", "prog", "{file}"],
        "run_cmd": ["./prog"],
        "extension": "cpp"
    },
    "java": {
        "image": "eclipse-temurin:17-jdk-jammy",
        "compile_cmd": ["javac", "{file}"],
        "run_cmd": ["java", "Main"],
        "extension": "java"
    },
    "go": {
        "image": "golang:1.22-alpine",
        "run_cmd": ["go", "run", "{file}"],
        "extension": "go"
    }
}

# Execution limits
EXECUTION_TIMEOUT_SECONDS = 10
MEMORY_LIMIT_MB = 256
CPU_LIMIT = "0.5"

# Sandbox directory (platform-specific)
if sys.platform == "win32":
    # Use Windows temp directory
    SANDBOX_BASE = os.path.join(os.environ.get("TEMP", "C:\\temp"), "skilltree")
else:
    SANDBOX_BASE = "/tmp/skilltree"


class CompileExecutor:
    """
    Secure code execution engine using Docker containers.
    Provides compilation, execution, and test case validation.
    """

    def __init__(self):
        """Initialize the executor and ensure sandbox directory exists."""
        self._ensure_sandbox_base()

    def _ensure_sandbox_base(self):
        """Create the base sandbox directory if it doesn't exist."""
        os.makedirs(SANDBOX_BASE, exist_ok=True)

    def _validate_language(self, language: str) -> bool:
        """Check if the language is supported."""
        return language.lower() in LANGUAGE_CONFIG

    def _check_docker_available(self) -> bool:
        """Verify Docker is installed and accessible."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _create_sandbox(self) -> tuple[str, Path]:
        """
        Create a unique sandbox directory for execution.
        Returns: (uuid_str, sandbox_path)
        """
        sandbox_id = str(uuid.uuid4())
        sandbox_path = Path(SANDBOX_BASE) / sandbox_id
        sandbox_path.mkdir(parents=True, exist_ok=True)
        return sandbox_id, sandbox_path

    def _cleanup_sandbox(self, sandbox_path: Path):
        """Remove sandbox directory and all contents."""
        try:
            if sandbox_path.exists():
                shutil.rmtree(sandbox_path)
        except Exception as e:
            # Log but don't fail on cleanup errors
            print(f"Warning: Failed to cleanup sandbox {sandbox_path}: {e}")

    def _write_code(self, sandbox_path: Path, code: str, language: str) -> str:
        """
        Write code to sandbox directory.
        Returns: filename
        """
        config = LANGUAGE_CONFIG[language.lower()]
        extension = config["extension"]
        
        # Java requires specific filename
        if language.lower() == "java":
            filename = "Main.java"
        else:
            filename = f"solution.{extension}"
        
        file_path = sandbox_path / filename
        file_path.write_text(code, encoding="utf-8")
        return filename

    def _get_docker_volume_path(self, path: Path) -> str:
        """
        Convert local path to Docker volume mount format.
        On Windows, converts C:\path to /c/path for Docker.
        """
        path_str = str(path.resolve())
        
        if sys.platform == "win32":
            # Convert Windows path to Docker format
            # C:\Users\... -> /c/Users/...
            path_str = path_str.replace("\\", "/")
            if len(path_str) >= 2 and path_str[1] == ":":
                drive = path_str[0].lower()
                path_str = f"/{drive}{path_str[2:]}"
        
        return path_str

    def _compile_code(
        self,
        sandbox_path: Path,
        language: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Compile code if needed (C++, Java).
        Returns: {"success": bool, "stderr": str}
        """
        config = LANGUAGE_CONFIG[language.lower()]
        
        # Check if compilation is needed
        if "compile_cmd" not in config:
            return {"success": True, "stderr": ""}

        compile_cmd = [cmd.format(file=filename) for cmd in config["compile_cmd"]]
        docker_volume = self._get_docker_volume_path(sandbox_path)
        
        docker_cmd = [
            "docker", "run",
            "--rm",
            "-v", f"{docker_volume}:/sandbox",
            "-w", "/sandbox",
            config["image"]
        ] + compile_cmd

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                timeout=30,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stderr": "Compilation timeout exceeded"
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": f"Compilation error: {str(e)}"
            }

    def _execute_code(
        self,
        sandbox_path: Path,
        language: str,
        filename: str,
        stdin_input: str = ""
    ) -> Dict[str, Any]:
        """
        Execute code in sandboxed Docker container.
        Returns: execution result dictionary
        """
        config = LANGUAGE_CONFIG[language.lower()]
        run_cmd = [cmd.format(file=filename) for cmd in config["run_cmd"]]
        docker_volume = self._get_docker_volume_path(sandbox_path)
        
        docker_cmd = [
            "docker", "run",
            "--rm",
            "-i",  # Interactive mode for stdin
            "--network=none",
            f"--memory={MEMORY_LIMIT_MB}m",
            f"--cpus={CPU_LIMIT}",
            "--read-only",
            "-v", f"{docker_volume}:/sandbox:ro",
            "-w", "/sandbox",
            config["image"]
        ] + run_cmd

        start_time = time.time()
        
        try:
            result = subprocess.run(
                docker_cmd,
                input=stdin_input,
                capture_output=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                text=True
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Determine status
            if result.returncode == 0:
                status = "ok"
            elif result.returncode == 137:  # SIGKILL (memory limit)
                status = "mle"
            else:
                status = "runtime_error"
            
            return {
                "output": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "execution_time_ms": execution_time_ms,
                "status": status
            }
            
        except subprocess.TimeoutExpired:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "output": "",
                "stderr": "Time limit exceeded",
                "exit_code": -1,
                "execution_time_ms": execution_time_ms,
                "status": "tle"
            }
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "output": "",
                "stderr": f"Execution error: {str(e)}",
                "exit_code": -1,
                "execution_time_ms": execution_time_ms,
                "status": "runtime_error"
            }

    def execute(
        self,
        code: str,
        language: str,
        stdin_input: str = ""
    ) -> Dict[str, Any]:
        """
        Execute code with full compilation and execution pipeline.
        
        Args:
            code: Source code to execute
            language: Programming language (python, javascript, cpp, java, go)
            stdin_input: Optional input to pass to the program
            
        Returns:
            Dictionary with execution results
        """
        # Validate inputs
        if not code or not code.strip():
            return {
                "output": "",
                "stderr": "Empty code provided",
                "exit_code": -1,
                "execution_time_ms": 0,
                "status": "runtime_error"
            }
        
        if not self._validate_language(language):
            return {
                "output": "",
                "stderr": f"Unsupported language: {language}",
                "exit_code": -1,
                "execution_time_ms": 0,
                "status": "runtime_error"
            }
        
        if not self._check_docker_available():
            return {
                "output": "",
                "stderr": "Docker is not available",
                "exit_code": -1,
                "execution_time_ms": 0,
                "status": "runtime_error"
            }
        
        sandbox_id, sandbox_path = self._create_sandbox()
        
        try:
            # Write code to sandbox
            filename = self._write_code(sandbox_path, code, language)
            
            # Compile if needed
            compile_result = self._compile_code(sandbox_path, language, filename)
            if not compile_result["success"]:
                return {
                    "output": "",
                    "stderr": compile_result["stderr"],
                    "exit_code": 1,
                    "execution_time_ms": 0,
                    "status": "compile_error"
                }
            
            # Execute code
            return self._execute_code(sandbox_path, language, filename, stdin_input)
            
        finally:
            # Always cleanup sandbox
            self._cleanup_sandbox(sandbox_path)

    def run_test_cases(
        self,
        code: str,
        language: str,
        test_cases: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Run code against multiple test cases.
        
        Args:
            code: Source code to test
            language: Programming language
            test_cases: List of {"input": str, "expected": str} dictionaries
            
        Returns:
            Dictionary with test results
        """
        if not test_cases:
            return {
                "tests_passed": 0,
                "tests_total": 0,
                "results": []
            }
        
        results = []
        tests_passed = 0
        
        for test_case in test_cases:
            test_input = test_case.get("input", "")
            expected_output = test_case.get("expected", "").strip()
            
            # Execute code with test input
            exec_result = self.execute(code, language, test_input)
            
            # Check if execution was successful
            if exec_result["status"] != "ok":
                results.append({
                    "input": test_input,
                    "expected": expected_output,
                    "actual": exec_result["stderr"],
                    "passed": False,
                    "time_ms": exec_result["execution_time_ms"],
                    "status": exec_result["status"]
                })
                continue
            
            # Compare output
            actual_output = exec_result["output"].strip()
            passed = actual_output == expected_output
            
            if passed:
                tests_passed += 1
            
            results.append({
                "input": test_input,
                "expected": expected_output,
                "actual": actual_output,
                "passed": passed,
                "time_ms": exec_result["execution_time_ms"],
                "status": "ok"
            })
        
        return {
            "tests_passed": tests_passed,
            "tests_total": len(test_cases),
            "results": results
        }


# Singleton instance
executor = CompileExecutor()
