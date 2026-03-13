"""AIOS Dashboard v4.0 服务器 - 真实数据版"""
import json
import time
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

# 修复 Windows 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PORT = 8889
DASHBOARD_ROOT = Path(__file__).parent
AIOS_ROOT = DASHBOARD_ROOT.parent.parent
AGENT_SYSTEM = AIOS_ROOT / "agent_system"
DATA_DIR = AGENT_SYSTEM / "data"
WORKSPACE_ROOT = AIOS_ROOT.parent


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/metrics':
            data = self.get_metrics()
            self.send_json_response(data)
        elif self.path == '/api/skills':
            data = self.get_skills()
            self.send_json_response(data)
        elif self.path == '/api/hexagram_timeline':
            data = self.get_hexagram_timeline()
            self.send_json_response(data)
        elif self.path.startswith('/api/logs'):
            data = self.get_logs()
            self.send_json_response(data)
        elif self.path == '/' or self.path == '/index.html':
            self.serve_file('index.html')
        else:
            self.send_error(404)

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def serve_file(self, filename):
        file_path = DASHBOARD_ROOT / filename
        if file_path.exists():
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)

    # ========== 真实数据读取 ==========

    def _read_jsonl(self, path, max_lines=200):
        """读取 JSONL 文件最后 N 行"""
        if not path.exists():
            return []
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            result = []
            for line in lines[-max_lines:]:
                line = line.strip()
                if line:
                    try:
                        result.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return result
        except Exception:
            return []

    def _read_json(self, path):
        """读取 JSON 文件"""
        if not path.exists():
            return {}
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except Exception:
            return {}

    def _get_task_stats(self):
        """从 task_executions.jsonl 计算真实统计"""
        # 优先读取真实数据文件
        execs = self._read_jsonl(DATA_DIR / "task_executions.jsonl", 500)
        if not execs:
            # fallback: 尝试 v2 格式
            execs = self._read_jsonl(DATA_DIR / "task_executions_v2.jsonl", 500)

        total = len(execs)
        if total == 0:
            return {"total": 0, "completed": 0, "failed": 0, "success_rate": 0, "today": 0}

        # 兼容多种状态字段
        completed = sum(1 for e in execs 
                       if e.get("status") in ("completed", "success") 
                       or e.get("success") is True)
        failed = sum(1 for e in execs 
                    if e.get("status") in ("failed", "error") 
                    or e.get("success") is False)
        success_rate = round(completed / max(total, 1) * 100, 1)

        # 今日改进数
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_count = sum(1 for e in execs
                         if e.get("timestamp", "").startswith(today_str)
                         or e.get("completed_at", "").startswith(today_str)
                         or e.get("started_at", "").startswith(today_str))

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "success_rate": success_rate,
            "today": today_count
        }

    def _get_trend_data(self):
        """从 health records 构建趋势数据"""
        health_dir = DATA_DIR / "health"
        if not health_dir.exists():
            return [], [], []

        # 取最近 12 个 health 快照
        files = sorted(health_dir.glob("health_*.json"))[-12:]
        labels = []
        evolution_trend = []
        success_trend = []

        for f in files:
            try:
                data = self._read_json(f)
                # 从文件名提取时间 health_YYYYMMDD_HHMMSS.json
                name = f.stem  # health_20260313_061008
                parts = name.split("_")
                if len(parts) >= 3:
                    t = parts[2]
                    labels.append(f"{t[:2]}:{t[2:4]}")
                else:
                    labels.append("--:--")

                evolution_trend.append(data.get("evolution_score", data.get("score", 0)))
                success_trend.append(data.get("success_rate", data.get("health_score", 0)))
            except Exception:
                pass

        return labels, evolution_trend, success_trend

    def get_metrics(self):
        """获取系统指标 - 全部真实数据"""
        agents = self.load_agents()
        task_stats = self._get_task_stats()
        
        # Evolution score = 成功率（真实数据驱动）
        evolution_score = task_stats["success_rate"]
        print(f"[DEBUG] task_stats={task_stats}, evolution_score={evolution_score}")
        
        labels, trend_evo, trend_success = self._get_trend_data()

        active_agents = len([a for a in agents 
                            if a.get('lifecycle_state') == 'active' 
                            or a.get('mode') == 'active'
                            or a.get('status') == 'active'])

        # 系统资源 - 真实数据
        cpu = mem = disk = gpu = 0
        try:
            import psutil
            cpu = round(psutil.cpu_percent(interval=0.1), 1)
            mem = round(psutil.virtual_memory().percent, 1)
            disk = round(psutil.disk_usage('C:\\' if sys.platform == 'win32' else '/').percent, 1)
        except ImportError:
            pass

        # GPU - 尝试真实读取，否则标记为不可用
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                gpu = int(result.stdout.strip().split('\n')[0])
        except Exception:
            gpu = -1  # -1 表示不可用

        from datetime import datetime
        return {
            "time": datetime.now().strftime("%H:%M:%S"),
            "active_agents": active_agents,
            "evolution_score": evolution_score,
            "improvements_today": task_stats["today"],
            "success_rate": task_stats["success_rate"],
            "agents": agents,
            "trend_evolution_labels": labels,
            "trend_evolution": trend_evo,
            "trend_success_labels": labels,
            "trend_success": trend_success,
            "cpu": cpu,
            "mem": mem,
            "disk": disk,
            "gpu": gpu,
            # 额外真实数据
            "task_total": task_stats["total"],
            "task_completed": task_stats["completed"],
            "task_failed": task_stats["failed"],
            "_data_source": "real"
        }

    def load_agents(self):
        """加载 Agent 数据 - 真实数据，无 fallback 假数据"""
        agents_file = DATA_DIR / "agents.json"
        data = self._read_json(agents_file)
        agents = data.get("agents", [])
        # 不再返回假数据，空就是空
        return agents

    def get_skills(self):
        """获取 Skills 列表"""
        skills_dir = WORKSPACE_ROOT / "skills"
        skills = []

        if skills_dir.exists():
            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue
                try:
                    with open(skill_md, 'r', encoding='utf-8') as f:
                        content = f.read()
                    lines = content.split('\n')
                    name = skill_dir.name
                    description = ''
                    for line in lines:
                        if line.startswith('# '):
                            name = line[2:].strip()
                        elif line.strip() and not line.startswith('#') and not description:
                            description = line.strip()
                            break
                    skills.append({
                        "name": name,
                        "path": str(skill_dir),
                        "version": "1.0.0",
                        "description": description,
                        "category": "general"
                    })
                except Exception:
                    pass

        return {"skills": skills}

    def get_hexagram_timeline(self):
        """获取卦象时间线 - 读真实数据"""
        timeline_file = DATA_DIR / "hexagram_timeline.jsonl"
        entries = self._read_jsonl(timeline_file, 50)
        return {
            "daily_timeline": entries[-24:],
            "hourly_timeline": entries[-12:],
            "transitions": [],
            "anomaly_transitions": [],
            "current": entries[-1] if entries else {},
            "stability": {}
        }

    def get_logs(self):
        """获取日志 - 读真实事件"""
        events_file = DATA_DIR / "events.jsonl"
        events = self._read_jsonl(events_file, 50)

        logs = []
        for event in events:
            ts = event.get('timestamp', '')
            if isinstance(ts, (int, float)):
                t_str = time.strftime('%H:%M:%S', time.localtime(ts))
            elif isinstance(ts, str) and len(ts) >= 19:
                t_str = ts[11:19]
            else:
                t_str = '--:--:--'

            logs.append({
                'time': t_str,
                'level': event.get('level', event.get('severity', 'info')),
                'message': event.get('message', event.get('description', json.dumps(event, ensure_ascii=False)[:120]))
            })

        # 不再返回假日志
        return {'logs': logs}

    def log_message(self, format, *args):
        if '/api/metrics' not in format:
            print(f"[{self.address_string()}] {format % args}")


print("=" * 60)
print(f"AIOS Dashboard v4.0 启动: http://localhost:{PORT}")
print(f"数据源: {DATA_DIR}")
print(f"模式: 真实数据（无随机/无 fallback 假数据）")
print("=" * 60)

httpd = HTTPServer(('127.0.0.1', PORT), DashboardHandler)
httpd.serve_forever()
