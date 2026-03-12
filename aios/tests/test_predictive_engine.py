"""
AIOS Predictive Engine 单元测试

测试覆盖：
1. 时间模式识别
2. 任务序列预测
3. 异常检测
4. 数据持久化
5. 边界条件
"""
import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys
import tempfile
import shutil

# 添加 core 到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from predictive_engine import PredictiveEngine, TimePattern, TaskSequence, Prediction


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def engine(temp_data_dir):
    """创建测试引擎实例"""
    return PredictiveEngine(data_dir=temp_data_dir)


class TestTimePatternRecognition:
    """测试时间模式识别"""
    
    def test_record_task_creates_time_pattern(self, engine):
        """测试记录任务创建时间模式"""
        engine.record_task("monitor", "查看系统状态")
        
        # 验证时间模式已创建
        assert len(engine.time_patterns) > 0
        
        # 验证模式内容
        pattern = list(engine.time_patterns.values())[0]
        assert pattern.task_type == "monitor"
        assert pattern.occurrence_count == 1
        assert 0 <= pattern.hour_of_day <= 23
        assert 0 <= pattern.day_of_week <= 6
    
    def test_repeated_task_increases_confidence(self, engine):
        """测试重复任务增加置信度"""
        # 记录同一任务多次
        for _ in range(5):
            engine.record_task("monitor", "查看系统状态")
            time.sleep(0.01)
        
        # 验证置信度增加
        pattern = list(engine.time_patterns.values())[0]
        assert pattern.occurrence_count == 5
        assert pattern.confidence > 0.1  # 初始置信度
        assert pattern.confidence <= 0.95  # 最大置信度
    
    def test_time_pattern_persistence(self, engine, temp_data_dir):
        """测试时间模式持久化"""
        engine.record_task("analysis", "分析数据")
        
        # 创建新引擎实例（模拟重启）
        new_engine = PredictiveEngine(data_dir=temp_data_dir)
        
        # 验证数据已加载
        assert len(new_engine.time_patterns) > 0
        pattern = list(new_engine.time_patterns.values())[0]
        assert pattern.task_type == "analysis"


class TestTaskSequencePrediction:
    """测试任务序列预测"""
    
    def test_sequence_detection(self, engine):
        """测试序列检测"""
        # 记录任务序列
        engine.record_task("monitor", "查看系统")
        time.sleep(0.01)
        engine.record_task("analysis", "分析数据")
        time.sleep(0.01)
        engine.record_task("code", "执行代码")
        
        # 验证序列已创建
        assert len(engine.task_sequences) > 0
    
    def test_predict_next_task(self, engine):
        """测试预测下一个任务"""
        # 建立模式：monitor → analysis → code
        for _ in range(3):
            engine.record_task("monitor", "查看系统")
            time.sleep(0.01)
            engine.record_task("analysis", "分析数据")
            time.sleep(0.01)
            engine.record_task("code", "执行代码")
            time.sleep(0.01)
        
        # 记录前两个任务
        engine.record_task("monitor", "查看系统")
        time.sleep(0.01)
        engine.record_task("analysis", "分析数据")
        
        # 预测下一个任务
        prediction = engine.predict_next_task()
        
        # 验证预测结果
        assert prediction is not None
        assert prediction["predicted_task"] == "code"
        assert prediction["confidence"] >= 0.5
        assert "reason" in prediction
    
    def test_no_prediction_with_insufficient_data(self, engine):
        """测试数据不足时无预测"""
        engine.record_task("monitor", "查看系统")
        
        prediction = engine.predict_next_task()
        assert prediction is None


class TestAnomalyDetection:
    """测试异常检测"""
    
    def test_detect_high_frequency_anomaly(self, engine):
        """测试检测高频异常"""
        # 记录同一任务10次
        for _ in range(10):
            engine.record_task("monitor", "查看系统")
            time.sleep(0.01)
        
        anomalies = engine.detect_anomalies()
        
        # 验证检测到高频异常
        assert len(anomalies) > 0
        high_freq = [a for a in anomalies if a["type"] == "high_frequency"]
        assert len(high_freq) > 0
        assert high_freq[0]["task_type"] == "monitor"
    
    def test_detect_rapid_execution_anomaly(self, engine):
        """测试检测快速执行异常"""
        # 记录两个任务，间隔很短
        engine.record_task("code", "执行代码1")
        time.sleep(0.001)  # 1ms 间隔
        engine.record_task("code", "执行代码2")
        
        anomalies = engine.detect_anomalies()
        
        # 验证检测到快速执行异常
        rapid_exec = [a for a in anomalies if a["type"] == "rapid_execution"]
        assert len(rapid_exec) > 0
        assert rapid_exec[0]["interval"] < 5.0
    
    def test_whitelist_prevents_false_positives(self, engine):
        """测试白名单防止误报"""
        # 记录白名单任务（快速执行）
        engine.record_task("simple", "简单任务1")
        time.sleep(0.001)
        engine.record_task("simple", "简单任务2")
        
        anomalies = engine.detect_anomalies()
        
        # 验证不会误报
        rapid_exec = [a for a in anomalies if a["type"] == "rapid_execution"]
        assert len(rapid_exec) == 0


