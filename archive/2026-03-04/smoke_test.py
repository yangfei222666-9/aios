"""30 秒 Smoke Test - 验证可观测层"""
from aios.observability.logger import get_logger
from aios.observability.tracer import start_trace
from aios.observability.metrics import METRICS

lg = get_logger('smoke')

with start_trace('smoke'):
    lg.info('hello', task_id='smoke-1')
    lg.emit_event('smoke_event', task_id='smoke-1', payload={'ok': True})
    METRICS.inc_counter('smoke.tests', labels={'status': 'success'})
    
print('OK Smoke test passed')
print('\nCheck output files:')
print('  - aios/logs/aios.jsonl')
print('  - events.jsonl')
