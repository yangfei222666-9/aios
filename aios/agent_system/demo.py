"""
AIOS Demo - Minimal Mock Executor
Shows how AIOS routes tasks to agents and tracks results.
"""
import time

tasks = [
    ("Analyze Python code quality", "coder"),
    ("Monitor system resources", "monitor"),
    ("Analyze error logs", "analyst")
]

print("AIOS Demo Runtime")
print("------------------")

for desc, router in tasks:
    start = time.time()
    time.sleep(1)  # Mock execution
    
    print(f"\n[TASK] {desc}")
    print(f"  Router: {router}")
    print(f"  Agent: {router}_agent")
    
    # Mock results
    results = {
        "coder": "Code looks clean. Suggest adding type hints.",
        "monitor": "CPU 12% | RAM 6.1GB/32GB",
        "analyst": "Pattern detected: retry loop in error logs"
    }
    
    print(f"  Result: {results[router]}")
    print(f"  Time: {round(time.time()-start, 1)}s")

print("\nDemo completed [OK]")
