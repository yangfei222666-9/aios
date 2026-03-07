#!/usr/bin/env python3
"""Coder Agent CLI - code, debug, refactor"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def main():
    parser = argparse.ArgumentParser(description="Coder Agent")
    parser.add_argument("--task", help="task description")
    parser.add_argument("--agent-id", default="coder", help="agent id")
    parser.add_argument("--ping", action="store_true")
    args = parser.parse_args()

    if args.ping:
        print("pong | coder")
        return

    if args.task:
        from task_executor import TaskExecutor
        executor = TaskExecutor()
        result = executor.execute({"type": "code", "description": args.task, "agent_id": args.agent_id})
        print(result)
    else:
        print("Coder Agent ready | code, debug, refactor")

if __name__ == "__main__":
    main()
