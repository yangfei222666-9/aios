#!/usr/bin/env python3
"""Reactor Agent CLI
负责回滚/修复类任务触发入口
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from auto_rollback import AutoRollback


def main():
    parser = argparse.ArgumentParser(description="Reactor Agent CLI")
    parser.add_argument("--rollback", action="store_true", help="trigger rollback")
    parser.add_argument("--agent-id", help="agent id")
    parser.add_argument("--backup-id", help="backup id")
    args = parser.parse_args()

    if not args.rollback:
        print("Reactor Agent started | rollback, fix, recovery")
        return

    if not (args.agent_id and args.backup_id):
        print("Missing --agent-id or --backup-id")
        return

    rollback = AutoRollback()
    result = rollback.rollback(args.agent_id, args.backup_id)
    print(result)


if __name__ == "__main__":
    main()
