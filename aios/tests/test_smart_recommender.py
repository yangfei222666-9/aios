"""
AIOS Smart Recommender 单元测试

测试覆盖：
1. 执行路径推荐
2. 耗时预测
3. 风险检查
4. 参数建议
5. 完整推荐报告
"""
import pytest
import sys
from pathlib import Path
import tempfile
import shutil
import time

# 添加 core 到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from smart_recommender import SmartRecommender
from adaptive_learning import AdaptiveLearning, ExecutionPattern, FailurePattern


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def recommender(temp_data_dir):
    """创建测试推荐器实例"""
    # 创建 AdaptiveLearning 实例
    from adaptive_learning import _adaptive_learning
    _adaptive_learning.data_dir = temp_data_dir
    _adaptive_learning.success_patterns_file = temp_data_dir / "success_patterns.jsonl"
    _adaptive_learning.failure_patterns_file = temp_data_dir / "failure_patterns.jsonl"
    _adaptive_learning.user_preferences_file = temp_data_dir / "user_preferences.json"
    _adaptive_learning.success_patterns = {}
    _adaptive_learning.failure_patterns = {}
    _adaptive_learning.user_preferences = {}
    
    return SmartRecommender()


class TestExecutionPathRecommendation:
    """测试执行路径推荐"""
    
    def test_recommend_with_history(self, recommender):
        """测试有历史数据时的推荐"""
        # 添加成功模式
        pattern = ExecutionPattern(
            pattern_id="test_pattern",
            task_type="simple",
            intent_action="view",
            intent_target="agent",
            agent_sequence=["planner", "executor"],
            success_count=5,
            failure_count=0,
            avg_duration=30.0,
            last_used=time.time(),
            confidence=1.0,
        )
        recommender.al.success_patterns["test_pattern"] = pattern
        
        # 获取推荐
        rec = recommender.recommend_execution_path("simple", "view", "agent")
        
        # 验证推荐
        assert rec is not None
        assert rec["pattern_id"] == "test_pattern"
        assert rec["agent_sequence"] == ["planner", "executor"]
        assert rec["confidence"] == 1.0
        assert rec["success_count"] == 5
    
    def test_no_recommendation_without_history(self, recommender):
        """测试无历史数据时无推荐"""
        rec = recommender.recommend_execution_path("unknown", "unknown", "unknown")
        assert rec is None


class TestDurationPrediction:
    """测试耗时预测"""
    
    def test_predict_with_sufficient_data(self, recommender):
        """测试有足够数据时的预测"""
        # 添加成功模式
        pattern = ExecutionPattern(
            pattern_id="test_pattern",
            task_type="simple",
            intent_action="view",
            intent_target="agent",
            agent_sequence=["planner"],
            success_count=5,
            failure_count=0,
            avg_duration=45.0,
            last_used=time.time(),
            confidence=0.9,
        )
        recommender.al.success_patterns["test_pattern"] = pattern
        
        # 预测耗时
        duration, message = recommender.predict_duration("simple", "view", "agent")
        
        # 验证预测
        assert duration == 45.0
        assert "45.0秒" in message
        assert "高" in message
    
    def test_predict_with_insufficient_data(self, recommender):
        """测试数据不足时使用默认值"""
        duration, message = recommender.predict_duration(
            "unknown", "unknown", "unknown", default_duration=60.0
        )
        
        # 验证使用默认值
        assert duration == 60.0
        assert "60.0秒" in message
        assert "低" in message
        assert "默认值" in message


class TestRiskChecking:
    """测试风险检查"""
    
    def test_detect_known_failure(self, recommender):
        """测试检测已知失败"""
        # 添加失败模式
        failure = FailurePattern(
            pattern_id="fail_pattern",
            task_description="删除文件失败",
            error_type="PermissionError",
            error_message="权限不足",
            context={"action": "delete", "target": "file"},
            occurrence_count=5,
            first_seen=time.time() - 86400,
            last_seen=time.time(),
            suggested_fix="检查文件权限",
        )
        recommender.al.failure_patterns["fail_pattern"] = failure
        
        # 检查风险
        context = {
            "task_type": "simple",
            "action": "delete",
            "target": "file",
        }
        risks = recommender.check_risks(context)
        
        # 验证检测到已知失败
        known_failures = [r for r in risks if r["type"] == "known_failure"]
        assert len(known_failures) > 0
        assert known_failures[0]["level"] == "high"
        assert "5 次" in known_failures[0]["message"]
    
    def test_detect_destructive_operation(self, recommender):
        """测试检测破坏性操作"""
        context = {"action": "delete"}
        risks = recommender.check_risks(context)
        
        # 验证检测到破坏性操作
        destructive = [r for r in risks if r["type"] == "destructive_operation"]
        assert len(destructive) > 0
        assert destructive[0]["level"] == "high"
        assert "不可逆" in destructive[0]["message"]
    
    def test_detect_system_modification(self, recommender):
        """测试检测系统修改"""
        context = {"action": "modify", "target": "system"}
        risks = recommender.check_risks(context)
        
        # 验证检测到系统修改
        system_mod = [r for r in risks if r["type"] == "system_modification"]
        assert len(system_mod) > 0
        assert system_mod[0]["level"] == "medium"
    
    def test_no_risks_for_safe_operation(self, recommender):
        """测试安全操作无风险"""
        context = {"action": "view", "target": "data"}
        risks = recommender.check_risks(context)
        
        # 验证无风险（或只有低风险）
        high_risks = [r for r in risks if r["level"] == "high"]
        assert len(high_risks) == 0


