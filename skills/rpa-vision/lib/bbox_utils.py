"""
Bounding Box Utilities - Unified xyxy Contract

从这一版开始，整个 Skill 里只允许一种 bbox：
(x1, y1, x2, y2)

统一规则：
- w = x2 - x1
- h = y2 - y1
- cx = (x1 + x2) // 2
- cy = (y1 + y2) // 2
"""


def bbox_width(bbox):
    """计算 bbox 宽度"""
    x1, y1, x2, y2 = bbox
    return x2 - x1


def bbox_height(bbox):
    """计算 bbox 高度"""
    x1, y1, x2, y2 = bbox
    return y2 - y1


def bbox_center(bbox):
    """计算 bbox 中心点"""
    x1, y1, x2, y2 = bbox
    return (x1 + x2) // 2, (y1 + y2) // 2


def validate_bbox_xyxy(bbox):
    """校验 bbox 是否符合 xyxy 格式"""
    if len(bbox) != 4:
        raise ValueError(f"Invalid bbox length: {len(bbox)}, expected 4")
    
    x1, y1, x2, y2 = bbox
    
    if x2 <= x1:
        raise ValueError(f"Invalid xyxy bbox: x2 ({x2}) <= x1 ({x1})")
    
    if y2 <= y1:
        raise ValueError(f"Invalid xyxy bbox: y2 ({y2}) <= y1 ({y1})")
    
    return True
