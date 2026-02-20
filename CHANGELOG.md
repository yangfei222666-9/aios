# CHANGELOG

## [Unreleased]

### Fixed
- **insight.py**: Separate test critical events from real critical events
  - Critical events now split into real vs test (identified by `sig="sig_abc"` or `test=True` in payload)
  - Output format: `⚠️ 致命事件(含测试): 1 (测试1)` when test events present
  - Output format: `⚠️ 致命事件: N` when only real critical events
- **insight.py**: Exclude deploy/restart windows from loop detection
  - Loop detection now filters out consecutive KERNEL events when all are `deploy/restart/rollout` operations
  - Reduces false positives from normal deployment batches
  - Added `excluded_deploy_restart` counter for traceability
  - Output includes: `ℹ️ 已排除部署窗口: N` when deployment windows excluded

### Technical Details
- `alerts.py`: No changes - maintains existing rule-based CRIT detection (does not read event logs directly)
- `baseline.py`: No changes - `evolution_score` and `grade` continue to be computed by `evolution_score()` function based on historical snapshots, not stored in baseline.jsonl

### Commit
```
fix(insight): separate test critical events and exclude deploy/restart windows from loop detection
```

---

## [0.2.0] - 2026-02-19

### Added
- 5-layer event architecture (KERNEL/COMMS/TOOL/MEM/SEC)
- Alert state machine (alert_fsm.py) with OPEN/ACK/RESOLVED states
- Safe execution wrapper (safe_run.py) with risk levels and rollback
- Job queue system (job_queue.py) with retry and dead-letter handling
- Daily insight reports with loop detection
- Reflection engine with rule-based strategy generation

### Changed
- Migrated from v0.1 flat event schema to v0.2 layered schema
- Backward compatibility maintained for v0.1 events

---

## [0.1.0] - 2026-02-18

### Added
- Initial AIOS event logging system
- Basic autolearn framework
- ARAM Helper integration
- Memory management (MEMORY.md, daily logs)
