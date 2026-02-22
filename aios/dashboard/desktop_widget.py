"""
AIOS Desktop Widget - 桌面悬浮小部件
使用 tkinter 创建一个置顶透明窗口显示 AIOS 数据
"""
import tkinter as tk
from tkinter import font
import json
from pathlib import Path
import threading
import time

DATA_FILE = Path(r"C:\Users\A\.openclaw\workspace\aios\dashboard\dashboard_data.json")

class AIOSWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AIOS")
        self.root.geometry("320x280+1560+20")  # 右上角位置
        self.root.attributes('-topmost', True)  # 置顶
        self.root.attributes('-alpha', 0.9)  # 半透明
        self.root.overrideredirect(True)  # 无边框
        
        # 背景
        self.root.configure(bg='#14141e')
        
        # 创建主框架
        self.frame = tk.Frame(self.root, bg='#14141e', padx=20, pady=20)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # 字体
        self.title_font = font.Font(family='Segoe UI', size=16, weight='bold')
        self.label_font = font.Font(family='Segoe UI', size=9)
        self.value_font = font.Font(family='Segoe UI', size=24, weight='bold')
        self.mini_font = font.Font(family='Segoe UI', size=18, weight='bold')
        self.badge_font = font.Font(family='Segoe UI', size=11, weight='bold')
        
        # 标题
        title_frame = tk.Frame(self.frame, bg='#14141e')
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(title_frame, text="AIOS", font=self.title_font, 
                fg='#00d4ff', bg='#14141e').pack(side=tk.LEFT)
        
        tk.Label(title_frame, text="●", font=self.title_font, 
                fg='#00ff88', bg='#14141e').pack(side=tk.RIGHT)
        
        # 分隔线
        tk.Frame(self.frame, height=1, bg='#333').pack(fill=tk.X, pady=(0, 15))
        
        # Evolution Score
        tk.Label(self.frame, text="EVOLUTION SCORE", font=self.label_font,
                fg='#888', bg='#14141e').pack(anchor=tk.W)
        
        score_frame = tk.Frame(self.frame, bg='#14141e')
        score_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.score_label = tk.Label(score_frame, text="0.316", font=self.value_font,
                                    fg='white', bg='#14141e')
        self.score_label.pack(side=tk.LEFT)
        
        self.grade_label = tk.Label(score_frame, text="DEGRADED", font=self.badge_font,
                                   fg='#ffc800', bg='#332200', padx=10, pady=2)
        self.grade_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 进度条
        self.progress_canvas = tk.Canvas(self.frame, height=6, bg='#14141e', 
                                        highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, pady=(0, 20))
        self.progress_bg = self.progress_canvas.create_rectangle(0, 0, 280, 6, 
                                                                 fill='#333', outline='')
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 88, 6, 
                                                                  fill='#00d4ff', outline='')
        
        # 网格指标
        grid_frame = tk.Frame(self.frame, bg='#14141e')
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Reactor
        reactor_box = tk.Frame(grid_frame, bg='#222', width=130, height=60)
        reactor_box.grid(row=0, column=0, padx=(0, 10), pady=(0, 10), sticky='nsew')
        tk.Label(reactor_box, text="Reactor", font=self.label_font,
                fg='#888', bg='#222').pack(anchor=tk.W, padx=12, pady=(10, 0))
        self.reactor_label = tk.Label(reactor_box, text="0.19", font=self.mini_font,
                                     fg='white', bg='#222')
        self.reactor_label.pack(anchor=tk.W, padx=12)
        
        # Base
        base_box = tk.Frame(grid_frame, bg='#222', width=130, height=60)
        base_box.grid(row=0, column=1, pady=(0, 10), sticky='nsew')
        tk.Label(base_box, text="Base", font=self.label_font,
                fg='#888', bg='#222').pack(anchor=tk.W, padx=12, pady=(10, 0))
        self.base_label = tk.Label(base_box, text="0.40", font=self.mini_font,
                                  fg='white', bg='#222')
        self.base_label.pack(anchor=tk.W, padx=12)
        
        # Alerts
        alerts_box = tk.Frame(grid_frame, bg='#222', width=130, height=60)
        alerts_box.grid(row=1, column=0, padx=(0, 10), sticky='nsew')
        tk.Label(alerts_box, text="Alerts", font=self.label_font,
                fg='#888', bg='#222').pack(anchor=tk.W, padx=12, pady=(10, 0))
        self.alerts_label = tk.Label(alerts_box, text="1", font=self.mini_font,
                                    fg='white', bg='#222')
        self.alerts_label.pack(anchor=tk.W, padx=12)
        
        # Actions
        actions_box = tk.Frame(grid_frame, bg='#222', width=130, height=60)
        actions_box.grid(row=1, column=1, sticky='nsew')
        tk.Label(actions_box, text="Actions", font=self.label_font,
                fg='#888', bg='#222').pack(anchor=tk.W, padx=12, pady=(10, 0))
        self.actions_label = tk.Label(actions_box, text="0", font=self.mini_font,
                                     fg='white', bg='#222')
        self.actions_label.pack(anchor=tk.W, padx=12)
        
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        
        # 允许拖动
        self.frame.bind('<Button-1>', self.start_move)
        self.frame.bind('<B1-Motion>', self.do_move)
        
        # 启动更新线程
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
        # 首次更新
        self.update_data()
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    
    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def update_data(self):
        try:
            if DATA_FILE.exists():
                data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
                
                # Evolution score
                score = data.get('evolution_v2', {}).get('v2_score', 0)
                grade = data.get('evolution_v2', {}).get('grade', 'unknown')
                reactor = data.get('evolution_v2', {}).get('reactor', 0)
                base = data.get('evolution_v2', {}).get('base', 0)
                
                # Alerts & Actions
                alerts = data.get('overview', {}).get('severity', {}).get('CRIT', 0)
                actions = data.get('sensors', {}).get('pending_actions', 0) or 0
                
                # 更新UI
                self.score_label.config(text=f"{score:.3f}")
                self.grade_label.config(text=grade.upper())
                
                # 根据 grade 改变颜色
                if grade == 'healthy':
                    self.grade_label.config(fg='#00ff88', bg='#002200')
                elif grade == 'degraded':
                    self.grade_label.config(fg='#ffc800', bg='#332200')
                else:
                    self.grade_label.config(fg='#ff4444', bg='#330000')
                
                # 更新进度条
                bar_width = int(280 * score)
                self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 6)
                
                self.reactor_label.config(text=f"{reactor:.2f}")
                self.base_label.config(text=f"{base:.2f}")
                self.alerts_label.config(text=str(alerts))
                self.actions_label.config(text=str(actions))
        except Exception as e:
            print(f"Update error: {e}")
    
    def update_loop(self):
        while self.running:
            self.update_data()
            time.sleep(30)  # 每30秒更新
    
    def run(self):
        self.root.mainloop()
        self.running = False

if __name__ == "__main__":
    widget = AIOSWidget()
    widget.run()
