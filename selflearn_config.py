# -*- coding: utf-8 -*-
"""
小九自学模块 - 定期从公开数据源学习新知识
"""

# 学习任务清单
TASKS = {
    "lol_patch": {
        "name": "LOL版本更新",
        "source": "https://lol.qq.com/act/lbp/common/guides/champDetail/champDetail_1.js",
        "interval_hours": 168,  # 每周
        "description": "检查国服LOL版本号变化，更新ARAM助手数据库"
    },
    "lol_hero_data": {
        "name": "英雄出装数据刷新",
        "source": "lol.qq.com champDetail API",
        "interval_hours": 168,  # 每周
        "description": "重新拉取172英雄的胜率和出装数据"
    },
    "tech_lessons": {
        "name": "技术教训回顾",
        "source": "memory/",
        "interval_hours": 72,  # 每3天
        "description": "回顾近期日志，提取教训更新到MEMORY.md"
    }
}
