# -*- coding: utf-8 -*-
"""
数独求解可视化工具 - Premium Edition
高级蓝紫色主题 + 生成动画
"""
import os
import random
import sys
import threading
import time
import tkinter as tk
from copy import deepcopy
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 导入路径配置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入算法和生成器
try:
    from src.algorithms.solver_basic_v1 import SudokuSolver as BasicSolver
    from src.algorithms.solver_mrv_lcv import MRVLCVSolver
    from src.algorithms.solver_ac3_mrv_lcv import AC3_MRV_LCV_Solver
    from src.generator.sudoku_generator import SudokuGenerator
    print("✓ 算法和生成器加载成功")
except ImportError as e:
    print(f"✗ 警告：导入失败 - {e}")
    BasicSolver = MRVLCVSolver = AC3_MRV_LCV_Solver = SudokuGenerator = None

# ==================== 高级配色方案 ====================
THEME = {
    # 主色调 - 蓝紫渐变
    "primary": "#6366f1",      # 靛蓝色
    "secondary": "#8b5cf6",    # 紫色
    "accent": "#ec4899",       # 粉色
    
    # 背景色
    "bg_dark": "#1e1b4b",      # 深蓝紫色背景
    "bg_medium": "#312e81",    # 中等蓝紫色
    "bg_light": "#4c1d95",     # 浅紫色
    "bg_card": "#2d2a5f",      # 卡片背景
    
    # 网格颜色
    "grid_bg1": "#3730a3",     # 网格背景1
    "grid_bg2": "#4338ca",     # 网格背景2
    "grid_line": "#6366f1",    # 网格线
    
    # 文字颜色
    "text_primary": "#f8fafc",   # 主文字（白色）
    "text_secondary": "#cbd5e1",  # 次要文字（浅灰）
    "text_accent": "#fbbf24",     # 强调文字（金色）
    
    # 状态颜色
    "success": "#10b981",      # 成功（绿色）
    "error": "#ef4444",        # 错误（红色）
    "warning": "#f59e0b",      # 警告（橙色）
    "info": "#3b82f6",         # 信息（蓝色）
    
    # 动画颜色
    "anim_generate": "#a78bfa",  # 生成动画（浅紫）
    "anim_try": "#60a5fa",       # 尝试填入（浅蓝）
    "anim_backtrack": "#f87171",  # 回溯（浅红）
    "anim_success": "#34d399",    # 成功（浅绿）
}

# ==================== 主窗口初始化 ====================
root = tk.Tk()
root.title("数独求解器 Premium - 蓝紫主题")
root.geometry("1400x900")
root.configure(bg=THEME["bg_dark"])

# 全局变量
sudoku_entries = [[None for _ in range(9)] for _ in range(9)]
original_puzzle = [[0 for _ in range(9)] for _ in range(9)]
is_animating = False
animation_queue = []
generation_step = 0

# ==================== 自定义样式 ====================
style = ttk.Style(root)
style.theme_use('clam')

# 按钮样式
style.configure("Premium.TButton",
    background=THEME["primary"],
    foreground=THEME["text_primary"],
    borderwidth=0,
    focuscolor='none',
    padding=(20, 12),
    font=("Segoe UI", 11, "bold"))
style.map("Premium.TButton",
    background=[('active', THEME["secondary"]), ('pressed', THEME["accent"])])

# 标签样式
style.configure("Premium.TLabel",
    background=THEME["bg_dark"],
    foreground=THEME["text_primary"],
    font=("Segoe UI", 10))

# 下拉框样式
style.configure("Premium.TCombobox",
    fieldbackground=THEME["bg_medium"],
    background=THEME["primary"],
    foreground=THEME["text_primary"],
    arrowcolor=THEME["text_primary"],
    borderwidth=0)

# LabelFrame样式
style.configure("Premium.TLabelframe",
    background=THEME["bg_card"],
    foreground=THEME["text_accent"],
    borderwidth=2,
    relief="flat")
style.configure("Premium.TLabelframe.Label",
    background=THEME["bg_card"],
    foreground=THEME["text_accent"],
    font=("Segoe UI", 11, "bold"))

# ==================== 顶部控制栏 ====================
top_frame = tk.Frame(root, bg=THEME["bg_dark"], pady=20)
top_frame.pack(fill=tk.X, padx=20)

# 标题
title_label = tk.Label(top_frame, 
    text="🎮 数独求解器 Premium Edition",
    font=("Segoe UI", 24, "bold"),
    bg=THEME["bg_dark"],
    fg=THEME["text_accent"])
title_label.pack(pady=(0, 15))

# 控制面板
control_panel = tk.Frame(top_frame, bg=THEME["bg_card"], relief="flat", bd=2)
control_panel.pack(fill=tk.X, pady=10, ipady=15)

