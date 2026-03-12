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
    
    # 4. 输出结果（简化版，只显示摘要）
    print("\n" + "=" * 60)
    print("读取结果摘要")
    print("=" * 60)
    print(f"应用角色: {ui_tree.get('role')}")
    print(f"应用标题: {ui_tree.get('title')}")
    print(f"子元素数量: {len(ui_tree.get('children', []))}")
    
    # 5. 提取可交互元素
    print("\n" + "=" * 60)
    print("可交互元素列表")
    print("=" * 60)
    
    interactive_elements = extract_interactive_elements(ui_tree)
    
    for i, elem in enumerate(interactive_elements, 1):
        print(f"\n{i}. {elem['role']}")
        if elem.get('title'):
            print(f"   标题: {elem['title']}")
        if elem.get('description'):
            print(f"   描述: {elem['description']}")
        if elem.get('x') and elem.get('y'):
            print(f"   位置: ({elem['x']}, {elem['y']})")
        if elem.get('width') and elem.get('height'):
            print(f"   大小: {elem['width']}x{elem['height']}")
    
    print(f"\n共找到 {len(interactive_elements)} 个可交互元素")
    
    # 6. 保存完整结果到 JSON
    import json
    output_file = "finder_ui_tree.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(ui_tree, f, indent=2, ensure_ascii=False)
    
    print(f"\n完整 UI 树已保存到: {output_file}")


if __name__ == "__main__":
    main()
