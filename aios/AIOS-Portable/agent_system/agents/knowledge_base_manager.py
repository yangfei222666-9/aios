"""Knowledge Base Manager - 学习 Agent 知识库管理"""
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import hashlib

class KnowledgeBaseManager:
    def __init__(self):
        self.kb_file = Path("data/knowledge/knowledge_base.json")
        self.learning_dir = Path("data/learning")
        self.reports_dir = Path("data/github_learning")
        
    def manage_knowledge(self):
        """管理知识库"""
        print("=" * 80)
        print("Knowledge Base Manager - 知识库管理")
        print("=" * 80)
        
        # 1. 收集学习报告
        reports = self._collect_reports()
        print(f"\n📚 收集到 {len(reports)} 份学习报告")
        
        # 2. 提取知识点
        knowledge = self._extract_knowledge(reports)
        print(f"🔍 提取到 {len(knowledge)} 个知识点")
        
        # 3. 去重和合并
        unique_knowledge = self._deduplicate(knowledge)
        print(f"✨ 去重后剩余 {len(unique_knowledge)} 个知识点")
        
        # 4. 分类整理
        categorized = self._categorize_knowledge(unique_knowledge)
        
        print(f"\n📊 知识分类:")
        for category, items in categorized.items():
            print(f"  {category}: {len(items)} 个")
        
        # 5. 生成索引
        index = self._build_index(unique_knowledge)
        print(f"\n🔎 索引关键词: {len(index)} 个")
        
        # 6. 保存知识库
        self._save_knowledge_base(unique_knowledge, categorized, index)
        
        # 7. 生成摘要
        summary = self._generate_summary(unique_knowledge, categorized)
        print(f"\n📝 知识库摘要:")
        print(summary)
        
        print(f"\n{'=' * 80}")
    
    def search(self, query):
        """搜索知识库"""
        print("=" * 80)
        print(f"Knowledge Base Search - 搜索: {query}")
        print("=" * 80)
        
        kb = self._load_knowledge_base()
        if not kb:
            print("\n✗ 知识库为空")
            return []
        
        # 简单关键词匹配
        results = []
        query_lower = query.lower()
        
        for item in kb.get("knowledge", []):
            title = item.get("title", "").lower()
            content = item.get("content", "").lower()
            tags = " ".join(item.get("tags", [])).lower()
            
            if query_lower in title or query_lower in content or query_lower in tags:
                results.append(item)
        
        print(f"\n🔍 找到 {len(results)} 个结果:\n")
        for i, item in enumerate(results[:5], 1):
            print(f"{i}. {item.get('title')}")
            print(f"   来源: {item.get('source')}")
            print(f"   标签: {', '.join(item.get('tags', []))}")
            print(f"   内容: {item.get('content')[:100]}...\n")
        
        return results
    
    def _collect_reports(self):
        """收集学习报告"""
        reports = []
        
        # 从 learning 目录收集
        if self.learning_dir.exists():
            for file in self.learning_dir.glob("*.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        reports.append({
                            "source": file.name,
                            "type": "learning",
                            "data": data
                        })
                except Exception as e:
                    print(f"  ✗ 读取失败: {file.name} - {e}")
        
        # 从 github_learning 目录收集
        if self.reports_dir.exists():
            for file in self.reports_dir.glob("*.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        reports.append({
                            "source": file.name,
                            "type": "github",
                            "data": data
                        })
                except Exception as e:
                    print(f"  ✗ 读取失败: {file.name} - {e}")
        
        return reports
    
    def _extract_knowledge(self, reports):
        """提取知识点"""
        knowledge = []
        
        for report in reports:
            data = report.get("data", {})
            source = report.get("source")
            
            # 提取项目信息
            if "projects" in data:
                for project in data.get("projects", []):
                    knowledge.append({
                        "title": project.get("name", "未命名项目"),
                        "content": project.get("description", ""),
                        "source": source,
                        "type": "project",
                        "tags": project.get("tags", []),
                        "url": project.get("url", ""),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 提取架构信息
            if "architecture" in data:
                arch = data.get("architecture", {})
                knowledge.append({
                    "title": f"架构: {arch.get('name', '未命名')}",
                    "content": arch.get("description", ""),
                    "source": source,
                    "type": "architecture",
                    "tags": arch.get("tags", []),
                    "timestamp": datetime.now().isoformat()
                })
            
            # 提取代码示例
            if "code_examples" in data:
                for example in data.get("code_examples", []):
                    knowledge.append({
                        "title": example.get("title", "代码示例"),
                        "content": example.get("code", ""),
                        "source": source,
                        "type": "code",
                        "tags": example.get("tags", []),
                        "timestamp": datetime.now().isoformat()
                    })
        
        return knowledge
    
    def _deduplicate(self, knowledge):
        """去重（基于内容哈希）"""
        seen = set()
        unique = []
        
        for item in knowledge:
            # 计算内容哈希
            content = item.get("title", "") + item.get("content", "")
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(item)
        
        return unique
    
    def _categorize_knowledge(self, knowledge):
        """分类知识"""
        categorized = defaultdict(list)
        
        for item in knowledge:
            item_type = item.get("type", "other")
            categorized[item_type].append(item)
        
        return dict(categorized)
    
    def _build_index(self, knowledge):
        """构建关键词索引"""
        index = defaultdict(list)
        
        for i, item in enumerate(knowledge):
            # 索引标题
            title = item.get("title", "")
            for word in title.split():
                if len(word) > 2:
                    index[word.lower()].append(i)
            
            # 索引标签
            for tag in item.get("tags", []):
                index[tag.lower()].append(i)
        
        return dict(index)
    
    def _save_knowledge_base(self, knowledge, categorized, index):
        """保存知识库"""
        kb = {
            "timestamp": datetime.now().isoformat(),
            "total": len(knowledge),
            "categories": {k: len(v) for k, v in categorized.items()},
            "knowledge": knowledge,
            "index": index
        }
        
        self.kb_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.kb_file, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 知识库已保存: {self.kb_file}")
    
    def _load_knowledge_base(self):
        """加载知识库"""
        if not self.kb_file.exists():
            return None
        
        with open(self.kb_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _generate_summary(self, knowledge, categorized):
        """生成摘要"""
        summary = f"知识库包含 {len(knowledge)} 个知识点\n"
        summary += "\n分类统计:\n"
        for category, items in categorized.items():
            summary += f"  • {category}: {len(items)} 个\n"
        
        # 最新知识
        recent = sorted(knowledge, key=lambda x: x.get("timestamp", ""), reverse=True)[:3]
        summary += "\n最新知识:\n"
        for item in recent:
            summary += f"  • {item.get('title')}\n"
        
        return summary

if __name__ == "__main__":
    import sys
    
    manager = KnowledgeBaseManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        # 搜索: python knowledge_base_manager.py search "关键词"
        if len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            manager.search(query)
        else:
            print("用法: python knowledge_base_manager.py search <关键词>")
    else:
        # 管理知识库
        manager.manage_knowledge()
