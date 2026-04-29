
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(os.getcwd())

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from executor.services import CompileExecutor

def test_executor():
    executor = CompileExecutor()
    print(f"Docker available: {executor._check_docker_available()}")
    
    code = "print('Hello World')"
    language = "python"
    
    print("\nExecuting simple print...")
    result = executor.execute(code, language)
    print(f"Result: {result}")
    
    code_fib = """
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)
print(fib(10))
"""
    print("\nExecuting Fibonacci print...")
    result_fib = executor.execute(code_fib, language)
    print(f"Result: {result_fib}")

if __name__ == "__main__":
    test_executor()
