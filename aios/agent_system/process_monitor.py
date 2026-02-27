#!/usr/bin/env python3
"""
AIOS Process Monitor - Zero-dependency process monitoring and auto-restart
"""
import json
import subprocess
import time
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    from notifier import process_down, process_restarted, process_restart_failed, process_circuit_break
    HAS_NOTIFIER = True
except ImportError:
    HAS_NOTIFIER = False

CONFIG_FILE = "process_monitor_config.json"
EVENTS_FILE = "process_monitor_events.jsonl"
LOG_FILE = "process_monitor.log"

class ProcessMonitor:
    def __init__(self):
        self.config_path = Path(__file__).parent / CONFIG_FILE
        self.events_path = Path(__file__).parent / EVENTS_FILE
        self.log_path = Path(__file__).parent / LOG_FILE
        self.config = self.load_config()
        self.failure_counts = {}
        self.circuit_broken = set()
        
    def load_config(self):
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            return {"processes": []}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Error loading config: {e}")
            return {"processes": []}
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"Error saving config: {e}")
    
    def log(self, message):
        """Write to log file"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception:
            pass
        print(log_line.strip())
    
    def record_event(self, event_type, name, details=None):
        """Record event to JSONL file"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "name": name,
            "details": details or {}
        }
        try:
            with open(self.events_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        except Exception as e:
            self.log(f"Error recording event: {e}")
    
    def check_port(self, port):
        """Check if port is listening using netstat"""
        try:
            result = subprocess.run(
                ['netstat', '-an'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    return True
            return False
        except Exception as e:
            self.log(f"Error checking port {port}: {e}")
            return False
    
    def check_process_name(self, name):
        """Check if process name exists using tasklist"""
        try:
            result = subprocess.run(
                ['tasklist'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return name.lower() in result.stdout.lower()
        except Exception as e:
            self.log(f"Error checking process {name}: {e}")
            return False
    
    def is_process_alive(self, process_config):
        """Check if process is alive based on port or name"""
        if 'port' in process_config and process_config['port']:
            return self.check_port(process_config['port'])
        elif 'process_name' in process_config:
            return self.check_process_name(process_config['process_name'])
        return False
    
    def start_process(self, process_config):
        """Start a process using configured command"""
        try:
            cmd = process_config['cmd']
            # Use shell=True for complex commands with cd, &&, etc.
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            return True
        except Exception as e:
            self.log(f"Error starting process {process_config['name']}: {e}")
            return False
    
    def check_and_restart(self, process_config):
        """Check process and restart if needed"""
        name = process_config['name']
        
        # Skip if circuit broken
        if name in self.circuit_broken:
            return
        
        # Check if alive
        is_alive = self.is_process_alive(process_config)
        
        self.record_event('process.check', name, {
            'alive': is_alive,
            'port': process_config.get('port'),
            'process_name': process_config.get('process_name')
        })
        
        if is_alive:
            # Reset failure count on success
            if name in self.failure_counts:
                self.failure_counts[name] = 0
            return
        
        # Process is down
        self.log(f"Process down: {name}")
        self.record_event('process.down', name)
        if HAS_NOTIFIER:
            process_down(name)
        
        # Try to restart
        self.log(f"Attempting to restart: {name}")
        success = self.start_process(process_config)
        
        if success:
            # Wait a bit and verify
            time.sleep(2)
            if self.is_process_alive(process_config):
                self.log(f"Restart successful: {name}")
                self.record_event('process.restart', name, {'success': True})
                self.failure_counts[name] = 0
                if HAS_NOTIFIER:
                    process_restarted(name)
            else:
                success = False
        
        if not success:
            # Restart failed
            self.failure_counts[name] = self.failure_counts.get(name, 0) + 1
            self.log(f"Restart failed: {name} (attempt {self.failure_counts[name]})")
            self.record_event('process.restart_failed', name, {
                'attempt': self.failure_counts[name]
            })
            if HAS_NOTIFIER:
                process_restart_failed(name, self.failure_counts[name], process_config.get('max_retries', 3))
            
            # Check circuit breaker
            max_retries = process_config.get('max_retries', 3)
            if self.failure_counts[name] >= max_retries:
                self.log(f"Circuit breaker triggered for {name} after {max_retries} failures")
                self.circuit_broken.add(name)
                self.record_event('process.circuit_break', name, {
                    'failures': self.failure_counts[name]
                })
                if HAS_NOTIFIER:
                    process_circuit_break(name, max_retries)
    
    def check_all(self):
        """Check all configured processes"""
        if not self.config.get('processes'):
            self.log("No processes configured")
            return
        
        for process in self.config['processes']:
            self.check_and_restart(process)
    
    def status(self):
        """Show status of all monitored processes"""
        if not self.config.get('processes'):
            print("No processes configured")
            return
        
        print("\n=== Process Monitor Status ===\n")
        for process in self.config['processes']:
            name = process['name']
            is_alive = self.is_process_alive(process)
            status = "RUNNING" if is_alive else "DOWN"
            
            if name in self.circuit_broken:
                status = "CIRCUIT_BROKEN"
            
            failures = self.failure_counts.get(name, 0)
            max_retries = process.get('max_retries', 3)
            
            print(f"[{status}] {name}")
            if 'port' in process:
                print(f"  Port: {process['port']}")
            if 'process_name' in process:
                print(f"  Process: {process['process_name']}")
            print(f"  Failures: {failures}/{max_retries}")
            print()
    
    def list_config(self):
        """List all configured processes"""
        if not self.config.get('processes'):
            print("No processes configured")
            return
        
        print("\n=== Configured Processes ===\n")
        for i, process in enumerate(self.config['processes'], 1):
            print(f"{i}. {process['name']}")
            print(f"   Command: {process['cmd']}")
            if 'port' in process:
                print(f"   Port: {process['port']}")
            if 'process_name' in process:
                print(f"   Process Name: {process['process_name']}")
            print(f"   Check Interval: {process.get('check_interval', 30)}s")
            print(f"   Max Retries: {process.get('max_retries', 3)}")
            print()
    
    def add_process(self):
        """Interactive process addition"""
        print("\n=== Add Process ===\n")
        
        name = input("Process name: ").strip()
        if not name:
            print("Name cannot be empty")
            return
        
        cmd = input("Start command: ").strip()
        if not cmd:
            print("Command cannot be empty")
            return
        
        port_str = input("Port to monitor (leave empty to skip): ").strip()
        port = int(port_str) if port_str else None
        
        process_name = None
        if not port:
            process_name = input("Process name to monitor (e.g., python.exe): ").strip()
            if not process_name:
                print("Must specify either port or process name")
                return
        
        check_interval = input("Check interval in seconds (default 30): ").strip()
        check_interval = int(check_interval) if check_interval else 30
        
        max_retries = input("Max retries before circuit break (default 3): ").strip()
        max_retries = int(max_retries) if max_retries else 3
        
        process_config = {
            "name": name,
            "cmd": cmd,
            "check_interval": check_interval,
            "max_retries": max_retries
        }
        
        if port:
            process_config["port"] = port
        if process_name:
            process_config["process_name"] = process_name
        
        self.config['processes'].append(process_config)
        self.save_config()
        
        print(f"\nProcess '{name}' added successfully")

def main():
    monitor = ProcessMonitor()
    
    if len(sys.argv) < 2:
        print("Usage: python process_monitor.py [status|check|list|add]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        monitor.status()
    elif command == 'check':
        print("Running process check...")
        monitor.check_all()
        print("Check complete")
    elif command == 'list':
        monitor.list_config()
    elif command == 'add':
        monitor.add_process()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, check, list, add")
        sys.exit(1)

if __name__ == '__main__':
    main()
