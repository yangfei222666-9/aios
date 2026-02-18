# Changelog

## v1.0.0 (2026-02-19)

Initial release.

### Core
- `executor.run()` — unified execution entry with auto error capture
- `errors.sign_strict()` / `sign_loose()` — dual-layer error signatures
- `lessons.find()` — two-tier lesson matching (strict → loose fallback)
- `circuit_breaker.allow()` — auto-trip after 3 same-sig failures in 30min
- `lifecycle.auto_promote()` — draft → verified → hardened auto-progression
- `logger.log_event()` — JSONL event logging with environment fingerprint

### Testing
- `retest.run(level)` — three-tier test runner (smoke / regression / full)
- 10 built-in test cases covering PowerShell, path, encoding, integrity, roundtrip

### Reporting
- `weekly_report.generate(days)` — top errors, categories, retest summary, env changes
- `proposals.generate(window_hours)` — auto-generated improvement proposals

### Data
- All JSONL records carry `schema_version: "1.0"` + `module_version: "1.0.0"`
- Lesson status lifecycle: draft → verified → hardened → deprecated
- Dedup via `dup_of` field

### CLI
- `python -m autolearn [health|retest|report|proposals|triage|version]`

### ARAM Integration
- `aram.py` CLI: build / check / report / status
- 172 champions, 100% build coverage
