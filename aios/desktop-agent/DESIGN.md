# Region Watcher Overlay — 主仆桌面代理

> 多区域、低频、按需触发、可复盘的桌面视觉监听插件。
> 主仆桌面代理的"眼睛"和"前端"。

## 为什么做

当前 AI 助手只能被动响应。用户卡在终端报错、盯着文档发呆、反复切窗口 — AI 看不见。

这个插件让 AI 能"看见"用户框选的屏幕区域，在关键时刻主动介入。

不是"全屏盯梢"，而是多区域、低频、按需触发。

## 核心原则

- 不用 OCR — 仆自己用轻量多模态直接看
- 不持续全屏截图 — 只监听用户框选的区域
- 每个区域独立频率 — 有的 3 秒，有的 15 秒
- 只有变化时才进一步处理 — 变化检测是省电层
- 截图留存用于学习/复盘
- 老师静默 — 不常驻监听输入，不抢操作权
- **Master is event-driven, not frame-driven** — 主代理事件驱动，不逐帧介入

## 主仆职责

**主（Master / 老师）：**
- 事件驱动，只在仆上报"变化/异常/卡住"时出场
- 理解、规划、教学
- 模型：豆包 2.0 Lite

**仆（Servant / 执行者）：**
- 区域视觉执行官，不是哲学家
- 看区域变化、判断内容类型、提取候选操作目标、做简单验证
- 模型：豆包 1.6 Flash

**用户：**
- 正常工作，不改变习惯
- 通过悬浮按钮框选监听区域
- 收到通知时决定是否采纳
- 可随时暂停/关闭

---

## 模块拆分（8 个模块）

### A. overlay_ui — 前台壳
- 悬浮按钮
- 框选模式（拖拽画矩形）
- 回车确认 / Esc 取消
- 已创建区域的边框和标签显示

### B. watch_region_manager — 区域资产管理
- 区域 CRUD
- 启用/暂停某个区域
- 保存/加载区域配置
- 不碰视觉模型

### C. capture_engine — 眼睛的快门
- 按 bounds 截图
- 多区域分别截图
- 支持 absolute / window_relative 坐标转换
- 返回 image 对象或 path

### D. change_detector — 省电层（最关键）
- pHash / 像素差 / 颜色直方图差异
- 输出 change_score
- 低于阈值 → 跳过，不调模型，不存图

### E. servant_vision — 仆模型看图
- 调用轻量多模态模型
- 返回：内容类型、是否重要、候选按钮/坐标、建议动作
- 多后端设计（豆包 1.6 Flash → 2.0 Lite → 其他）

### F. master_router — 升级路由
- 决定哪些事件需要升级给主
- 打包上下文
- 接收主的判断
- 平时应该很安静

### G. snapshot_store — 证据库
- 存图 + 分类目录
- 写 metadata JSON
- 支持学习/复盘
- retention 管理（后做）

### H. scheduler_runtime — 发动机
- 多区域调度（每个区域按自己的秒数）
- 节流控制
- 异常恢复
- 开始/暂停/停止全局监听

---

## 区域配置 Schema

### 单个区域

```json
{
    "id": "watch_1",
    "name": "微信聊天区",
    "enabled": true,
    "app_hint": "WeChat",
    "window_hint": "微信",
    "mode": "absolute",
    "bounds": { "x": 120, "y": 160, "w": 820, "h": 640 },
    "interval_sec": 3,
    "change_threshold": 0.08,
    "vision_enabled": true,
    "vision_mode": "light_mm",
    "save_snapshots": true,
    "snapshot_group": "watch_1_wechat",
    "snapshot_root": "./captures",
    "purpose": "message_monitor",
    "cooldown_sec": 10,
    "created_at": "2026-03-13T17:00:00+08:00",
    "updated_at": "2026-03-13T17:00:00+08:00"
}
```

**mode 类型：**
- `absolute` — 绝对屏幕坐标（v1 先做这个）
- `window_relative` — 相对窗口坐标（窗口移动后跟着走）

**purpose 类型：**
- `message_monitor` / `error_monitor` / `report_monitor` / `button_watch`

### 三类区域

