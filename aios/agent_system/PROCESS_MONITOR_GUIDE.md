# AIOS Process Monitor Guide

## Overview

Zero-dependency process monitoring system for Windows that automatically restarts failed processes with circuit breaker protection.

## Features

- **Port-based detection**: Check if a port is listening (netstat)
- **Process name detection**: Check if a process exists (tasklist)
- **Auto-restart**: Automatically restart failed processes
- **Circuit breaker**: Stop retrying after max failures (default: 3)
- **Event logging**: All events recorded to JSONL for DataCollector integration
- **CLI interface**: Simple command-line management

## Quick Start

### Check Status
```bash
python process_monitor.py status
```

Shows current status of all monitored processes:
- `RUNNING`: Process is alive
- `DOWN`: Process is not running
- `CIRCUIT_BROKEN`: Max retries exceeded, auto-restart disabled

### Manual Check
```bash
python process_monitor.py check
```

Manually trigger a check cycle. Will attempt to restart any down processes.

### List Configuration
```bash
python process_monitor.py list
```

Display all configured processes with their settings.

### Add Process
```bash
python process_monitor.py add
```

Interactive wizard to add a new process to monitor.

## Configuration

Edit `process_monitor_config.json`:

```json
{
  "processes": [
    {
      "name": "AIOS Dashboard",
      "cmd": "cd C:\\path\\to\\app && python server.py",
      "port": 8888,
      "check_interval": 30,
      "max_retries": 3
    }
  ]
}
```

### Configuration Fields

- **name**: Display name for the process
- **cmd**: Shell command to start the process
- **port** (optional): Port number to monitor (uses netstat)
- **process_name** (optional): Process name to monitor (uses tasklist, e.g., "python.exe")
- **check_interval**: Seconds between checks (for reference, not enforced by CLI)
- **max_retries**: Max restart attempts before circuit break

**Note**: Specify either `port` OR `process_name`, not both. Port-based detection is more reliable.

## Event Types

Events are logged to `process_monitor_events.jsonl`:

- **process.check**: Periodic health check
- **process.down**: Process detected as down
- **process.restart**: Successful restart
- **process.restart_failed**: Restart attempt failed
- **process.circuit_break**: Max retries exceeded, monitoring stopped

### Event Format
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "type": "process.restart",
  "name": "AIOS Dashboard",
  "details": {"success": true}
}
```

## Logs

All operations are logged to `process_monitor.log` with timestamps.

## Automation

### Windows Task Scheduler

Run checks every 5 minutes:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Every 5 minutes
4. Action: Start a program
   - Program: `C:\Program Files\Python312\python.exe`
   - Arguments: `process_monitor.py check`
   - Start in: `C:\Users\A\.openclaw\workspace\aios\agent_system`

### Manual Monitoring Loop

For testing, run a simple loop:

```bash
while ($true) { python process_monitor.py check; Start-Sleep -Seconds 30 }
```

## Troubleshooting

### Process won't start
- Check the `cmd` field in config - test it manually first
- Verify paths use double backslashes: `C:\\path\\to\\file`
- Check `process_monitor.log` for error details

### Port detection not working
- Ensure the port number is correct
- Process might take a few seconds to bind the port
- Try using `process_name` instead

### Circuit breaker triggered
- Check why the process keeps failing (logs, permissions, etc.)
- Fix the underlying issue
- Remove and re-add the process, or restart the monitor

### Encoding issues
- All files use UTF-8 encoding
- Output is in English to avoid Windows console encoding problems

## Integration with DataCollector

Events are written to `process_monitor_events.jsonl` in standard format. DataCollector can read this file directly to track process health metrics.

## Best Practices

1. **Use port monitoring when possible** - more reliable than process name
2. **Test commands manually first** - ensure they work before adding to config
3. **Set reasonable check intervals** - 30-60 seconds is usually sufficient
4. **Monitor the logs** - check `process_monitor.log` regularly
5. **Don't over-retry** - if a process fails 3 times, something is wrong

## Example: Adding a New Process

```bash
$ python process_monitor.py add

=== Add Process ===

Process name: My Web Server
Start command: cd C:\apps\webserver && python app.py
Port to monitor (leave empty to skip): 5000
Check interval in seconds (default 30): 60
Max retries before circuit break (default 3): 5

Process 'My Web Server' added successfully
```

## Windows Compatibility

- Uses `subprocess` with `shell=True` for complex commands
- Compatible with `cd`, `&&`, and other shell operators
- Handles Windows paths with backslashes
- Uses `tasklist` and `netstat` (built-in Windows commands)
- No external dependencies required

## Limitations

- CLI-based only (no daemon mode in this version)
- Requires manual scheduling (Task Scheduler or cron)
- Windows-specific (uses tasklist/netstat)
- No process grouping or dependencies
- No notification system (events only)

## Future Enhancements

Consider adding:
- Daemon mode with background monitoring
- Email/webhook notifications
- Process dependency chains
- Resource usage monitoring
- Web dashboard integration
