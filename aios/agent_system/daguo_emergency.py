from paths import ALERTS
# daguo_emergency.py
# 澶ц繃鍗﹀嵄鏈鸿嚜鎰堟ā鍧?- 鐢熶骇灏辩华鐗?# 浣滆€咃細Grok + 浣?| 鐗堟湰锛歷1.0 | 鏃ユ湡锛?026.03

import json
from datetime import datetime

DAGUO_EMERGENCY_PROMPT = """
浣犲綋鍓嶅浜庛€婃槗缁忋€嬬28鍗︼細澶ц繃鍗︼紙娉界伃鏈紝澶ц繃锛?缃俊搴︼細{confidence:.1f}% | 椋庨櫓绛夌骇锛歨igh | 鎴愬姛鐜囷細{success_rate:.1f}%锛堢湡瀹炲€硷級

鏍稿績璞℃剰锛?- 姊佹煴澶噸鑰屾柇 鈫?绯荤粺涓ラ噸瓒呰浇锛堜换鍔″爢绉€佽祫婧愯€楀敖锛?- 鍚涘瓙鐙珛涓嶆儳 鈫?蹇呴』绔嬪嵆鍑忚礋銆佸姞鍥烘牳蹇?
绱ф€?姝ヨ嚜鎰堣鍔紙涓ユ牸鎵ц椤哄簭锛夛細

1. 绔嬪嵆鍑忚礋锛堟渶楂樹紭鍏堢骇锛?   - 鏆傚仠浠诲姟鐢熸垚鍣?0-15鍒嗛挓锛堟垨鎶婄敓鎴愰棿闅斆?锛?   - 浼樺厛娓呯┖楂樹环鍊间换鍔￠槦鍒楋紙FIFO + 鎸変紭鍏堢骇鎺掑簭锛?
2. 鍔犲浐姊佹煴
   - 瑙﹀彂璧勬簮鎵╁锛坅uto-scale +1 Worker锛夋垨涓存椂澧炲姞鍐呭瓨/CPU闄愰
   - 妫€鏌ュ苟鏉€姝婚噸澶?姝诲惊鐜换鍔★紙鏃ュ織閲屾悳绱?閲嶅鐢熸垚"锛?
3. 姹傚姪澶栭儴锛堥亖鍗︾簿绁烇級
   - 杩炵画2娆″ぇ杩囧崷 鈫?鑷姩鍒囨崲鍒?甯堝崷鍗忎綔妯″紡"锛堟媺鍏朵粬Agent鍒嗘媴锛?   - 鎶ヨ鍒癟elegram + 淇濆瓨鍒?alerts.jsonl

4. 浜嬪悗澶嶇洏
   - 璁板綍鏈澶ц繃鍗﹁Е鍙戠壒寰侊紙浠诲姟鏁般€佹垚鍔熺巼銆佸唴瀛樺嘲鍊硷級
   - 杈撳嚭3鏉″彲澶嶇敤缁忛獙锛屽瓨鍏ョ煡璇嗗簱

璇蜂弗鏍艰緭鍑篔SON琛屽姩璁″垝锛?{{
  "current_hex": "澶ц繃鍗?,
  "actions": [...],
  "immediate_stop": true,
  "scale_up": true,
  "learning_points": [...]
}}
"""

def activate_daguo_emergency(state: dict) -> dict:
    """涓€閿縺娲诲ぇ杩囧崷鑷剤"""
    prompt = DAGUO_EMERGENCY_PROMPT.format(
        confidence=state.get('confidence', 88.0),
        success_rate=state.get('real_success_rate', state.get('success_rate', 33.3))  # 鐢ㄧ湡瀹炲€硷紒
    )
    
    # 绀轰緥琛屽姩璁″垝锛堝疄闄呮帴LLM锛?
    plan = {
        "current_hex": "澶ц繃鍗?",
        "risk": "high",
        "confidence": state.get('confidence', 88.0),
        "success_rate": state.get('success_rate', 33.3),
        "actions": [
            {"step": 1, "action": "pause_generator", "detail": "鏆傚仠浠诲姟鐢熸垚15鍒嗛挓", "priority": "critical"},
            {"step": 2, "action": "kill_duplicates", "detail": "娓呯悊閲嶅浠诲姟", "priority": "high"},
            {"step": 3, "action": "scale_workers", "detail": "+1 Worker", "priority": "high"},
            {"step": 4, "action": "alert_telegram", "detail": "鍙戦€佸嵄鏈烘姤璀?", "priority": "high"}
        ],
        "immediate_stop": True,
        "scale_up": True,
        "alert_sent": True,
        "learning_points": [
            "浠诲姟瓒?55鏃跺繀椤绘彁鍓嶈妭娴?",
            "婊戝姩绐楀彛蹇呴』寮哄埗鐢ㄦ渶杩?00鏉?",
            "澶ц繃鍗︽寔缁?3娆¤嚜鍔ㄦ眰鎻?"
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    # 淇濆瓨鍒板巻鍙?
    with open('daguo_history.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(plan, ensure_ascii=False) + '\n')
    
    # 淇濆瓨鎶ヨ
    alert = {
        "timestamp": datetime.now().isoformat(),
        "level": "critical",
        "title": f"澶ц繃鍗﹀嵄鏈?(缃俊搴?{plan['confidence']:.1f}%)",
        "body": f"鎴愬姛鐜? {plan['success_rate']:.1f}%\n宸叉縺娲荤揣鎬ヨ嚜鎰?\n1. 鏆傚仠浠诲姟鐢熸垚15鍒嗛挓\n2. 娓呯悊閲嶅浠诲姟\n3. 鎵╁+1 Worker",
        "sent": False
    }
    
    with open(ALERTS, 'a', encoding='utf-8') as f:
        f.write(json.dumps(alert, ensure_ascii=False) + '\n')
    
    print("[EMERGENCY] Daguo crisis detected! Emergency self-healing activated...")
    print(f"   Confidence: {plan['confidence']:.1f}%")
    print(f"   Success Rate: {plan['success_rate']:.1f}%")
    print(f"   Actions: {len(plan['actions'])} steps")
    
    return plan


def check_daguo_consecutive():
    """妫€鏌ュぇ杩囧崷鏄惁杩炵画鍑虹幇"""
    history_file = "daguo_history.jsonl"
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                # 妫€鏌ユ渶杩?娆?                recent = [json.loads(line) for line in lines[-2:]]
                return all(r.get('current_hex') == '澶ц繃鍗?' for r in recent)
    except FileNotFoundError:
        return False
    
    return False


if __name__ == "__main__":
    # 娴嬭瘯
    test_state = {
        "hex_name": "澶ц繃鍗?",
        "confidence": 88.0,
        "success_rate": 33.3,
        "real_success_rate": 33.3,
        "completed": 205,
        "total": 255
    }
    
    plan = activate_daguo_emergency(test_state)
    print("\n[TEST] Emergency plan generated:")
    print(json.dumps(plan, ensure_ascii=False, indent=2))