class TestPredictionByTime:
    """测试基于时间的预测"""
    
    def test_predict_by_current_time(self, engine):
        """测试基于当前时间预测"""
        now = datetime.now()
        
        # 记录当前时间的任务多次（建立模式）
        for _ in range(6):
            engine.record_task("monitor", "查看系统")
            time.sleep(0.01)
        
        # 预测当前时间的任务
        predictions = engine.predict_by_time()
        
        # 验证预测结果
        if predictions:
            assert predictions[0]["predicted_task"] == "monitor"
            assert predictions[0]["confidence"] >= 0.5
    
    def test_no_prediction_for_different_time(self, engine):
        """测试不同时间无预测"""
        # 记录任务（但置信度不够）
        engine.record_task("monitor", "查看系统")
        
        predictions = engine.predict_by_time()
        
        # 验证无高置信度预测
        high_conf = [p for p in predictions if p["confidence"] >= 0.5]
        assert len(high_conf) == 0


class TestStatistics:
    """测试统计功能"""
    
    def test_get_stats(self, engine):
        """测试获取统计信息"""
        # 记录一些任务
        engine.record_task("monitor", "查看系统")
        time.sleep(0.01)
        engine.record_task("analysis", "分析数据")
        time.sleep(0.01)
        engine.record_task("code", "执行代码")
        
        stats = engine.get_stats()
        
        # 验证统计数据
        assert "time_patterns" in stats
        assert "task_sequences" in stats
        assert "task_history_count" in stats
        assert stats["task_history_count"] == 3
    
    def test_high_confidence_counting(self, engine):
        """测试高置信度计数"""
        # 建立高置信度模式
        for _ in range(10):
            engine.record_task("monitor", "查看系统")
            time.sleep(0.01)
        
        stats = engine.get_stats()
        
        # 验证高置信度计数
        assert stats["high_confidence_patterns"] > 0


class TestEdgeCases:
    """测试边界条件"""
    
    def test_empty_history(self, engine):
        """测试空历史"""
        prediction = engine.predict_next_task()
        assert prediction is None
        
        predictions = engine.predict_by_time()
        assert len(predictions) == 0
        
        anomalies = engine.detect_anomalies()
        assert len(anomalies) == 0
    
    def test_single_task_history(self, engine):
        """测试单任务历史"""
        engine.record_task("monitor", "查看系统")
        
        prediction = engine.predict_next_task()
        assert prediction is None
    
    def test_task_history_limit(self, engine):
        """测试任务历史限制"""
        # 记录超过100个任务
        for i in range(150):
            engine.record_task(f"task_{i % 5}", f"任务{i}")
            time.sleep(0.001)
        
        # 验证只保留最近100条
        assert len(engine.task_history) <= 100


class TestDataStructures:
    """测试数据结构"""
    
    def test_time_pattern_structure(self):
        """测试 TimePattern 数据结构"""
        pattern = TimePattern(
            pattern_id="test_h10_d1",
            task_type="monitor",
            hour_of_day=10,
            day_of_week=1,
            occurrence_count=5,
            last_occurred=time.time(),
            confidence=0.5,
        )
        
        assert pattern.pattern_id == "test_h10_d1"
        assert pattern.task_type == "monitor"
        assert pattern.confidence == 0.5
    
    def test_task_sequence_structure(self):
        """测试 TaskSequence 数据结构"""
        sequence = TaskSequence(
            sequence_id="monitor_analysis_code",
            task_sequence=["monitor", "analysis", "code"],
            occurrence_count=3,
            avg_interval=60.0,
            confidence=0.6,
        )
        
        assert len(sequence.task_sequence) == 3
        assert sequence.avg_interval == 60.0
    
    def test_prediction_structure(self):
        """测试 Prediction 数据结构"""
        prediction = Prediction(
            prediction_id="pred_001",
            prediction_type="sequence",
            predicted_task="code",
            predicted_time=time.time() + 60,
            confidence=0.8,
            actual_occurred=None,
            actual_time=None,
        )
        
        assert prediction.prediction_type == "sequence"
        assert prediction.confidence == 0.8


class TestIntegration:
    """集成测试"""
    
    def test_full_prediction_workflow(self, engine):
        """测试完整预测工作流"""
        # 1. 建立模式
        for _ in range(5):
            engine.record_task("monitor", "查看系统")
            time.sleep(0.01)
            engine.record_task("analysis", "分析数据")
            time.sleep(0.01)
            engine.record_task("code", "执行代码")
            time.sleep(0.01)
        
        # 2. 记录前两个任务
        engine.record_task("monitor", "查看系统")
        time.sleep(0.01)
        engine.record_task("analysis", "分析数据")
        
        # 3. 预测下一个任务
        prediction = engine.predict_next_task()
        assert prediction is not None
        assert prediction["predicted_task"] == "code"
        
        # 4. 获取统计
        stats = engine.get_stats()
        assert stats["task_history_count"] >= 15
        assert stats["high_confidence_sequences"] > 0
    
    def test_anomaly_detection_workflow(self, engine):
        """测试异常检测工作流"""
        # 1. 正常任务
        engine.record_task("monitor", "查看系统")
        time.sleep(0.1)
        engine.record_task("analysis", "分析数据")
        time.sleep(0.1)
        
        # 2. 异常：高频重复
        for _ in range(10):
            engine.record_task("error_task", "错误任务")
            time.sleep(0.01)
        
        # 3. 检测异常
        anomalies = engine.detect_anomalies()
        
        # 4. 验证检测结果
        assert len(anomalies) > 0
        high_freq = [a for a in anomalies if a["type"] == "high_frequency"]
        assert len(high_freq) > 0


def test_global_instance():
    """测试全局实例"""
    from predictive_engine import get_predictive_engine
    
    engine1 = get_predictive_engine()
    engine2 = get_predictive_engine()
    
    # 验证是同一个实例
    assert engine1 is engine2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
