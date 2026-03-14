"""
视觉管理桌面 v0.1 - 最小原型
基于 UI-TARS + UIVisionAgent
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt
from PIL import Image
import pyautogui

# 添加 agent_system 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "agent_system"))
from ui_vision_agent import UIVisionAgent, ActionExecutor


class VisionDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.agent = UIVisionAgent()
        self.executor = ActionExecutor()
        self.current_screenshot = None
        self.current_result = None
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("视觉管理桌面 v0.1")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主容器
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 顶部：截图区域
        screenshot_layout = QHBoxLayout()
        
        self.screenshot_label = QLabel("截图区域")
        self.screenshot_label.setMinimumSize(800, 450)
        self.screenshot_label.setStyleSheet("border: 2px solid #ccc; background: #f5f5f5;")
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        screenshot_layout.addWidget(self.screenshot_label)
        
        # 右侧按钮
        btn_layout = QVBoxLayout()
        
        self.btn_capture = QPushButton("截取当前屏幕")
        self.btn_capture.clicked.connect(self.capture_screen)
        btn_layout.addWidget(self.btn_capture)
        
        self.btn_load = QPushButton("加载图片文件")
        self.btn_load.clicked.connect(self.load_image)
        btn_layout.addWidget(self.btn_load)
        
        btn_layout.addStretch()
        screenshot_layout.addLayout(btn_layout)
        
        layout.addLayout(screenshot_layout)
        
        # 中部：任务输入
        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("任务描述:"))
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("例如：点击登录按钮")
        task_layout.addWidget(self.task_input)
        
        self.btn_analyze = QPushButton("分析")
        self.btn_analyze.clicked.connect(self.analyze)
        self.btn_analyze.setEnabled(False)
        task_layout.addWidget(self.btn_analyze)
        
        layout.addLayout(task_layout)
        
        # 底部：结果显示
        result_label = QLabel("分析结果:")
        layout.addWidget(result_label)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        layout.addWidget(self.result_text)
        
        # 执行按钮
        exec_layout = QHBoxLayout()
        exec_layout.addStretch()
        
        self.btn_execute = QPushButton("执行操作")
        self.btn_execute.clicked.connect(self.execute_action)
        self.btn_execute.setEnabled(False)
        self.btn_execute.setStyleSheet("background: #4CAF50; color: white; padding: 8px 16px;")
        exec_layout.addWidget(self.btn_execute)
        
        layout.addLayout(exec_layout)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def capture_screen(self):
        """截取当前屏幕"""
        self.statusBar().showMessage("正在截图...")
        
        # 最小化窗口
        self.showMinimized()
        QApplication.processEvents()
        
        # 等待窗口最小化完成
        import time
        time.sleep(0.5)
        
        # 截图
        screenshot = pyautogui.screenshot()
        self.current_screenshot = screenshot
        
        # 恢复窗口
        self.showNormal()
        
        # 显示截图
        self.display_screenshot(screenshot)
        
        self.btn_analyze.setEnabled(True)
        self.statusBar().showMessage("截图完成")
    
    def load_image(self):
        """加载图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            screenshot = Image.open(file_path)
            self.current_screenshot = screenshot
            self.display_screenshot(screenshot)
            self.btn_analyze.setEnabled(True)
            self.statusBar().showMessage(f"已加载: {Path(file_path).name}")
    
    def display_screenshot(self, screenshot):
        """显示截图"""
        # 转换为 QPixmap
        screenshot.save("temp_screenshot.png")
        pixmap = QPixmap("temp_screenshot.png")
        
        # 缩放到适合显示
        scaled = pixmap.scaled(
            self.screenshot_label.width() - 10,
            self.screenshot_label.height() - 10,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.screenshot_label.setPixmap(scaled)
    
    def analyze(self):
        """分析截图"""
        if not self.current_screenshot:
            self.statusBar().showMessage("请先截图或加载图片")
            return
        
        task_desc = self.task_input.text().strip()
        if not task_desc:
            self.statusBar().showMessage("请输入任务描述")
            return
        
        self.statusBar().showMessage("正在分析...")
        self.result_text.clear()
        
        # 调用 UIVisionAgent
        result = self.agent.perceive(task_desc, self.current_screenshot)
        self.current_result = result
        
        # 显示结果
        output = f"状态: {result.status}\n"
        output += f"推理: {result.thought}\n"
        output += f"操作: {result.action.type} {result.action.params}\n"
        output += f"置信度: {result.confidence:.2f}\n"
        
        self.result_text.setText(output)
        
        # 根据置信度决定是否允许执行
        if result.status == "ok" and result.confidence >= 0.7:
            self.btn_execute.setEnabled(True)
            self.statusBar().showMessage("分析完成 - 可执行")
        else:
            self.btn_execute.setEnabled(False)
            self.statusBar().showMessage("分析完成 - 置信度不足，不建议执行")
    
    def execute_action(self):
        """执行操作"""
        if not self.current_result:
            return
        
        self.statusBar().showMessage("正在执行...")
        
        # 执行
        exec_result = self.executor.execute(self.current_result.action)
        
        if exec_result["success"]:
            self.statusBar().showMessage("✅ 执行成功")
            self.result_text.append("\n执行结果: 成功")
        else:
            self.statusBar().showMessage(f"❌ 执行失败: {exec_result['error']}")
            self.result_text.append(f"\n执行结果: 失败 - {exec_result['error']}")
        
        self.btn_execute.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    window = VisionDesktop()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
