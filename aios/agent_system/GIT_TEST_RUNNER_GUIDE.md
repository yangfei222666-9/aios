# Git Test Runner Guide

Automated testing system for AIOS repository that detects new commits and runs pytest automatically.

## Quick Start

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system

# Check for new commits and run tests
python git_test_runner.py check

# View last test result
python git_test_runner.py status

# View test history
python git_test_runner.py history

# Force run tests (ignore commit check)
python git_test_runner.py run
```

## Commands

### `check`
Checks if there's a new commit since last run. If yes, runs pytest and logs results.

**Example output:**
```
New commit detected: abc1234
Running tests...

[PASS] Commit abc1234 - All tests passed (45/45, 12.3s)
   Author: yangfei222666-9
   Message: fix scheduler priority
```

Or if tests fail:
```
New commit detected: def5678
Running tests...

[FAIL] Commit def5678 - Tests failed (43/45, 15.1s)
   Author: yangfei222666-9
   Message: refactor reactor
   
   Failed tests:
   - test_scheduler.py::test_priority - AssertionError
   - test_reactor.py::test_rollback - TimeoutError
   
   Suggestion: Check scheduler priority and task queue logic; Review async operations or increase timeout limits
```

### `status`
Shows the most recent test result without running tests again.

### `history`
Displays the last 10 test runs with timestamps and pass/fail status.

**Example output:**
```
Recent test results:

[PASS] 2026-02-27T14:30:22 | abc1234 | 45/45 passed | 12.3s
[FAIL] 2026-02-27T13:15:10 | def5678 | 43/45 passed | 15.1s
[PASS] 2026-02-27T12:00:05 | 9ab0cde | 45/45 passed | 11.8s
```

### `run`
Forces a test run on the current commit, regardless of whether it's new.

## Files

- **git_test_runner.py** - Main script
- **git_test_state.json** - Tracks last checked commit and result
- **git_test_events.jsonl** - Event log (all test runs and commits)

## Event Log Format

The `git_test_events.jsonl` file contains one JSON object per line:

```json
{"timestamp": "2026-02-27T14:30:15", "type": "git.new_commit", "commit": "abc1234...", "author": "yangfei222666-9", "message": "fix scheduler"}
{"timestamp": "2026-02-27T14:30:16", "type": "test.started", "commit": "abc1234..."}
{"timestamp": "2026-02-27T14:30:28", "type": "test.completed", "commit": "abc1234...", "passed": 45, "failed": 0, "errors": 0, "duration": 12.3}
```

Event types:
- `git.new_commit` - New commit detected
- `test.started` - Test run started
- `test.completed` - All tests passed
- `test.failed` - Some tests failed (includes failure details)

## Integration

### Manual Checks
Run `python git_test_runner.py check` periodically (e.g., after git pull).

### Automated Checks
Add to a scheduled task or cron job:

**Windows Task Scheduler:**
```
Program: C:\Program Files\Python312\python.exe
Arguments: C:\Users\A\.openclaw\workspace\aios\agent_system\git_test_runner.py check
Start in: C:\Users\A\.openclaw\workspace
```

### Git Hook
Add to `.git/hooks/post-merge`:

```bash
#!/bin/sh
cd C:/Users/A/.openclaw/workspace/aios/agent_system
python git_test_runner.py check
```

## Troubleshooting

### "Could not get current commit"
- Ensure Git is installed at `C:\Program Files\Git\bin\git.exe`
- Check that you're in a valid Git repository

### "No module named pytest"
- Install pytest: `pip install pytest`
- Or ensure Python 3.12 is at `C:\Program Files\Python312\python.exe`

### Tests timeout
- Default timeout is 60 seconds
- Edit `TEST_TIMEOUT` in the script if needed

### Tests not found (collected 0 items)
- The script handles this gracefully and reports 0/0 tests
- Check that test files follow pytest naming conventions (test_*.py or *_test.py)
- Ensure tests are in the correct directory (aios/tests/)
- If tests have import errors, they won't be collected

### Encoding errors
- Script uses UTF-8 encoding
- If you see garbled text, check your terminal encoding

## Configuration

Edit these constants at the top of `git_test_runner.py`:

```python
REPO_PATH = Path(r"C:\Users\A\.openclaw\workspace")
GIT_EXE = r"C:\Program Files\Git\bin\git.exe"
PYTHON_EXE = r"C:\Program Files\Python312\python.exe"
TEST_PATH = "aios/tests/"
TEST_TIMEOUT = 60
```

## Exit Codes

- `0` - Success (all tests passed)
- `1` - Failure (tests failed or error occurred)
- `130` - Interrupted (Ctrl+C)

Use in scripts:
```bash
python git_test_runner.py check
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Tests failed!"
fi
```
