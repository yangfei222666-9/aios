#!/usr/bin/env python3
"""
AIOS Store - SQLite 统一存储层
替换 JSONL 全文扫描，提供索引查询 + 缓存
"""

import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

AIOS_DIR = Path(__file__).resolve().parent
DB_PATH = AIOS_DIR / "aios.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化所有表"""
    with db() as conn:
        conn.executescript("""
        -- 经验库（替换 experience_db_v4.jsonl）
        CREATE TABLE IF NOT EXISTS experience (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            idem_key    TEXT UNIQUE NOT NULL,
            error_type  TEXT NOT NULL,
            strategy    TEXT NOT NULL,
            strategy_version TEXT,
            task_id     TEXT,
            confidence  REAL DEFAULT 0.8,
            recovery_time REAL DEFAULT 0.0,
            success     INTEGER DEFAULT 1,
            created_at  REAL NOT NULL  -- unix timestamp，用于时间衰减
        );
        CREATE INDEX IF NOT EXISTS idx_exp_error ON experience(error_type, success);

        -- 回滚备份（替换 config_backups.jsonl）
        CREATE TABLE IF NOT EXISTS rollback_backup (
            backup_id   TEXT PRIMARY KEY,
            agent_id    TEXT NOT NULL,
            improvement_id TEXT,
            config_json TEXT NOT NULL,
            created_at  REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_rb_agent ON rollback_backup(agent_id);

        -- 回滚历史（替换 rollback_history.jsonl）
        CREATE TABLE IF NOT EXISTS rollback_history (
            rollback_id TEXT PRIMARY KEY,
            agent_id    TEXT NOT NULL,
            backup_id   TEXT NOT NULL,
            improvement_id TEXT,
            config_json TEXT,
            created_at  REAL NOT NULL
        );

        -- 路由决策日志（替换 router_decisions.jsonl）
        CREATE TABLE IF NOT EXISTS router_decision (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id     TEXT,
            agent       TEXT,
            model       TEXT,
            confidence  REAL,
            reason_codes TEXT,  -- JSON array
            input_snap  TEXT,   -- JSON
            duration_ms INTEGER,
            created_at  REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_rd_task ON router_decision(task_id);
        """)
    print(f"[STORE] DB initialized: {DB_PATH}")


# ─────────────────────────────────────────────
# 经验库 API
# ─────────────────────────────────────────────

def exp_save(record: Dict) -> bool:
    """幂等写入经验（返回 True=新增，False=已存在）"""
    import hashlib
    error_type = record.get("error_type", "unknown")
    strategy = record.get("strategy", "default_recovery")
    idem_key = hashlib.sha256(f"{error_type}:{strategy}".encode()).hexdigest()[:16]

    with db() as conn:
        try:
            conn.execute("""
                INSERT INTO experience
                    (idem_key, error_type, strategy, strategy_version,
                     task_id, confidence, recovery_time, success, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                idem_key, error_type, strategy,
                record.get("strategy_version", ""),
                record.get("task_id", ""),
                record.get("confidence", 0.8),
                record.get("recovery_time", 0.0),
                1 if record.get("success", True) else 0,
                time.time(),
            ))
            return True
        except sqlite3.IntegrityError:
            return False  # 幂等命中


def exp_query(error_type: str, limit: int = 3, decay_days: float = 30.0) -> List[Dict]:
    """
    查询历史成功策略，按时间衰减置信度排序。

    衰减公式：
        effective_confidence = confidence * exp(-λ * age_days)
        λ = ln(2) / half_life_days  (half_life = decay_days/2)
    """
    import math
    half_life = decay_days / 2.0
    lam = math.log(2) / half_life
    now = time.time()

    with db() as conn:
        rows = conn.execute("""
            SELECT * FROM experience
            WHERE error_type = ? AND success = 1
            ORDER BY created_at DESC
            LIMIT 50
        """, (error_type,)).fetchall()

    results = []
    for r in rows:
        age_days = (now - r["created_at"]) / 86400.0
        eff_conf = r["confidence"] * math.exp(-lam * age_days)
        results.append({
            "error_type": r["error_type"],
            "strategy": r["strategy"],
            "strategy_version": r["strategy_version"],
            "confidence": r["confidence"],
            "effective_confidence": round(eff_conf, 4),
            "age_days": round(age_days, 1),
            "task_id": r["task_id"],
        })

    results.sort(key=lambda x: x["effective_confidence"], reverse=True)
    return results[:limit]


# ─────────────────────────────────────────────
# 真回滚 API
# ─────────────────────────────────────────────

def rollback_backup(agent_id: str, config: Dict, improvement_id: str) -> str:
    """备份 agent 配置，返回 backup_id"""
    backup_id = f"{agent_id}_{int(time.time())}"
    with db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO rollback_backup
                (backup_id, agent_id, improvement_id, config_json, created_at)
            VALUES (?,?,?,?,?)
        """, (backup_id, agent_id, improvement_id,
              json.dumps(config, ensure_ascii=False), time.time()))
    return backup_id


