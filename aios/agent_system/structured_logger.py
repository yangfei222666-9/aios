#!/usr/bin/env python3
"""
Structured Logging for AIOS

Replaces print() with structured JSON logging.

Features:
- JSON format
- Contextual fields (agent_id, task_id, trace_id)
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Searchable and parseable
- Automatic context propagation

Usage:
    from structured_logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Task started", agent_id="agent-001", task_id="task-123")
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import contextvars

# Context variables for automatic propagation
agent_id_var = contextvars.ContextVar('agent_id', default=None)
task_id_var = contextvars.ContextVar('task_id', default=None)
trace_id_var = contextvars.ContextVar('trace_id', default=None)

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context from contextvars
        agent_id = agent_id_var.get()
        if agent_id:
            log_data["agent_id"] = agent_id
        
        task_id = task_id_var.get()
        if task_id:
            log_data["task_id"] = task_id
        
        trace_id = trace_id_var.get()
        if trace_id:
            log_data["trace_id"] = trace_id
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

class StructuredLogger(logging.LoggerAdapter):
    """Logger adapter that adds structured fields"""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add extra fields"""
        # Extract extra fields
        extra_fields = {}
        for key in list(kwargs.keys()):
            if key not in ['exc_info', 'stack_info', 'stacklevel', 'extra']:
                extra_fields[key] = kwargs.pop(key)
        
        # Add to extra
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['extra_fields'] = extra_fields
        
        return msg, kwargs

def get_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """
    Get a structured logger
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (default: INFO)
        
    Returns:
        StructuredLogger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Add structured handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    
    return StructuredLogger(logger, {})

def set_context(agent_id: Optional[str] = None, 
                task_id: Optional[str] = None, 
                trace_id: Optional[str] = None):
    """
    Set logging context
    
    Args:
        agent_id: Agent ID
        task_id: Task ID
        trace_id: Trace ID for distributed tracing
    """
    if agent_id:
        agent_id_var.set(agent_id)
    if task_id:
        task_id_var.set(task_id)
    if trace_id:
        trace_id_var.set(trace_id)

def clear_context():
    """Clear logging context"""
    agent_id_var.set(None)
    task_id_var.set(None)
    trace_id_var.set(None)

# Example usage and demo
if __name__ == "__main__":
    print("=" * 80)
    print("  Structured Logging - Demo")
    print("=" * 80)
    print()
    
    # Get logger
    logger = get_logger(__name__)
    
    # Basic logging
    print("Basic logging:")
    logger.info("Application started")
    logger.warning("This is a warning")
    logger.error("This is an error")
    print()
    
    # Logging with extra fields
    print("Logging with extra fields:")
    logger.info("Task started", task_type="analysis", priority="high")
    logger.info("Processing data", records_processed=1000, duration_ms=250)
    print()
    
    # Logging with context
    print("Logging with context:")
    set_context(agent_id="agent-001", task_id="task-123", trace_id="trace-abc")
    logger.info("Task executing")
    logger.info("Step 1 completed", step="data_loading")
    logger.info("Step 2 completed", step="data_processing")
    clear_context()
    print()
    
    # Logging with exception
    print("Logging with exception:")
    try:
        raise ValueError("Something went wrong")
    except Exception as e:
        logger.error("Task failed", error_type="ValueError", exc_info=True)
    print()
    
    print("=" * 80)
    print("  Demo completed!")
    print("=" * 80)
