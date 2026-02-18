# Autolearn v1.0 API Reference

## Stable API (兼容承诺)

以下接口为 v1.0 稳定 API，升级不会破坏兼容性。

### executor.run(intent, tool, payload, do_task) → dict
统一执行入口。do_task 成功返回 `{"ok": True, ...}`，失败抛异常。
返回: `{ok, result?, error?, error_sig?, sig_loose?, tips?, tripped?, checklist?}`

### errors.sign_strict(exc_type, msg) → str
严格签名：异常类型 + 标准化消息 → 12 字符 hex

### errors.sign_loose(msg) → dict
宽松签名：关键词集合 → `{keywords: list, sig: str}`

### lessons.find(sig_strict, sig_loose?) → tips[]
双层匹配查教训：先 strict，没有再 loose

### retest.run(level="smoke|regression|full") → dict
分级复测：`{ok, passed, failed, level, ts}`

### weekly_report.generate(days=7) → str (markdown)
生成周报

### proposals.generate(window_hours=72) → list
生成自动提案

### circuit_breaker.allow(sig_strict) → bool
熔断检查：True=允许执行，False=已熔断

## Data Schema v1.0

所有 JSONL 记录包含:
- `schema_version`: "1.0"
- `module_version`: "1.0.0"
- `ts`: unix timestamp

### events.jsonl
`{type, intent, tool, ok?, error?, error_sig?, sig_loose?, tips_count?, tripped?, env?, schema_version, module_version, ts}`

### lessons.jsonl
`{id, error_sig, sig_loose, title, solution, tags[], status, dup_of?, symptom, cause, fix_steps, retest_id, rollback, schema_version, module_version, ts}`

Status lifecycle: `draft → verified → hardened → deprecated`

### retest_results.jsonl
`{suite, test, ok, err, schema_version, module_version, ts}`
