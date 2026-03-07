from paths import TASK_QUEUE
#!/usr/bin/env python3
"""
Recovery 鏈哄埗婕旂ず - 瀹屾暣娴佺▼灞曠ず

婕旂ず鍦烘櫙锛?1. 鍚姩鏃舵竻鐞嗚繃鏈熼攣锛坰tartup_cleanup锛?2. 浠诲姟鎵ц鏃跺箓绛夊姞閿侊紙try_acquire_spawn_lock锛?3. 浠诲姟瓒呮椂鍚庤嚜鍔ㄦ仮澶嶏紙reclaim_zombie_tasks锛?4. 鍛ㄦ湡鎬ф仮澶嶆壂鎻忥紙HeartbeatSchedulerV5.tick锛?"""
import json
import time
from pathlib import Path
from spawn_lock import (
    startup_cleanup,
    try_acquire_spawn_lock,
    release_spawn_lock,
    get_idempotency_metrics,
    transition_status,
)
from heartbeat_v5 import reclaim_zombie_tasks


def demo_startup_cleanup():
    """婕旂ず 1: 鍚姩鏃舵竻鐞嗚繃鏈熼攣"""
    print("=" * 60)
    print("婕旂ず 1: 鍚姩鏃舵竻鐞嗚繃鏈熼攣")
    print("=" * 60)
    
    cleaned = startup_cleanup()
    print(f"鉁?娓呯悊浜?{cleaned} 涓繃鏈熼攣\n")


