#!/usr/bin/env python3
"""Evolution Agent CLI
启动自我改进闭环（可单次运行 / 诊断）
"""

import argparse
import sys
from pathlib import Path

# allow relative imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from self_improving_loop import SelfImprovingLoop


def main():
    parser = argparse.ArgumentParser(description="Evolution Agent CLI")
    parser.add_argument("--agent-id", default="evolution", help="target agent id")
    parser.add_argument("--check", action="store_true", help="only check if improvement should run")
    parser.add_argument("--run-once", action="store_true", help="run improvement cycle once")
    args = parser.parse_args()

    loop = SelfImprovingLoop()

    if args.check:
        should = loop.should_run_improvement(args.agent_id)
        print(f"should_run_improvement={should}")
        return

    if args.run_once:
        applied = loop._run_improvement_cycle(args.agent_id)
        print(f"applied_improvements={applied}")
        return

    # default: just check and run if needed
    if loop.should_run_improvement(args.agent_id):
        applied = loop._run_improvement_cycle(args.agent_id)
        print(f"applied_improvements={applied}")
    else:
        print("no_improvement_needed")


if __name__ == "__main__":
    main()
