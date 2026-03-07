#!/usr/bin/env python3
"""Designer Agent CLI - architecture, optimization"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def main():
    parser = argparse.ArgumentParser(description="Designer Agent")
    parser.add_argument("--ping", action="store_true")
    args = parser.parse_args()

    if args.ping:
        print("pong | designer")
        return

    print("Designer Agent ready | architecture, optimization")

if __name__ == "__main__":
    main()
