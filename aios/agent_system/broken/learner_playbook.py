#!/usr/bin/env python3
"""
AIOS Playbook Learner Agent - 涓撻棬瀛︿範 Playbook 鏁堟灉

鑱岃矗锛?1. 鐩戞帶鎵€鏈?Playbook 鐨勬墽琛岃褰?2. 鍒嗘瀽鎵ц鎴愬姛鐜囥€佷慨澶嶆晥鏋?3. 璇嗗埆鏈€鏈夋晥鍜屾棤鏁堢殑 Playbook
4. 鐢熸垚 Playbook 浼樺寲寤鸿
5. 杩借釜 Playbook 鏁堟灉瓒嬪娍

瀛︿範鍐呭锛?- 鍝簺 Playbook 鎴愬姛鐜囨渶楂?- 鍝簺 Playbook 淇鏁堟灉鏈€濂?- 鍝簺 Playbook 浠庢湭鎴愬姛杩?- 涓嶅悓閿欒绫诲瀷閫傚悎鍝釜 Playbook
- Playbook 鏁堟灉闅忔椂闂寸殑鍙樺寲

杈撳嚭锛?- PLAYBOOK_LEARNER_OK - 鏃犻噸瑕佸彂鐜?- PLAYBOOK_LEARNER_SUGGESTIONS:N - 鐢熸垚浜?N 鏉″缓璁?"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

# 娣诲姞 AIOS 璺緞
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class PlaybookLearnerAgent:
    """Playbook 瀛︿範 Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"
        self.playbooks_dir = AIOS_ROOT / "playbooks"

    def run(self) -> Dict:
        """杩愯瀛︿範娴佺▼"""
        print("=" * 60)
        print("  Playbook Learner Agent")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "playbook_learner",
            "learning": {}
        }

        # 1. 鏀堕泦 Playbook 鎵ц鏁版嵁
        print("[1/5] 鏀堕泦 Playbook 鎵ц鏁版嵁...")
        playbook_data = self._collect_playbook_data()
        report["learning"]["raw_data"] = playbook_data
        print(f"  收集了 {playbook_data['total_executions']} 次执行")

        # 2. 鍒嗘瀽鎴愬姛鐜?        print("[2/5] 鍒嗘瀽鎴愬姛鐜?..")
        success_analysis = self._analyze_success_rate(playbook_data)
        report["learning"]["success_rate"] = success_analysis
        print(f"  鏈€浣?Playbook: {success_analysis.get('best_playbook', 'N/A')}")

        # 3. 鍒嗘瀽淇鏁堟灉
        print("[3/5] 鍒嗘瀽淇鏁堟灉...")
        fix_analysis = self._analyze_fix_effectiveness(playbook_data)
        report["learning"]["fix_effectiveness"] = fix_analysis
        print(f"  鏈€鏈夋晥 Playbook: {fix_analysis.get('most_effective', 'N/A')}")

        # 4. 璇嗗埆鏃犳晥 Playbook
        print("[4/5] 璇嗗埆鏃犳晥 Playbook...")
        ineffective = self._identify_ineffective_playbooks(playbook_data)
        report["learning"]["ineffective"] = ineffective
        print(f"  璇嗗埆浜?{len(ineffective.get('playbooks', []))} 涓棤鏁?Playbook")

        # 5. 鐢熸垚寤鸿
        print("[5/5] 鐢熸垚寤鸿...")
        suggestions = self._generate_suggestions(report["learning"])
        report["suggestions"] = suggestions
        print(f"  生成了 {len(suggestions)} 条建议")

        # 淇濆瓨鎶ュ憡
        self._save_report(report)

        print()
        print("=" * 60)
        if suggestions:
            print(f"  完成！生成 {len(suggestions)} 条建议")
        else:
            print("  瀹屾垚锛佹棤閲嶈鍙戠幇")
        print("=" * 60)

        return report

    def _collect_playbook_data(self) -> Dict:
        """鏀堕泦 Playbook 鎵ц鏁版嵁"""
        playbook_stats = defaultdict(lambda: {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "fixes": 0,  # 鎴愬姛淇闂鐨勬鏁?            "no_fixes": 0,  # 鎵ц鎴愬姛浣嗛棶棰樻湭淇
            "error_types": []
        })
        
        if not self.events_file.exists():
            return {"total_executions": 0, "playbooks": {}}

        # 璇诲彇鏈€杩?7 澶╃殑鏁版嵁
        cutoff = datetime.now() - timedelta(days=7)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # 鍙鐞?reactor_action 浜嬩欢
                    if event.get("type") != "reactor_action":
                        continue
                    
                    # 妫€鏌ユ椂闂?                    event_time = datetime.fromisoformat(event.get("timestamp", ""))
                    if event_time < cutoff:
                        continue
                    
                    playbook = event.get("playbook_id", "unknown")
                    success = event.get("success", False)
                    fixed = event.get("fixed", False)  # 鏄惁鐪熸淇浜嗛棶棰?                    error_type = event.get("error_type", "")
                    
                    playbook_stats[playbook]["executions"] += 1
                    if success:
                        playbook_stats[playbook]["successes"] += 1
                        if fixed:
                            playbook_stats[playbook]["fixes"] += 1
                        else:
                            playbook_stats[playbook]["no_fixes"] += 1
                    else:
                        playbook_stats[playbook]["failures"] += 1
                    
                    if error_type:
                        playbook_stats[playbook]["error_types"].append(error_type)
                    
                except Exception as e:
                    continue

        return {
            "total_executions": sum(s["executions"] for s in playbook_stats.values()),
            "playbooks": dict(playbook_stats)
        }

    def _analyze_success_rate(self, data: Dict) -> Dict:
        """鍒嗘瀽鎴愬姛鐜?""
        playbooks = data.get("playbooks", {})
        
        success_rates = {}
        for playbook, stats in playbooks.items():
            if stats["executions"] >= 3:  # 鑷冲皯 3 娆℃墽琛?                success_rates[playbook] = {
                    "executions": stats["executions"],
                    "success_rate": stats["successes"] / stats["executions"],
                    "failures": stats["failures"]
                }
        
        # 鎵惧嚭鏈€浣冲拰鏈€宸?        if success_rates:
            best = max(success_rates.items(), key=lambda x: x[1]["success_rate"])
            worst = min(success_rates.items(), key=lambda x: x[1]["success_rate"])
            
            return {
                "playbooks": success_rates,
                "best_playbook": best[0],
                "best_rate": best[1]["success_rate"],
                "worst_playbook": worst[0],
                "worst_rate": worst[1]["success_rate"]
            }
        
        return {"playbooks": {}}

    def _analyze_fix_effectiveness(self, data: Dict) -> Dict:
        """鍒嗘瀽淇鏁堟灉"""
        playbooks = data.get("playbooks", {})
        
        fix_rates = {}
        for playbook, stats in playbooks.items():
            if stats["successes"] >= 3:  # 鑷冲皯 3 娆℃垚鍔熸墽琛?                fix_rates[playbook] = {
                    "successes": stats["successes"],
                    "fixes": stats["fixes"],
                    "fix_rate": stats["fixes"] / stats["successes"],  # 鎴愬姛鎵ц涓湡姝ｄ慨澶嶇殑姣斾緥
                    "no_fixes": stats["no_fixes"]
                }
        
        # 鎵惧嚭鏈€鏈夋晥鍜屾渶鏃犳晥
        if fix_rates:
            most_effective = max(fix_rates.items(), key=lambda x: x[1]["fix_rate"])
            least_effective = min(fix_rates.items(), key=lambda x: x[1]["fix_rate"])
            
            return {
                "playbooks": fix_rates,
                "most_effective": most_effective[0],
                "most_effective_rate": most_effective[1]["fix_rate"],
                "least_effective": least_effective[0],
                "least_effective_rate": least_effective[1]["fix_rate"]
            }
        
        return {"playbooks": {}}

    def _identify_ineffective_playbooks(self, data: Dict) -> Dict:
        """璇嗗埆鏃犳晥 Playbook"""
        playbooks = data.get("playbooks", {})
        
        ineffective = []
        for playbook, stats in playbooks.items():
            # 鏉′欢锛氭墽琛?鈮? 娆★紝浣嗘垚鍔熺巼 <30% 鎴栦慨澶嶇巼 <20%
            if stats["executions"] >= 5:
                success_rate = stats["successes"] / stats["executions"]
                fix_rate = stats["fixes"] / stats["successes"] if stats["successes"] > 0 else 0
                
                if success_rate < 0.3 or (success_rate >= 0.3 and fix_rate < 0.2):
                    ineffective.append({
                        "playbook": playbook,
                        "executions": stats["executions"],
                        "success_rate": success_rate,
                        "fix_rate": fix_rate,
                        "reason": "浣庢垚鍔熺巼" if success_rate < 0.3 else "浣庝慨澶嶇巼"
                    })
        
        return {
            "playbooks": ineffective,
            "count": len(ineffective)
        }

    def _generate_suggestions(self, learning: Dict) -> List[Dict]:
        """鐢熸垚寤鸿"""
        suggestions = []

        # 1. 鎴愬姛鐜囧缓璁?        success_data = learning.get("success_rate", {})
        if success_data.get("worst_rate", 1.0) < 0.5:
            suggestions.append({
                "type": "low_success_rate",
                "priority": "high",
                "playbook": success_data["worst_playbook"],
                "description": f"Playbook '{success_data['worst_playbook']}' 鎴愬姛鐜囦粎 {success_data['worst_rate']:.1%}",
                "action": "妫€鏌?Playbook 瑙勫垯鏄惁杩囨椂鎴栨潯浠惰繃浜庝弗鏍?
            })

        # 2. 淇鏁堟灉寤鸿
        fix_data = learning.get("fix_effectiveness", {})
        if fix_data.get("least_effective_rate", 1.0) < 0.3:
            suggestions.append({
                "type": "low_fix_rate",
                "priority": "high",
                "playbook": fix_data["least_effective"],
                "description": f"Playbook '{fix_data['least_effective']}' 淇鐜囦粎 {fix_data['least_effective_rate']:.1%}锛堟墽琛屾垚鍔熶絾闂鏈慨澶嶏級",
                "action": "浼樺寲 Playbook 鐨勪慨澶嶉€昏緫锛岀‘淇濈湡姝ｈВ鍐抽棶棰?
            })

        # 3. 鏃犳晥 Playbook 寤鸿
        ineffective_data = learning.get("ineffective", {})
        for item in ineffective_data.get("playbooks", []):
            suggestions.append({
                "type": "ineffective_playbook",
                "priority": "medium",
                "playbook": item["playbook"],
                "description": f"Playbook '{item['playbook']}' {item['reason']}锛堟垚鍔熺巼 {item['success_rate']:.1%}锛屼慨澶嶇巼 {item['fix_rate']:.1%}锛?,
                "action": f"鑰冭檻绂佺敤鎴栭噸鍐欐 Playbook"
            })

        return suggestions

    def _save_report(self, report: Dict):
        """淇濆瓨鎶ュ憡"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"playbook_learning_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n馃搫 鎶ュ憡宸蹭繚瀛? {report_file}")


def main():
    """涓诲嚱鏁?""
    agent = PlaybookLearnerAgent()
    report = agent.run()
    
    suggestions = report.get("suggestions", [])
    if suggestions:
        print(f"\nPLAYBOOK_LEARNER_SUGGESTIONS:{len(suggestions)}")
    else:
        print("\nPLAYBOOK_LEARNER_OK")


if __name__ == "__main__":
    main()