class TestParameterSuggestions:
    """测试参数建议"""
    
    def test_suggest_format_from_preference(self, recommender):
        """测试基于偏好建议格式"""
        # 设置用户偏好（使用 learn_preference 方法）
        recommender.al.learn_preference("output", "output_format", "json")
        
        # 获取建议
        suggestions = recommender.suggest_parameters("simple", {})
        
        # 验证建议
        assert "format" in suggestions
        assert suggestions["format"] == "json"
    
    def test_suggest_limit_for_analysis(self, recommender):
        """测试为分析任务建议限制"""
        suggestions = recommender.suggest_parameters("analysis", {})
        
        # 验证建议
        assert "limit" in suggestions
        assert suggestions["limit"] == 10
    
    def test_suggest_timeout_for_code(self, recommender):
        """测试为代码任务建议超时"""
        suggestions = recommender.suggest_parameters("code", {})
        
        # 验证建议
        assert "timeout" in suggestions
        assert suggestions["timeout"] == 120
    
    def test_no_duplicate_suggestions(self, recommender):
        """测试不重复建议已有参数"""
        current_params = {"format": "xml", "limit": 20}
        suggestions = recommender.suggest_parameters("analysis", current_params)
        
        # 验证不重复建议
        assert "format" not in suggestions
        assert "limit" not in suggestions


class TestRecommendationReport:
    """测试推荐报告"""
    
    def test_generate_complete_report(self, recommender):
        """测试生成完整报告"""
        # 添加成功模式
        pattern = ExecutionPattern(
            pattern_id="test_pattern",
            task_type="simple",
            intent_action="view",
            intent_target="agent",
            agent_sequence=["planner", "executor"],
            success_count=5,
            failure_count=0,
            avg_duration=30.0,
            last_used=time.time(),
            confidence=0.9,
        )
        recommender.al.success_patterns["test_pattern"] = pattern
        
        # 生成报告
        report = recommender.generate_recommendation_report(
            task_type="simple",
            intent_action="view",
            intent_target="agent",
            context={"action": "view", "target": "agent"},
            default_duration=60.0
        )
        
        # 验证报告内容
        assert "智能推荐报告" in report
        assert "执行路径推荐" in report
        assert "耗时预测" in report
        assert "风险检查" in report
        assert "参数建议" in report
    
    def test_report_shows_risks(self, recommender):
        """测试报告显示风险"""
        report = recommender.generate_recommendation_report(
            task_type="simple",
            intent_action="delete",
            intent_target="file",
            context={"action": "delete"},
            default_duration=10.0
        )
        
        # 验证报告包含风险警告
        assert "风险检查" in report
        assert "不可逆" in report or "风险" in report
    
    def test_report_shows_no_risks(self, recommender):
        """测试报告显示无风险"""
        report = recommender.generate_recommendation_report(
            task_type="simple",
            intent_action="view",
            intent_target="data",
            context={"action": "view", "target": "data"},
            default_duration=10.0
        )
        
        # 验证报告显示无风险
        assert "风险检查" in report
        assert "未发现潜在风险" in report


class TestIntegration:
    """集成测试"""
    
    def test_full_recommendation_workflow(self, recommender):
        """测试完整推荐工作流"""
        # 1. 添加历史数据
        pattern = ExecutionPattern(
            pattern_id="workflow_pattern",
            task_type="analysis",
            intent_action="analyze",
            intent_target="data",
            agent_sequence=["analyzer", "reporter"],
            success_count=10,
            failure_count=1,
            avg_duration=120.0,
            last_used=time.time(),
            confidence=0.9,
        )
        recommender.al.success_patterns["workflow_pattern"] = pattern
        
        # 2. 设置用户偏好
        recommender.al.learn_preference("output", "output_format", "markdown")
        
        # 3. 获取推荐
        path_rec = recommender.recommend_execution_path("analysis", "analyze", "data")
        duration, _ = recommender.predict_duration("analysis", "analyze", "data")
        risks = recommender.check_risks({"action": "analyze", "target": "data"})
        params = recommender.suggest_parameters("analysis", {})
        
        # 4. 验证所有推荐
        assert path_rec is not None
        assert path_rec["confidence"] == 0.9
        assert duration == 120.0
        assert "format" in params
        assert params["format"] == "markdown"
        assert "limit" in params


class TestEdgeCases:
    """测试边界条件"""
    
    def test_empty_context(self, recommender):
        """测试空上下文"""
        risks = recommender.check_risks({})
        assert isinstance(risks, list)
    
    def test_none_values(self, recommender):
        """测试 None 值"""
        rec = recommender.recommend_execution_path(None, None, None)
        assert rec is None
    
    def test_empty_parameters(self, recommender):
        """测试空参数"""
        suggestions = recommender.suggest_parameters("unknown", {})
        assert isinstance(suggestions, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
