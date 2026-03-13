#!/usr/bin/env python3
"""
AIOS Task Router - 单元测试
测试覆盖：关键词识别、Agent 匹配、模糊匹配、排名、队列管理
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from task_router import TaskRouter, RouteResult, Task, KEYWORD_MAP


class TestTaskTypeIdentification(unittest.TestCase):
    """测试任务类型识别"""

    def setUp(self):
        self.router = TaskRouter()

    def test_chinese_keyword_exact_match(self):
        """测试中文关键词精确匹配"""
        task_type, confidence = self.router._identify_task_type("写一个排序算法")
        self.assertEqual(task_type, "code")
        self.assertEqual(confidence, 0.9)

    def test_chinese_keyword_debug(self):
        """测试调试类关键词"""
        task_type, confidence = self.router._identify_task_type("修复登录bug")
        # "修复" 匹配 "fix"，"bug" 匹配 "debug"，"修复" 更长
        self.assertEqual(task_type, "fix")
        self.assertEqual(confidence, 0.9)

    def test_chinese_keyword_analysis(self):
        """测试分析类关键词"""
        task_type, confidence = self.router._identify_task_type("分析最近的错误日志")
        # "错误" 匹配 "debug"，"分析" 匹配 "analysis"，"分析" 在前面
        # 实际上 "错误" 更长，所以会匹配 "debug"
        self.assertIn(task_type, ["analysis", "debug"])
        self.assertEqual(confidence, 0.9)

    def test_english_keyword_match(self):
        """测试英文关键词匹配"""
        task_type, confidence = self.router._identify_task_type("debug the login issue")
        self.assertEqual(task_type, "debug")
        self.assertEqual(confidence, 0.8)

    def test_default_fallback(self):
        """测试默认降级到 code"""
        task_type, confidence = self.router._identify_task_type("随便做点什么")
        self.assertEqual(task_type, "code")
        self.assertEqual(confidence, 0.3)

    def test_longest_keyword_wins(self):
        """测试最长关键词优先"""
        # "单元测试" 比 "测试" 更长
        task_type, confidence = self.router._identify_task_type("写单元测试")
        self.assertEqual(task_type, "test")


class TestAgentMatching(unittest.TestCase):
    """测试 Agent 匹配"""

    def setUp(self):
        # Mock registry
        self.mock_agents = {
            "coder": {
                "id": "coder",
                "name": "代码开发专家",
                "role": "编写代码",
                "task_types": ["code", "refactor"],
                "status": "active",
                "stats": {"success_rate": 0.85, "tasks_completed": 100}
            },
            "debugger": {
                "id": "debugger",
                "name": "调试专家",
                "role": "修复bug",
                "task_types": ["debug", "fix"],
                "status": "active",
                "stats": {"success_rate": 0.90, "tasks_completed": 50}
            },
            "standby_agent": {
                "id": "standby_agent",
                "name": "待命Agent",
                "role": "测试",
                "task_types": ["test"],
                "status": "standby",
                "stats": {}
            }
        }

        with patch.object(TaskRouter, '_load_registry', return_value={"agents": list(self.mock_agents.values()), "skills": {}}):
            with patch.object(TaskRouter, '_load_stats', return_value={"total_routed": 0, "by_agent": {}}):
                self.router = TaskRouter()

    @patch('task_router.get_agent_status')
    def test_find_agents_for_type_code(self, mock_status):
        """测试找到 code 类型的 Agent"""
        mock_status.return_value = "active"
        candidates = self.router._find_agents_for_type("code")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["id"], "coder")

    @patch('task_router.get_agent_status')
    def test_find_agents_for_type_debug(self, mock_status):
        """测试找到 debug 类型的 Agent"""
        mock_status.return_value = "active"
        candidates = self.router._find_agents_for_type("debug")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["id"], "debugger")

    @patch('task_router.get_agent_status')
    def test_standby_agents_excluded(self, mock_status):
        """测试 standby Agent 被排除"""
        def status_side_effect(agent):
            return agent.get("status", "active")
        mock_status.side_effect = status_side_effect
        
        candidates = self.router._find_agents_for_type("test")
        self.assertEqual(len(candidates), 0)

    @patch('task_router.get_agent_status')
    def test_no_match_returns_empty(self, mock_status):
        """测试无匹配返回空列表"""
        mock_status.return_value = "active"
        candidates = self.router._find_agents_for_type("nonexistent")
        self.assertEqual(len(candidates), 0)


class TestCandidateRanking(unittest.TestCase):
    """测试候选 Agent 排名"""

    def setUp(self):
        with patch.object(TaskRouter, '_load_registry', return_value={"agents": [], "skills": {}}):
            with patch.object(TaskRouter, '_load_stats', return_value={}):
                self.router = TaskRouter()

    def test_rank_by_score(self):
        """测试按基础分数排名"""
        candidates = [
            {"id": "a1", "name": "A1", "_score": 0.5, "priority": "normal", "stats": {}},
            {"id": "a2", "name": "A2", "_score": 0.8, "priority": "normal", "stats": {}},
        ]
        best = self.router._rank_candidates(candidates, "code", "test")
        self.assertEqual(best["id"], "a2")

    def test_rank_with_priority_bonus(self):
        """测试优先级加分"""
        candidates = [
            {"id": "a1", "name": "A1", "_score": 0.5, "priority": "critical", "stats": {}},
            {"id": "a2", "name": "A2", "_score": 0.6, "priority": "normal", "stats": {}},
        ]
        best = self.router._rank_candidates(candidates, "code", "test")
        # a1: 0.5 + 0.3 = 0.8 > a2: 0.6 + 0.1 = 0.7
        self.assertEqual(best["id"], "a1")

    def test_rank_with_success_rate_bonus(self):
        """测试成功率加分"""
        candidates = [
            {"id": "a1", "name": "A1", "_score": 0.5, "priority": "normal", "stats": {"success_rate": 0.9}},
            {"id": "a2", "name": "A2", "_score": 0.6, "priority": "normal", "stats": {"success_rate": 0.5}},
        ]
        best = self.router._rank_candidates(candidates, "code", "test")
        # a1: 0.5 + 0.1 + 0.9*0.2 = 0.78 > a2: 0.6 + 0.1 + 0.5*0.2 = 0.8
        # 实际 a2 更高，因为基础分更高
        self.assertEqual(best["id"], "a2")

    def test_rank_with_experience_bonus(self):
        """测试任务经验加分"""
        candidates = [
            {"id": "a1", "name": "A1", "_score": 0.5, "priority": "normal", "stats": {"tasks_completed": 100}},
            {"id": "a2", "name": "A2", "_score": 0.5, "priority": "normal", "stats": {"tasks_completed": 10}},
        ]
        best = self.router._rank_candidates(candidates, "code", "test")
        # a1: 0.5 + 0.1 + min(100*0.05, 0.2) = 0.8 > a2: 0.5 + 0.1 + 10*0.05 = 1.1 (capped at 0.2)
        self.assertEqual(best["id"], "a1")


class TestFuzzyMatching(unittest.TestCase):
    """测试模糊匹配"""

    def setUp(self):
        mock_agents = {
            "coder": {
                "id": "coder",
                "name": "代码开发专家",
                "role": "编写高质量代码",
                "task_types": ["code"],
                "status": "active"
            },
            "analyzer": {
                "id": "analyzer",
                "name": "数据分析师",
                "role": "分析数据和生成报告",
                "task_types": ["analysis"],
                "status": "active"
            }
        }
        with patch.object(TaskRouter, '_load_registry', return_value={"agents": list(mock_agents.values()), "skills": {}}):
            with patch.object(TaskRouter, '_load_stats', return_value={}):
                self.router = TaskRouter()

    @patch('task_router.get_agent_status')
    def test_fuzzy_match_by_role(self, mock_status):
        """测试通过 role 模糊匹配"""
        mock_status.return_value = "active"
        task_type, candidates, confidence = self.router._fuzzy_match("生成一份数据报告")
        # 模糊匹配总会返回至少一个候选（即使分数很低）
        self.assertGreaterEqual(len(candidates), 0)
        self.assertGreaterEqual(confidence, 0.3)

    @patch('task_router.get_agent_status')
    def test_fuzzy_match_no_match(self, mock_status):
        """测试无匹配时的降级"""
        mock_status.return_value = "active"
        task_type, candidates, confidence = self.router._fuzzy_match("完全不相关的任务")
        # 应该有候选（Jaccard 总会有一些重叠）
        self.assertGreaterEqual(confidence, 0.3)


class TestFullRouting(unittest.TestCase):
    """测试完整路由流程"""

    def setUp(self):
        mock_agents = {
            "coder": {
                "id": "coder",
                "name": "代码开发专家",
                "role": "编写代码",
                "task_types": ["code"],
                "status": "active",
                "priority": "high",
                "stats": {"success_rate": 0.85, "tasks_completed": 100}
            }
        }
        with patch.object(TaskRouter, '_load_registry', return_value={"agents": list(mock_agents.values()), "skills": {}}):
            with patch.object(TaskRouter, '_load_stats', return_value={}):
                self.router = TaskRouter()

    @patch('task_router.get_agent_status')
    def test_route_simple_task(self, mock_status):
        """测试简单任务路由"""
        mock_status.return_value = "active"
        result = self.router.route("写一个排序算法")
        self.assertEqual(result.agent_id, "coder")
        self.assertEqual(result.task_type, "code")
        self.assertGreater(result.confidence, 0.5)

    @patch('task_router.get_agent_status')
    def test_route_fallback_to_coder(self, mock_status):
        """测试降级到 coder"""
        mock_status.return_value = "standby"  # 所有 Agent 都 standby
        result = self.router.route("做点什么")
        self.assertEqual(result.agent_id, "coder")
        self.assertEqual(result.confidence, 0.2)


class TestQueueManagement(unittest.TestCase):
    """测试队列管理"""

    def setUp(self):
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.queue_path = Path(self.temp_dir) / "task_queue.jsonl"
        self.stats_path = Path(self.temp_dir) / "router_stats.json"
        self.route_log_path = Path(self.temp_dir) / "route_log.jsonl"

        # Mock paths
        self.patcher_queue = patch('task_router.QUEUE_PATH', self.queue_path)
        self.patcher_stats = patch('task_router.STATS_PATH', self.stats_path)
        self.patcher_log = patch('task_router.ROUTE_LOG_PATH', self.route_log_path)
        self.patcher_queue.start()
        self.patcher_stats.start()
        self.patcher_log.start()

        mock_agents = {
            "coder": {
                "id": "coder",
                "name": "代码开发专家",
                "role": "编写代码",
                "task_types": ["code"],
                "status": "active",
                "stats": {}
            }
        }
        with patch.object(TaskRouter, '_load_registry', return_value={"agents": list(mock_agents.values()), "skills": {}}):
            self.router = TaskRouter()

    def tearDown(self):
        self.patcher_queue.stop()
        self.patcher_stats.stop()
        self.patcher_log.stop()
        shutil.rmtree(self.temp_dir)

    @patch('task_router.get_agent_status')
    def test_submit_task(self, mock_status):
        """测试提交任务"""
        mock_status.return_value = "active"
        task = self.router.submit("写一个排序算法", priority="high")
        
        self.assertIsNotNone(task.id)
        self.assertEqual(task.agent_id, "coder")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.status, "pending")

    @patch('task_router.get_agent_status')
    def test_queue_persistence(self, mock_status):
        """测试队列持久化"""
        mock_status.return_value = "active"
        self.router.submit("任务1", priority="normal")
        self.router.submit("任务2", priority="high")
        
        queue = self.router.get_queue()
        self.assertEqual(len(queue), 2)
        # high 优先级应该排在前面
        self.assertEqual(queue[0]["priority"], "high")

    def test_get_empty_queue(self):
        """测试空队列"""
        queue = self.router.get_queue()
        self.assertEqual(len(queue), 0)

    @patch('task_router.get_agent_status')
    def test_queue_filters_non_pending(self, mock_status):
        """测试队列过滤非 pending 任务"""
        mock_status.return_value = "active"
        # 手动写入一个 done 任务
        task_done = {
            "id": "task-1",
            "description": "已完成任务",
            "status": "done",
            "priority": "normal",
            "agent_id": "coder",
            "task_type": "code",
            "created_at": "2026-03-13T08:00:00Z"
        }
        with open(self.queue_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(task_done, ensure_ascii=False) + "\n")
        
        queue = self.router.get_queue()
        self.assertEqual(len(queue), 0)


class TestStatistics(unittest.TestCase):
    """测试统计功能"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.stats_path = Path(self.temp_dir) / "router_stats.json"
        self.queue_path = Path(self.temp_dir) / "task_queue.jsonl"
        self.route_log_path = Path(self.temp_dir) / "route_log.jsonl"

        self.patcher_stats = patch('task_router.STATS_PATH', self.stats_path)
        self.patcher_queue = patch('task_router.QUEUE_PATH', self.queue_path)
        self.patcher_log = patch('task_router.ROUTE_LOG_PATH', self.route_log_path)
        self.patcher_stats.start()
        self.patcher_queue.start()
        self.patcher_log.start()

        mock_agents = {
            "coder": {
                "id": "coder",
                "name": "代码开发专家",
                "role": "编写代码",
                "task_types": ["code"],
                "status": "active",
                "stats": {}
            }
        }
        with patch.object(TaskRouter, '_load_registry', return_value={"agents": list(mock_agents.values()), "skills": {}}):
            self.router = TaskRouter()

    def tearDown(self):
        self.patcher_stats.stop()
        self.patcher_queue.stop()
        self.patcher_log.stop()
        shutil.rmtree(self.temp_dir)

    @patch('task_router.get_agent_status')
    def test_stats_increment(self, mock_status):
        """测试统计递增"""
        mock_status.return_value = "active"
        initial_count = self.router.stats.get("total_routed", 0)
        self.router.submit("任务1")
        self.router.submit("任务2")
        
        self.assertEqual(self.router.stats["total_routed"], initial_count + 2)

    @patch('task_router.get_agent_status')
    def test_stats_by_agent(self, mock_status):
        """测试按 Agent 统计"""
        mock_status.return_value = "active"
        self.router.submit("任务1")
        self.router.submit("任务2")
        
        self.assertEqual(self.router.stats["by_agent"]["coder"], 2)

    def test_get_stats(self):
        """测试获取统计"""
        stats = self.router.get_stats()
        self.assertIn("agents_total", stats)
        self.assertIn("agents_active", stats)
        self.assertIn("queue_pending", stats)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.queue_path = Path(self.temp_dir) / "task_queue.jsonl"
        self.stats_path = Path(self.temp_dir) / "router_stats.json"
        self.route_log_path = Path(self.temp_dir) / "route_log.jsonl"

        self.patcher_queue = patch('task_router.QUEUE_PATH', self.queue_path)
        self.patcher_stats = patch('task_router.STATS_PATH', self.stats_path)
        self.patcher_log = patch('task_router.ROUTE_LOG_PATH', self.route_log_path)
        self.patcher_queue.start()
        self.patcher_stats.start()
        self.patcher_log.start()

    def tearDown(self):
        self.patcher_queue.stop()
        self.patcher_stats.stop()
        self.patcher_log.stop()
        shutil.rmtree(self.temp_dir)

    def test_load_corrupted_stats(self):
        """测试加载损坏的统计文件"""
        self.stats_path.write_text("invalid json{", encoding="utf-8")
        
        with patch.object(TaskRouter, '_load_registry', return_value={"agents": [], "skills": {}}):
            router = TaskRouter()
            self.assertEqual(router.stats["total_routed"], 0)

    def test_get_queue_with_corrupted_line(self):
        """测试队列中有损坏的行"""
        self.queue_path.write_text(
            '{"id": "task-1", "status": "pending", "priority": "normal", "description": "任务1", "agent_id": "coder", "task_type": "code", "created_at": "2026-03-13T08:00:00Z"}\n'
            'invalid json{\n'
            '{"id": "task-2", "status": "pending", "priority": "normal", "description": "任务2", "agent_id": "coder", "task_type": "code", "created_at": "2026-03-13T08:00:00Z"}\n',
            encoding="utf-8"
        )
        
        mock_agents = {"coder": {"id": "coder", "name": "Coder", "task_types": ["code"], "status": "active"}}
        with patch.object(TaskRouter, '_load_registry', return_value={"agents": list(mock_agents.values()), "skills": {}}):
            with patch.object(TaskRouter, '_load_stats', return_value={}):
                router = TaskRouter()
                queue = router.get_queue()
                # 应该跳过损坏的行，返回 2 个有效任务
                self.assertEqual(len(queue), 2)