def demo_idempotent_spawn():
    """婕旂ず 2: 骞傜瓑 spawn锛堝悓涓€浠诲姟鍙墽琛屼竴娆★級"""
    print("=" * 60)
    print("婕旂ず 2: 骞傜瓑 spawn锛堝悓涓€浠诲姟鍙墽琛屼竴娆★級")
    print("=" * 60)
    
    task = {"id": "demo-task-001", "zombie_retries": 0}
    
    # 绗竴娆″皾璇曪細鎴愬姛鑾峰彇閿?    token1 = try_acquire_spawn_lock(task)
    if token1:
        print(f"鉁?绗竴娆?spawn: 鎴愬姛鑾峰彇閿?(token={token1[:8]}...)")
    else:
        print("鉂?绗竴娆?spawn: 骞傜瓑鍛戒腑锛堜笉搴旇鍙戠敓锛?)
    
    # 绗簩娆″皾璇曪細骞傜瓑鍛戒腑锛?5 鍒嗛挓鍐咃級
    token2 = try_acquire_spawn_lock(task)
    if token2:
        print("鉂?绗簩娆?spawn: 鎴愬姛鑾峰彇閿侊紙涓嶅簲璇ュ彂鐢燂級")
    else:
        print("鉁?绗簩娆?spawn: 骞傜瓑鍛戒腑锛堣烦杩囬噸澶嶆墽琛岋級")
    
    # 閲婃斁閿?    if token1:
        released = release_spawn_lock(task, token1)
        print(f"鉁?閲婃斁閿? {'鎴愬姛' if released else '澶辫触'}")
    
    # 閲婃斁鍚庡彲浠ラ噸鏂拌幏鍙?    token3 = try_acquire_spawn_lock(task)
    if token3:
        print(f"鉁?绗笁娆?spawn: 鎴愬姛鑾峰彇閿?(token={token3[:8]}...)")
        release_spawn_lock(task, token3)
    
    print()


def demo_zombie_recovery():
    """婕旂ず 3: 鍍靛案浠诲姟鎭㈠"""
    print("=" * 60)
    print("婕旂ず 3: 鍍靛案浠诲姟鎭㈠锛堣秴鏃朵换鍔¤嚜鍔ㄩ噸璇曪級")
    print("=" * 60)
    
    # 鍒涘缓涓€涓秴鏃剁殑 running 浠诲姟
    queue_file = TASK_QUEUE
    
    # 璇诲彇鐜版湁浠诲姟
    tasks = []
    if queue_file.exists():
        with open(queue_file, "r", encoding="utf-8") as f:
            tasks = [json.loads(l) for l in f if l.strip()]
    
    # 娣诲姞涓€涓秴鏃朵换鍔★紙妯℃嫙锛?    demo_task = {
        "id": "demo-zombie-001",
        "status": "running",
        "worker_id": "demo-worker",
        "started_at": time.time() - 400,  # 瓒呮椂 400s
        "last_heartbeat_at": time.time() - 400,
        "created_at": time.time() - 500,
        "updated_at": time.time() - 400,
        "zombie_retries": 0,
    }
    
    tasks.append(demo_task)
    
    # 鍐欏叆闃熷垪
    with open(queue_file, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    
    print(f"馃摑 鍒涘缓瓒呮椂浠诲姟: demo-zombie-001 (running 400s)")
    
    # 鎵ц鎭㈠
    result = reclaim_zombie_tasks(timeout_seconds=300, max_retries=2)
    
    print(f"鉁?鎭㈠缁撴灉:")
    print(f"   - 鍥炴敹: {result['reclaimed']} 涓换鍔?)
    print(f"   - 閲嶈瘯: {result['retried']} 涓换鍔?)
    print(f"   - 姘镐箙澶辫触: {result['permanently_failed']} 涓换鍔?)
    
    # 楠岃瘉缁撴灉
    with open(queue_file, "r", encoding="utf-8") as f:
        tasks = [json.loads(l) for l in f if l.strip()]
    
    demo_task_after = next((t for t in tasks if t["id"] == "demo-zombie-001"), None)
    
    if demo_task_after:
        print(f"鉁?浠诲姟鐘舵€? {demo_task_after['status']}")
        print(f"鉁?閲嶈瘯娆℃暟: {demo_task_after.get('zombie_retries', 0)}")
        print(f"鉁?worker_id: {demo_task_after.get('worker_id', 'None (宸叉竻绌?')}")
    
    # 娓呯悊婕旂ず浠诲姟
    tasks = [t for t in tasks if t["id"] != "demo-zombie-001"]
    with open(queue_file, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    
    print()


def demo_metrics():
    """婕旂ず 4: 骞傜瓑鎸囨爣"""
    print("=" * 60)
    print("婕旂ず 4: 骞傜瓑鎸囨爣锛堝彲瑙傛祴鎬э級")
    print("=" * 60)
    
    metrics = get_idempotency_metrics()
    
    print("馃搳 褰撳墠鎸囨爣:")
    print(f"   - 鎬诲姞閿佹鏁? {metrics['acquire_total']}")
    print(f"   - 鎴愬姛鍔犻攣: {metrics['acquire_success']}")
    print(f"   - 骞傜瓑鍛戒腑: {metrics['idempotent_hit_total']}")
    print(f"   - 骞傜瓑鍛戒腑鐜? {metrics['idempotent_hit_rate']:.1%}")
    print(f"   - 骞冲潎寤惰繜: {metrics['lock_acquire_latency_ms_avg']:.2f}ms")
    print(f"   - 杩囨湡閿佹仮澶? {metrics['stale_lock_recovered_total']}")
    
    print()


def demo_transition_status():
    """婕旂ず 5: 鍘熷瓙鐘舵€佽浆鎹?""
    print("=" * 60)
    print("婕旂ず 5: 鍘熷瓙鐘舵€佽浆鎹紙CAS 璇箟锛?)
    print("=" * 60)
    
    task = {
        "id": "demo-transition-001",
        "status": "running",
        "worker_id": "demo-worker",
        "started_at": time.time(),
        "last_heartbeat_at": time.time(),
    }
    
    print(f"馃摑 鍒濆鐘舵€? {task['status']}")
    print(f"   worker_id: {task.get('worker_id')}")
    
    # 姝ｅ父杞崲锛歳unning 鈫?queued
    ok = transition_status(
        task,
        from_status="running",
        to_status="queued",
        extra={"zombie_retries": 1},
    )
    
    print(f"鉁?杞崲缁撴灉: {'鎴愬姛' if ok else '澶辫触'}")
    print(f"   鏂扮姸鎬? {task['status']}")
    print(f"   worker_id: {task.get('worker_id', 'None (宸叉竻绌?')}")
    print(f"   zombie_retries: {task.get('zombie_retries')}")
    
    # CAS 澶辫触锛氱姸鎬佷笉鍖归厤
    ok2 = transition_status(
        task,
        from_status="running",  # 褰撳墠宸茬粡鏄?queued
        to_status="failed",
    )
    
    print(f"鉁?CAS 淇濇姢: {'澶辫触锛堥鏈燂級' if not ok2 else '鎴愬姛锛堜笉搴旇锛?}")
    print(f"   鐘舵€佷繚鎸? {task['status']}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AIOS Recovery 鏈哄埗瀹屾暣婕旂ず")
    print("=" * 60 + "\n")
    
    try:
        demo_startup_cleanup()
        demo_idempotent_spawn()
        demo_transition_status()
        demo_zombie_recovery()
        demo_metrics()
        
        print("=" * 60)
        print("鉁?婕旂ず瀹屾垚锛?)
        print("=" * 60)
        print("\n鏍稿績鐗规€?")
        print("  1. 鉁?鍚姩鏃惰嚜鍔ㄦ竻鐞嗚繃鏈熼攣")
        print("  2. 鉁?骞傜瓑 spawn锛?5 鍒嗛挓绐楀彛鍐呭悓涓€浠诲姟鍙墽琛屼竴娆★級")
        print("  3. 鉁?鍘熷瓙鐘舵€佽浆鎹紙CAS 璇箟 + 鑷姩娓呯┖ worker 瀛楁锛?)
        print("  4. 鉁?鍍靛案浠诲姟鑷姩鎭㈠锛堣秴鏃?鈫?閲嶈瘯 鈫?姘镐箙澶辫触锛?)
        print("  5. 鉁?瀹屾暣鍙娴嬫€э紙骞傜瓑鍛戒腑鐜囥€佸欢杩熴€佹仮澶嶆鏁帮級")
        print("\n瑙傚療鏈? 2026-03-06 12:00 ~ 2026-03-08 12:00 (48h)")
        print("澶嶇洏鏃堕棿: 2026-03-08 11:05")
        
    except Exception as e:
        print(f"\n鉂?婕旂ず澶辫触: {e}")
        import traceback
        traceback.print_exc()


