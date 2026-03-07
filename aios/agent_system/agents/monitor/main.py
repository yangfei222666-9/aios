#!/usr/bin/env python3
"""Monitor Agent CLI - resource monitoring & alerts"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def main():
    parser = argparse.ArgumentParser(description="Monitor Agent")
    parser.add_argument("--ping", action="store_true")
    args = parser.parse_args()

    if args.ping:
        print("pong | monitor")
        return

    print("Monitor Agent ready | resource monitoring & alerts")

if __name__ == "__main__":
    main()
