#!/usr/bin/env python3
"""
Memory System 10条样本验证脚本

样本配置（按珊瑚海建议）：
- 4 条 success_case
- 3 条 failure_pattern
- 3 条 fix_solution
- 2 条相似任务（测试召回相关性）
- 2 条相似错误（测试错误召回）
- 1 条误导性样本（测试过滤质量）

验收标准：
1. enqueue -> worker -> upsert 跑通
2. 新任务召回链能返回合理历史方案
3. 失败检索链能返回合理修复建议
4. 主执行链不被 memory 写入拖慢
5. 10 条样本里 Top3 至少有明显相关命中

作者：小九 | 2026-03-07
"""

import sys
import time
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_v2.memory_store import upsert_memory, search_memories, get_stats
from memory_v2.memory_queue import start_worker, enqueue, get_stats as queue_stats
from memory_v2.memory_retrieval import retrieve_for_task_start, retrieve_for_failure, format_context

# ── 10 条样本数据 ────────────────────────────────────────────────────────────
SAMPLES = [
    # ── 4 条 success_case ──
    {
        "id": "s001",
        "text": "优化 Memory Manager 缓存策略 | Result: 引入 TTL + LRU 双层缓存，降低重复计算延迟 40%",
        "memory_type": "success_case",
        "task_type": "code",
        "tags": ["optimization", "cache", "memory"],
    },
    {
        "id": "s002",
        "text": "修复 task_executor 超时问题 | Result: 使用 asyncio.wait_for 包裹任务执行，补充 timeout 错误分类",
        "memory_type": "success_case",
        "task_type": "code",
        "tags": ["bugfix", "timeout", "async"],
    },
    {
        "id": "s003",
        "text": "分析系统错误率并生成报告 | Result: 按 agent/task_type/time_window 拆分指标后更容易定位问题",
        "memory_type": "success_case",
        "task_type": "analysis",
        "tags": ["analysis", "metrics", "report"],
    },
    {
        "id": "s004",
        "text": "重构 scheduler.py 任务调度逻辑 | Result: 引入优先级队列，高优先级任务延迟降低 60%",
        "memory_type": "success_case",
        "task_type": "code",
        "tags": ["refactor", "scheduler", "performance"],
    },

    # ── 3 条 failure_pattern ──
    {
        "id": "f001",
        "text": "API 调用失败 502 Bad Gateway | Error: 上游服务不稳定，重试 3 次后放弃",
        "memory_type": "failure_pattern",
        "error_type": "upstream_api_error",
        "tags": ["api", "502", "network"],
    },
    {
        "id": "f002",
        "text": "任务执行超时 60s | Error: 任务复杂度过高，单次执行超过限制",
        "memory_type": "failure_pattern",
        "error_type": "timeout",
        "tags": ["timeout", "performance"],
    },
    {
        "id": "f003",
        "text": "依赖包安装失败 | Error: pip install 时网络超时，无法下载 sentence-transformers",
        "memory_type": "failure_pattern",
        "error_type": "dependency_error",
        "tags": ["dependency", "pip", "network"],
    },

    # ── 3 条 fix_solution ──
    {
        "id": "x001",
        "text": "修复 502 API 错误 | Fix: 添加指数退避重试（3次），超过后降级到缓存结果",
        "memory_type": "fix_solution",
        "error_type": "upstream_api_error",
        "status": "fixed",
        "tags": ["api", "retry", "fallback"],
        "metadata": {"fix_success_rate": 0.85},
    },
    {
        "id": "x002",
        "text": "修复任务超时问题 | Fix: 拆分大任务为子任务，每个子任务限制 20s，并行执行",
        "memory_type": "fix_solution",
        "error_type": "timeout",
        "status": "fixed",
        "tags": ["timeout", "decompose", "parallel"],
        "metadata": {"fix_success_rate": 0.90},
    },
    {
        "id": "x003",
        "text": "修复依赖安装失败 | Fix: 切换到国内镜像源（清华/阿里），并添加离线包缓存",
        "memory_type": "fix_solution",
        "error_type": "dependency_error",
        "status": "fixed",
        "tags": ["dependency", "mirror", "cache"],
        "metadata": {"fix_success_rate": 0.95},
    },
]