1. **固定区域** — 绝对坐标，不跟窗口走
2. **应用相对区域** — 绑定 app window，窗口移动后跟着走
3. **临时任务区域** — 框一次，监听几分钟后自动失效

### 全局配置

```json
{
    "overlay_enabled": true,
    "default_interval_sec": 5,
    "default_change_threshold": 0.08,
    "default_snapshot_root": "./captures",
    "max_parallel_regions": 4,
    "master_enabled": false,
    "servant_model": "doubao-1.6-flash",
    "master_model": "doubao-2.0-lite"
}
```

---

## 监听主循环

```python
def main_loop():
    while runtime.is_running:
        now = time.time()

        for region in region_manager.list_enabled_regions():
            if not scheduler.should_run(region, now):
                continue

            try:
                # 1. 截该区域
                capture = capture_engine.capture(region)

                # 2. 计算变化
                diff = change_detector.compare(region.id, capture.image)

                # 3. 变化不大 → 跳过
                if diff.score < region.change_threshold:
                    scheduler.mark_done(region.id, now, changed=False)
                    continue

                # 4. 保存截图
                snapshot_path = None
                if region.save_snapshots:
                    snapshot_path = snapshot_store.save(
                        region=region, image=capture.image,
                        timestamp=now,
                        extra={"change_score": diff.score, "bounds": region.bounds}
                    )

                # 5. 节流判断
                if not scheduler.can_invoke_vision(region.id, now, region.cooldown_sec):
                    scheduler.mark_done(region.id, now, changed=True)
                    continue

                # 6. 仆模型看图
                vision_result = None
                if region.vision_enabled:
                    vision_result = servant_vision.analyze(
                        image=capture.image,
                        context={
                            "region_name": region.name,
                            "purpose": region.purpose,
                            "app_hint": region.app_hint,
                            "change_score": diff.score,
                        }
                    )

                # 7. 保存分析结果
                snapshot_store.save_metadata(region, now, {
                    "change_score": diff.score,
                    "snapshot_path": snapshot_path,
                    "vision_result": vision_result,
                })

                # 8. 判断是否上报主代理
                if master_router.should_escalate(region, vision_result):
                    master_result = master_router.route(
                        region=region,
                        vision_result=vision_result,
                        snapshot_path=snapshot_path,
                    )
                    snapshot_store.save_master_result(region, now, master_result)

                # 9. 更新调度状态
                scheduler.mark_done(region.id, now, changed=True)

            except Exception as e:
                scheduler.mark_error(region.id, now, str(e))
                logger.exception(f"Region watch failed: {region.id}")

        time.sleep(0.2)
```

**关键点：** 到时才轮到 → 先变化检测 → 没变化就走 → 有变化才存/看 → 有价值才升级给主。

---

## 截图存储结构

```
captures/
├── watch_1/
│   └── 2026-03-13/
│       ├── 16-30-01.png
│       ├── 16-30-01.json    # metadata
│       └── 16-30-04.png
└── watch_2/
    └── 2026-03-13/
        └── 16-30-03.png
```

每张图配 metadata：

```json
{
    "watch_id": "watch_1",
    "timestamp": "2026-03-13T16:30:01+08:00",
    "app": "WeChat",
    "change_score": 0.21,
    "vision_invoked": true,
    "vision_summary": "检测到新消息气泡出现",
    "action_taken": null
}
```

---

## 4 个省资源开关

1. **区域独立频率** — 有的 3s，有的 15s，不一刀切
2. **变化阈值** — 变化小就别惊动模型
3. **事件节流** — 同类变化短时间不重复分析
4. **分级存储** — 无变化不存/只存摘要，有变化存截图+metadata，有动作存前后对照

---

## UI 交互流程

### 创建监听区

1. 点击桌面悬浮按钮（👁）
2. 菜单：新建监听区 / 查看监听区 / 暂停全部 / 开始全部 / 打开截图目录 / 退出
3. 点"新建" → 半透明遮罩 + 拖拽画矩形（实时显示大小坐标）
4. Enter 确认 → 弹出配置小窗（名称、秒数、用途、是否存图、是否启用视觉）
5. 创建成功 → 区域显示细边框 + 小标签（"微信聊天区 | 3s"）