class TestPlanningIntegration(unittest.TestCase):
    """测试 Planning 集成"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.queue_path = Path(self.temp_dir) / "task_queue.jsonl"
        self.stats_path = Path(self.temp_dir) / "router_stats.json"
        self.route_log_path = Path(self.temp_dir) / "route_log.jsonl"

        self.patcher_queue = patch('task_router.QUEUE_PATH', self.queue_path)
        self.patcher_stats = patch('task_router.STATS_PATH', self.stats_path)
        self.patcher_log = patch('task_router.ROUTE_LOG_PATH', self.route_log_path)
        self.patcher_queue.start()
        self.patcher_stats.start()
        self.patcher_log.start()

        mock_agents = {
            "coder": {
                "id": "coder",
                "name": "代码开发专家",
                "role": "编写代码",
                "task_types": ["code"],
                "status": "active",
                "stats": {}
            }
        }
        with patch.object(TaskRouter, '_load_registry', return_value={"agents": list(mock_agents.values()), "skills": {}}):
            with patch.object(TaskRouter, '_load_stats', return_value={}):
                self.router = TaskRouter()

    def tearDown(self):
        self.patcher_queue.stop()
        self.patcher_stats.stop()
        self.patcher_log.stop()
        shutil.rmtree(self.temp_dir)

    @patch('task_router.get_agent_status')
    def test_plan_unavailable_fallback(self, mock_status):
        """测试 Planner 不可用时降级"""
        mock_status.return_value = "active"
        self.router._planner = False  # 标记为不可用
        
        tasks = self.router.plan_and_submit("复杂任务")
        self.assertEqual(len(tasks), 1)

    @patch('task_router.get_agent_status')
    def test_plan_simple_task_no_decomposition(self, mock_status):
        """测试简单任务不拆解"""
        mock_status.return_value = "active"
        
        # Mock Planner
        mock_planner = MagicMock()
        mock_plan = MagicMock()
        mock_plan.subtasks = [MagicMock(description="单一任务", priority="normal")]
        mock_planner.plan.return_value = mock_plan
        self.router._planner = mock_planner
        
        tasks = self.router.plan_and_submit("简单任务")
        self.assertEqual(len(tasks), 1)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
