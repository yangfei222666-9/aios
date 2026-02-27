#!/usr/bin/env python3
"""
AIOS Optimization Learner - 涓撻棬瀛︿範浼樺寲鏁堟灉

鑱岃矗锛?1. 鐩戞帶鎵€鏈変紭鍖栨搷浣滅殑鎵ц璁板綍
2. 鍒嗘瀽浼樺寲鍓嶅悗鐨勬€ц兘鍙樺寲
3. 璇嗗埆鏈夋晥鍜屾棤鏁堢殑浼樺寲
4. 鐢熸垚浼樺寲绛栫暐寤鸿
5. 杩借釜浼樺寲鏁堟灉瓒嬪娍

瀛︿範鍐呭锛?- 鍝簺浼樺寲鏈€鏈夋晥
- 鍝簺浼樺寲娌℃湁鏁堟灉鎴栧弽鏁堟灉
- 涓嶅悓鍦烘櫙閫傚悎鍝浼樺寲
- 浼樺寲鐨勬渶浣虫椂鏈?- 浼樺寲鏁堟灉鐨勬寔缁€?
杈撳嚭锛?- OPTIMIZATION_LEARNER_OK - 鏃犻噸瑕佸彂鐜?- OPTIMIZATION_LEARNER_SUGGESTIONS:N - 鐢熸垚浜?N 鏉″缓璁?"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

# 娣诲姞 AIOS 璺緞
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class OptimizationLearner:
    """浼樺寲鏁堟灉瀛︿範 Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.optimizer_reports_dir = AIOS_ROOT / "agent_system" / "data" / "optimizer_reports"
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"

    def run(self) -> Dict:
        """杩愯瀛︿範娴佺▼"""
        print("=" * 60)
        print("  Optimization Learner")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "optimization_learner",
            "learning": {}
        }

        # 1. 鏀堕泦浼樺寲鏁版嵁
        print("[1/5] 鏀堕泦浼樺寲鏁版嵁...")
        optimization_data = self._collect_optimization_data()
        report["learning"]["raw_data"] = optimization_data
        print(f"  收集了 {optimization_data['total_optimizations']} 个优化")

        # 2. 鍒嗘瀽浼樺寲鏁堟灉
        print("[2/5] 鍒嗘瀽浼樺寲鏁堟灉...")
        effectiveness_analysis = self._analyze_effectiveness(optimization_data)
        report["learning"]["effectiveness"] = effectiveness_analysis
        print(f"  有效优化：{effectiveness_analysis.get('effective_count', 0)} 个")

        # 3. 璇嗗埆鏃犳晥浼樺寲
        print("[3/5] 璇嗗埆鏃犳晥浼樺寲...")
        ineffective_analysis = self._identify_ineffective(optimization_data)
        report["learning"]["ineffective"] = ineffective_analysis
        print(f"  无效优化：{len(ineffective_analysis.get('optimizations', []))} 个")

        # 4. 鍒嗘瀽浼樺寲瓒嬪娍
        print("[4/5] 鍒嗘瀽浼樺寲瓒嬪娍...")
        trend_analysis = self._analyze_trends(optimization_data)
        report["learning"]["trends"] = trend_analysis
        print(f"  识别了 {len(trend_analysis.get('trends', []))} 个趋势")

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

    def _collect_optimization_data(self) -> Dict:
        """鏀堕泦浼樺寲鏁版嵁"""
        optimizations = []
        
        # 浠?optimizer_reports 璇诲彇
        if self.optimizer_reports_dir.exists():
            for report_file in sorted(self.optimizer_reports_dir.glob("optimizer_*.json")):
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    
                    timestamp = report.get("timestamp", "")
                    phases = report.get("phases", {})
                    
                    # 鎻愬彇搴旂敤鐨勪紭鍖?                    results = phases.get("results", {})
                    for opt in results.get("applied_optimizations", []):
                        optimizations.append({
                            "timestamp": timestamp,
                            "type": opt.get("type", "unknown"),
                            "target": opt.get("target", ""),
                            "description": opt.get("description", ""),
                            "risk": opt.get("risk", "low"),
                            "expected_improvement": opt.get("expected_improvement", ""),
                            "actual_improvement": None  # 闇€瑕佸悗缁獙璇?                        })
                except:
                    continue
        
        # 浠?events.jsonl 璇诲彇浼樺寲鎵ц璁板綍
        if self.events_file.exists():
            cutoff = datetime.now() - timedelta(days=7)
            
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # 鍙鐞嗕紭鍖栦簨浠?                        if event.get("type") != "optimization":
                            continue
                        
                        # 妫€鏌ユ椂闂?                        event_time = datetime.fromisoformat(event.get("timestamp", ""))
                        if event_time < cutoff:
                            continue
                        
                        optimizations.append({
                            "timestamp": event.get("timestamp"),
                            "type": event.get("optimization_type", "unknown"),
                            "target": event.get("target", ""),
                            "description": event.get("description", ""),
                            "risk": event.get("risk", "low"),
                            "expected_improvement": event.get("expected_improvement", ""),
                            "actual_improvement": event.get("actual_improvement", None)
                        })
                    except:
                        continue
        
        return {
            "total_optimizations": len(optimizations),
            "optimizations": optimizations
        }

    def _analyze_effectiveness(self, data: Dict) -> Dict:
        """鍒嗘瀽浼樺寲鏁堟灉"""
        optimizations = data.get("optimizations", [])
        
        # 鎸夌被鍨嬪垎缁?        by_type = defaultdict(lambda: {
            "total": 0,
            "effective": 0,
            "ineffective": 0,
            "unknown": 0
        })
        
        for opt in optimizations:
            opt_type = opt["type"]
            by_type[opt_type]["total"] += 1
            
            # 鍒ゆ柇鏁堟灉
            actual = opt.get("actual_improvement")
            if actual is None:
                by_type[opt_type]["unknown"] += 1
            elif actual == "positive" or (isinstance(actual, (int, float)) and actual > 0):
                by_type[opt_type]["effective"] += 1
            else:
                by_type[opt_type]["ineffective"] += 1
        
        # 璁＄畻鏈夋晥鐜?        effectiveness = {}
        for opt_type, stats in by_type.items():
            if stats["total"] - stats["unknown"] > 0:
                effectiveness[opt_type] = {
                    "total": stats["total"],
                    "effective": stats["effective"],
                    "ineffective": stats["ineffective"],
                    "effectiveness_rate": stats["effective"] / (stats["total"] - stats["unknown"])
                }
        
        # 鎵惧嚭鏈€鏈夋晥鍜屾渶鏃犳晥鐨勭被鍨?        if effectiveness:
            most_effective = max(effectiveness.items(), key=lambda x: x[1]["effectiveness_rate"])
            least_effective = min(effectiveness.items(), key=lambda x: x[1]["effectiveness_rate"])
            
            return {
                "by_type": effectiveness,
                "most_effective_type": most_effective[0],
                "most_effective_rate": most_effective[1]["effectiveness_rate"],
                "least_effective_type": least_effective[0],
                "least_effective_rate": least_effective[1]["effectiveness_rate"],
                "effective_count": sum(s["effective"] for s in by_type.values())
            }
        
        return {"by_type": {}, "effective_count": 0}

    def _identify_ineffective(self, data: Dict) -> Dict:
        """璇嗗埆鏃犳晥浼樺寲"""
        optimizations = data.get("optimizations", [])
        
        ineffective = []
        for opt in optimizations:
            actual = opt.get("actual_improvement")
            
            # 鏉′欢锛氭湁瀹為檯鏁堟灉鏁版嵁锛屼笖鏁堟灉涓鸿礋鎴栭浂
            if actual is not None:
                if actual == "negative" or (isinstance(actual, (int, float)) and actual <= 0):
                    ineffective.append({
                        "type": opt["type"],
                        "target": opt["target"],
                        "description": opt["description"],
                        "expected": opt["expected_improvement"],
                        "actual": actual,
                        "timestamp": opt["timestamp"]
                    })
        
        return {
            "optimizations": ineffective,
            "count": len(ineffective)
        }

    def _analyze_trends(self, data: Dict) -> Dict:
        """鍒嗘瀽浼樺寲瓒嬪娍"""
        optimizations = data.get("optimizations", [])
        
        # 鎸夋椂闂存帓搴?        optimizations_sorted = sorted(optimizations, key=lambda x: x["timestamp"])
        
        # 鎸夊懆缁熻
        weekly_stats = defaultdict(lambda: {"total": 0, "effective": 0})
        
        for opt in optimizations_sorted:
            try:
                week = datetime.fromisoformat(opt["timestamp"]).strftime("%Y-W%W")
                weekly_stats[week]["total"] += 1
                
                actual = opt.get("actual_improvement")
                if actual == "positive" or (isinstance(actual, (int, float)) and actual > 0):
                    weekly_stats[week]["effective"] += 1
            except:
                continue
        
        # 璇嗗埆瓒嬪娍
        trends = []
        weeks = sorted(weekly_stats.keys())
        
        if len(weeks) >= 2:
            # 姣旇緝鏈€杩戜袱鍛?            recent_week = weekly_stats[weeks[-1]]
            prev_week = weekly_stats[weeks[-2]]
            
            if recent_week["total"] > prev_week["total"] * 1.5:
                trends.append({
                    "type": "increasing_optimizations",
                    "description": f"浼樺寲棰戠巼涓婂崌锛坽prev_week['total']} 鈫?{recent_week['total']}锛?
                })
            
            if recent_week["total"] > 0 and prev_week["total"] > 0:
                recent_rate = recent_week["effective"] / recent_week["total"]
                prev_rate = prev_week["effective"] / prev_week["total"]
                
                if recent_rate < prev_rate * 0.7:
                    trends.append({
                        "type": "declining_effectiveness",
                        "description": f"浼樺寲鏈夋晥鐜囦笅闄嶏紙{prev_rate:.1%} 鈫?{recent_rate:.1%}锛?
                    })
        
        return {
            "trends": trends,
            "weekly_stats": dict(weekly_stats)
        }

    def _generate_suggestions(self, learning: Dict) -> List[Dict]:
        """鐢熸垚寤鸿"""
        suggestions = []

        # 1. 鏈夋晥鎬у缓璁?        effectiveness_data = learning.get("effectiveness", {})
        if effectiveness_data.get("least_effective_rate", 1.0) < 0.3:
            suggestions.append({
                "type": "low_effectiveness",
                "priority": "high",
                "optimization_type": effectiveness_data["least_effective_type"],
                "description": f"浼樺寲绫诲瀷 '{effectiveness_data['least_effective_type']}' 鏈夋晥鐜囦粎 {effectiveness_data['least_effective_rate']:.1%}",
                "action": f"鍋滄浣跨敤姝ょ被浼樺寲锛屾垨閲嶆柊璁捐绛栫暐"
            })

        # 2. 鏃犳晥浼樺寲寤鸿
        ineffective_data = learning.get("ineffective", {})
        if ineffective_data.get("count", 0) >= 3:
            suggestions.append({
                "type": "too_many_ineffective",
                "priority": "medium",
                "description": f"鍙戠幇 {ineffective_data['count']} 涓棤鏁堜紭鍖?,
                "action": "瀹℃煡浼樺寲绛栫暐锛屾彁楂樹紭鍖栬川閲?
            })

        # 3. 瓒嬪娍寤鸿
        trend_data = learning.get("trends", {})
        for trend in trend_data.get("trends", []):
            if trend["type"] == "declining_effectiveness":
                suggestions.append({
                    "type": "declining_trend",
                    "priority": "high",
                    "description": trend["description"],
                    "action": "妫€鏌ヤ紭鍖栫瓥鐣ユ槸鍚﹁繃鏃讹紝鎴栫郴缁熸槸鍚﹀凡杈惧埌浼樺寲鐡堕"
                })

        # 4. 鏈€浣冲疄璺靛缓璁?        if effectiveness_data.get("most_effective_rate", 0) >= 0.8:
            suggestions.append({
                "type": "best_practice",
                "priority": "low",
                "optimization_type": effectiveness_data["most_effective_type"],
                "description": f"浼樺寲绫诲瀷 '{effectiveness_data['most_effective_type']}' 琛ㄧ幇浼樼锛堟湁鏁堢巼 {effectiveness_data['most_effective_rate']:.1%}锛?,
                "action": "鎺ㄥ箍姝ょ被浼樺寲鍒版洿澶氬満鏅?
            })

        return suggestions

    def _save_report(self, report: Dict):
        """淇濆瓨鎶ュ憡"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"optimization_learning_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n馃搫 鎶ュ憡宸蹭繚瀛? {report_file}")


def main():
    """涓诲嚱鏁?""
    agent = OptimizationLearner()
    report = agent.run()
    
    suggestions = report.get("suggestions", [])
    if suggestions:
        print(f"\nOPTIMIZATION_LEARNER_SUGGESTIONS:{len(suggestions)}")
    else:
        print("\nOPTIMIZATION_LEARNER_OK")


if __name__ == "__main__":
    main()