### 管理区域

列表显示：名称、状态、秒数、最近变化时间、最近截图时间
操作：编辑 / 暂停 / 启动 / 删除 / 打开截图目录

### 临时静默

- 暂停全部 10 分钟
- 暂停全部 1 小时
- 继续监听

---

## 失败控制 + 人工教学回路

### 防止无限循环（硬约束）

每个任务步骤最多自动重试 2 次，第 3 次进入三选一：跳过 / 回滚 / 人工教学。

写进执行引擎，不靠提示词自觉。

### 步骤状态机

```
PENDING → RUNNING → SUCCESS
                  → FAILED_RETRYABLE (attempt < 2) → 重试
                  → FAILED_NEEDS_HUMAN (attempt >= 2)
                  → SKIPPED
                  → ROLLED_BACK
```

每步都有 step_id：

```json
{
    "task_id": "task_001",
    "step_id": "open_wechat_chat",
    "attempt": 1,
    "max_attempts": 2,
    "status": "failed"
}
```

### 人工提示框

两次失败后弹出：
- 当前想做什么 / 仆尝试了什么 / 为什么失败
- 按钮：跳过 / 回滚到上一步 / 手动教学 / 再试一次（不显眼）

### 人工教学模式（RPA 录制）

1. 悬浮按钮 → "开始教学"
2. 系统录制：鼠标轨迹、点击点位、活跃窗口、截图前后状态
3. 用户手动操作一遍
4. 点"完成教学" → 仆回看理解（点了什么、为什么、成功标志）
5. 仆尝试复现
6. 对了 → 学会了 / 错了 → 再试 1-2 次 / 还错 → 标记"半学会"

---

## 目录结构

```
desktop-agent/
├── DESIGN.md                # 本文档
├── main.py                  # 主循环
├── config.py                # 全局配置 + 区域配置加载
├── overlay_ui.py            # 悬浮按钮 + 框选交互
├── watch_region_manager.py  # 区域 CRUD
├── capture_engine.py        # 按区域截图
├── change_detector.py       # 变化检测（pHash/像素差）
├── servant_vision.py        # 仆模型看图（多后端）
├── master_router.py         # 升级路由
├── snapshot_store.py        # 截图 + metadata 归档
├── scheduler_runtime.py     # 多区域调度引擎
├── failure_controller.py    # 失败控制 + 重试状态机
├── teaching_recorder.py     # 人工教学录制
├── telegram_notify.py       # 通知推送
├── compressors/
│   ├── trace_compressor.py      # 执行轨迹压缩
│   ├── vision_event_compressor.py  # 区域监听事件压缩
│   ├── lesson_compressor.py     # 教学记录压缩
│   └── context_budget.py        # 上下文预算器
├── captures/                # 截图存储
├── regions.json             # 区域配置持久化
└── requirements.txt
```

---

## 分版计划

### v1 — 最小闭环（当前目标）
- 悬浮按钮 + 框选多区域
- 每区独立秒数
- 定时截图 + 变化检测
- 保存截图到分类文件夹
- 区域列表管理

### v2 — 接仆模型
- 仆多模态分析
- 识别新消息/错误/报告
- 标出候选按钮 + 坐标
- 通知推送

### v3 — 主仆执行闭环
- 主代理升级判断
- 执行验证
- 失败控制 + 人工教学
- 经验入库

---

## 上下文压缩系统

主仆 + 观察 + 学习系统，上下文爆炸是必然的。压缩必须是系统能力，不是临时手搓摘要。

**核心原则：压缩的是重复和噪音，不是证据和约束。**

### 4 层压缩架构

```
原始层（黑匣子）→ 事件摘要层（去噪）→ 任务轨迹层（主代理常用）→ 经验规则层（长期记忆）
```

**Layer 1 — 原始层：** 全部原始事件进库，但不喂模型。截图 metadata、区域变化、鼠标/点击/窗口事件、主仆对话、执行日志、验证结果。

**Layer 2 — 事件摘要层：** 原始事件压成短事件块。

