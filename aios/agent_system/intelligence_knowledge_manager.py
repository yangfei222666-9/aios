#!/usr/bin/env python3
"""
Knowledge Manager Agent

Responsibilities:
1. Extract knowledge from events, logs, and reports
2. Deduplicate and merge similar knowledge
3. Build knowledge graph (relationships)
4. Provide knowledge retrieval
5. Auto-update MEMORY.md

Knowledge Sources:
- events.jsonl
- Learning reports (28 recommendations)
- Agent execution traces
- User corrections
- System metrics

Output:
- KNOWLEDGE_EXTRACTED:N - Extracted N new knowledge items
- KNOWLEDGE_UPDATED:N - Updated N existing items
- KNOWLEDGE_OK - No new knowledge
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
import hashlib

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class KnowledgeManager:
    """Knowledge Manager Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "knowledge"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_file = self.data_dir / "knowledge_base.json"
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"
        
        # Load existing knowledge base
        self.knowledge_base = self._load_knowledge_base()

    def run(self) -> Dict:
        """Run knowledge management"""
        print("=" * 80)
        print(f"  Knowledge Manager Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "knowledge_manager",
            "extracted": [],
            "updated": [],
            "merged": []
        }

        # 1. Extract knowledge from learning reports
        print("[1/6] Extracting knowledge from learning reports...")
        learning_knowledge = self._extract_from_learning_reports()
        report["extracted"].extend(learning_knowledge)
        print(f"  Extracted {len(learning_knowledge)} items from learning reports")

        # 2. Extract knowledge from events
        print("[2/6] Extracting knowledge from events...")
        event_knowledge = self._extract_from_events()
        report["extracted"].extend(event_knowledge)
        print(f"  Extracted {len(event_knowledge)} items from events")

        # 3. Deduplicate knowledge
        print("[3/6] Deduplicating knowledge...")
        deduplicated = self._deduplicate_knowledge(report["extracted"])
        report["deduplicated"] = deduplicated
        print(f"  Deduplicated to {len(deduplicated)} unique items")

        # 4. Merge with existing knowledge
        print("[4/6] Merging with existing knowledge...")
        merged = self._merge_knowledge(deduplicated)
        report["merged"] = merged
        print(f"  Merged {len(merged)} items")

        # 5. Build knowledge graph
        print("[5/6] Building knowledge graph...")
        graph = self._build_knowledge_graph()
        report["graph"] = graph
        print(f"  Built graph with {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

        # 6. Update MEMORY.md
        print("[6/6] Updating MEMORY.md...")
        memory_updated = self._update_memory()
        report["memory_updated"] = memory_updated
        print(f"  {'Updated' if memory_updated else 'No update needed'}")

        # Save knowledge base
        self._save_knowledge_base()
        self._save_report(report)

        print()
        print("=" * 80)
        extracted = len(report["extracted"])
        updated = len(report["merged"])
        print(f"  Completed! Extracted {extracted}, Updated {updated}")
        print("=" * 80)

        return report

    def _load_knowledge_base(self) -> Dict:
        """Load existing knowledge base"""
        if self.knowledge_base_file.exists():
            with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                kb = json.load(f)
                # Ensure items key exists
                if "items" not in kb:
                    kb["items"] = []
                return kb
        
        return {
            "version": "1.0",
            "last_updated": None,
            "items": []
        }

    def _extract_from_learning_reports(self) -> List[Dict]:
        """Extract knowledge from learning reports"""
        knowledge = []
        
        # Read learning reports
        learning_dir = self.data_dir.parent / "learning"
        if not learning_dir.exists():
            return knowledge
        
        # Get latest orchestrator report
        orchestrator_reports = sorted(learning_dir.glob("orchestrator_*.json"))
        if not orchestrator_reports:
            return knowledge
        
        with open(orchestrator_reports[-1], 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # Extract recommendations
        for recommendation in report.get("all_suggestions", []):
            knowledge.append({
                "type": "recommendation",
                "category": recommendation.get("type", "unknown"),
                "priority": recommendation.get("priority", "low"),
                "content": recommendation.get("description", ""),
                "action": recommendation.get("action", ""),
                "source": "learning_agent",
                "timestamp": report.get("timestamp"),
                "confidence": 0.8
            })
        
        return knowledge

    def _extract_from_events(self) -> List[Dict]:
        """Extract knowledge from events"""
        knowledge = []
        
        if not self.events_file.exists():
            return knowledge
        
        # Track error patterns
        error_patterns = defaultdict(int)
        cutoff = datetime.now() - timedelta(days=7)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    # Extract error patterns
                    if event.get("type") in ["error", "failure"]:
                        error_type = event.get("error_type", "unknown")
                        error_patterns[error_type] += 1
                
                except:
                    continue
        
        # Convert to knowledge items (only frequent errors)
        for error_type, count in error_patterns.items():
            if count >= 3:
                knowledge.append({
                    "type": "error_pattern",
                    "category": "reliability",
                    "priority": "high" if count >= 10 else "medium",
                    "content": f"Error '{error_type}' occurred {count} times in last 7 days",
                    "action": f"Investigate and fix '{error_type}' error",
                    "source": "events",
                    "timestamp": datetime.now().isoformat(),
                    "confidence": min(count / 10, 1.0)
                })
        
        return knowledge

    def _deduplicate_knowledge(self, knowledge: List[Dict]) -> List[Dict]:
        """Deduplicate knowledge items"""
        seen = set()
        deduplicated = []
        
        for item in knowledge:
            # Generate hash based on content
            content_hash = hashlib.md5(
                f"{item['category']}:{item['content']}".encode()
            ).hexdigest()
            
            if content_hash not in seen:
                seen.add(content_hash)
                item["hash"] = content_hash
                deduplicated.append(item)
        
        return deduplicated

    def _merge_knowledge(self, new_knowledge: List[Dict]) -> List[Dict]:
        """Merge new knowledge with existing"""
        merged = []
        
        existing_hashes = {item.get("hash") for item in self.knowledge_base["items"]}
        
        for item in new_knowledge:
            if item["hash"] not in existing_hashes:
                # New knowledge
                self.knowledge_base["items"].append(item)
                merged.append(item)
            else:
                # Update existing (increase confidence)
                for existing in self.knowledge_base["items"]:
                    if existing.get("hash") == item["hash"]:
                        existing["confidence"] = min(existing.get("confidence", 0.5) + 0.1, 1.0)
                        existing["last_seen"] = item["timestamp"]
                        merged.append(existing)
                        break
        
        return merged

    def _build_knowledge_graph(self) -> Dict:
        """Build knowledge graph"""
        nodes = []
        edges = []
        
        # Create nodes from knowledge items
        for i, item in enumerate(self.knowledge_base["items"]):
            nodes.append({
                "id": i,
                "type": item["type"],
                "category": item["category"],
                "content": item["content"][:50] + "..."
            })
        
        # Create edges based on category relationships
        category_groups = defaultdict(list)
        for i, item in enumerate(self.knowledge_base["items"]):
            category_groups[item["category"]].append(i)
        
        # Connect items in same category
        for category, node_ids in category_groups.items():
            for i in range(len(node_ids) - 1):
                edges.append({
                    "from": node_ids[i],
                    "to": node_ids[i + 1],
                    "type": "same_category"
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }

    def _update_memory(self) -> bool:
        """Update MEMORY.md with important knowledge"""
        memory_file = AIOS_ROOT / "MEMORY.md"
        if not memory_file.exists():
            return False
        
        # Get high-priority knowledge
        high_priority = [
            item for item in self.knowledge_base["items"]
            if item["priority"] == "high" and item.get("confidence", 0) >= 0.7
        ]
        
        if not high_priority:
            return False
        
        # Read current MEMORY.md
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory_content = f.read()
        
        # Append new knowledge (if not already there)
        new_entries = []
        for item in high_priority[:5]:  # Top 5
            if item["content"] not in memory_content:
                new_entries.append(f"- {item['content']} ({item['timestamp'][:10]})")
        
        if new_entries:
            # Append to MEMORY.md
            with open(memory_file, 'a', encoding='utf-8') as f:
                f.write("\n\n## 自动提取的知识 (Knowledge Manager)\n")
                f.write("\n".join(new_entries))
            return True
        
        return False

    def _save_knowledge_base(self):
        """Save knowledge base"""
        self.knowledge_base["last_updated"] = datetime.now().isoformat()
        
        with open(self.knowledge_base_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)

    def _save_report(self, report: Dict):
        """Save report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"knowledge_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """Main function"""
    manager = KnowledgeManager()
    report = manager.run()
    
    extracted = len(report.get("extracted", []))
    updated = len(report.get("merged", []))
    
    if extracted > 0:
        print(f"\nKNOWLEDGE_EXTRACTED:{extracted}")
    if updated > 0:
        print(f"KNOWLEDGE_UPDATED:{updated}")
    if extracted == 0 and updated == 0:
        print("\nKNOWLEDGE_OK")


if __name__ == "__main__":
    main()
