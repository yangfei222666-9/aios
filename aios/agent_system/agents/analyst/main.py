#!/usr/bin/env python3
"""Analyst Agent CLI - analysis, report, insight"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def main():
    parser = argparse.ArgumentParser(description="Analyst Agent")
    parser.add_argument("--ping", action="store_true")
    args = parser.parse_args()

    if args.ping:
        print("pong | analyst")
        return

    print("Analyst Agent ready | analysis, report, insight")

if __name__ == "__main__":
    main()