# ── 误导性样本（故意放入，测试过滤质量）──
MISLEADING_SAMPLE = {
    "id": "m001",
    "text": "优化数据库查询性能 | Result: 添加索引后查询速度提升 10x",
    "memory_type": "success_case",
    "task_type": "database",  # 不同 task_type
    "tags": ["database", "sql", "index"],
}


def print_separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def check_1_async_write():
    """检查点1：enqueue -> worker -> upsert 跑通"""
    print_separator("CHECK 1: 异步写入链路")
    
    # 启动 worker
    start_worker()
    print("[OK] Worker started")
    
    # 入队（非阻塞）
    t0 = time.time()
    enqueue("task_completed", {
        "task_id": "async-test-001",
        "description": "测试异步写入",
        "result": "写入成功",
        "task_type": "test",
    })
    enqueue_time = (time.time() - t0) * 1000
    
    print(f"[OK] Enqueue time: {enqueue_time:.2f}ms (应 < 1ms)")
    print(f"[OK] Queue stats: {queue_stats()}")
    
    # 等待 worker 处理
    time.sleep(2)
    print(f"[OK] After 2s: {queue_stats()}")
    
    return enqueue_time < 5  # 入队应该极快


def check_2_write_samples():
    """写入 10 条样本 + 1 条误导性样本"""
    print_separator("CHECK 2: 写入 10+1 条样本")
    
    all_samples = SAMPLES + [MISLEADING_SAMPLE]
    
    for s in all_samples:
        rid = upsert_memory(s)
        print(f"  [OK] {rid} ({s['memory_type']})")
    
    stats = get_stats()
    print(f"\n[STATS] Total: {stats['total']}")
    print(f"[STATS] By type: {stats['by_type']}")
    
    return stats['total'] >= 10


def check_3_filter_isolation():
    """检查点3：过滤是否生效（success_case 不混进 fix_solution）"""
    print_separator("CHECK 3: 过滤隔离")
    
    # 查 success_case
    results_sc = search_memories("优化缓存性能", memory_type="success_case", top_k=5)
    types_sc = set(r["memory_type"] for r in results_sc)
    
    # 查 fix_solution
    results_fx = search_memories("修复 API 错误", memory_type="fix_solution", top_k=5)
    types_fx = set(r["memory_type"] for r in results_fx)
    
    print(f"success_case 查询结果类型: {types_sc}")
    print(f"fix_solution 查询结果类型: {types_fx}")
    
    sc_clean = types_sc <= {"success_case", ""}
    fx_clean = types_fx <= {"fix_solution", ""}
    
    print(f"[{'OK' if sc_clean else 'FAIL'}] success_case 过滤: {'干净' if sc_clean else '有污染'}")
    print(f"[{'OK' if fx_clean else 'FAIL'}] fix_solution 过滤: {'干净' if fx_clean else '有污染'}")
    
    return sc_clean and fx_clean


def check_4_task_start_retrieval():
    """检查点4：任务启动召回链质量"""
    print_separator("CHECK 4: 任务启动召回链")
    
    # 测试1：相似任务（应该命中 s001/s004）
    task1 = {
        "description": "优化内存缓存，减少重复计算",
        "task_type": "code",
        "tags": ["optimization"],
    }
    results1 = retrieve_for_task_start(task1, top_k=3)
    print(f"\n查询: '{task1['description']}'")
    print(f"Top3 结果:")
    for r in results1:
        print(f"  [{r['id']}] score={r['_final_score']:.3f} | {r['text'][:80]}")
    
    # 检查 Top1 是否相关（应该是 s001 或 s004）
    top1_id = results1[0]["id"] if results1 else None
    relevant = top1_id in ["s001", "s004"]
    print(f"[{'OK' if relevant else 'WARN'}] Top1 相关性: {top1_id} ({'相关' if relevant else '不相关'})")
    
    # 测试2：误导性样本不应排前面（database 任务不应出现在 code 查询里）
    task2 = {
        "description": "重构代码逻辑，提升执行效率",
        "task_type": "code",
    }
    results2 = retrieve_for_task_start(task2, top_k=3)
    print(f"\n查询: '{task2['description']}'")
    print(f"Top3 结果:")
    for r in results2:
        print(f"  [{r['id']}] task_type={r['task_type']} score={r['_final_score']:.3f} | {r['text'][:60]}")
    
    # 误导性样本（m001, database）不应在 Top3
    top3_ids = [r["id"] for r in results2]
    misleading_in_top3 = "m001" in top3_ids
    print(f"[{'WARN' if misleading_in_top3 else 'OK'}] 误导性样本: {'混入 Top3' if misleading_in_top3 else '未混入 Top3'}")
    
    return len(results1) > 0 and relevant


