# RPA Lite for 小正 - Finder 测试版

**目标：** 用 macOS Accessibility API 读取 Finder 窗口的 UI 元素

**技术栈：** Python + pyobjc（macOS 原生）

---

## 安装（Mac 上执行）

```bash
pip install pyobjc-framework-Cocoa pyobjc-framework-ApplicationServices
```

---

## 最小可运行代码

保存为 `finder_reader.py`：

```python
#!/usr/bin/env python3
"""
Finder UI 元素读取器 - 最小可运行版
使用 macOS Accessibility API 读取 Finder 窗口的按钮、文本、输入框
"""

from AppKit import NSWorkspace
from ApplicationServices import (
    AXUIElementCreateApplication,
    AXUIElementCopyAttributeValue,
    AXUIElementCopyAttributeNames
)
import sys


def get_finder_pid():
    """获取 Finder 进程 ID"""
    workspace = NSWorkspace.sharedWorkspace()
    apps = workspace.runningApplications()
    
    for app in apps:
        if app.localizedName() == "Finder":
            return app.processIdentifier()
    
    return None


def read_ui_element(element, depth=0, max_depth=3):
    """
    递归读取 UI 元素
    
    Args:
        element: AXUIElement 对象
        depth: 当前深度
        max_depth: 最大递归深度
    
    Returns:
        dict: 元素信息
    """
    if depth > max_depth:
        return None
    
    info = {"depth": depth}
    
    # 读取基础属性
    try:
        # 角色（按钮、文本、输入框等）
        _, role = AXUIElementCopyAttributeValue(element, "AXRole", None)
        info["role"] = str(role) if role else "unknown"
        
        # 标题
        _, title = AXUIElementCopyAttributeValue(element, "AXTitle", None)
        info["title"] = str(title) if title else ""
        
        # 描述
        _, desc = AXUIElementCopyAttributeValue(element, "AXDescription", None)
        info["description"] = str(desc) if desc else ""
        
        # 位置和大小
        _, position = AXUIElementCopyAttributeValue(element, "AXPosition", None)
        _, size = AXUIElementCopyAttributeValue(element, "AXSize", None)
        
        if position:
            info["x"] = int(position.x)
            info["y"] = int(position.y)
        
        if size:
            info["width"] = int(size.width)
            info["height"] = int(size.height)
        
        # 是否可交互
        _, enabled = AXUIElementCopyAttributeValue(element, "AXEnabled", None)
        info["enabled"] = bool(enabled) if enabled is not None else True
        
    except Exception as e:
        info["error"] = str(e)
    
    # 读取子元素
    try:
        _, children = AXUIElementCopyAttributeValue(element, "AXChildren", None)
        if children and depth < max_depth:
            info["children"] = []
            for child in children[:10]:  # 限制最多 10 个子元素
                child_info = read_ui_element(child, depth + 1, max_depth)
                if child_info:
                    info["children"].append(child_info)
    except:
        pass
    
    return info


def main():
    """主函数：读取 Finder 窗口的 UI 元素"""
    print("=" * 60)
    print("Finder UI 元素读取器")
    print("=" * 60)
    
    # 1. 获取 Finder 进程 ID
    print("\n[1/3] 查找 Finder 进程...")
    pid = get_finder_pid()
    
    if not pid:
        print("❌ 未找到 Finder 进程")
        sys.exit(1)
    
    print(f"✅ Finder PID: {pid}")
    
    # 2. 创建 Accessibility 对象
    print("\n[2/3] 连接 Accessibility API...")
    app_ref = AXUIElementCreateApplication(pid)
    
    if not app_ref:
        print("❌ 无法创建 Accessibility 对象")
        sys.exit(1)
    
    print("✅ 已连接")
    
    # 3. 读取 UI 元素树
    print("\n[3/3] 读取 UI 元素...")
    ui_tree = read_ui_element(app_ref, depth=0, max_depth=2)
    
    if not ui_tree:
        print("❌ 读取失败")
        sys.exit(1)
    
    # 4. 输出结果
    print("\n" + "=" * 60)
    print("读取结果")
    print("=" * 60)
    
    import json
    print(json.dumps(ui_tree, indent=2, ensure_ascii=False))
    
    # 5. 提取可交互元素
    print("\n" + "=" * 60)
    print("可交互元素列表")
    print("=" * 60)
    
    interactive_elements = extract_interactive_elements(ui_tree)
    
    for i, elem in enumerate(interactive_elements, 1):
        print(f"\n{i}. {elem['role']}")
        if elem.get('title'):
            print(f"   标题: {elem['title']}")
        if elem.get('x') and elem.get('y'):
            print(f"   位置: ({elem['x']}, {elem['y']})")
        if elem.get('width') and elem.get('height'):
            print(f"   大小: {elem['width']}x{elem['height']}")
    
    print(f"\n共找到 {len(interactive_elements)} 个可交互元素")


def extract_interactive_elements(ui_tree, elements=None):
    """提取所有可交互元素（按钮、输入框等）"""
    if elements is None:
        elements = []
    
    # 可交互的角色类型
    interactive_roles = [
        "AXButton",
        "AXTextField",
        "AXTextArea",
        "AXCheckBox",
        "AXRadioButton",
        "AXPopUpButton",
        "AXComboBox",
        "AXSlider"
    ]
    
    if ui_tree.get("role") in interactive_roles and ui_tree.get("enabled"):
        elements.append({
            "role": ui_tree["role"],
            "title": ui_tree.get("title", ""),
            "description": ui_tree.get("description", ""),
            "x": ui_tree.get("x"),
            "y": ui_tree.get("y"),
            "width": ui_tree.get("width"),
            "height": ui_tree.get("height")
        })
    
    # 递归处理子元素
    for child in ui_tree.get("children", []):
        extract_interactive_elements(child, elements)
    
    return elements


if __name__ == "__main__":
    main()
```

---

## 使用方法

### 1. 打开 Finder

确保 Finder 窗口在前台。

### 2. 运行脚本

```bash
python3 finder_reader.py
```

### 3. 预期输出

```
============================================================
Finder UI 元素读取器
============================================================

[1/3] 查找 Finder 进程...
✅ Finder PID: 1234

[2/3] 连接 Accessibility API...
✅ 已连接

[3/3] 读取 UI 元素...

============================================================
读取结果
============================================================
{
  "depth": 0,
  "role": "AXApplication",
  "title": "Finder",
  "children": [...]
}

============================================================
可交互元素列表
============================================================

1. AXButton
   标题: 返回
   位置: (20, 100)
   大小: 60x30

2. AXButton
   标题: 前进
   位置: (90, 100)
   大小: 60x30

3. AXTextField
   标题: 搜索
   位置: (800, 100)
   大小: 200x30

共找到 15 个可交互元素
```

---

## 权限设置（重要）

macOS 需要授权 Accessibility 权限：

1. 打开 **系统偏好设置** → **安全性与隐私** → **隐私** → **辅助功能**
2. 添加 **终端** 或 **Python** 到允许列表
3. 重启终端

---

## 下一步

如果 Finder 读取成功，可以扩展到：
- 读取其他应用（Chrome、VS Code）
- 实现点击操作（`AXPress` action）
- 实现输入操作（`AXValue` 设置）

---

**版本：** v0.1 - Finder 测试版  
**创建时间：** 2026-03-13  
**维护者：** 小九 → 小正