# 第一行：难度和算法选择
row1 = tk.Frame(control_panel, bg=THEME["bg_card"])
row1.pack(fill=tk.X, padx=20, pady=(10, 5))

tk.Label(row1, text="难度：", bg=THEME["bg_card"], 
    fg=THEME["text_primary"], font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
difficulty_var = tk.StringVar(value="中等")
difficulty_menu = ttk.Combobox(row1, textvariable=difficulty_var,
    values=["简单", "中等", "困难"], state="readonly", width=12, style="Premium.TCombobox")
difficulty_menu.pack(side=tk.LEFT, padx=10)

tk.Label(row1, text="算法：", bg=THEME["bg_card"],
    fg=THEME["text_primary"], font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(30, 5))
algorithm_var = tk.StringVar(value="MRV+LCV算法")
alg_menu = ttk.Combobox(row1, textvariable=algorithm_var,
    values=["基础DFS算法", "MRV+LCV算法", "AC3+MRV+LCV算法"],
    state="readonly", width=20, style="Premium.TCombobox")
alg_menu.pack(side=tk.LEFT, padx=10)

# 动画开关
animate_var = tk.BooleanVar(value=True)
animate_check = tk.Checkbutton(row1, text="启用动画",
    variable=animate_var, bg=THEME["bg_card"], fg=THEME["text_primary"],
    selectcolor=THEME["bg_medium"], font=("Segoe UI", 10),
    activebackground=THEME["bg_card"], activeforeground=THEME["text_accent"])
animate_check.pack(side=tk.LEFT, padx=30)

# 速度选择
tk.Label(row1, text="速度：", bg=THEME["bg_card"],
    fg=THEME["text_primary"], font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
speed_var = tk.StringVar(value="中")
speed_menu = ttk.Combobox(row1, textvariable=speed_var,
    values=["慢", "中", "快"], state="readonly", width=8, style="Premium.TCombobox")
speed_menu.pack(side=tk.LEFT, padx=10)

# 第二行：功能按钮
row2 = tk.Frame(control_panel, bg=THEME["bg_card"])
row2.pack(fill=tk.X, padx=20, pady=(5, 10))

def create_button(parent, text, command, width=15):
    btn = tk.Button(parent, text=text, command=command,
        bg=THEME["primary"], fg=THEME["text_primary"],
        font=("Segoe UI", 11, "bold"), relief="flat",
        cursor="hand2", width=width, height=1,
        activebackground=THEME["secondary"],
        activeforeground=THEME["text_primary"])
    return btn

clear_btn = create_button(row2, "🗑️ 清空", lambda: clear_sudoku(), 12)
clear_btn.pack(side=tk.LEFT, padx=8)

fill_btn = create_button(row2, "✨ 生成数独", lambda: fill_with_difficulty(), 15)
fill_btn.pack(side=tk.LEFT, padx=8)

solve_btn = create_button(row2, "🚀 开始求解", lambda: solve_sudoku(), 15)
solve_btn.pack(side=tk.LEFT, padx=8)

compare_btn = create_button(row2, "📊 对比算法", lambda: compare_algorithms(), 15)
compare_btn.pack(side=tk.LEFT, padx=8)

# ==================== 主体区域 ====================
main_container = tk.Frame(root, bg=THEME["bg_dark"])
main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# 左侧面板：数独网格 + 性能统计
left_panel = tk.Frame(main_container, bg=THEME["bg_dark"], width=420)
left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
left_panel.pack_propagate(False)  # 固定宽度

# 数独网格区域
grid_container = tk.Frame(left_panel, bg=THEME["bg_card"], relief="flat", bd=2)
grid_container.pack(fill=tk.X, pady=(0, 10))

# 网格标题
grid_title = tk.Label(grid_container, text="数独盘面",
    bg=THEME["bg_card"], fg=THEME["text_accent"],
    font=("Segoe UI", 12, "bold"))
grid_title.pack(pady=8)

# 数独网格容器
grid_frame = tk.Frame(grid_container, bg=THEME["bg_dark"], relief="solid", bd=2)
grid_frame.pack(padx=10, pady=(0, 10))

# 创建9x9网格（缩小尺寸）
for row in range(9):
    for col in range(9):
        # 计算背景颜色（3x3宫格交替）
        block_row, block_col = row // 3, col // 3
        bg_color = THEME["grid_bg1"] if (block_row + block_col) % 2 == 0 else THEME["grid_bg2"]
        
        entry = tk.Entry(grid_frame,
            width=2,
            font=("Consolas", 16, "bold"),
            justify=tk.CENTER,
            bg=bg_color,
            fg=THEME["text_primary"],
            insertbackground=THEME["text_accent"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=THEME["grid_line"],
            highlightcolor=THEME["accent"])
        
        # 设置边距（3x3宫格之间加粗）
        padx = (1, 3) if (col + 1) % 3 == 0 else (1, 1)
        pady = (1, 3) if (row + 1) % 3 == 0 else (1, 1)
        
        entry.grid(row=row, column=col, padx=padx, pady=pady, sticky="nsew")
        sudoku_entries[row][col] = entry

# 配置网格权重
for i in range(9):
    grid_frame.grid_rowconfigure(i, weight=1, minsize=38)
    grid_frame.grid_columnconfigure(i, weight=1, minsize=38)

# 性能统计区（在数独盘面下方）
stats_frame = ttk.LabelFrame(left_panel, text="⚡ 性能统计",
    style="Premium.TLabelframe", padding=10)
stats_frame.pack(fill=tk.BOTH, expand=True)

perf_labels = {}
metrics = [
    ("algorithm", "算法", "未选择"),
    ("time", "耗时", "0.000 秒"),
    ("nodes", "搜索节点", "0"),
    ("backtracks", "回溯次数", "0"),
    ("status", "状态", "待求解")
]

for key, label_text, default_value in metrics:
    stat_row = tk.Frame(stats_frame, bg=THEME["bg_card"])
    stat_row.pack(fill=tk.X, pady=3)
    
    tk.Label(stat_row, text=f"{label_text}：",
        bg=THEME["bg_card"], fg=THEME["text_secondary"],
        font=("Segoe UI", 9)).pack(side=tk.LEFT)
    
    value_label = tk.Label(stat_row, text=default_value,
        bg=THEME["bg_card"], fg=THEME["text_accent"],
        font=("Segoe UI", 10, "bold"))
    value_label.pack(side=tk.LEFT, padx=8)
    perf_labels[key] = value_label

# 右侧面板：搜索树可视化（增大）
right_panel = tk.Frame(main_container, bg=THEME["bg_dark"])
right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# 搜索树可视化区
tree_frame = ttk.LabelFrame(right_panel, text="🌳 搜索树可视化",
    style="Premium.TLabelframe", padding=5)
tree_frame.pack(fill=tk.BOTH, expand=True)

# 搜索树画布（带滚动条）
tree_canvas_frame = tk.Frame(tree_frame, bg=THEME["bg_medium"])
tree_canvas_frame.pack(fill=tk.BOTH, expand=True)

tree_canvas = tk.Canvas(tree_canvas_frame, bg=THEME["bg_medium"], highlightthickness=0)
tree_scrollbar_y = tk.Scrollbar(tree_canvas_frame, orient=tk.VERTICAL, command=tree_canvas.yview)
tree_scrollbar_x = tk.Scrollbar(tree_canvas_frame, orient=tk.HORIZONTAL, command=tree_canvas.xview)

tree_canvas.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)

tree_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
tree_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# ==================== 搜索树可视化类（自适应蛇形布局）====================
class SearchTreeVisualizer:
    """搜索树可视化 - 自适应蛇形布局，充分利用页面空间"""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.nodes = {}
        self.node_counter = 0
        self.current_path = []
        self.root_node = None
        
        # 基础布局参数
        self.base_node_radius = 12
        self.base_node_spacing = 28
        self.margin = 20
        
        # 动态计算的参数
        self.node_radius = self.base_node_radius
        self.node_spacing = self.base_node_spacing
        self.nodes_per_row = 20
        self.row_height = 50
        
        # 颜色
        self.colors = {
            'trying': THEME["anim_try"],
            'backtrack': THEME["anim_backtrack"],
            'success': THEME["anim_success"],
            'default': THEME["bg_light"],
            'text': THEME["text_primary"],
            'line': THEME["text_secondary"],
            'line_success': THEME["success"],
            'row_indicator': THEME["text_accent"],
        }
        
        self.row_labels = []
    
    def _get_canvas_size(self):
        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        return max(width, 400), max(height, 300)
    
    def _calculate_layout_params(self):
        width, height = self._get_canvas_size()
        usable_width = width - self.margin * 2 - 40
        self.nodes_per_row = max(10, int(usable_width / self.base_node_spacing))
        self.node_spacing = usable_width / self.nodes_per_row
        usable_height = height - self.margin * 2
        max_rows = max(4, int(usable_height / 50))
        self.row_height = usable_height / max_rows
        self.node_radius = min(self.base_node_radius, 
                               int(self.node_spacing * 0.35),
                               int(self.row_height * 0.25))
        self.node_radius = max(8, self.node_radius)
    
    def _get_node_position(self, index):
        row = index // self.nodes_per_row
        col_in_row = index % self.nodes_per_row
        if row % 2 == 0:
            x = self.margin + 40 + col_in_row * self.node_spacing + self.node_spacing / 2
        else:
            x = self.margin + 40 + (self.nodes_per_row - 1 - col_in_row) * self.node_spacing + self.node_spacing / 2
        y = self.margin + row * self.row_height + self.row_height / 2
        return x, y, row
    
    def clear(self):
        self.canvas.delete("all")
        self.nodes = {}
        self.node_counter = 0
        self.current_path = []
        self.root_node = None
        self.row_labels = []
        self._calculate_layout_params()
        width, height = self._get_canvas_size()
        self.canvas.create_text(
            width // 2, height // 2,
            text="开始求解后显示搜索树",
            fill=THEME["text_secondary"],
            font=("Segoe UI", 11),
            tags="placeholder"
        )
    
    def _draw_row_indicator(self, row_num):
        y = self.margin + row_num * self.row_height + self.row_height / 2
        if row_num not in self.row_labels:
            self.row_labels.append(row_num)
            self.canvas.create_rectangle(
                5, y - 12, 35, y + 12,
                fill=THEME["bg_card"], outline=THEME["grid_line"],
                tags=f"row_bg_{row_num}"
            )
            self.canvas.create_text(
                20, y, text=f"L{row_num + 1}",
                fill=self.colors['row_indicator'],
                font=("Consolas", 8, "bold"),
                tags=f"row_label_{row_num}"
            )
    
    def _draw_connection_line(self, parent_x, parent_y, parent_row, x, y, current_row, node_id):
        if parent_row == current_row:
            return self.canvas.create_line(
                parent_x + self.node_radius, parent_y,
                x - self.node_radius, y,
                fill=self.colors['line'], width=2,
                tags=f"line_{node_id}"
            )
        else:
            mid_y = (parent_y + y) / 2
            return self.canvas.create_line(
                parent_x, parent_y + self.node_radius,
                parent_x, mid_y,
                x, mid_y,
                x, y - self.node_radius,
                fill=self.colors['line'], width=2,
                smooth=True,
                tags=f"line_{node_id}"
            )
    
    def add_node(self, row, col, value, parent_id=None):
        self.canvas.delete("placeholder")
        if self.node_counter == 0:
            self._calculate_layout_params()
        
        node_id = self.node_counter
        self.node_counter += 1
        x, y, current_row = self._get_node_position(node_id)
        self._draw_row_indicator(current_row)
        
        line_id = None
        if parent_id is not None and parent_id in self.nodes:
            parent = self.nodes[parent_id]
            parent_row = self._get_node_position(parent_id)[2]
            line_id = self._draw_connection_line(
                parent['x'], parent['y'], parent_row,
                x, y, current_row, node_id
            )
        
        oval_id = self.canvas.create_oval(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill=self.colors['trying'], outline=THEME["text_primary"], width=1,
            tags=f"node_{node_id}"
        )
        
        font_size = max(7, min(9, int(self.node_radius * 0.7)))
        text_id = self.canvas.create_text(
            x, y, text=str(value),
            fill=self.colors['text'], font=("Consolas", font_size, "bold"),
            tags=f"text_{node_id}"
        )
        
        self.nodes[node_id] = {
            'x': x, 'y': y,
            'row': row, 'col': col, 'value': value,
            'oval_id': oval_id, 'text_id': text_id,
            'parent_id': parent_id, 'line_id': line_id,
            'state': 'trying', 'display_row': current_row
        }
        
        self.current_path.append(node_id)
        if self.root_node is None:
            self.root_node = node_id
        self.canvas.update_idletasks()
        return node_id
    
    def backtrack_node(self):
        if not self.current_path:
            return
        node_id = self.current_path.pop()
        if node_id in self.nodes:
            node = self.nodes[node_id]
            self.canvas.itemconfig(node['oval_id'], fill=self.colors['backtrack'])
            node['state'] = 'backtrack'
    
    def mark_success_path(self):
        for node_id in self.current_path:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                self.canvas.itemconfig(node['oval_id'], fill=self.colors['success'])
                if node['line_id']:
                    self.canvas.itemconfig(node['line_id'], fill=self.colors['line_success'], width=2)
                node['state'] = 'success'
        if self.nodes:
            width, height = self._get_canvas_size()
            self.canvas.create_text(
                width // 2, height - 15,
                text=f"✓ 搜索完成! 共 {len(self.nodes)} 步",
                fill=THEME["success"],
                font=("Segoe UI", 9, "bold"),
                tags="success_msg"
            )
    
    def get_current_parent_id(self):
        if self.current_path:
            return self.current_path[-1]
        return None

# 创建搜索树可视化器实例
search_tree_viz = SearchTreeVisualizer(tree_canvas)

# ==================== 核心功能函数 ====================
def get_speed_params():
    """获取动画速度参数"""
    speed_map = {
        "慢": (600, 800),
        "中": (300, 400),
        "快": (100, 150)
    }
    return speed_map.get(speed_var.get(), (300, 400))

def disable_buttons():
    """禁用所有按钮"""
    for btn in [clear_btn, fill_btn, solve_btn, compare_btn]:
        btn.config(state="disabled")
    difficulty_menu.config(state="disabled")
    alg_menu.config(state="disabled")
    speed_menu.config(state="disabled")

def enable_buttons():
    """启用所有按钮"""
    for btn in [clear_btn, fill_btn, solve_btn, compare_btn]:
        btn.config(state="normal")
    difficulty_menu.config(state="readonly")
    alg_menu.config(state="readonly")
    speed_menu.config(state="readonly")

def clear_sudoku():
    """清空数独"""
    global original_puzzle
    disable_buttons()
    
    for row in range(9):
        for col in range(9):
            entry = sudoku_entries[row][col]
            entry.config(state="normal")
            entry.delete(0, tk.END)
            block_row, block_col = row // 3, col // 3
            bg_color = THEME["grid_bg1"] if (block_row + block_col) % 2 == 0 else THEME["grid_bg2"]
            entry.config(bg=bg_color, fg=THEME["text_primary"])
            original_puzzle[row][col] = 0
    
    update_performance(None)
    search_tree_viz.clear()  # 清空搜索树
    enable_buttons()

def read_sudoku():
    """读取当前数独盘面"""
    sudoku_data = [[0 for _ in range(9)] for _ in range(9)]
    for row in range(9):
        for col in range(9):
            value = sudoku_entries[row][col].get().strip()
            if value.isdigit() and 1 <= int(value) <= 9:
                sudoku_data[row][col] = int(value)
    return sudoku_data

def fill_sudoku(sudoku_data, is_initial=False):
    """填充数独盘面"""
    global original_puzzle
    
    if is_initial:
        for row in range(9):
            for col in range(9):
                original_puzzle[row][col] = sudoku_data[row][col]
    
    for row in range(9):
        for col in range(9):
            value = sudoku_data[row][col]
            entry = sudoku_entries[row][col]
            entry.config(state="normal")
            entry.delete(0, tk.END)
            
            if value != 0:
                entry.insert(0, str(value))
                # 原始题目用金色，求解答案用白色
                if is_initial or original_puzzle[row][col] != 0:
                    entry.config(fg=THEME["text_accent"])
                else:
                    entry.config(fg=THEME["text_primary"])
            
            block_row, block_col = row // 3, col // 3
            bg_color = THEME["grid_bg1"] if (block_row + block_col) % 2 == 0 else THEME["grid_bg2"]
            entry.config(bg=bg_color)

def update_performance(perf_data):
    """更新性能统计"""
    if perf_data is None:
        perf_labels['algorithm'].config(text="未选择")
        perf_labels['time'].config(text="0.000 秒")
        perf_labels['nodes'].config(text="0")
        perf_labels['backtracks'].config(text="0")
        perf_labels['status'].config(text="待求解", fg=THEME["text_secondary"])
    else:
        perf_labels['algorithm'].config(text=perf_data.get('algorithm', '未知'))
        perf_labels['time'].config(text=f"{perf_data.get('time', 0):.3f} 秒")
        perf_labels['nodes'].config(text=str(perf_data.get('nodes', 0)))
        perf_labels['backtracks'].config(text=str(perf_data.get('backtracks', 0)))
        
        status = perf_data.get('status', '未知')
        if status == '成功':
            perf_labels['status'].config(text=status, fg=THEME["success"])
        elif status == '失败':
            perf_labels['status'].config(text=status, fg=THEME["error"])
        else:
            perf_labels['status'].config(text=status, fg=THEME["warning"])

# ==================== 生成动画 ====================
def animate_generation_step(row, col, value, step_type="fill"):
    """生成过程动画
    step_type: 'fill' - 填入数字, 'try' - 尝试, 'backtrack' - 回溯
    """
    if not animate_var.get():
        return
    
    entry = sudoku_entries[row][col]
    interval, duration = get_speed_params()
    
    def update():
        entry.config(state="normal")
        
        if step_type == "fill":
            # 填入数字 - 紫色闪烁
            entry.config(bg=THEME["anim_generate"])
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
            entry.config(fg=THEME["text_primary"])
            
            # 恢复原色（保持数字和金色）
            def restore():
                block_row, block_col = row // 3, col // 3
                bg_color = THEME["grid_bg1"] if (block_row + block_col) % 2 == 0 else THEME["grid_bg2"]
                entry.config(bg=bg_color, fg=THEME["text_accent"])
                # 保持数字不变
            
            root.after(duration, restore)
            
        elif step_type == "try":
            # 尝试 - 蓝色
            entry.config(bg=THEME["anim_try"])
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
            entry.config(fg=THEME["text_primary"])
            
        elif step_type == "backtrack":
            # 回溯 - 红色闪烁
            entry.config(bg=THEME["anim_backtrack"])
            entry.delete(0, tk.END)
            entry.config(fg=THEME["text_primary"])
            
            def restore():
                block_row, block_col = row // 3, col // 3
                bg_color = THEME["grid_bg1"] if (block_row + block_col) % 2 == 0 else THEME["grid_bg2"]
                entry.config(bg=bg_color)
            
            root.after(duration // 2, restore)
    
    root.after(0, update)  # 立即执行，不延迟

def fill_with_difficulty():
    """生成数独（带动画）"""
    if SudokuGenerator is None:
        messagebox.showerror("错误", "数独生成器未加载")
        return
    
    level = difficulty_var.get()
    difficulty_map = {"简单": "Easy", "中等": "Medium", "困难": "Hard"}
    target_difficulty = difficulty_map.get(level, "Medium")
    
    def generate_with_animation():
        disable_buttons()
        perf_labels['status'].config(text=f"正在生成{level}数独...", fg=THEME["warning"])
        
        try:
            # 先清空
            for row in range(9):
                for col in range(9):
                    entry = sudoku_entries[row][col]
                    entry.config(state="normal")
                    entry.delete(0, tk.END)
            
            # 生成数独
            generator = SudokuGenerator()
            puzzle, info = generator.generate_puzzle_with_difficulty(
                target_difficulty=target_difficulty,
                symmetric=True,
                max_retries=20
            )
            
            # 保存原始题目
            global original_puzzle
            for r in range(9):
                for c in range(9):
                    original_puzzle[r][c] = puzzle[r][c]
            
            # 动画展示生成过程
            if animate_var.get():
                cells = [(r, c, puzzle[r][c]) for r in range(9) for c in range(9) if puzzle[r][c] != 0]
                random.shuffle(cells)  # 随机顺序展示
                
                interval, _ = get_speed_params()
                delay = max(interval // 10, 30)  # 生成动画更快
                
                # 使用函数来避免闭包问题
                def schedule_animation(idx, row, col, val):
                    root.after(idx * delay, lambda: animate_generation_step(row, col, val, "fill"))
                
                for idx, (r, c, val) in enumerate(cells):
                    schedule_animation(idx, r, c, val)
                
                # 动画结束后更新状态（不再调用fill_sudoku，因为数字已经在了）
                final_info = info  # 保存info避免闭包问题
                root.after(len(cells) * delay + 500, lambda: [
                    perf_labels['status'].config(
                        text=f"✓ 已生成 {final_info['level']} 难度（提示数:{final_info['clues']}）",
                        fg=THEME["success"]),
                    enable_buttons()
                ])
            else:
                # 无动画直接显示
                fill_sudoku(puzzle, is_initial=True)
                perf_labels['status'].config(
                    text=f"✓ 已生成 {info['level']} 难度（提示数:{info['clues']}）",
                    fg=THEME["success"])
                enable_buttons()
                
        except Exception as e:
            messagebox.showerror("生成失败", str(e))
            enable_buttons()
    
    threading.Thread(target=generate_with_animation, daemon=True).start()

# ==================== 求解动画 ====================
def animation_fill_cell(row, col, value, is_try=True):
    """求解过程填充动画"""
    if not animate_var.get():
        # 无动画模式，直接填充
        entry = sudoku_entries[row][col]
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, str(value))
        if not is_try:
            entry.config(fg=THEME["text_primary"])
        return
    
    entry = sudoku_entries[row][col]
    interval, duration = get_speed_params()
    
    # 立即更新UI
    entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, str(value))
    
    if is_try:
        # 尝试填入 - 蓝色背景
        entry.config(bg=THEME["anim_try"], fg=THEME["text_primary"])
        
        # 同步更新搜索树 - 添加蓝色节点
        parent_id = search_tree_viz.get_current_parent_id()
        search_tree_viz.add_node(row, col, value, parent_id)
        
        root.update_idletasks()
        time.sleep(interval / 1000.0)  # 暂停以显示动画
    else:
        # 最终答案 - 恢复原色
        entry.config(fg=THEME["text_primary"])
        block_row, block_col = row // 3, col // 3
        bg_color = THEME["grid_bg1"] if (block_row + block_col) % 2 == 0 else THEME["grid_bg2"]
        entry.config(bg=bg_color)

def animation_backtrack_cell(row, col):
    """求解过程回溯动画"""
    if not animate_var.get():
        # 无动画模式，直接清空
        entry = sudoku_entries[row][col]
        entry.config(state="normal")
        entry.delete(0, tk.END)
        return
    
    entry = sudoku_entries[row][col]
    interval, duration = get_speed_params()
    
    # 立即显示回溯效果
    entry.config(state="normal", bg=THEME["anim_backtrack"])
    entry.delete(0, tk.END)
    entry.insert(0, "✗")
    entry.config(fg=THEME["error"])
    
    # 同步更新搜索树 - 标记当前节点为红色并回溯
    search_tree_viz.backtrack_node()
    
    root.update_idletasks()
    
    # 暂停显示
    time.sleep(max(duration / 1000.0, 0.1))
    
    # 恢复原状
    entry.delete(0, tk.END)
    block_row, block_col = row // 3, col // 3
    bg_color = THEME["grid_bg1"] if (block_row + block_col) % 2 == 0 else THEME["grid_bg2"]
    entry.config(bg=bg_color, fg=THEME["text_primary"])
    root.update_idletasks()

def animation_ac3_prune_cell(row, col, value):
    """AC3剪枝动画"""
    if not animate_var.get():
        return
    
    entry = sudoku_entries[row][col]
    interval, _ = get_speed_params()
    
    # 立即显示剪枝效果
    entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, str(value))
    entry.config(fg=THEME["text_secondary"], font=("Consolas", 12, "italic"))
    root.update_idletasks()
    
    # 短暂暂停
    time.sleep(max(interval / 3000.0, 0.05))
    
    # 清空
    entry.delete(0, tk.END)
    entry.config(font=("Consolas", 20, "bold"))
    root.update_idletasks()

def solve_sudoku():
    """求解数独"""
    global is_animating
    
    selected_alg = algorithm_var.get()
    sudoku_data = read_sudoku()
    
    if all(value == 0 for row in sudoku_data for value in row):
        perf_labels['status'].config(text="请先生成或输入数独", fg=THEME["error"])
        return
    
    disable_buttons()
    is_animating = animate_var.get()
    perf_labels['algorithm'].config(text=selected_alg)
    perf_labels['status'].config(text="求解中...", fg=THEME["warning"])
    
    # 清空搜索树
    search_tree_viz.clear()
    
    def run_solver():
        try:
            puzzle = deepcopy(sudoku_data)
            
            if selected_alg == "基础DFS算法":
                if BasicSolver is None:
                    raise ImportError("基础DFS算法未加载")
                solver = BasicSolver()
                solver.set_animation_callbacks(
                    fill_cb=animation_fill_cell,
                    backtrack_cb=animation_backtrack_cell)
                solution = solver.solve(puzzle)
                
            elif selected_alg == "MRV+LCV算法":
                if MRVLCVSolver is None:
                    raise ImportError("MRV+LCV算法未加载")
                solver = MRVLCVSolver()
                solver.set_animation_callbacks(
                    fill_cb=animation_fill_cell,
                    backtrack_cb=animation_backtrack_cell)
                solution = solver.solve(puzzle)
                
            elif selected_alg == "AC3+MRV+LCV算法":
                if AC3_MRV_LCV_Solver is None:
                    raise ImportError("AC3+MRV+LCV算法未加载")
                solver = AC3_MRV_LCV_Solver()
                solver.set_animation_callbacks(
                    fill_cb=animation_fill_cell,
                    backtrack_cb=animation_backtrack_cell,
                    ac3_prune_cb=animation_ac3_prune_cell)
                solution = solver.solve(puzzle)
            else:
                raise ValueError(f"未知算法: {selected_alg}")
            
            # 使用纯算法时间（不包含动画）
            actual_time = solver.stats.pure_solve_time if hasattr(solver.stats, 'pure_solve_time') else solver.stats.solve_time
            
            final_perf = {
                'algorithm': selected_alg,
                'time': actual_time,
                'nodes': solver.stats.nodes,
                'backtracks': solver.stats.backtracks,
                'status': '成功' if solution else '失败'
            }
            
            root.after(0, finish_solve, solution is not None, solution, final_perf)
            
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("求解错误", str(e)))
            root.after(0, lambda: perf_labels['status'].config(text="出错", fg=THEME["error"]))
            root.after(0, enable_buttons)
    
    threading.Thread(target=run_solver, daemon=True).start()