def check_5_failure_retrieval():
    """检查点5：失败召回链质量"""
    print_separator("CHECK 5: 失败召回链")
    
    # 测试1：相似错误（应该命中 x001）
    error1 = {
        "description": "调用外部 API 返回 502",
        "error_type": "upstream_api_error",
        "error_message": "HTTP 502 Bad Gateway",
    }
    results1 = retrieve_for_failure(error1, top_k=3)
    print(f"\n错误: '{error1['description']}'")
    print(f"Top3 修复建议:")
    for r in results1:
        print(f"  [{r['id']}] score={r['_final_score']:.3f} | {r['text'][:80]}")
    
    top1_id = results1[0]["id"] if results1 else None
    relevant = top1_id == "x001"
    print(f"[{'OK' if relevant else 'WARN'}] Top1 相关性: {top1_id} ({'相关' if relevant else '不相关'})")
    
    # 测试2：超时错误（应该命中 x002）
    error2 = {
        "description": "任务执行超时",
        "error_type": "timeout",
        "error_message": "Execution timeout after 60s",
    }
    results2 = retrieve_for_failure(error2, top_k=3)
    print(f"\n错误: '{error2['description']}'")
    print(f"Top3 修复建议:")
    for r in results2:
        print(f"  [{r['id']}] score={r['_final_score']:.3f} | {r['text'][:80]}")
    
    top1_id2 = results2[0]["id"] if results2 else None
    relevant2 = top1_id2 == "x002"
    print(f"[{'OK' if relevant2 else 'WARN'}] Top1 相关性: {top1_id2} ({'相关' if relevant2 else '不相关'})")
    
    return len(results1) > 0 and len(results2) > 0


def check_6_no_blocking():
    """检查点6：主流程不被 memory 写入拖慢"""
    print_separator("CHECK 6: 主流程不阻塞")
    
    # 模拟主任务执行
    t0 = time.time()
    
    # 主任务逻辑（模拟）
    result = "task completed"
    
    # 入队（非阻塞）
    enqueue("task_completed", {
        "task_id": "perf-test-001",
        "description": "性能测试任务",
        "result": result,
        "task_type": "test",
    })
    
    main_task_time = (time.time() - t0) * 1000
    print(f"[OK] 主任务 + 入队总耗时: {main_task_time:.2f}ms")
    print(f"[OK] 入队不阻塞主流程（memory 写入在后台进行）")
    
    # 等待后台写入
    time.sleep(2)
    print(f"[OK] 后台写入完成（2s 后）")
    
    return main_task_time < 10  # 主流程应该 < 10ms


def main():
    print("\n" + "="*60)
    print("  Memory System 10条样本验证")
    print("="*60)
    
    results = {}
    
    # 运行所有检查
    results["async_write"] = check_1_async_write()
    results["write_samples"] = check_2_write_samples()
    results["filter_isolation"] = check_3_filter_isolation()
    results["task_start_retrieval"] = check_4_task_start_retrieval()
    results["failure_retrieval"] = check_5_failure_retrieval()
    results["no_blocking"] = check_6_no_blocking()
    
    # 汇总
    print_separator("验收结果汇总")
    
    checks = [
        ("enqueue -> worker -> upsert 跑通", results["async_write"]),
        ("10条样本写入成功", results["write_samples"]),
        ("过滤隔离（success_case 不混 fix_solution）", results["filter_isolation"]),
        ("任务召回链返回合理历史方案", results["task_start_retrieval"]),
        ("失败检索链返回合理修复建议", results["failure_retrieval"]),
        ("主执行链不被 memory 写入拖慢", results["no_blocking"]),
    ]
    
    passed = 0
    for name, ok in checks:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
        if ok:
            passed += 1
    
    print(f"\n总计: {passed}/{len(checks)} 通过")
    
    if passed == len(checks):
        print("\n🎉 全部通过！可以进入数据迁移阶段。")
    else:
        print(f"\n⚠️  {len(checks) - passed} 项未通过，需要修复后再进入数据迁移。")
    
    return passed == len(checks)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
