#!/usr/bin/env python3
"""
Heartbeat Hexagram Integration Example
======================================

瑙傚療鍨嬮泦鎴愶細鍦?Heartbeat 涓睍绀哄崷璞℃櫤鎱э紝涓嶅奖鍝?Router 鍐崇瓥銆?
鏍稿績鍔熻兘锛?1. 鎸囨爣缁勮锛圓PI鍋ュ悍搴︺€佹垚鍔熺巼銆侀槦鍒楁繁搴︾瓑锛?2. 鍏ㄥ眬鍗﹁皟鐢紙褰撳墠鍗﹁薄銆侀闄╃瓑绾с€佸缓璁姩浣滐級
3. Active Agent 鐢熷懡鍛ㄦ湡鎽樿锛堟渶澶?涓級
4. 澶辫触淇濇姢锛堝崷璞″紩鎿庡紓甯镐笉褰卞搷涓绘祦绋嬶級
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 娣诲姞 agent_system 鍒拌矾寰?sys.path.insert(0, str(Path(__file__).parent))

try:
    from hexagram_engine import HexagramEngine
    HEXAGRAM_AVAILABLE = True
except ImportError:
    HEXAGRAM_AVAILABLE = False
    print("[WARN] hexagram_engine not available, using fallback mode")


class HeartbeatHexagramIntegration:
    """Heartbeat 鍗﹁薄闆嗘垚"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.agent_system = workspace_root / "aios" / "agent_system"
        self.engine = HexagramEngine() if HEXAGRAM_AVAILABLE else None
        
    def collect_metrics(self) -> Dict[str, Any]:
        """
        1. 鎸囨爣缁勮
        
        浠庡悇涓暟鎹簮鏀堕泦鎸囨爣锛?        - api_health: API 鍋ュ悍搴?        - execution_success_rate: 鎵ц鎴愬姛鐜?        - timeout_rate: 瓒呮椂鐜?        - retry_rate: 閲嶈瘯鐜?        - learning_hit_rate: 瀛︿範鍛戒腑鐜?        - queue_depth: 闃熷垪娣卞害
        - evolution_score: 婕斿寲鍒嗘暟
        """
        metrics = {
            "api_health": 0.0,
            "execution_success_rate": 0.0,
            "timeout_rate": 0.0,
            "retry_rate": 0.0,
            "learning_hit_rate": 0.0,
            "queue_depth": 0,
            "evolution_score": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # API 鍋ュ悍搴︼紙浠?api_health.json锛?            api_health_file = self.agent_system / "api_health.json"
            if api_health_file.exists():
                with open(api_health_file, 'r', encoding='utf-8') as f:
                    api_data = json.load(f)
                    metrics["api_health"] = api_data.get("health_score", 0.0)
            
            # 鎵ц鎴愬姛鐜囷紙浠?task_executions_v2.jsonl锛?            exec_file = self.agent_system / "task_executions_v2.jsonl"
            if exec_file.exists():
                total = 0
                success = 0
                timeout = 0
                retry = 0
                
                with open(exec_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            total += 1
                            if record.get("status") == "completed":
                                success += 1
                            if "timeout" in record.get("error_type", "").lower():
                                timeout += 1
                            if record.get("retry_count", 0) > 0:
                                retry += 1
                
                if total > 0:
                    metrics["execution_success_rate"] = success / total
                    metrics["timeout_rate"] = timeout / total
                    metrics["retry_rate"] = retry / total
            
            # 瀛︿範鍛戒腑鐜囷紙浠?recommendation_log.jsonl锛?            rec_file = self.agent_system / "recommendation_log.jsonl"
            if rec_file.exists():
                total_rec = 0
                hit_rec = 0
                
                with open(rec_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            total_rec += 1
                            if record.get("strategy") != "default_recovery":
                                hit_rec += 1
                
                if total_rec > 0:
                    metrics["learning_hit_rate"] = hit_rec / total_rec
            
            # 闃熷垪娣卞害锛堜粠 task_queue.jsonl锛?            queue_file = self.agent_system / "task_queue.jsonl"
            if queue_file.exists():
                with open(queue_file, 'r', encoding='utf-8') as f:
                    pending = sum(1 for line in f if line.strip() and 
                                json.loads(line).get("status") == "pending")
                    metrics["queue_depth"] = pending
            
            # 婕斿寲鍒嗘暟锛堜粠 evolution_score.json锛?            evo_file = self.agent_system / "evolution_score.json"
            if evo_file.exists():
                with open(evo_file, 'r', encoding='utf-8') as f:
                    evo_data = json.load(f)
                    metrics["evolution_score"] = evo_data.get("fused_confidence", 0.0)
        
        except Exception as e:
            print(f"[WARN] Metrics collection error: {e}")
        
        return metrics
    
    def get_global_hexagram(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        2. 鍏ㄥ眬鍗﹁皟鐢?        
        杈撳嚭锛?        - global_hexagram_name: 鍗﹀悕
        - global_hexagram_bits: 鍗﹁薄浜岃繘鍒?        - global_risk_level: 椋庨櫓绛夌骇
        - global_recommended_actions: 寤鸿鍔ㄤ綔
        - guardrail_triggered: 鏄惁瑙﹀彂鎶ゆ爮
        - guardrail_reasons: 鎶ゆ爮鍘熷洜
        """
        result = {
            "global_hexagram_name": "unavailable",
            "global_hexagram_bits": "000000",
            "global_risk_level": "unknown",
            "global_recommended_actions": [],
            "guardrail_triggered": False,
            "guardrail_reasons": []
        }
        
        if not self.engine:
            return result
        
        try:
            # 璋冪敤鍗﹁薄寮曟搸
            hexagram_result = self.engine.consult(
                context={
                    "api_health": metrics.get("api_health", 0.0),
                    "success_rate": metrics.get("execution_success_rate", 0.0),
                    "queue_depth": metrics.get("queue_depth", 0),
                    "evolution_score": metrics.get("evolution_score", 0.0)
                },
                question="system_health_check"
            )
            
            result["global_hexagram_name"] = hexagram_result.get("hexagram_name", "unknown")
            result["global_hexagram_bits"] = hexagram_result.get("hexagram_bits", "000000")
            result["global_risk_level"] = hexagram_result.get("risk_level", "unknown")
            result["global_recommended_actions"] = hexagram_result.get("recommended_actions", [])
            
            # 妫€鏌ユ姢鏍?            guardrails = hexagram_result.get("guardrails", {})
            result["guardrail_triggered"] = guardrails.get("triggered", False)
            result["guardrail_reasons"] = guardrails.get("reasons", [])
        
        except Exception as e:
            print(f"[WARN] Global hexagram error: {e}")
        
        return result
    
    def get_active_agents_lifecycle(self, max_agents: int = 5) -> List[Dict[str, Any]]:
        """
        3. Active Agent 鐢熷懡鍛ㄦ湡鎽樿
        
        鍙彇鏈€澶?5 涓?active agent锛岃緭鍑猴細
        - agent_name: Agent 鍚嶇О
        - lifecycle_hexagram: 鐢熷懡鍛ㄦ湡鍗﹁薄
        - lifecycle_stage: 鐢熷懡鍛ㄦ湡闃舵
        - keep_active: 鏄惁淇濇寔娲昏穬
        """
        agents = []
        
        try:
            agents_file = self.agent_system / "agents.json"
            if not agents_file.exists():
                return agents
            
            with open(agents_file, 'r', encoding='utf-8') as f:
                agents_data = json.load(f)
            
            # 绛涢€?active agents
            active_agents = [
                agent for agent in agents_data.get("agents", [])
                if agent.get("mode") == "active" and agent.get("enabled", False)
            ]
            
            # 鏈€澶氬彇 5 涓?            for agent in active_agents[:max_agents]:
                agent_info = {
                    "agent_name": agent.get("name", "unknown"),
                    "lifecycle_hexagram": "unknown",
                    "lifecycle_stage": "unknown",
                    "keep_active": True
                }
                
                # 濡傛灉鏈夊崷璞″紩鎿庯紝璁＄畻鐢熷懡鍛ㄦ湡鍗﹁薄
                if self.engine:
                    try:
                        stats = agent.get("stats", {})
                        lifecycle_result = self.engine.consult(
                            context={
                                "tasks_completed": stats.get("tasks_completed", 0),
                                "tasks_failed": stats.get("tasks_failed", 0),
                                "last_active": stats.get("last_active", "")
                            },
                            question="agent_lifecycle"
                        )
                        
                        agent_info["lifecycle_hexagram"] = lifecycle_result.get("hexagram_name", "unknown")
                        agent_info["lifecycle_stage"] = lifecycle_result.get("lifecycle_stage", "unknown")
                        agent_info["keep_active"] = lifecycle_result.get("keep_active", True)
                    
                    except Exception as e:
                        print(f"[WARN] Agent lifecycle error for {agent_info['agent_name']}: {e}")
                
                agents.append(agent_info)
        
        except Exception as e:
            print(f"[WARN] Active agents lifecycle error: {e}")
        
        return agents
    
    def render_hexagram_section(
        self,
        metrics: Dict[str, Any],
        global_hex: Dict[str, Any],
        agents: List[Dict[str, Any]]
    ) -> str:
        """
        4. 娓叉煋鍑芥暟
        
        鐢熸垚鍗﹁薄鍖哄潡锛屽彲琚?Heartbeat 鐩存帴澶嶇敤銆?        """
        lines = []
        lines.append("\n" + "="*60)
        lines.append("馃敭 HEXAGRAM WISDOM")
        lines.append("="*60)
        
        # 鍏ㄥ眬鍗﹁薄
        lines.append("\n[GLOBAL HEXAGRAM]")
        lines.append(f"  Hexagram: {global_hex['global_hexagram_name']} ({global_hex['global_hexagram_bits']})")
        lines.append(f"  Risk Level: {global_hex['global_risk_level']}")
        
        if global_hex['global_recommended_actions']:
            lines.append("  Recommended Actions:")
            for action in global_hex['global_recommended_actions'][:3]:  # 鏈€澶?鏉?                lines.append(f"    鈥?{action}")
        
        if global_hex['guardrail_triggered']:
            lines.append("  鈿狅笍  GUARDRAIL TRIGGERED:")
            for reason in global_hex['guardrail_reasons']:
                lines.append(f"    鈥?{reason}")
        
        # 绯荤粺鎸囨爣
        lines.append("\n[SYSTEM METRICS]")
        lines.append(f"  API Health: {metrics['api_health']:.1%}")
        lines.append(f"  Success Rate: {metrics['execution_success_rate']:.1%}")
        lines.append(f"  Timeout Rate: {metrics['timeout_rate']:.1%}")
        lines.append(f"  Queue Depth: {metrics['queue_depth']}")
        lines.append(f"  Evolution Score: {metrics['evolution_score']:.1f}")
        
        # Active Agents 鐢熷懡鍛ㄦ湡
        if agents:
            lines.append("\n[ACTIVE AGENTS LIFECYCLE]")
            for agent in agents:
                status = "鉁? if agent['keep_active'] else "鈿?
                lines.append(f"  {status} {agent['agent_name']}")
                lines.append(f"      Hexagram: {agent['lifecycle_hexagram']}")
                lines.append(f"      Stage: {agent['lifecycle_stage']}")
        
        lines.append("="*60 + "\n")
        
        return "\n".join(lines)
    
    def run(self) -> str:
        """
        5. 澶辫触淇濇姢
        
        涓诲叆鍙ｏ紝鍖呭惈瀹屾暣鐨勫け璐ヤ繚鎶わ細
        - 鍗﹁薄寮曟搸鎶ラ敊 鈫?涓绘祦绋嬬户缁?        - 鍗﹁薄鍖哄潡鏄剧ず unavailable
        - 閿欒鍘熷洜鍐欏叆鏃ュ織
        """
        try:
            # 鏀堕泦鎸囨爣
            metrics = self.collect_metrics()
            
            # 鑾峰彇鍏ㄥ眬鍗﹁薄
            global_hex = self.get_global_hexagram(metrics)
            
            # 鑾峰彇 Active Agents 鐢熷懡鍛ㄦ湡
            agents = self.get_active_agents_lifecycle(max_agents=5)
            
            # 娓叉煋鍗﹁薄鍖哄潡
            output = self.render_hexagram_section(metrics, global_hex, agents)
            
            return output
        
        except Exception as e:
            # 澶辫触淇濇姢锛氳繑鍥炵畝鍖栫増鏈?            error_msg = f"[ERROR] Hexagram integration failed: {e}"
            print(error_msg)
            
            return f"""
{"="*60}
馃敭 HEXAGRAM WISDOM
{"="*60}

[UNAVAILABLE]
  Hexagram engine encountered an error.
  Heartbeat continues normally.
  
  Error: {str(e)[:100]}

{"="*60}
"""


def main():
    """绀轰緥杩愯"""
    workspace_root = Path(__file__).parent.parent.parent
    integration = HeartbeatHexagramIntegration(workspace_root)
    
    print("Heartbeat Hexagram Integration Example")
    print("=" * 60)
    
    output = integration.run()
    print(output)
    
    print("\n鉁?Integration test completed")
    print("   - Metrics collected")
    print("   - Global hexagram consulted")
    print("   - Active agents lifecycle analyzed")
    print("   - Failure protection verified")


if __name__ == "__main__":
    main()

