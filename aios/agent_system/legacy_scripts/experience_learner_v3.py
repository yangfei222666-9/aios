# experience_learner_v3.py - Phase 3 最终生产版（已解决所有问题）
import lancedb
from datetime import datetime
from cachetools import TTLCache
from embedding_generator import generate_embedding
from kun_strategy import get_kun_thresholds  # 动态坤卦阈值

class KunExperienceLearnerV3:
    def __init__(self, db_path="experience_db.lance"):
        self.db = lancedb.connect(db_path)
        self.table_name = "success_patterns"
        self.table = self._get_or_create_table()
        self.cache = TTLCache(maxsize=200, ttl=3600)
        self.kun_thresholds = get_kun_thresholds()
    
    def _get_or_create_table(self):
        if self.table_name in self.db.table_names():
            return self.db.open_table(self.table_name)
        
        # 创建空表（先用空数据初始化）
        import pyarrow as pa
        schema = pa.schema([
            pa.field("vector", pa.list_(pa.float32(), 384)),
            pa.field("task_id", pa.string()),
            pa.field("error_type", pa.string()),
            pa.field("strategy_used", pa.string()),
            pa.field("success", pa.bool_()),
            pa.field("timestamp", pa.string()),
            pa.field("regen_time", pa.float64()),
            pa.field("confidence", pa.float64())
        ])
        
        table = self.db.create_table(self.table_name, schema=schema)
        print("[KUN_DB v3.0] LanceDB experience library ready")
        return table
    
    def recommend(self, task: dict) -> dict:
        error_type = task.get('error_type', 'unknown')
        
        if error_type in self.cache:
            recommended = self.cache[error_type]
        else:
            try:
                embedding = generate_embedding(task.get('prompt', ''))
                results = (self.table.search(embedding)
                          .where(f"error_type = '{error_type}'")
                          .limit(3)
                          .to_list())
                
                if results:
                    best = max(results, key=lambda x: x.get('confidence', 0))
                    recommended = best['strategy_used']
                    self.cache[error_type] = recommended
                else:
                    recommended = "default_recovery"
            except Exception as e:
                print(f"[KUN_DB] Query failed, fallback to default: {e}")
                recommended = "default_recovery"
        
        task['enhanced_prompt'] = f"[KUN_LEARNED v3.0] Historical success strategy: {recommended}\n{task.get('prompt', '')}"
        print(f"[KUN_LEARN v3.0] Recommended strategy for {error_type}: {recommended}")
        return task
    
    def save_success(self, task_result: dict):
        try:
            embedding = generate_embedding(task_result.get('prompt', ''))
            confidence = 0.98 if task_result.get('success_rate', 0) > self.kun_thresholds['success_rate'] else 0.80
            
            self.table.add([{
                "vector": embedding,
                "task_id": task_result['id'],
                "error_type": task_result.get('error_type'),
                "strategy_used": task_result.get('strategy'),
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "regen_time": task_result.get('duration', 0),
                "confidence": confidence
            }])
            print(f"[KUN_SAVE v3.0] New trajectory saved to LanceDB (confidence={confidence:.2f})")
        except Exception as e:
            print(f"[KUN_SAVE] Save failed: {e}")

# 全局单例
learner_v3 = KunExperienceLearnerV3()
