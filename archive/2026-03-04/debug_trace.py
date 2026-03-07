"""Debug trace context"""
from aios.observability.logger import get_logger
from aios.observability.tracer import start_trace, current_trace_id

lg = get_logger('debug')

print("Before trace:", current_trace_id())

with start_trace('debug-trace') as sp:
    print("Inside trace:", current_trace_id())
    print("Span:", sp.span_id)
    lg.info('inside trace', task_id='debug-1')

print("After trace:", current_trace_id())