```json
{
    "event_id": "evt_1021",
    "type": "region_watch",
    "summary": "微信聊天区在 17:03-17:05 出现 3 次明显变化，仆判定为新消息到达",
    "evidence_refs": ["snap_001", "snap_002"],
    "importance": 0.72
}
```

**Layer 3 — 任务轨迹层：** 一连串事件压成任务过程。

```json
{
    "task_id": "task_wechat_report_review",
    "goal": "查看小九新报告并给出建议",
    "compressed_trace": [
        "检测到微信窗口变化",
        "仆识别为新报告消息",
        "主提取核心结论",
        "生成建议并准备回复"
    ],
    "failures": [],
    "result": "success"
}
```

**Layer 4 — 经验规则层：** 多次成功轨迹压成可复用经验。

```json
{
    "rule_id": "rule_wechat_new_report_review",
    "pattern": "微信报告区变化 + 标题命中小九 + 新文本块增加",
    "action_strategy": "仆先看图，主再提炼建议",
    "success_rate": 0.84
}
```

### 3 种压缩器

| 压缩器 | 输入 | 输出 |
|--------|------|------|
| `trace_compressor` | step logs + servant reports + verification results | 任务压缩轨迹 |
| `vision_event_compressor` | region snapshots + change scores + vision outputs | 区域事件摘要 |
| `lesson_compressor` | human teaching trace + servant replay results | lesson card / reusable skill card |

### 6 类最该压缩的内容

1. **主仆来回对话** → 压成：任务目标、尝试次数、当前失败原因、已验证无效方法、下一步候选
2. **区域监听日志** → 压成：时间窗变化次数、触发模型次数、最终判定
3. **截图历史** → 只进：图 ID、时间、变化类型、关键结论（图本身不进上下文）
4. **教学过程** → 压成：目标任务、操作序列、成功判据、关键视觉锚点、是否学会
5. **错误恢复链** → 压成：错误模式、已尝试恢复动作、哪些无效、推荐下一步
6. **日常监控报告** → 只留：结论、是否异常、趋势、需要行动吗

### 压缩摘要统一结构

```json
{
    "summary_id": "sum_001",
    "scope": "task",
    "source_ids": ["evt_11", "evt_12", "evt_13"],
    "objective": "读取微信中的小九报告",
    "compressed_text": "检测到微信区域变化，仆识别为新报告，主提炼出磁盘使用率趋近阈值但无严重异常。",
    "key_facts": ["C盘使用率 79.9%", "当前无严重事件", "Evolution Score 0.4"],
    "failed_attempts": [],
    "next_action": "继续监听；7天内安排磁盘清理",
    "importance": 0.81,
    "created_at": "2026-03-13T17:06:00+08:00"
}
```

### 4 个必须加的机制

1. **上下文预算器** — 每次喂上下文前先算 token 预算（当前任务 / 历史摘要 / 规则记忆 / 失败案例）
2. **摘要刷新器** — 任务长了自动把旧过程压缩掉
3. **证据索引** — 摘要里永远保留原始数据引用（evidence_refs / snapshot_ids / step_ids）
4. **分任务模板压缩** — 不同任务用不同摘要模板（RPA→保留动作结果、UI学习→保留视觉锚点、报告→保留结论风险）

### 压缩思路（参考 TRAE）

- **分层压缩** — 原始→事件→任务→规则，不是一次压成一句话
- **保留引用不保留全文** — 摘要只存 refs，需要时回溯原始证据
- **滚动摘要** — 长会话每隔一段做 short/mid/mission summary
- **目标导向压缩** — 不同任务压缩重点不同，不一刀切

### 实现时机

- v1：数据结构定好（event schema 里预留 evidence_refs、importance 字段）
- v2：trace_compressor + vision_event_compressor 实现
- v3：lesson_compressor + 上下文预算器 + 摘要刷新器

---

## 非目标（v1 不做）

- 自动操作用户电脑
- 全屏幕理解
- 多显示器支持
- 历史行为学习
- 与太极OS 深度集成

---

**项目状态：** 设计完成，待开发  
**维护者：** 小九 + 珊瑚海  
**创建时间：** 2026-03-13
