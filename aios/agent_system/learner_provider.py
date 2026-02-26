#!/usr/bin/env python3
"""
AIOS Provider Learner Agent - 涓撻棬瀛︿範 Provider 鎬ц兘

鑱岃矗锛?1. 鐩戞帶鎵€鏈?Provider 鐨勮皟鐢ㄨ褰?2. 鍒嗘瀽鎴愬姛鐜囥€佸搷搴旀椂闂淬€侀敊璇被鍨?3. 璇嗗埆鏈€浣?Provider 鍜岄棶棰?Provider
4. 鐢熸垚 Provider 鍒囨崲寤鸿
5. 杩借釜 Provider 鎬ц兘瓒嬪娍

瀛︿範鍐呭锛?- 鍝釜 Provider 鎴愬姛鐜囨渶楂?- 鍝釜 Provider 鍝嶅簲鏈€蹇?- 鍝簺閿欒绫诲瀷鏈€甯歌
- 涓嶅悓浠诲姟绫诲瀷閫傚悎鍝釜 Provider
- Provider 鎬ц兘闅忔椂闂寸殑鍙樺寲瓒嬪娍

杈撳嚭锛?- PROVIDER_LEARNER_OK - 鏃犻噸瑕佸彂鐜?- PROVIDER_LEARNER_SUGGESTIONS:N - 鐢熸垚浜?N 鏉″缓璁?"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

# 娣诲姞 AIOS 璺緞
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class ProviderLearnerAgent:
    """Provider 瀛︿範 Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"

    def run(self) -> Dict:
        """杩愯瀛︿範娴佺▼"""
        print("=" * 60)
        print("  Provider Learner Agent")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "provider_learner",
            "learning": {}
        }

        # 1. 鏀堕泦 Provider 璋冪敤鏁版嵁
        print("[1/5] 鏀堕泦 Provider 璋冪敤鏁版嵁...")
        provider_data = self._collect_provider_data()
        report["learning"]["raw_data"] = provider_data
        print(f"  鏀堕泦浜?{provider_data['total_calls']} 娆¤皟鐢?)

        # 2. 鍒嗘瀽鎴愬姛鐜?        print("[2/5] 鍒嗘瀽鎴愬姛鐜?..")
        success_analysis = self._analyze_success_rate(provider_data)
        report["learning"]["success_rate"] = success_analysis
        print(f"  鏈€浣?Provider: {success_analysis.get('best_provider', 'N/A')}")

        # 3. 鍒嗘瀽鍝嶅簲鏃堕棿
        print("[3/5] 鍒嗘瀽鍝嶅簲鏃堕棿...")
        latency_analysis = self._analyze_latency(provider_data)
        report["learning"]["latency"] = latency_analysis
        print(f"  鏈€蹇?Provider: {latency_analysis.get('fastest_provider', 'N/A')}")

        # 4. 鍒嗘瀽閿欒妯″紡
        print("[4/5] 鍒嗘瀽閿欒妯″紡...")
        error_analysis = self._analyze_errors(provider_data)
        report["learning"]["errors"] = error_analysis
        print(f"  璇嗗埆浜?{len(error_analysis.get('error_types', []))} 绉嶉敊璇被鍨?)

        # 5. 鐢熸垚寤鸿
        print("[5/5] 鐢熸垚寤鸿...")
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

    def _collect_provider_data(self) -> Dict:
        """鏀堕泦 Provider 璋冪敤鏁版嵁"""
        provider_stats = defaultdict(lambda: {
            "calls": 0,
            "successes": 0,
            "failures": 0,
            "total_duration": 0,
            "durations": [],
            "errors": []
        })
        
        if not self.events_file.exists():
            return {"total_calls": 0, "providers": {}}

        # 璇诲彇鏈€杩?7 澶╃殑鏁版嵁
        cutoff = datetime.now() - timedelta(days=7)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # 鍙鐞?router_call 浜嬩欢
                    if event.get("type") != "router_call":
                        continue
                    
                    # 妫€鏌ユ椂闂?                    event_time = datetime.fromisoformat(event.get("timestamp", ""))
                    if event_time < cutoff:
                        continue
                    
                    provider = event.get("provider", "unknown")
                    success = event.get("success", False)
                    duration = event.get("duration_ms", 0)
                    error = event.get("error", "")
                    
                    provider_stats[provider]["calls"] += 1
                    if success:
                        provider_stats[provider]["successes"] += 1
                    else:
                        provider_stats[provider]["failures"] += 1
                        if error:
                            provider_stats[provider]["errors"].append(error)
                    
                    provider_stats[provider]["total_duration"] += duration
                    provider_stats[provider]["durations"].append(duration)
                    
                except Exception as e:
                    continue

        return {
            "total_calls": sum(s["calls"] for s in provider_stats.values()),
            "providers": dict(provider_stats)
        }

    def _analyze_success_rate(self, data: Dict) -> Dict:
        """鍒嗘瀽鎴愬姛鐜?""
        providers = data.get("providers", {})
        
        success_rates = {}
        for provider, stats in providers.items():
            if stats["calls"] >= 5:  # 鑷冲皯 5 娆¤皟鐢ㄦ墠鏈夌粺璁℃剰涔?                success_rates[provider] = {
                    "calls": stats["calls"],
                    "success_rate": stats["successes"] / stats["calls"],
                    "failures": stats["failures"]
                }
        
        # 鎵惧嚭鏈€浣冲拰鏈€宸?        if success_rates:
            best = max(success_rates.items(), key=lambda x: x[1]["success_rate"])
            worst = min(success_rates.items(), key=lambda x: x[1]["success_rate"])
            
            return {
                "providers": success_rates,
                "best_provider": best[0],
                "best_rate": best[1]["success_rate"],
                "worst_provider": worst[0],
                "worst_rate": worst[1]["success_rate"]
            }
        
        return {"providers": {}}

    def _analyze_latency(self, data: Dict) -> Dict:
        """鍒嗘瀽鍝嶅簲鏃堕棿"""
        providers = data.get("providers", {})
        
        latency_stats = {}
        for provider, stats in providers.items():
            if stats["calls"] >= 5:
                durations = stats["durations"]
                latency_stats[provider] = {
                    "calls": stats["calls"],
                    "avg_ms": stats["total_duration"] / stats["calls"],
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "p50_ms": sorted(durations)[len(durations) // 2],
                    "p95_ms": sorted(durations)[int(len(durations) * 0.95)]
                }
        
        # 鎵惧嚭鏈€蹇拰鏈€鎱?        if latency_stats:
            fastest = min(latency_stats.items(), key=lambda x: x[1]["avg_ms"])
            slowest = max(latency_stats.items(), key=lambda x: x[1]["avg_ms"])
            
            return {
                "providers": latency_stats,
                "fastest_provider": fastest[0],
                "fastest_avg_ms": fastest[1]["avg_ms"],
                "slowest_provider": slowest[0],
                "slowest_avg_ms": slowest[1]["avg_ms"]
            }
        
        return {"providers": {}}

    def _analyze_errors(self, data: Dict) -> Dict:
        """鍒嗘瀽閿欒妯″紡"""
        providers = data.get("providers", {})
        
        error_analysis = {}
        all_errors = []
        
        for provider, stats in providers.items():
            errors = stats.get("errors", [])
            if errors:
                # 缁熻閿欒绫诲瀷
                error_types = {}
                for error in errors:
                    error_type = error.split(":")[0] if ":" in error else error
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                error_analysis[provider] = {
                    "total_errors": len(errors),
                    "error_types": error_types,
                    "most_common": max(error_types.items(), key=lambda x: x[1]) if error_types else None
                }
                
                all_errors.extend(errors)
        
        # 鍏ㄥ眬閿欒缁熻
        global_error_types = {}
        for error in all_errors:
            error_type = error.split(":")[0] if ":" in error else error
            global_error_types[error_type] = global_error_types.get(error_type, 0) + 1
        
        return {
            "by_provider": error_analysis,
            "error_types": global_error_types,
            "total_errors": len(all_errors)
        }

    def _generate_suggestions(self, learning: Dict) -> List[Dict]:
        """鐢熸垚寤鸿"""
        suggestions = []

        # 1. 鎴愬姛鐜囧缓璁?        success_data = learning.get("success_rate", {})
        if success_data.get("worst_rate", 1.0) < 0.8:
            suggestions.append({
                "type": "low_success_rate",
                "priority": "high",
                "provider": success_data["worst_provider"],
                "description": f"{success_data['worst_provider']} 鎴愬姛鐜囦粎 {success_data['worst_rate']:.1%}锛屽缓璁垏鎹㈠埌 {success_data.get('best_provider', 'N/A')}锛坽success_data.get('best_rate', 0):.1%}锛?,
                "action": f"鑰冭檻灏嗛粯璁?Provider 浠?{success_data['worst_provider']} 鍒囨崲鍒?{success_data.get('best_provider', 'N/A')}"
            })

        # 2. 寤惰繜寤鸿
        latency_data = learning.get("latency", {})
        if latency_data.get("slowest_avg_ms", 0) > latency_data.get("fastest_avg_ms", 0) * 2:
            suggestions.append({
                "type": "high_latency",
                "priority": "medium",
                "provider": latency_data["slowest_provider"],
                "description": f"{latency_data['slowest_provider']} 骞冲潎鍝嶅簲 {latency_data['slowest_avg_ms']:.0f}ms锛屾瘮 {latency_data['fastest_provider']}锛坽latency_data['fastest_avg_ms']:.0f}ms锛夋參 2 鍊嶄互涓?,
                "action": f"瀵瑰欢杩熸晱鎰熺殑浠诲姟浼樺厛浣跨敤 {latency_data['fastest_provider']}"
            })

        # 3. 閿欒妯″紡寤鸿
        error_data = learning.get("errors", {})
        for provider, analysis in error_data.get("by_provider", {}).items():
            if analysis["total_errors"] >= 5:
                most_common = analysis.get("most_common")
                if most_common:
                    suggestions.append({
                        "type": "frequent_errors",
                        "priority": "medium",
                        "provider": provider,
                        "description": f"{provider} 棰戠箒鍑虹幇 '{most_common[0]}' 閿欒锛坽most_common[1]} 娆★級",
                        "action": f"妫€鏌?{provider} 鐨勯厤缃垨 API 闄愬埗"
                    })

        return suggestions

    def _save_report(self, report: Dict):
        """淇濆瓨鎶ュ憡"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"provider_learning_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n馃搫 鎶ュ憡宸蹭繚瀛? {report_file}")


def main():
    """涓诲嚱鏁?""
    agent = ProviderLearnerAgent()
    report = agent.run()
    
    suggestions = report.get("suggestions", [])
    if suggestions:
        print(f"\nPROVIDER_LEARNER_SUGGESTIONS:{len(suggestions)}")
    else:
        print("\nPROVIDER_LEARNER_OK")


if __name__ == "__main__":
    main()

