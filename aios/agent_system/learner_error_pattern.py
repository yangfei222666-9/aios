#!/usr/bin/env python3
"""
AIOS Error Pattern Learner - 涓撻棬瀛︿範閿欒妯″紡

鑱岃矗锛?1. 鐩戞帶鎵€鏈夐敊璇簨浠?2. 璇嗗埆閲嶅鍑虹幇鐨勯敊璇ā寮?3. 鍒嗘瀽閿欒鏍瑰洜鍜屼紶鎾矾寰?4. 鐢熸垚閿欒棰勯槻寤鸿
5. 杩借釜閿欒瓒嬪娍

瀛︿範鍐呭锛?- 鍝簺閿欒鏈€甯歌
- 鍝簺閿欒浼氬鑷磋繛閿佸弽搴?- 鍝簺閿欒鍙互棰勯槻
- 閿欒鍙戠敓鐨勬椂闂磋寰?- 閿欒淇鐨勬湁鏁堟柟娉?
杈撳嚭锛?- ERROR_LEARNER_OK - 鏃犻噸瑕佸彂鐜?- ERROR_LEARNER_SUGGESTIONS:N - 鐢熸垚浜?N 鏉″缓璁?"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict, Counter

# 娣诲姞 AIOS 璺緞
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer

class ErrorPatternLearner:
    """閿欒妯″紡瀛︿範 Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = TraceAnalyzer()
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"

    def run(self) -> Dict:
        """杩愯瀛︿範娴佺▼"""
        print("=" * 60)
        print("  Error Pattern Learner")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "error_pattern_learner",
            "learning": {}
        }

        # 1. 鏀堕泦閿欒鏁版嵁
        print("[1/6] 鏀堕泦閿欒鏁版嵁...")
        error_data = self._collect_error_data()
        report["learning"]["raw_data"] = error_data
        print(f"  鏀堕泦浜?{error_data['total_errors']} 涓敊璇?)

        # 2. 璇嗗埆閲嶅閿欒
        print("[2/6] 璇嗗埆閲嶅閿欒...")
        repeat_analysis = self._identify_repeat_errors(error_data)
        report["learning"]["repeat_errors"] = repeat_analysis
        print(f"  璇嗗埆浜?{len(repeat_analysis.get('patterns', []))} 涓噸澶嶉敊璇ā寮?)

        # 3. 鍒嗘瀽閿欒鏍瑰洜
        print("[3/6] 鍒嗘瀽閿欒鏍瑰洜...")
        root_cause_analysis = self._analyze_root_causes(error_data)
        report["learning"]["root_causes"] = root_cause_analysis
        print(f"  璇嗗埆浜?{len(root_cause_analysis.get('causes', []))} 涓牴鍥?)

        # 4. 鍒嗘瀽閿欒浼犳挱
        print("[4/6] 鍒嗘瀽閿欒浼犳挱...")
        propagation_analysis = self._analyze_error_propagation(error_data)
        report["learning"]["propagation"] = propagation_analysis
        print(f"  璇嗗埆浜?{len(propagation_analysis.get('chains', []))} 涓敊璇摼")

        # 5. 鍒嗘瀽鏃堕棿瑙勫緥
        print("[5/6] 鍒嗘瀽鏃堕棿瑙勫緥...")
        temporal_analysis = self._analyze_temporal_patterns(error_data)
        report["learning"]["temporal"] = temporal_analysis
        print(f"  璇嗗埆浜?{len(temporal_analysis.get('patterns', []))} 涓椂闂磋寰?)

        # 6. 鐢熸垚寤鸿
        print("[6/6] 鐢熸垚寤鸿...")
        suggestions = self._generate_suggestions(report["learning"])
        report["suggestions"] = suggestions
        print(f"  鐢熸垚浜?{len(suggestions)} 鏉″缓璁?)

        # 淇濆瓨鎶ュ憡
        self._save_report(report)

        print()
        print("=" * 60)
        if suggestions:
            print(f"  瀹屾垚锛佺敓鎴?{len(suggestions)} 鏉″缓璁?)
        else:
            print("  瀹屾垚锛佹棤閲嶈鍙戠幇")
        print("=" * 60)

        return report

    def _collect_error_data(self) -> Dict:
        """鏀堕泦閿欒鏁版嵁"""
        errors = []
        
        # 浠?events.jsonl 鏀堕泦
        if self.events_file.exists():
            cutoff = datetime.now() - timedelta(days=7)
            
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # 鍙鐞嗛敊璇簨浠?                        if event.get("type") not in ["error", "failure", "exception"]:
                            continue
                        
                        # 妫€鏌ユ椂闂?                        timestamp_str = event.get("timestamp", "")
                        if not timestamp_str:
                            continue
                        event_time = datetime.fromisoformat(timestamp_str)
                        if event_time < cutoff:
                            continue
                        
                        errors.append({
                            "timestamp": event.get("timestamp"),
                            "error_type": event.get("error_type", "unknown"),
                            "error_message": event.get("error_message", ""),
                            "component": event.get("component", "unknown"),
                            "agent_id": event.get("agent_id", ""),
                            "context": event.get("context", {})
                        })
                    except:
                        continue
        
        # 浠?trace 鏁版嵁鏀堕泦澶辫触浠诲姟
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            if not trace.get("success", True):
                errors.append({
                    "timestamp": trace.get("timestamp", ""),
                    "error_type": trace.get("error_type", "task_failure"),
                    "error_message": trace.get("error_message", ""),
                    "component": "agent",
                    "agent_id": trace.get("agent_id", ""),
                    "context": trace.get("context", {})
                })
        
        return {
            "total_errors": len(errors),
            "errors": errors
        }

    def _identify_repeat_errors(self, data: Dict) -> Dict:
        """璇嗗埆閲嶅閿欒"""
        errors = data.get("errors", [])
        
        # 鎸夐敊璇鍚嶅垎缁?        error_signatures = defaultdict(list)
        for error in errors:
            # 鐢熸垚閿欒绛惧悕锛堢被鍨?+ 缁勪欢锛?            signature = f"{error['error_type']}@{error['component']}"
            error_signatures[signature].append(error)
        
        # 鎵惧嚭閲嶅 鈮? 娆＄殑閿欒
        repeat_patterns = []
        for signature, occurrences in error_signatures.items():
            if len(occurrences) >= 3:
                repeat_patterns.append({
                    "signature": signature,
                    "occurrences": len(occurrences),
                    "first_seen": occurrences[0]["timestamp"],
                    "last_seen": occurrences[-1]["timestamp"],
                    "affected_agents": list(set(e["agent_id"] for e in occurrences if e["agent_id"]))
                })
        
        # 鎸夊嚭鐜版鏁版帓搴?        repeat_patterns.sort(key=lambda x: x["occurrences"], reverse=True)
        
        return {
            "patterns": repeat_patterns,
            "total_patterns": len(repeat_patterns)
        }

    def _analyze_root_causes(self, data: Dict) -> Dict:
        """鍒嗘瀽閿欒鏍瑰洜"""
        errors = data.get("errors", [])
        
        # 缁熻閿欒绫诲瀷
        error_types = Counter(e["error_type"] for e in errors)
        
        # 缁熻缁勪欢
        components = Counter(e["component"] for e in errors)
        
        # 璇嗗埆鏍瑰洜锛堝嚭鐜伴鐜囨渶楂樼殑閿欒绫诲瀷锛?        root_causes = []
        for error_type, count in error_types.most_common(5):
            if count >= 3:
                # 鎵惧嚭璇ラ敊璇被鍨嬬殑鎵€鏈夊疄渚?                instances = [e for e in errors if e["error_type"] == error_type]
                affected_components = Counter(e["component"] for e in instances)
                
                root_causes.append({
                    "error_type": error_type,
                    "occurrences": count,
                    "affected_components": dict(affected_components),
                    "most_affected": affected_components.most_common(1)[0][0] if affected_components else "unknown"
                })
        
        return {
            "causes": root_causes,
            "total_error_types": len(error_types),
            "total_components": len(components)
        }

    def _analyze_error_propagation(self, data: Dict) -> Dict:
        """鍒嗘瀽閿欒浼犳挱锛堥敊璇摼锛?""
        errors = data.get("errors", [])
        
        # 鎸夋椂闂存帓搴?        errors_sorted = sorted(errors, key=lambda x: x["timestamp"])
        
        # 璇嗗埆閿欒閾撅紙5鍒嗛挓鍐呰繛缁彂鐢熺殑閿欒锛?        chains = []
        current_chain = []
        
        for i, error in enumerate(errors_sorted):
            # 璺宠繃绌?timestamp
            if not error.get("timestamp"):
                continue
            
            if not current_chain:
                current_chain.append(error)
            else:
                # 妫€鏌ユ椂闂撮棿闅?                try:
                    last_time = datetime.fromisoformat(current_chain[-1]["timestamp"])
                    curr_time = datetime.fromisoformat(error["timestamp"])
                except ValueError:
                    continue
                
                if (curr_time - last_time).total_seconds() <= 300:  # 5鍒嗛挓
                    current_chain.append(error)
                else:
                    # 淇濆瓨褰撳墠閾撅紙鈮?涓敊璇級
                    if len(current_chain) >= 2:
                        chains.append({
                            "length": len(current_chain),
                            "start_time": current_chain[0]["timestamp"],
                            "end_time": current_chain[-1]["timestamp"],
                            "error_types": [e["error_type"] for e in current_chain],
                            "components": [e["component"] for e in current_chain]
                        })
                    
                    # 寮€濮嬫柊閾?                    current_chain = [error]
        
        # 淇濆瓨鏈€鍚庝竴鏉￠摼
        if len(current_chain) >= 2:
            chains.append({
                "length": len(current_chain),
                "start_time": current_chain[0]["timestamp"],
                "end_time": current_chain[-1]["timestamp"],
                "error_types": [e["error_type"] for e in current_chain],
                "components": [e["component"] for e in current_chain]
            })
        
        return {
            "chains": chains,
            "total_chains": len(chains),
            "longest_chain": max(chains, key=lambda x: x["length"]) if chains else None
        }

    def _analyze_temporal_patterns(self, data: Dict) -> Dict:
        """鍒嗘瀽鏃堕棿瑙勫緥"""
        errors = data.get("errors", [])
        
        # 鎸夊皬鏃剁粺璁?        hourly_counts = Counter()
        for error in errors:
            try:
                hour = datetime.fromisoformat(error["timestamp"]).hour
                hourly_counts[hour] += 1
            except:
                continue
        
        # 璇嗗埆楂樺嘲鏃舵锛堥敊璇暟 > 骞冲潎鍊?* 1.5锛?        if hourly_counts:
            avg_count = sum(hourly_counts.values()) / len(hourly_counts)
            peak_hours = [hour for hour, count in hourly_counts.items() if count > avg_count * 1.5]
        else:
            peak_hours = []
        
        return {
            "patterns": [
                {
                    "type": "peak_hours",
                    "hours": sorted(peak_hours),
                    "description": f"閿欒楂樺嘲鏃舵锛歿', '.join(f'{h}:00' for h in sorted(peak_hours))}"
                }
            ] if peak_hours else [],
            "hourly_distribution": dict(hourly_counts)
        }

    def _generate_suggestions(self, learning: Dict) -> List[Dict]:
        """鐢熸垚寤鸿"""
        suggestions = []

        # 1. 閲嶅閿欒寤鸿
        repeat_data = learning.get("repeat_errors", {})
        for pattern in repeat_data.get("patterns", [])[:3]:  # 鍓?3 涓?            suggestions.append({
                "type": "repeat_error",
                "priority": "high",
                "description": f"閿欒 '{pattern['signature']}' 閲嶅鍑虹幇 {pattern['occurrences']} 娆?,
                "action": "鍒跺畾鑷姩淇绛栫暐鎴栨坊鍔犻闃叉€ф鏌?
            })

        # 2. 鏍瑰洜寤鸿
        root_cause_data = learning.get("root_causes", {})
        for cause in root_cause_data.get("causes", [])[:2]:  # 鍓?2 涓?            suggestions.append({
                "type": "root_cause",
                "priority": "high",
                "description": f"閿欒绫诲瀷 '{cause['error_type']}' 鏄富瑕佹牴鍥狅紙{cause['occurrences']} 娆★級锛屼富瑕佸奖鍝?{cause['most_affected']}",
                "action": f"浼樺厛淇 {cause['most_affected']} 缁勪欢鐨?{cause['error_type']} 闂"
            })

        # 3. 閿欒閾惧缓璁?        propagation_data = learning.get("propagation", {})
        if propagation_data.get("longest_chain"):
            chain = propagation_data["longest_chain"]
            suggestions.append({
                "type": "error_chain",
                "priority": "medium",
                "description": f"鍙戠幇閿欒閾撅紙{chain['length']} 涓繛缁敊璇級锛屾秹鍙婄粍浠讹細{', '.join(set(chain['components']))}",
                "action": "娣诲姞鐔旀柇鍣ㄦ垨閿欒闅旂鏈哄埗锛岄槻姝㈤敊璇紶鎾?
            })

        # 4. 鏃堕棿瑙勫緥寤鸿
        temporal_data = learning.get("temporal", {})
        for pattern in temporal_data.get("patterns", []):
            if pattern["type"] == "peak_hours":
                suggestions.append({
                    "type": "temporal_pattern",
                    "priority": "low",
                    "description": pattern["description"],
                    "action": "鍦ㄩ珮宄版椂娈靛鍔犵洃鎺ч鐜囨垨闄嶄綆璐熻浇"
                })

        return suggestions

    def _save_report(self, report: Dict):
        """淇濆瓨鎶ュ憡"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"error_pattern_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n馃搫 鎶ュ憡宸蹭繚瀛? {report_file}")


def main():
    """涓诲嚱鏁?""
    agent = ErrorPatternLearner()
    report = agent.run()
    
    suggestions = report.get("suggestions", [])
    if suggestions:
        print(f"\nERROR_LEARNER_SUGGESTIONS:{len(suggestions)}")
    else:
        print("\nERROR_LEARNER_OK")


if __name__ == "__main__":
    main()

