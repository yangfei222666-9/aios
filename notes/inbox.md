# Inbox

- 2026-02-17T13:35:00+08:00 我今天部署完成了 OpenClaw。下一步：完善笔记系统（自动创建 notes/inbox.md）、设置白名单自动执行（notes 与 sandbox）、做一次 ASR 端到端测试。
- 2026-02-17T13:36:00+08:00 明天把 OpenClaw 的 3 个核心技能（status / note / search）跑一遍，并记录结果。
---
## daily_check 模板（每天一遍）
- [ ] daily_check | {DATE} | {TZ}
  - status
    - ASR: {OK/FAIL} | {detail}
    - TTS: {OK/FAIL} | {detail}
    - Network/API: {OK/FAIL} | {detail}
    - Logs: {path}
  - search
    - Query: "OpenClaw skills test"
    - Result: {OK/FAIL} | {title_or_error}
  - note
    - 今日一句总结：{one_line}
    - 明日最重要一件事：{one_thing}
  - 下一步
    - 若 ASR FAIL：检查 LINEAR16/16k/mono + Key 权限
    - 若 Network FAIL：离线降级 + 队列写入，网络恢复后同步
---
- [ ] daily_check | 2026-02-17 | Asia/Kuala_Lumpur
  - status
    - ASR: FAIL | 需要配置ASR服务
    - TTS: FAIL | 需要配置TTS服务
    - Network/API: OK | Telegram连接正常，web_search编码错误
    - Logs: C:\Users\A\.openclaw\logs\
  - search
    - Query: "OpenClaw skills test"
    - Result: FAIL | web_search编码错误（中文字符>255）
- search_fallback | query=OpenClaw 教程 | provider= | results=0 | success=
- search_daily_test | query=OpenClaw skills test | provider=duckduckgo_html | success=true | titles=无结果
- search_daily_test | query=你好 | provider=duckduckgo_html | success=true | titles=无结果
- search_daily_test | query=马来西亚 新山 天气 | provider=duckduckgo_html | success=true | titles=无结果
- [ ] daily_check | 2026-02-17 | Asia/Kuala_Lumpur
  - status
    - ASR: FAIL | 需要配置ASR服务
    - TTS: FAIL | 需要配置TTS服务
    - Network/API: OK | Telegram连接正常，search使用fallback
    - Logs: C:\Users\A\.openclaw\logs\
  - search (使用fallback)
    - Query: "OpenClaw skills test" | Provider: duckduckgo_html | Top1: "无结果"
    - Query: "你好" | Provider: duckduckgo_html | Top1: "无结果"
    - Query: "马来西亚 新山 天气" | Provider: duckduckgo_html | Top1: "无结果"  - note
    - 今日一句总结：成功集成search_fallback到daily_check
    - 明日最重要一件事：测试ASR/TTS配置
  - 下一步
    - 若 ASR FAIL：检查 LINEAR16/16k/mono + Key 权限
    - 若 Network FAIL：离线降级 + 队列写入，网络恢复后同步
- search_result | query=OpenClaw | provider=all_failed | fallback_level=2 | success=false | error=所有搜索方法都失败 | elapsed_ms=60
- search_result | query=你好 | provider=all_failed | fallback_level=2 | success=false | error=所有搜索方法都失败 | elapsed_ms=18
- search_result | query=马来西亚 新山 天气 | provider=all_failed | fallback_level=2 | success=false | error=所有搜索方法都失败 | elapsed_ms=18
- search_twolevel | query=OpenClaw | provider=ddg_json | fallback_level=1 | success=true | top1="OpenClaw: OpenClaw is a free and open-source autonomous artificial intelligen..." | elapsed_ms=229
- search_twolevel | query=你好 | provider=bot_detected | fallback_level=2 | success=false | error=Bot检测触发 | elapsed_ms=237
- search_twolevel | query=马来西亚 新山 天气 | provider=bot_detected | fallback_level=2 | success=false | error=Bot检测触发 | elapsed_ms=148
- search_step1 | query=你好 | provider=ddg_json_empty | success=True | has_result=False
- search_step2_retry | original=你好 | retry=你好 wiki | provider=ddg_json_empty | success=True | has_result=False
- search_step3_html | query=你好 | status=not_implemented
- search_final | query=你好 | provider=html_not_implemented | fallback_level=2 | success=False | top1="(html fallback needed)" | elapsed_ms=247
- search_step1 | query=马来西亚 | provider=ddg_json_empty | success=True | has_result=False
- search_step2_retry | original=马来西亚 | retry=马来西亚 wiki | provider=ddg_json_empty | success=True | has_result=False
- search_step3_html | query=马来西亚 | status=not_implemented
- search_final | query=马来西亚 | provider=html_not_implemented | fallback_level=2 | success=False | top1="(html fallback needed)" | elapsed_ms=130
- search_step1 | query=OpenClaw | provider=ddg_json | success=True | has_result=True
- search_final | query=OpenClaw | provider=ddg_json | fallback_level=1 | success=True | top1="OpenClaw" | elapsed_ms=71
- search_step1 | query=天气 | provider=ddg_json_empty | success=True | has_result=False
- search_step2_retry | original=天气 | retry=天气 wiki | provider=ddg_json_empty | success=True | has_result=False
- search_step3_html | query=天气 | status=not_implemented
- search_final | query=天气 | provider=html_not_implemented | fallback_level=2 | success=False | top1="(html fallback needed)" | elapsed_ms=120
- search_step1 | query=nonexistent | provider=ddg_json_empty | success=True | has_result=False
- search_step3_html | query=nonexistent | status=not_implemented
- search_final | query=nonexistent | provider=html_not_implemented | fallback_level=2 | success=False | top1="(html fallback needed)" | elapsed_ms=72
- [ ] daily_check | 2026-02-17 | Asia/Kuala_Lumpur
  - status
    - ASR: FAIL | 需要配置ASR服务
    - TTS: FAIL | 需要配置TTS服务
    - Network/API: OK | OpenClaw网关运行正常
    - Logs: C:\Users\A\.openclaw\logs\
  - search
    - Query: "OpenClaw skills test"
    - Result: FAIL | (no_json_result)

## 2026-02-17T17:29:00+08:00
明天开会

2026-02-17T17:46:00+08:00 明天开会

2026-02-17T17:46:00+08:00 测试内容

2026-02-17T17:46:00+08:00 明天开会

2026-02-17T17:46:00+08:00 测试内容
