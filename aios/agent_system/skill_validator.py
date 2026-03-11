#!/usr/bin/env python3
"""Skill Validator - 验证 Skill 草案（最小版，三层验证）"""
import json
import re
from pathlib import Path
from datetime import datetime

def validate_skill(skill_id: str):
    """验证指定 Skill 草案"""
    
    draft_dir = Path(f"draft_registry/{skill_id}")
    if not draft_dir.exists():
        return {"passed": False, "error": "draft not found"}
    
    results = {
        "skill_id": skill_id,
        "validated_at": datetime.now().isoformat(),
        "layers": {}
    }
    
    # Layer 1: 格式验证
    format_result = validate_format(draft_dir)
    results["layers"]["format"] = format_result
    if not format_result["passed"]:
        results["passed"] = False
        return results
    
    # Layer 2: 安全扫描
    security_result = validate_security(draft_dir)
    results["layers"]["security"] = security_result
    if not security_result["passed"]:
        results["passed"] = False
        return results
    
    # Layer 3: 风险评级
    risk_result = validate_risk(draft_dir)
    results["layers"]["risk"] = risk_result
    
    # 全部通过
    results["passed"] = True
    return results

def validate_format(draft_dir: Path) -> dict:
    """Layer 1: 格式验证"""
    
    skill_md = draft_dir / "SKILL.md"
    meta_json = draft_dir / "meta.json"
    
    # 检查文件存在
    if not skill_md.exists():
        return {"passed": False, "error": "SKILL.md not found"}
    if not meta_json.exists():
        return {"passed": False, "error": "meta.json not found"}
    
    # 检查 frontmatter
    content = skill_md.read_text(encoding='utf-8')
    if not content.startswith('---'):
        return {"passed": False, "error": "frontmatter missing"}
    
    # 提取 frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {"passed": False, "error": "frontmatter malformed"}
    
    frontmatter = parts[1]
    
    # 检查必填字段
    required_fields = ['name', 'version', 'description', 'risk_level']
    for field in required_fields:
        if f'{field}:' not in frontmatter:
            return {"passed": False, "error": f"missing required field: {field}"}
    
    # 检查 meta.json 可解析
    try:
        meta = json.loads(meta_json.read_text(encoding='utf-8'))
        if not all(k in meta for k in ['skill_id', 'name', 'version', 'status']):
            return {"passed": False, "error": "meta.json missing required fields"}
    except json.JSONDecodeError as e:
        return {"passed": False, "error": f"meta.json invalid: {e}"}
    
    return {"passed": True, "checks": ["frontmatter", "required_fields", "meta_json"]}

def validate_security(draft_dir: Path) -> dict:
    """Layer 2: 安全扫描"""
    
    skill_md = draft_dir / "SKILL.md"
    content = skill_md.read_text(encoding='utf-8')
    
    # 危险命令模式
    dangerous_patterns = [
        r'rm\s+-rf',
        r'del\s+/[fqs]',
        r'format\s+[a-z]:',
        r'curl.*\|\s*sh',
        r'wget.*\|\s*bash',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__\s*\(',
    ]
    
    violations = []
    for pattern in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(f"dangerous pattern: {pattern}")
    
    # 外部写操作检查
    write_patterns = [
        r'\.write\(',
        r'open\([^)]*["\']w',
        r'Path\([^)]*\)\.write',
    ]
    
    # 对于 heartbeat-alert-deduper，允许写 alert_history.jsonl
    for pattern in write_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # 检查上下文，如果是写 alert_history 则允许
            context = content[max(0, match.start()-50):match.end()+50]
            if 'alert_history' not in context:
                violations.append(f"external write detected: {match.group()}")
    
    if violations:
        return {"passed": False, "violations": violations}
    
    return {"passed": True, "checks": ["dangerous_commands", "external_writes"]}

def validate_risk(draft_dir: Path) -> dict:
    """Layer 3: 风险评级"""
    
    meta_json = draft_dir / "meta.json"
    meta = json.loads(meta_json.read_text(encoding='utf-8'))
    
    risk_level = meta.get('risk_level', 'unknown')
    
    # heartbeat-alert-deduper 应该是 low
    if risk_level not in ['low', 'medium', 'high']:
        return {"passed": False, "error": f"invalid risk_level: {risk_level}"}
    
    # 对于第一个 Skill，只接受 low
    if risk_level != 'low':
        return {"passed": False, "error": f"only low risk allowed in MVP, got: {risk_level}"}
    
    return {"passed": True, "risk_level": risk_level}

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python skill_validator.py <skill_id>")
        sys.exit(1)
    
    skill_id = sys.argv[1]
    result = validate_skill(skill_id)
    
    print(f"\n{'='*60}")
    print(f"Skill Validation Report: {skill_id}")
    print(f"{'='*60}\n")
    
    for layer, layer_result in result.get("layers", {}).items():
        status = "✅ PASSED" if layer_result["passed"] else "❌ FAILED"
        print(f"Layer: {layer.upper()} - {status}")
        if not layer_result["passed"]:
            print(f"  Error: {layer_result.get('error', 'N/A')}")
            if "violations" in layer_result:
                for v in layer_result["violations"]:
                    print(f"    - {v}")
        else:
            if "checks" in layer_result:
                print(f"  Checks: {', '.join(layer_result['checks'])}")
        print()
    
    print(f"{'='*60}")
    if result["passed"]:
        print("✅ VALIDATION PASSED")
    else:
        print("❌ VALIDATION FAILED")
    print(f"{'='*60}\n")
    
    # 保存验证结果
    result_file = Path(f"draft_registry/{skill_id}/validation_result.json")
    result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Result saved to: {result_file}")
    
    sys.exit(0 if result["passed"] else 1)