def rollback_apply(agent_id: str, backup_id: str) -> Dict:
    """
    真回滚：从备份恢复配置到 agents.json
    """
    agents_file = AIOS_DIR / "agents.json"

    # 1. 读备份
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM rollback_backup WHERE backup_id = ?", (backup_id,)
        ).fetchone()

    if not row:
        return {"success": False, "error": f"Backup not found: {backup_id}"}

    config = json.loads(row["config_json"])

    # 2. 写回 agents.json
    try:
        data = json.loads(agents_file.read_text(encoding="utf-8"))
        agents_list = data.get("agents", data) if isinstance(data, dict) else data

        updated = False
        for i, agent in enumerate(agents_list):
            if agent.get("id") == agent_id:
                # 只恢复可回滚字段，保留 id/name/created_at
                safe_keys = {"timeout", "retry", "priority", "model",
                             "enabled", "schedule", "tools", "skills",
                             "system_prompt", "thinking"}
                for k, v in config.items():
                    if k in safe_keys:
                        agents_list[i][k] = v
                updated = True
                break

        if not updated:
            return {"success": False, "error": f"Agent not found in agents.json: {agent_id}"}

        # 写回文件
        if isinstance(data, dict):
            data["agents"] = agents_list
        else:
            data = agents_list
        agents_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    except Exception as e:
        return {"success": False, "error": str(e)}

    # 3. 记录回滚历史
    rollback_id = f"rollback_{int(time.time())}"
    with db() as conn:
        conn.execute("""
            INSERT INTO rollback_history
                (rollback_id, agent_id, backup_id, improvement_id, config_json, created_at)
            VALUES (?,?,?,?,?,?)
        """, (rollback_id, agent_id, backup_id,
              row["improvement_id"],
              row["config_json"], time.time()))

    return {
        "success": True,
        "rollback_id": rollback_id,
        "backup_id": backup_id,
        "agent_id": agent_id,
        "config_restored": config,
    }


def rollback_history(agent_id: str = None, limit: int = 20) -> List[Dict]:
    """查询回滚历史"""
    with db() as conn:
        if agent_id:
            rows = conn.execute(
                "SELECT * FROM rollback_history WHERE agent_id=? ORDER BY created_at DESC LIMIT ?",
                (agent_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM rollback_history ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# JSONL 迁移工具
# ─────────────────────────────────────────────

def migrate_jsonl(jsonl_path: Path, table: str):
    """把旧 JSONL 文件迁移到 SQLite"""
    if not jsonl_path.exists():
        print(f"[MIGRATE] Skip (not found): {jsonl_path.name}")
        return 0

    lines = [l for l in jsonl_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    count = 0

    if table == "experience":
        for line in lines:
            try:
                rec = json.loads(line)
                if exp_save(rec):
                    count += 1
            except Exception:
                pass

    elif table == "rollback_backup":
        with db() as conn:
            for line in lines:
                try:
                    rec = json.loads(line)
                    conn.execute("""
                        INSERT OR IGNORE INTO rollback_backup
                            (backup_id, agent_id, improvement_id, config_json, created_at)
                        VALUES (?,?,?,?,?)
                    """, (
                        rec.get("backup_id", f"migrated_{count}"),
                        rec.get("agent_id", "unknown"),
                        rec.get("improvement_id", ""),
                        json.dumps(rec.get("config", {}), ensure_ascii=False),
                        time.time(),
                    ))
                    count += 1
                except Exception:
                    pass

    print(f"[MIGRATE] {jsonl_path.name} → {table}: {count} rows")
    return count


def migrate_all():
    """一键迁移所有旧 JSONL"""
    init_db()
    migrate_jsonl(AIOS_DIR / "experience_db_v4.jsonl", "experience")
    migrate_jsonl(AIOS_DIR / "data" / "rollback" / "config_backups.jsonl", "rollback_backup")
    print("[MIGRATE] Done.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_all()
    else:
        init_db()
        print("[STORE] Ready.")
