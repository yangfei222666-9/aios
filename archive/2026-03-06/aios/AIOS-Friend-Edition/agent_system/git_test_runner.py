#!/usr/bin/env python3
"""
AIOS Git Commit Auto-Testing System
Detects new commits, runs pytest, analyzes results, and logs events.
"""

import json
import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configuration
REPO_PATH = Path(r"C:\Users\A\.openclaw\workspace")
AGENT_SYSTEM_PATH = REPO_PATH / "aios" / "agent_system"
STATE_FILE = AGENT_SYSTEM_PATH / "git_test_state.json"
EVENTS_FILE = AGENT_SYSTEM_PATH / "git_test_events.jsonl"
GIT_EXE = r"C:\Program Files\Git\bin\git.exe"

try:
    from notifier import test_passed, test_failed
    HAS_NOTIFIER = True
except ImportError:
    HAS_NOTIFIER = False
PYTHON_EXE = r"C:\Program Files\Python312\python.exe"
TEST_PATHS = [
    "aios/tests/test_event_bus.py",
    "aios/tests/test_circuit_breaker.py",
]
TEST_TIMEOUT = 60


class GitTestRunner:
    def __init__(self):
        self.repo_path = REPO_PATH
        self.state_file = STATE_FILE
        self.events_file = EVENTS_FILE
        
    def _run_command(self, cmd: List[str], timeout: int = 30, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Run a command and return (returncode, stdout, stderr)"""
        import tempfile
        stdout_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False, encoding='utf-8')
        stderr_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False, encoding='utf-8')
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.repo_path,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=timeout
            )
            stdout_file.close()
            stderr_file.close()
            with open(stdout_file.name, 'r', encoding='utf-8', errors='replace') as f:
                stdout = f.read()
            with open(stderr_file.name, 'r', encoding='utf-8', errors='replace') as f:
                stderr = f.read()
            return result.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            stdout_file.close()
            stderr_file.close()
            return -1, "", "Command timeout"
        except Exception as e:
            stdout_file.close()
            stderr_file.close()
            return -1, "", str(e)
        finally:
            import os
            try: os.unlink(stdout_file.name)
            except: pass
            try: os.unlink(stderr_file.name)
            except: pass
    
    def _log_event(self, event: Dict):
        """Append event to JSONL log"""
        event['timestamp'] = datetime.now().isoformat()
        try:
            with open(self.events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Warning: Failed to log event: {e}")
    
    def _load_state(self) -> Dict:
        """Load state from JSON file"""
        if not self.state_file.exists():
            return {"last_commit": None, "last_result": None}
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"last_commit": None, "last_result": None}
    
    def _save_state(self, state: Dict):
        """Save state to JSON file"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save state: {e}")
    
    def get_current_commit(self) -> Optional[Dict[str, str]]:
        """Get current commit hash, author, and message"""
        code, stdout, stderr = self._run_command([GIT_EXE, "log", "-1", "--format=%H|%an|%s"])
        if code != 0:
            print(f"Error getting commit: {stderr}")
            return None
        
        parts = stdout.strip().split('|', 2)
        if len(parts) != 3:
            return None
        
        return {
            "hash": parts[0],
            "author": parts[1],
            "message": parts[2]
        }
    
    def run_tests(self) -> Dict:
        """Run pytest and parse results"""
        print("Running tests...")
        
        cmd = [PYTHON_EXE, "-m", "pytest"] + TEST_PATHS + ["-v", "--tb=short", "-x", "--no-header", "-p", "no:cacheprovider", "-p", "no:cov"]
        code, stdout, stderr = self._run_command(cmd, timeout=TEST_TIMEOUT)
        
        # Parse pytest output
        result = {
            "returncode": code,
            "stdout": stdout,
            "stderr": stderr,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "duration": 0.0,
            "failures": []
        }
        
        # Handle case where no tests are collected
        if "collected 0 items" in stdout:
            result["total"] = 0
            result["duration"] = 0.1
            return result
        
        # Extract summary line (e.g., "= 12 passed, 2 failed in 3.45s =")
        summary_pattern = r'=+\s*(?:(\d+)\s+passed)?[,\s]*(?:(\d+)\s+failed)?[,\s]*(?:(\d+)\s+error)?.*?in\s+([\d.]+)s?\s*=+'
        match = re.search(summary_pattern, stdout)
        if match:
            result["passed"] = int(match.group(1) or 0)
            result["failed"] = int(match.group(2) or 0)
            result["errors"] = int(match.group(3) or 0)
            result["duration"] = float(match.group(4) or 0)
            result["total"] = result["passed"] + result["failed"] + result["errors"]
        
        # Alternative: Look for Chinese summary format
        if result["total"] == 0:
            cn_pattern = r'总计:\s*(\d+)\s*\|\s*✅\s*(\d+)\s*\|\s*❌\s*(\d+)'
            match = re.search(cn_pattern, stdout)
            if match:
                result["total"] = int(match.group(1))
                result["passed"] = int(match.group(2))
                result["failed"] = int(match.group(3))
        
        # Extract failed test details
        if result["failed"] > 0 or result["errors"] > 0:
            # Pattern: FAILED test_file.py::test_name - ErrorType: message
            failure_pattern = r'FAILED\s+([\w/_.]+)::([\w_]+)\s*-\s*(\w+)(?::\s*(.+))?'
            for match in re.finditer(failure_pattern, stdout):
                result["failures"].append({
                    "file": match.group(1),
                    "test": match.group(2),
                    "error_type": match.group(3),
                    "message": (match.group(4) or "").strip()
                })
        
        return result
    
    def analyze_failures(self, failures: List[Dict]) -> str:
        """Generate suggestions based on failure patterns"""
        if not failures:
            return ""
        
        suggestions = []
        error_types = [f["error_type"] for f in failures]
        
        if "AssertionError" in error_types:
            suggestions.append("Check assertion logic and expected values")
        if "TimeoutError" in error_types or "Timeout" in error_types:
            suggestions.append("Review async operations or increase timeout limits")
        if "AttributeError" in error_types:
            suggestions.append("Verify object attributes and initialization")
        if "ImportError" in error_types or "ModuleNotFoundError" in error_types:
            suggestions.append("Check module dependencies and import paths")
        
        # Check for common file patterns
        files = [f["file"] for f in failures]
        if any("scheduler" in f.lower() for f in files):
            suggestions.append("Review scheduler priority and task queue logic")
        if any("reactor" in f.lower() for f in files):
            suggestions.append("Check reactor event handling and state management")
        
        return "; ".join(suggestions) if suggestions else "Review test logs for details"
    
    def format_result(self, commit: Dict, test_result: Dict) -> str:
        """Format test result for display"""
        commit_short = commit["hash"][:7]
        passed = test_result["passed"]
        failed = test_result["failed"]
        errors = test_result["errors"]
        total = test_result["total"]
        duration = test_result["duration"]
        
        if failed == 0 and errors == 0:
            output = f"[PASS] Commit {commit_short} - All tests passed ({passed}/{total}, {duration:.1f}s)\n"
        else:
            output = f"[FAIL] Commit {commit_short} - Tests failed ({passed}/{total}, {duration:.1f}s)\n"
        
        output += f"   Author: {commit['author']}\n"
        output += f"   Message: {commit['message']}\n"
        
        if test_result["failures"]:
            output += "\n   Failed tests:\n"
            for failure in test_result["failures"]:
                output += f"   - {failure['file']}::{failure['test']} - {failure['error_type']}\n"
            
            suggestion = self.analyze_failures(test_result["failures"])
            if suggestion:
                output += f"\n   Suggestion: {suggestion}\n"
        
        return output
    
    def check(self) -> bool:
        """Check for new commits and run tests if found"""
        state = self._load_state()
        current_commit = self.get_current_commit()
        
        if not current_commit:
            print("Error: Could not get current commit")
            return False
        
        if state["last_commit"] == current_commit["hash"]:
            print(f"No new commits (current: {current_commit['hash'][:7]})")
            return True
        
        print(f"New commit detected: {current_commit['hash'][:7]}")
        self._log_event({
            "type": "git.new_commit",
            "commit": current_commit["hash"],
            "author": current_commit["author"],
            "message": current_commit["message"]
        })
        
        # Run tests
        self._log_event({"type": "test.started", "commit": current_commit["hash"]})
        test_result = self.run_tests()
        
        # Log result
        if test_result["failed"] == 0 and test_result["errors"] == 0:
            self._log_event({
                "type": "test.completed",
                "commit": current_commit["hash"],
                "passed": test_result["passed"],
                "failed": test_result["failed"],
                "errors": test_result["errors"],
                "duration": test_result["duration"]
            })
            if HAS_NOTIFIER and test_result["passed"] > 0:
                test_passed(current_commit["hash"], current_commit["author"],
                           current_commit["message"], test_result["passed"],
                           test_result["passed"] + test_result["failed"],
                           test_result["duration"])
        else:
            self._log_event({
                "type": "test.failed",
                "commit": current_commit["hash"],
                "passed": test_result["passed"],
                "failed": test_result["failed"],
                "errors": test_result["errors"],
                "failures": test_result["failures"]
            })
            if HAS_NOTIFIER:
                test_failed(current_commit["hash"], current_commit["author"],
                           current_commit["message"], test_result["passed"],
                           test_result["failed"],
                           test_result["passed"] + test_result["failed"],
                           test_result["duration"], test_result["failures"])
        
        # Display result
        print("\n" + self.format_result(current_commit, test_result))
        
        # Update state
        state["last_commit"] = current_commit["hash"]
        state["last_result"] = {
            "commit": current_commit,
            "test_result": test_result
        }
        self._save_state(state)
        
        return test_result["failed"] == 0 and test_result["errors"] == 0
    
    def status(self):
        """Show last test result"""
        state = self._load_state()
        
        if not state.get("last_result"):
            print("No test results yet. Run 'check' or 'run' first.")
            return
        
        last = state["last_result"]
        print(self.format_result(last["commit"], last["test_result"]))
    
    def run(self) -> bool:
        """Force run tests on current commit"""
        current_commit = self.get_current_commit()
        
        if not current_commit:
            print("Error: Could not get current commit")
            return False
        
        print(f"Running tests for commit: {current_commit['hash'][:7]}")
        self._log_event({"type": "test.started", "commit": current_commit["hash"]})
        
        test_result = self.run_tests()
        
        # Log result
        if test_result["failed"] == 0 and test_result["errors"] == 0:
            self._log_event({
                "type": "test.completed",
                "commit": current_commit["hash"],
                "passed": test_result["passed"],
                "failed": test_result["failed"],
                "errors": test_result["errors"],
                "duration": test_result["duration"]
            })
            if HAS_NOTIFIER and test_result["passed"] > 0:
                test_passed(current_commit["hash"], current_commit["author"],
                           current_commit["message"], test_result["passed"],
                           test_result["passed"] + test_result["failed"],
                           test_result["duration"])
        else:
            self._log_event({
                "type": "test.failed",
                "commit": current_commit["hash"],
                "passed": test_result["passed"],
                "failed": test_result["failed"],
                "errors": test_result["errors"],
                "failures": test_result["failures"]
            })
            if HAS_NOTIFIER:
                test_failed(current_commit["hash"], current_commit["author"],
                           current_commit["message"], test_result["passed"],
                           test_result["failed"],
                           test_result["passed"] + test_result["failed"],
                           test_result["duration"], test_result["failures"])
        
        # Display result
        print("\n" + self.format_result(current_commit, test_result))
        
        # Update state
        state = self._load_state()
        state["last_commit"] = current_commit["hash"]
        state["last_result"] = {
            "commit": current_commit,
            "test_result": test_result
        }
        self._save_state(state)
        
        return test_result["failed"] == 0 and test_result["errors"] == 0
    
    def history(self):
        """Show last 10 test events"""
        if not self.events_file.exists():
            print("No history yet.")
            return
        
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                events = [json.loads(line) for line in f]
        except Exception as e:
            print(f"Error reading history: {e}")
            return
        
        # Filter test completion/failure events
        test_events = [e for e in events if e["type"] in ("test.completed", "test.failed")]
        recent = test_events[-10:]
        
        if not recent:
            print("No test results in history.")
            return
        
        print("Recent test results:\n")
        for event in recent:
            commit_short = event["commit"][:7]
            timestamp = event["timestamp"][:19]  # Remove microseconds
            passed = event.get("passed", 0)
            failed = event.get("failed", 0)
            errors = event.get("errors", 0)
            total = passed + failed + errors
            duration = event.get("duration", 0)
            
            status = "[PASS]" if event["type"] == "test.completed" else "[FAIL]"
            print(f"{status} {timestamp} | {commit_short} | {passed}/{total} passed | {duration:.1f}s")


def main():
    if len(sys.argv) < 2:
        print("Usage: python git_test_runner.py <command>")
        print("\nCommands:")
        print("  check    - Check for new commits and run tests")
        print("  status   - Show last test result")
        print("  history  - Show recent test history (last 10)")
        print("  run      - Force run tests on current commit")
        sys.exit(1)
    
    runner = GitTestRunner()
    command = sys.argv[1].lower()
    
    try:
        if command == "check":
            success = runner.check()
            sys.exit(0 if success else 1)
        elif command == "status":
            runner.status()
        elif command == "history":
            runner.history()
        elif command == "run":
            success = runner.run()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