def finish_solve(success, result_board, final_perf):
    """完成求解"""
    global is_animating
    is_animating = False
    
    update_performance(final_perf)
    
    if success:
        # 标记搜索树成功路径为绿色
        search_tree_viz.mark_success_path()
        perf_labels['status'].config(text="✓ 求解成功", fg=THEME["success"])
    else:
        perf_labels['status'].config(text="✗ 求解失败", fg=THEME["error"])
    
    enable_buttons()

# ==================== 算法对比 ====================
performance_data = {
    "基础DFS": {"time": 0, "nodes": 0, "backtracks": 0},
    "MRV+LCV": {"time": 0, "nodes": 0, "backtracks": 0},
    "AC3+MRV+LCV": {"time": 0, "nodes": 0, "backtracks": 0},
}

def compare_algorithms():
    """对比所有算法并显示图表"""
    sudoku_data = read_sudoku()
    
    if all(value == 0 for row in sudoku_data for value in row):
        messagebox.showwarning("提示", "请先生成或输入数独")
        return
    
    disable_buttons()
    perf_labels['status'].config(text="正在对比算法...", fg=THEME["warning"])
    
    def run_comparison():
        try:
            # 测试基础DFS（对比时不使用动画，获取真实性能）
            if BasicSolver:
                puzzle = deepcopy(sudoku_data)
                solver = BasicSolver()
                solver.solve(puzzle)
                actual_time = solver.stats.pure_solve_time if hasattr(solver.stats, 'pure_solve_time') else solver.stats.solve_time
                performance_data["基础DFS"]["time"] = actual_time
                performance_data["基础DFS"]["nodes"] = solver.stats.nodes
                performance_data["基础DFS"]["backtracks"] = solver.stats.backtracks
            
            # 测试MRV+LCV
            if MRVLCVSolver:
                puzzle = deepcopy(sudoku_data)
                solver = MRVLCVSolver()
                solver.solve(puzzle)
                actual_time = solver.stats.pure_solve_time if hasattr(solver.stats, 'pure_solve_time') else solver.stats.solve_time
                performance_data["MRV+LCV"]["time"] = actual_time
                performance_data["MRV+LCV"]["nodes"] = solver.stats.nodes
                performance_data["MRV+LCV"]["backtracks"] = solver.stats.backtracks
            
            # 测试AC3+MRV+LCV
            if AC3_MRV_LCV_Solver:
                puzzle = deepcopy(sudoku_data)
                solver = AC3_MRV_LCV_Solver()
                solver.solve(puzzle)
                actual_time = solver.stats.pure_solve_time if hasattr(solver.stats, 'pure_solve_time') else solver.stats.solve_time
                performance_data["AC3+MRV+LCV"]["time"] = actual_time
                performance_data["AC3+MRV+LCV"]["nodes"] = solver.stats.nodes
                performance_data["AC3+MRV+LCV"]["backtracks"] = solver.stats.backtracks
            
            # 显示图表
            root.after(0, lambda: [
                show_chart(),
                perf_labels['status'].config(text="✓ 对比完成", fg=THEME["success"])
            ])
            
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("对比失败", str(e)))
        finally:
            root.after(0, enable_buttons)
    
    threading.Thread(target=run_comparison, daemon=True).start()

