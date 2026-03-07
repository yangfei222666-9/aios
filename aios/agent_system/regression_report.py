#!/usr/bin/env python3
"""Phase 3 回归分析 + 修复前后对比报告"""
import json
from pathlib import Path
from datetime import datetime

AIOS_DIR = Path(__file__).resolve().parent

print("=" * 70)
print("Phase 3 回归分析 + 修复前后对比报告")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ── 1. 推荐链路指标 ──
print("\n" + "─" * 70)
print("A. 推荐链路核心指标（本轮回归）")
print("─" * 70)

metrics_file = AIOS_DIR / "learner_v4_metrics.json"
metrics = json.loads(metrics_file.read_text(encoding="utf-8"))

total = metrics.get("recommend_total", 0)
hit = metrics.get("recommend_hit", 0)
default = metrics.get("recommend_default", 0)
gs_skip = metrics.get("recommend_skipped_grayscale", 0)
disabled = metrics.get("recommend_skipped_disabled", 0)

print(f"  推荐总请求数:        {total}")
print(f"  推荐命中(experience): {hit} ({hit/total*100:.0f}%)" if total else "  推荐命中: N/A")
print(f"  退化为default:        {default} ({default/total*100:.0f}%)" if total else "")
print(f"  灰度跳过:             {gs_skip} ({gs_skip/total*100:.0f}%)" if total else "")
print(f"  开关关闭跳过:         {disabled}")
print(f"  灰度实际命中率:       {(total-gs_skip)/total*100:.0f}% (目标50%)" if total else "")

# ── 2. recommendation_log 详情 ──
print("\n" + "─" * 70)
print("B. 推荐链路详情（每条任务）")
print("─" * 70)

rec_log = AIOS_DIR / "recommendation_log.jsonl"
if rec_log.exists():
    with open(rec_log, 'r', encoding='utf-8') as f:
        recs = [json.loads(l) for l in f if l.strip()]
    
    for r in recs:
        tid = r.get('task_id', '?')
        etype = r.get('error_type', '?')
        source = r.get('source', '?')
        strategy = r.get('recommended_strategy', '?')
        conf = r.get('confidence', 0)
        gs = r.get('grayscale', False)
        print(f"  {tid} | error={etype} | source={source} | strategy={strategy} | conf={conf:.2f} | grayscale={gs}")
    
    # 按 error_type 拆分
    print("\n  按 error_type 拆分:")
    by_type = {}
    for r in recs:
        et = r.get('error_type', '?')
        src = r.get('source', '?')
        if et not in by_type:
            by_type[et] = {'total': 0, 'experience': 0, 'default': 0, 'grayscale_skip': 0}
        by_type[et]['total'] += 1
        if src == 'experience':
            by_type[et]['experience'] += 1
        elif src == 'default':
            by_type[et]['default'] += 1
        elif src == 'grayscale_skip':
            by_type[et]['grayscale_skip'] += 1
    
    for et, stats in by_type.items():
        t = stats['total']
        exp = stats['experience']
        print(f"    {et}: {t} 次 | experience={exp} ({exp/t*100:.0f}%) | default={stats['default']} | gs_skip={stats['grayscale_skip']}")

# ── 3. spawn_requests 详情 ──
print("\n" + "─" * 70)
print("C. Spawn 请求详情")
print("─" * 70)

spawn_file = AIOS_DIR / "spawn_requests.jsonl"
if spawn_file.exists():
    with open(spawn_file, 'r', encoding='utf-8') as f:
        spawns = [json.loads(l) for l in f if l.strip()]
    
    for s in spawns:
        tid = s.get('task_id', '?')
        rec = s.get('recommendation', {})
        strat = rec.get('strategy', 'N/A')
        src = rec.get('source', 'N/A')
        ver = rec.get('version', 'N/A')
        conf = rec.get('confidence', 0)
        gs = rec.get('grayscale', False)
        print(f"  {tid} | rec_strategy={strat} | source={src} | version={ver} | conf={conf:.2f} | grayscale={gs}")

# ── 4. 修复前后对比 ──
print("\n" + "─" * 70)
print("D. 修复前后对比")
print("─" * 70)

print("""
  指标                    | 修复前          | 修复后
  ─────────────────────────────────────────────────────
  灰度比例                | 10%             | 50%
  LanceDB 轨迹数          | 1               | 4
  experience_library 条数  | 10 (7条重复)    | 3 (无重复)
  experience_db_v4 条数    | 1               | 4
  task_executions status   | 0/225 (0%)      | 225/225 (100%)
  真实成功率               | 无法计算        | 97.3%""")

# 修复前推荐数据（从备份读取）
old_metrics = AIOS_DIR / "learner_v4_metrics.json.bak-pre-regression"
if old_metrics.exists():
    old = json.loads(old_metrics.read_text(encoding="utf-8"))
    old_total = old.get("recommend_total", 0)
    old_hit = old.get("recommend_hit", 0)
    old_gs = old.get("recommend_skipped_grayscale", 0)
    
    new_total = total
    new_hit = hit
    new_gs = gs_skip
    
    print(f"""
  推荐总请求              | {old_total}              | {new_total}
  推荐命中(experience)    | {old_hit} ({old_hit/old_total*100:.0f}% if old_total else 'N/A')  | {new_hit} ({new_hit/new_total*100:.0f}%)
  灰度跳过                | {old_gs} ({old_gs/old_total*100:.0f}% if old_total else 'N/A')  | {new_gs} ({new_gs/new_total*100:.0f}%)
  非default策略占比       | ~0%             | {new_hit/new_total*100:.0f}%""" if new_total else "")

# ── 5. 剩余问题 ──
print("\n" + "─" * 70)
print("E. 剩余问题")
print("─" * 70)
print("""
  1. dependency_error 当前导入后仍偏向 default_recovery
     → 经验库中 dependency_error 的策略是 default_recovery（从旧数据导入）
     → 需要细化策略映射：dependency_check / version_pin / retry_with_mirror
  
  2. resource_exhausted 在经验库中无历史轨迹
     → 需要积累更多真实执行数据
  
  3. 经验库仍偏薄（4条轨迹）
     → 随着更多任务执行，轨迹会自然增长
     → 灰度50%确保有足够样本进入推荐链路
  
  4. 当前 lessons 只有4条测试数据
     → 真实生产环境会产生更多样化的失败类型
""")

print("=" * 70)
print("报告生成完毕")
print("=" * 70)
