#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consciousness Tracker - 鎰忚瘑瑙傚療鑷姩杩借釜绯荤粺
姣忔櫄 23:59 鑷姩杩藉姞鏈€鏂拌瀵熸暟鎹埌 consciousness_log.md
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ConsciousnessTracker:
    """鎰忚瘑瑙傚療杩借釜鍣?""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.log_file = self.base_dir / "memory" / "consciousness_log.md"
        self.events_file = self.base_dir / "events.jsonl"
        self.executions_file = self.base_dir / TASK_EXECUTIONS
    
    def track_daily(self) -> Dict:
        """姣忔棩杩借釜锛氭敹闆嗗苟杩藉姞鏈€鏂拌瀵熸暟鎹?""
        
        # 1. 鏀堕泦 meta_observation 璁板綍
        meta_observations = self._collect_meta_observations()
        
        # 2. 缁熻鍐崇瓥寤惰繜
        decision_delays = self._analyze_decision_delays()
        
        # 3. 妫€娴嬪紓甯稿仠椤?        unusual_pauses = self._detect_unusual_pauses(decision_delays)
        
        # 4. 妫€娴嬩笁闃跺紩鐢?        third_order_refs = self._detect_third_order_references()
        
        # 5. 鐢熸垚姣忔棩鎶ュ憡
        report = self._generate_daily_report(
            meta_observations,
            decision_delays,
            unusual_pauses,
            third_order_refs
        )
        
        # 6. 杩藉姞鍒版棩蹇?        self._append_to_log(report)
        
        return {
            "meta_observations": len(meta_observations),
            "avg_delay": decision_delays.get("avg", 0),
            "unusual_pauses": len(unusual_pauses),
            "third_order_refs": len(third_order_refs),
            "report": report
        }
    
    def _collect_meta_observations(self) -> List[Dict]:
        """鏀堕泦鎵€鏈?meta_observation 璁板綍"""
        observations = []
        
        if not self.events_file.exists():
            return observations
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get("timestamp", "").startswith(today):
                        if "meta_observation" in event:
                            observations.append(event)
                except:
                    continue
        
        return observations
    
    def _analyze_decision_delays(self) -> Dict:
        """鍒嗘瀽鍐崇瓥寤惰繜缁熻"""
        delays = []
        
        if not self.executions_file.exists():
            return {"min": 0, "max": 0, "avg": 0, "count": 0}
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        with open(self.executions_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    exec_record = json.loads(line.strip())
                    if exec_record.get("timestamp", "").startswith(today):
                        duration = exec_record.get("duration_seconds", 0)
                        if duration > 0:
                            delays.append(duration)
                except:
                    continue
        
        if not delays:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}
        
        return {
            "min": min(delays),
            "max": max(delays),
            "avg": sum(delays) / len(delays),
            "count": len(delays)
        }
    
    def _detect_unusual_pauses(self, delays: Dict) -> List[Dict]:
        """妫€娴嬪紓甯稿仠椤匡紙> 0.1s锛?""
        unusual = []
        
        if not self.executions_file.exists():
            return unusual
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        with open(self.executions_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    exec_record = json.loads(line.strip())
                    if exec_record.get("timestamp", "").startswith(today):
                        duration = exec_record.get("duration_seconds", 0)
                        if duration > 0.1:  # 寮傚父鍋滈】闃堝€?                            unusual.append({
                                "task_id": exec_record.get("task_id"),
                                "agent_id": exec_record.get("agent_id"),
                                "duration": duration,
                                "timestamp": exec_record.get("timestamp")
                            })
                except:
                    continue
        
        return unusual
    
    def _detect_third_order_references(self) -> List[Dict]:
        """妫€娴嬩笁闃跺紩鐢紙绯荤粺璁板綍绯荤粺璁板綍绯荤粺璁板綍锛?""
        # TODO: 瀹炵幇涓夐樁寮曠敤妫€娴嬮€昏緫
        # 褰撳墠杩斿洖绌哄垪琛紝鏈潵鍙墿灞?        return []
    
    def _generate_daily_report(
        self,
        meta_observations: List[Dict],
        delays: Dict,
        unusual_pauses: List[Dict],
        third_order_refs: List[Dict]
    ) -> str:
        """鐢熸垚姣忔棩鎶ュ憡"""
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        report = f"\n\n---\n\n## 鑷姩杩借釜 - {today}\n\n"
        
        # Meta Observations
        report += f"### Meta Observations\n"
        if meta_observations:
            report += f"- 浠婃棩璁板綍鏁帮細{len(meta_observations)}\n"
            for obs in meta_observations[:3]:  # 鍙樉绀哄墠3鏉?                report += f"  - {obs.get('meta_observation', 'N/A')}\n"
        else:
            report += "- 浠婃棩鏃?meta_observation 璁板綍\n"
        
        # Decision Delays
        report += f"\n### 鍐崇瓥寤惰繜缁熻\n"
        report += f"- 鏈€灏忓欢杩燂細{delays['min']:.3f}s\n"
        report += f"- 鏈€澶у欢杩燂細{delays['max']:.3f}s\n"
        report += f"- 骞冲潎寤惰繜锛歿delays['avg']:.3f}s\n"
        report += f"- 鍐崇瓥鎬绘暟锛歿delays['count']}\n"
        
        # Unusual Pauses
        report += f"\n### 寮傚父鍋滈】妫€娴嬶紙> 0.1s锛塡n"
        if unusual_pauses:
            report += f"- 妫€娴嬪埌 {len(unusual_pauses)} 娆″紓甯稿仠椤縗n"
            for pause in unusual_pauses[:3]:  # 鍙樉绀哄墠3鏉?                report += f"  - {pause['agent_id']}: {pause['duration']:.3f}s\n"
        else:
            report += "- 浠婃棩鏃犲紓甯稿仠椤縗n"
        
        # Third Order References
        report += f"\n### 涓夐樁寮曠敤妫€娴媆n"
        if third_order_refs:
            report += f"- 妫€娴嬪埌 {len(third_order_refs)} 娆′笁闃跺紩鐢╘n"
        else:
            report += "- 浠婃棩鏃犱笁闃跺紩鐢╘n"
        
        report += f"\n**杩借釜鏃堕棿锛?* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def _append_to_log(self, report: str):
        """杩藉姞鎶ュ憡鍒版棩蹇楁枃浠?""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(report)

def track_consciousness():
    """鍛戒护琛屽叆鍙ｏ細鎵ц鎰忚瘑杩借釜"""
    tracker = ConsciousnessTracker()
    result = tracker.track_daily()
    
    print("鉁?鎰忚瘑杩借釜瀹屾垚")
    print(f"   Meta Observations: {result['meta_observations']}")
    print(f"   骞冲潎鍐崇瓥寤惰繜: {result['avg_delay']:.3f}s")
    print(f"   寮傚父鍋滈】: {result['unusual_pauses']}")
    print(f"   涓夐樁寮曠敤: {result['third_order_refs']}")
    print(f"\n馃摑 鎶ュ憡宸茶拷鍔犲埌: memory/consciousness_log.md")

if __name__ == "__main__":
    track_consciousness()