# ==================== 统计图表 ====================
def show_chart():
    """显示统计图表"""
    has_data = any(performance_data[alg]["nodes"] > 0 for alg in performance_data)
    
    if not has_data:
        messagebox.showinfo("提示", "请先运行「对比算法」以获取统计数据")
        return
    
    chart_window = tk.Toplevel(root)
    chart_window.title("算法性能统计图表")
    chart_window.geometry("1000x700")
    chart_window.configure(bg=THEME["bg_dark"])
    
    algorithms = ["基础DFS", "MRV+LCV", "AC3+MRV+LCV"]
    times = [performance_data[alg]["time"] for alg in algorithms]
    nodes = [performance_data[alg]["nodes"] for alg in algorithms]
    backtracks = [performance_data[alg]["backtracks"] for alg in algorithms]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor(THEME["bg_dark"])
    
    # 图表1：执行时间对比
    colors1 = [THEME["primary"], THEME["secondary"], THEME["accent"]]
    bars1 = ax1.bar(algorithms, times, color=colors1, alpha=0.8, edgecolor='white', linewidth=2)
    ax1.set_ylabel('执行时间 (秒)', fontsize=12, color='white')
    ax1.set_title('执行时间对比', fontsize=14, fontweight='bold', color=THEME["text_accent"])
    ax1.tick_params(colors='white')
    ax1.set_facecolor(THEME["bg_medium"])
    ax1.grid(axis='y', alpha=0.3, color='white')
    
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}s', ha='center', va='bottom',
                fontsize=10, fontweight='bold', color='white')
    
    # 图表2：节点数和回溯次数
    x = range(len(algorithms))
    width = 0.35
    bars2 = ax2.bar([i - width/2 for i in x], nodes, width,
                    label='搜索节点', color=THEME["info"], alpha=0.8)
    bars3 = ax2.bar([i + width/2 for i in x], backtracks, width,
                    label='回溯次数', color=THEME["warning"], alpha=0.8)
    
    ax2.set_ylabel('数量', fontsize=12, color='white')
    ax2.set_title('搜索节点 vs 回溯次数', fontsize=14, fontweight='bold', color=THEME["text_accent"])
    ax2.set_xticks(x)
    ax2.set_xticklabels(algorithms)
    ax2.tick_params(colors='white')
    ax2.set_facecolor(THEME["bg_medium"])
    ax2.legend(facecolor=THEME["bg_card"], edgecolor='white', labelcolor='white')
    ax2.grid(axis='y', alpha=0.3, color='white')
    
    plt.tight_layout()
    
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

# ==================== 启动应用 ====================
if __name__ == "__main__":
    print("🎮 数独求解器 Premium Edition 启动中...")
    root.mainloop()
