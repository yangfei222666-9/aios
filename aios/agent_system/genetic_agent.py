"""
遗传Agent - 基于遗传算法的自动优化系统
通过选择、交叉、变异来进化Agent配置和策略
"""
import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class GeneticAgent:
    """遗传Agent - 自动进化优化"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.data_dir = workspace / "aios" / "agent_system" / "data"
        self.genetic_dir = self.data_dir / "genetic"
        self.genetic_dir.mkdir(parents=True, exist_ok=True)
        
        # 遗传算法参数
        self.population_size = 10  # 种群大小
        self.mutation_rate = 0.1   # 变异率
        self.crossover_rate = 0.7  # 交叉率
        self.elite_size = 2        # 精英保留数量
        
        # 配置空间
        self.config_space = {
            "timeout": [30, 60, 90, 120, 180],
            "max_retries": [1, 2, 3, 5, 7],
            "thinking": ["off", "low", "medium", "high"],
            "priority": [0.0625, 0.125, 0.25, 0.5, 1.0],
            "model": ["claude-sonnet-4-6", "claude-opus-4-6"]
        }
    
    def load_population(self) -> List[Dict]:
        """加载种群"""
        pop_file = self.genetic_dir / "population.json"
        if pop_file.exists():
            with open(pop_file, encoding="utf-8") as f:
                return json.load(f)
        return []
    
    def save_population(self, population: List[Dict]):
        """保存种群"""
        pop_file = self.genetic_dir / "population.json"
        with open(pop_file, "w", encoding="utf-8") as f:
            json.dump(population, f, indent=2, ensure_ascii=False)
    
    def initialize_population(self) -> List[Dict]:
        """初始化种群"""
        print("🧬 初始化种群...")
        population = []
        
        for i in range(self.population_size):
            individual = {
                "id": f"gen0-{i}",
                "generation": 0,
                "config": {
                    "timeout": random.choice(self.config_space["timeout"]),
                    "max_retries": random.choice(self.config_space["max_retries"]),
                    "thinking": random.choice(self.config_space["thinking"]),
                    "priority": random.choice(self.config_space["priority"]),
                    "model": random.choice(self.config_space["model"])
                },
                "fitness": 0.0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "avg_duration": 0.0,
                "created_at": datetime.now().isoformat()
            }
            population.append(individual)
        
        self.save_population(population)
        print(f"  ✓ 创建了 {len(population)} 个个体")
        return population
    
    def evaluate_fitness(self, individual: Dict) -> float:
        """评估适应度"""
        # 适应度 = 成功率 * 0.5 + (1 - 归一化耗时) * 0.3 + (1 - 归一化超时) * 0.2
        
        completed = individual.get("tasks_completed", 0)
        failed = individual.get("tasks_failed", 0)
        total = completed + failed
        
        if total == 0:
            return 0.0
        
        # 成功率 (0-1)
        success_rate = completed / total
        
        # 耗时 (归一化到0-1，越小越好)
        avg_duration = individual.get("avg_duration", 60)
        normalized_duration = min(avg_duration / 180, 1.0)  # 180秒为最大
        
        # 超时配置 (归一化到0-1，适中最好)
        timeout = individual["config"]["timeout"]
        normalized_timeout = abs(timeout - 90) / 90  # 90秒为最优
        
        # 综合适应度
        fitness = (
            success_rate * 0.5 +
            (1 - normalized_duration) * 0.3 +
            (1 - normalized_timeout) * 0.2
        )
        
        return round(fitness, 4)
    
    def select_parents(self, population: List[Dict]) -> List[Dict]:
        """选择父代（锦标赛选择）"""
        parents = []
        tournament_size = 3
        
        for _ in range(len(population) - self.elite_size):
            # 随机选择tournament_size个个体
            tournament = random.sample(population, tournament_size)
            # 选择适应度最高的
            winner = max(tournament, key=lambda x: x["fitness"])
            parents.append(winner)
        
        return parents
    
    def crossover(self, parent1: Dict, parent2: Dict, generation: int) -> Dict:
        """交叉（单点交叉）"""
        if random.random() > self.crossover_rate:
            # 不交叉，直接返回parent1的副本
            return self._copy_individual(parent1, generation)
        
        # 交叉
        child_config = {}
        for key in parent1["config"]:
            # 随机选择父代之一的基因
            child_config[key] = random.choice([
                parent1["config"][key],
                parent2["config"][key]
            ])
        
        child = {
            "id": f"gen{generation}-{random.randint(1000, 9999)}",
            "generation": generation,
            "config": child_config,
            "fitness": 0.0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_duration": 0.0,
            "parents": [parent1["id"], parent2["id"]],
            "created_at": datetime.now().isoformat()
        }
        
        return child
    
    def mutate(self, individual: Dict):
        """变异"""
        for key in individual["config"]:
            if random.random() < self.mutation_rate:
                # 变异：随机选择新值
                individual["config"][key] = random.choice(self.config_space[key])
    
    def _copy_individual(self, individual: Dict, generation: int) -> Dict:
        """复制个体"""
        return {
            "id": f"gen{generation}-{random.randint(1000, 9999)}",
            "generation": generation,
            "config": individual["config"].copy(),
            "fitness": 0.0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_duration": 0.0,
            "parent": individual["id"],
            "created_at": datetime.now().isoformat()
        }
    
    def evolve(self) -> Dict:
        """进化一代"""
        print("🧬 开始进化...")
        
        # 加载当前种群
        population = self.load_population()
        if not population:
            population = self.initialize_population()
        
        current_gen = max(ind["generation"] for ind in population)
        next_gen = current_gen + 1
        
        print(f"  当前代: {current_gen}, 下一代: {next_gen}")
        
        # 1. 评估适应度
        for ind in population:
            ind["fitness"] = self.evaluate_fitness(ind)
        
        # 2. 排序（按适应度降序）
        population.sort(key=lambda x: x["fitness"], reverse=True)
        
        print(f"  最佳适应度: {population[0]['fitness']:.4f}")
        print(f"  平均适应度: {sum(ind['fitness'] for ind in population) / len(population):.4f}")
        
        # 3. 精英保留
        new_population = population[:self.elite_size]
        print(f"  保留精英: {self.elite_size} 个")
        
        # 4. 选择父代
        parents = self.select_parents(population)
        
        # 5. 交叉和变异
        while len(new_population) < self.population_size:
            # 随机选择两个父代
            parent1, parent2 = random.sample(parents, 2)
            
            # 交叉
            child = self.crossover(parent1, parent2, next_gen)
            
            # 变异
            self.mutate(child)
            
            new_population.append(child)
        
        # 6. 保存新种群
        self.save_population(new_population)
        
        # 7. 生成报告
        report = {
            "generation": next_gen,
            "best_fitness": new_population[0]["fitness"],
            "avg_fitness": sum(ind["fitness"] for ind in new_population) / len(new_population),
            "best_config": new_population[0]["config"],
            "timestamp": datetime.now().isoformat()
        }
        
        report_file = self.genetic_dir / f"evolution_gen{next_gen}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ 进化完成，新种群已保存")
        return report
    
    def get_best_config(self) -> Dict:
        """获取最佳配置"""
        population = self.load_population()
        if not population:
            return None
        
        # 评估适应度
        for ind in population:
            ind["fitness"] = self.evaluate_fitness(ind)
        
        # 返回最佳个体
        best = max(population, key=lambda x: x["fitness"])
        return best["config"]
    
    def update_individual_stats(self, individual_id: str, completed: int, failed: int, avg_duration: float):
        """更新个体统计"""
        population = self.load_population()
        
        for ind in population:
            if ind["id"] == individual_id:
                ind["tasks_completed"] = completed
                ind["tasks_failed"] = failed
                ind["avg_duration"] = avg_duration
                break
        
        self.save_population(population)

def main():
    """主函数"""
    workspace = Path("C:/Users/A/.openclaw/workspace")
    agent = GeneticAgent(workspace)
    
    print("=" * 80)
    print("遗传Agent - 自动进化优化系统")
    print("=" * 80)
    print()
    
    # 检查是否已有种群
    population = agent.load_population()
    
    if not population:
        print("首次运行，初始化种群...")
        agent.initialize_population()
    else:
        print(f"已有种群: {len(population)} 个个体")
        print(f"当前代: {max(ind['generation'] for ind in population)}")
        print()
        
        # 进化
        report = agent.evolve()
        
        print()
        print("=" * 80)
        print("进化报告")
        print("=" * 80)
        print(f"代数: {report['generation']}")
        print(f"最佳适应度: {report['best_fitness']:.4f}")
        print(f"平均适应度: {report['avg_fitness']:.4f}")
        print(f"最佳配置:")
        for key, value in report['best_config'].items():
            print(f"  - {key}: {value}")
        print("=" * 80)

if __name__ == "__main__":
    main()
