# -*- coding: utf-8 -*-
"""
数独求解可视化工具 - 像素农场版 🌾
可爱像素风农场游戏 UI 风格
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
    print("🌱 算法和生成器加载成功!")
except ImportError as e:
    print(f"⚠ 警告：导入失败 - {e}")
    BasicSolver = MRVLCVSolver = AC3_MRV_LCV_Solver = SudokuGenerator = None

# ==================== 像素农场配色方案 ====================
THEME = {
    # 主色调 - 温暖农场色
    "primary": "#8B4513",       # 棕色（木头）
    "secondary": "#228B22",     # 森林绿
    "accent": "#FF6B35",        # 橙色（胡萝卜）
    
    # 背景色 - 草地和天空
    "bg_sky": "#87CEEB",        # 天空蓝
    "bg_grass": "#90EE90",      # 浅草绿
    "bg_dirt": "#DEB887",       # 泥土色
    "bg_wood": "#D2691E",       # 木板色
    "bg_panel": "#FFEFD5",      # 羊皮纸色（面板背景）
    "bg_panel_dark": "#F5DEB3", # 深羊皮纸
    
    # 农田格子颜色
    "field_light": "#98FB98",   # 浅绿农田
    "field_dark": "#7CCD7C",    # 深绿农田
    "field_border": "#556B2F",  # 农田边框
    
    # 文字颜色
    "text_dark": "#4A3728",     # 深棕色文字
    "text_light": "#FFFAF0",    # 花白色文字
    "text_gold": "#DAA520",     # 金色文字
    "text_red": "#CD5C5C",      # 红色文字
    
    # 状态颜色
    "success": "#32CD32",       # 酸橙绿
    "error": "#DC143C",         # 深红
    "warning": "#FFA500",       # 橙色
    "info": "#4169E1",          # 皇家蓝
    
    # 动画颜色 - 农场主题
    "anim_plant": "#98FB98",    # 种植（浅绿）
    "anim_water": "#87CEFA",    # 浇水（浅蓝）
    "anim_wither": "#CD853F",   # 枯萎（秘鲁色）
    "anim_harvest": "#FFD700",  # 收获（金色）
    
    # 像素边框
    "border_dark": "#4A3728",   # 深色边框
    "border_light": "#8B7355",  # 浅色边框
}

# ==================== 主窗口初始化 ====================
root = tk.Tk()
root.title("🌾 数独农场 - Sudoku Farm 🌻")
root.geometry("1400x900")
root.configure(bg=THEME["bg_sky"])

# 全局变量
sudoku_entries = [[None for _ in range(9)] for _ in range(9)]
original_puzzle = [[0 for _ in range(9)] for _ in range(9)]
is_animating = False
animation_queue = []
generation_step = 0

# ==================== 像素风格辅助函数 ====================
def create_pixel_border(parent, bg_color, border_color, border_width=4):
    """创建像素风格边框的Frame"""
    outer = tk.Frame(parent, bg=border_color, padx=border_width, pady=border_width)
    inner = tk.Frame(outer, bg=bg_color)
    inner.pack(fill=tk.BOTH, expand=True)
    return outer, inner

def create_pixel_button(parent, text, command, width=12, bg_color=None, emoji=""):
    """创建像素风格按钮"""
    if bg_color is None:
        bg_color = THEME["primary"]
    
    btn_frame = tk.Frame(parent, bg=THEME["border_dark"], padx=3, pady=3)
    
    btn = tk.Button(btn_frame, text=f"{emoji} {text}" if emoji else text,
        command=command,
        bg=bg_color,
        fg=THEME["text_light"],
        font=("Courier New", 10, "bold"),
        relief="raised",
        bd=3,
        cursor="hand2",
        width=width,
        height=1,
        activebackground=THEME["accent"],
        activeforeground=THEME["text_light"])
    btn.pack()
    
    return btn_frame, btn

# ==================== 自定义样式 ====================
style = ttk.Style(root)
style.theme_use('clam')

# 像素风下拉框样式
style.configure("Pixel.TCombobox",
    fieldbackground=THEME["bg_panel"],
    background=THEME["primary"],
    foreground=THEME["text_dark"],
    arrowcolor=THEME["text_dark"],
    borderwidth=2,
    relief="raised")

# 像素风LabelFrame样式
style.configure("Pixel.TLabelframe",
    background=THEME["bg_panel"],
    foreground=THEME["text_dark"],
    borderwidth=4,
    relief="ridge")
style.configure("Pixel.TLabelframe.Label",
    background=THEME["bg_panel"],
    foreground=THEME["primary"],
    font=("Courier New", 11, "bold"))

# ==================== 顶部标题栏 ====================
# 天空背景
sky_frame = tk.Frame(root, bg=THEME["bg_sky"], height=80)
sky_frame.pack(fill=tk.X)
sky_frame.pack_propagate(False)

# 标题 - 像素风格
title_label = tk.Label(sky_frame,
    text="🌾 数独农场 Sudoku Farm 🌻",
    font=("Courier New", 28, "bold"),
    bg=THEME["bg_sky"],
    fg=THEME["primary"])
title_label.pack(pady=20)

# 装饰云朵
cloud1 = tk.Label(sky_frame, text="☁", font=("Arial", 24), bg=THEME["bg_sky"], fg="white")
cloud1.place(x=50, y=10)
cloud2 = tk.Label(sky_frame, text="☁", font=("Arial", 20), bg=THEME["bg_sky"], fg="white")
cloud2.place(x=1300, y=20)
sun_label = tk.Label(sky_frame, text="☀", font=("Arial", 30), bg=THEME["bg_sky"], fg="#FFD700")
sun_label.place(x=1200, y=5)

# ==================== 控制面板（任务面板风格）====================
control_outer = tk.Frame(root, bg=THEME["border_dark"], padx=4, pady=4)
control_outer.pack(fill=tk.X, padx=20, pady=(0, 10))

control_panel = tk.Frame(control_outer, bg=THEME["bg_panel"])
control_panel.pack(fill=tk.X)

# 面板标题
panel_title = tk.Label(control_panel,
    text="📋 农场任务面板 Farm Tasks",
    font=("Courier New", 12, "bold"),
    bg=THEME["bg_panel"],
    fg=THEME["primary"])
panel_title.pack(pady=(8, 5))

# 分隔线
separator = tk.Frame(control_panel, bg=THEME["border_light"], height=2)
separator.pack(fill=tk.X, padx=20, pady=5)

# 第一行：设置选项
row1 = tk.Frame(control_panel, bg=THEME["bg_panel"])
row1.pack(fill=tk.X, padx=20, pady=5)

# 难度选择
tk.Label(row1, text="🌱 难度:", bg=THEME["bg_panel"],
    fg=THEME["text_dark"], font=("Courier New", 10, "bold")).pack(side=tk.LEFT, padx=5)
difficulty_var = tk.StringVar(value="中等")
difficulty_menu = ttk.Combobox(row1, textvariable=difficulty_var,
    values=["简单", "中等", "困难"], state="readonly", width=10, style="Pixel.TCombobox")
difficulty_menu.pack(side=tk.LEFT, padx=8)

# 算法选择
tk.Label(row1, text="🔧 工具:", bg=THEME["bg_panel"],
    fg=THEME["text_dark"], font=("Courier New", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
algorithm_var = tk.StringVar(value="MRV+LCV算法")
alg_menu = ttk.Combobox(row1, textvariable=algorithm_var,
    values=["基础DFS算法", "MRV+LCV算法", "AC3+MRV+LCV算法"],
    state="readonly", width=18, style="Pixel.TCombobox")
alg_menu.pack(side=tk.LEFT, padx=8)

# 动画开关
animate_var = tk.BooleanVar(value=True)
animate_check = tk.Checkbutton(row1, text="🎬 动画",
    variable=animate_var, bg=THEME["bg_panel"], fg=THEME["text_dark"],
    selectcolor=THEME["bg_panel_dark"], font=("Courier New", 10, "bold"),
    activebackground=THEME["bg_panel"], activeforeground=THEME["accent"])
animate_check.pack(side=tk.LEFT, padx=20)

# 速度选择
tk.Label(row1, text="⚡ 速度:", bg=THEME["bg_panel"],
    fg=THEME["text_dark"], font=("Courier New", 10, "bold")).pack(side=tk.LEFT, padx=5)
speed_var = tk.StringVar(value="中")
speed_menu = ttk.Combobox(row1, textvariable=speed_var,
    values=["慢", "中", "快"], state="readonly", width=6, style="Pixel.TCombobox")
speed_menu.pack(side=tk.LEFT, padx=8)

# 第二行：功能按钮
row2 = tk.Frame(control_panel, bg=THEME["bg_panel"])
row2.pack(fill=tk.X, padx=20, pady=(5, 10))

# 按钮容器
btn_container = tk.Frame(row2, bg=THEME["bg_panel"])
btn_container.pack()

clear_frame, clear_btn = create_pixel_button(btn_container, "清理农田", lambda: clear_sudoku(), 12, "#CD853F", "🧹")
clear_frame.pack(side=tk.LEFT, padx=6)

fill_frame, fill_btn = create_pixel_button(btn_container, "播种", lambda: fill_with_difficulty(), 10, "#228B22", "🌱")
fill_frame.pack(side=tk.LEFT, padx=6)

solve_frame, solve_btn = create_pixel_button(btn_container, "开始收获", lambda: solve_sudoku(), 12, "#FF6B35", "🌾")
solve_frame.pack(side=tk.LEFT, padx=6)

compare_frame, compare_btn = create_pixel_button(btn_container, "工具对比", lambda: compare_algorithms(), 12, "#4169E1", "📊")
compare_frame.pack(side=tk.LEFT, padx=6)

# ==================== 主体区域 ====================
# 草地背景
main_container = tk.Frame(root, bg=THEME["bg_grass"])
main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# 左侧面板：数独农田 + 状态公告板
left_panel = tk.Frame(main_container, bg=THEME["bg_grass"], width=420)
left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
left_panel.pack_propagate(False)

# ==================== 数独农田区域 ====================
grid_outer = tk.Frame(left_panel, bg=THEME["border_dark"], padx=4, pady=4)
grid_outer.pack(fill=tk.X, pady=(0, 10))

grid_container = tk.Frame(grid_outer, bg=THEME["bg_panel"])
grid_container.pack(fill=tk.X)

# 农田标题
grid_title = tk.Label(grid_container,
    text="🌻 数独农田 Sudoku Field 🌻",
    bg=THEME["bg_panel"], fg=THEME["primary"],
    font=("Courier New", 11, "bold"))
grid_title.pack(pady=8)

# 数独网格容器（农田风格）
grid_frame_outer = tk.Frame(grid_container, bg=THEME["field_border"], padx=3, pady=3)
grid_frame_outer.pack(padx=10, pady=(0, 10))

grid_frame = tk.Frame(grid_frame_outer, bg=THEME["field_border"])
grid_frame.pack()

# 创建9x9农田格子
for row in range(9):
    for col in range(9):
        # 计算背景颜色（3x3宫格交替 - 农田风格）
        block_row, block_col = row // 3, col // 3
        bg_color = THEME["field_light"] if (block_row + block_col) % 2 == 0 else THEME["field_dark"]
        
        entry = tk.Entry(grid_frame,
            width=2,
            font=("Courier New", 14, "bold"),
            justify=tk.CENTER,
            bg=bg_color,
            fg=THEME["text_dark"],
            insertbackground=THEME["accent"],
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground=THEME["field_border"],
            highlightcolor=THEME["accent"])
        
        # 设置边距（3x3宫格之间加粗 - 像素风格）
        padx = (1, 4) if (col + 1) % 3 == 0 and col < 8 else (1, 1)
        pady = (1, 4) if (row + 1) % 3 == 0 and row < 8 else (1, 1)
        
        entry.grid(row=row, column=col, padx=padx, pady=pady, sticky="nsew")
        sudoku_entries[row][col] = entry

# 配置网格权重
for i in range(9):
    grid_frame.grid_rowconfigure(i, weight=1, minsize=36)
    grid_frame.grid_columnconfigure(i, weight=1, minsize=36)

# ==================== 状态公告板 ====================
stats_outer = tk.Frame(left_panel, bg=THEME["border_dark"], padx=4, pady=4)
stats_outer.pack(fill=tk.BOTH, expand=True)

stats_frame = tk.Frame(stats_outer, bg=THEME["bg_panel"])
stats_frame.pack(fill=tk.BOTH, expand=True)

# 公告板标题
stats_title = tk.Label(stats_frame,
    text="📜 农场公告板 Status Board",
    bg=THEME["bg_panel"], fg=THEME["primary"],
    font=("Courier New", 11, "bold"))
stats_title.pack(pady=8)

# 分隔线
stats_sep = tk.Frame(stats_frame, bg=THEME["border_light"], height=2)
stats_sep.pack(fill=tk.X, padx=15, pady=5)

perf_labels = {}
metrics = [
    ("algorithm", "🔧 工具", "未选择"),
    ("time", "⏱ 耗时", "0.000 秒"),
    ("nodes", "🌱 种植数", "0"),
    ("backtracks", "🔄 重种数", "0"),
    ("status", "📋 状态", "等待播种...")
]

for key, label_text, default_value in metrics:
    stat_row = tk.Frame(stats_frame, bg=THEME["bg_panel"])
    stat_row.pack(fill=tk.X, pady=4, padx=15)
    
    tk.Label(stat_row, text=f"{label_text}:",
        bg=THEME["bg_panel"], fg=THEME["text_dark"],
        font=("Courier New", 9, "bold")).pack(side=tk.LEFT)
    
    value_label = tk.Label(stat_row, text=default_value,
        bg=THEME["bg_panel"], fg=THEME["text_gold"],
        font=("Courier New", 10, "bold"))
    value_label.pack(side=tk.LEFT, padx=10)
    perf_labels[key] = value_label

# 装饰小动物
deco_frame = tk.Frame(stats_frame, bg=THEME["bg_panel"])
deco_frame.pack(fill=tk.X, pady=10)
tk.Label(deco_frame, text="🐔  🐷  🐮  🐑", font=("Arial", 16),
    bg=THEME["bg_panel"]).pack()

# ==================== 右侧面板：搜索路径可视化 ====================
right_panel = tk.Frame(main_container, bg=THEME["bg_grass"])
right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# 搜索路径区域（关卡地图风格）
tree_outer = tk.Frame(right_panel, bg=THEME["border_dark"], padx=4, pady=4)
tree_outer.pack(fill=tk.BOTH, expand=True)

tree_container = tk.Frame(tree_outer, bg=THEME["bg_panel"])
tree_container.pack(fill=tk.BOTH, expand=True)

# 路径标题
tree_title = tk.Label(tree_container,
    text="🗺 探索路径 Adventure Map 🗺",
    bg=THEME["bg_panel"], fg=THEME["primary"],
    font=("Courier New", 11, "bold"))
tree_title.pack(pady=8)

# 搜索树画布（带滚动条）
tree_canvas_outer = tk.Frame(tree_container, bg=THEME["border_light"], padx=2, pady=2)
tree_canvas_outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

tree_canvas_frame = tk.Frame(tree_canvas_outer, bg=THEME["bg_dirt"])
tree_canvas_frame.pack(fill=tk.BOTH, expand=True)

tree_canvas = tk.Canvas(tree_canvas_frame, bg=THEME["bg_dirt"], highlightthickness=0)
tree_scrollbar_y = tk.Scrollbar(tree_canvas_frame, orient=tk.VERTICAL, command=tree_canvas.yview)
tree_scrollbar_x = tk.Scrollbar(tree_canvas_frame, orient=tk.HORIZONTAL, command=tree_canvas.xview)

tree_canvas.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)

tree_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
tree_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


# ==================== 搜索树可视化类（自适应蛇形布局）====================
class SearchTreeVisualizer:
    """搜索路径可视化 - 自适应蛇形布局，充分利用页面空间"""
    
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
        self.nodes_per_row = 20  # 每行节点数，动态调整
        self.row_height = 50     # 行高
        
        # 像素农场风格颜色
        self.colors = {
            'trying': THEME["anim_water"],     # 浇水蓝 - 尝试中
            'backtrack': THEME["anim_wither"], # 枯萎棕 - 回溯
            'success': THEME["anim_harvest"],  # 收获金 - 成功
            'default': THEME["bg_panel_dark"],
            'text': THEME["text_dark"],
            'line': THEME["border_light"],
            'line_success': THEME["success"],
            'row_indicator': THEME["text_gold"],
        }
        
        # 行信息
        self.row_labels = []
    
    def _get_canvas_size(self):
        """获取画布实际尺寸"""
        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        return max(width, 400), max(height, 300)
    
    def _calculate_layout_params(self):
        """根据画布大小动态计算布局参数"""
        width, height = self._get_canvas_size()
        
        # 可用宽度（减去边距和行号区域）
        usable_width = width - self.margin * 2 - 40
        
        # 计算每行可容纳的节点数
        self.nodes_per_row = max(10, int(usable_width / self.base_node_spacing))
        
        # 计算实际节点间距（均匀分布）
        self.node_spacing = usable_width / self.nodes_per_row
        
        # 计算可用行数和行高
        usable_height = height - self.margin * 2
        max_rows = max(4, int(usable_height / 50))
        self.row_height = usable_height / max_rows
        
        # 节点大小自适应
        self.node_radius = min(self.base_node_radius, 
                               int(self.node_spacing * 0.35),
                               int(self.row_height * 0.25))
        self.node_radius = max(8, self.node_radius)
    
    def _get_node_position(self, index):
        """根据节点序号计算蛇形布局位置"""
        row = index // self.nodes_per_row
        col_in_row = index % self.nodes_per_row
        
        # 蛇形布局：偶数行从左到右，奇数行从右到左
        if row % 2 == 0:
            x = self.margin + 40 + col_in_row * self.node_spacing + self.node_spacing / 2
        else:
            x = self.margin + 40 + (self.nodes_per_row - 1 - col_in_row) * self.node_spacing + self.node_spacing / 2
        
        y = self.margin + row * self.row_height + self.row_height / 2
        
        return x, y, row
    
    def clear(self):
        """清空搜索路径"""
        self.canvas.delete("all")
        self.nodes = {}
        self.node_counter = 0
        self.current_path = []
        self.root_node = None
        self.row_labels = []
        
        # 重新计算布局参数
        self._calculate_layout_params()
        
        # 显示提示文字
        width, height = self._get_canvas_size()
        self.canvas.create_text(
            width // 2, height // 2,
            text="🌾 开始收获后显示探索路径 🌾",
            fill=THEME["text_dark"],
            font=("Courier New", 11, "bold"),
            tags="placeholder"
        )
    
    def _draw_row_indicator(self, row_num):
        """绘制行号指示器"""
        y = self.margin + row_num * self.row_height + self.row_height / 2
        
        # 检查是否已绘制该行指示器
        if row_num not in self.row_labels:
            self.row_labels.append(row_num)
            # 绘制行号背景
            self.canvas.create_rectangle(
                5, y - 12, 35, y + 12,
                fill=THEME["bg_panel"], outline=THEME["border_light"],
                tags=f"row_bg_{row_num}"
            )
            # 绘制行号文字
            self.canvas.create_text(
                20, y, text=f"L{row_num + 1}",
                fill=self.colors['row_indicator'],
                font=("Courier New", 8, "bold"),
                tags=f"row_label_{row_num}"
            )
    
    def _draw_connection_line(self, parent_x, parent_y, parent_row, x, y, current_row, node_id):
        """绘制节点间的连接线，处理跨行情况"""
        if parent_row == current_row:
            # 同一行内的连接
            return self.canvas.create_line(
                parent_x + self.node_radius, parent_y,
                x - self.node_radius, y,
                fill=self.colors['line'], width=2,
                tags=f"line_{node_id}"
            )
        else:
            # 跨行连接 - 使用折线
            # 计算中间点
            if parent_row % 2 == 0:
                # 父节点在偶数行（从左到右），连接到右边缘再向下
                mid_x = parent_x + self.node_spacing / 2
            else:
                # 父节点在奇数行（从右到左），连接到左边缘再向下
                mid_x = parent_x - self.node_spacing / 2
            
            mid_y = (parent_y + y) / 2
            
            # 绘制折线
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
        """添加节点 - 使用蛇形自适应布局"""
        self.canvas.delete("placeholder")
        
        # 首次添加时计算布局参数
        if self.node_counter == 0:
            self._calculate_layout_params()
        
        node_id = self.node_counter
        self.node_counter += 1
        
        # 计算节点位置
        x, y, current_row = self._get_node_position(node_id)
        
        # 绘制行指示器
        self._draw_row_indicator(current_row)
        
        # 绘制连接线
        line_id = None
        if parent_id is not None and parent_id in self.nodes:
            parent = self.nodes[parent_id]
            parent_row = self._get_node_position(parent_id)[2]
            line_id = self._draw_connection_line(
                parent['x'], parent['y'], parent_row,
                x, y, current_row, node_id
            )
        
        # 绘制节点（像素方块风格）
        oval_id = self.canvas.create_rectangle(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill=self.colors['trying'],
            outline=THEME["border_dark"], width=2,
            tags=f"node_{node_id}"
        )
        
        # 节点数字
        font_size = max(7, min(9, int(self.node_radius * 0.7)))
        text_id = self.canvas.create_text(
            x, y, text=str(value),
            fill=self.colors['text'],
            font=("Courier New", font_size, "bold"),
            tags=f"text_{node_id}"
        )
        
        # 保存节点信息
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
        """回溯 - 标记为枯萎"""
        if not self.current_path:
            return
        
        node_id = self.current_path.pop()
        if node_id in self.nodes:
            node = self.nodes[node_id]
            self.canvas.itemconfig(node['oval_id'], fill=self.colors['backtrack'])
            node['state'] = 'backtrack'
    
    def mark_success_path(self):
        """标记成功路径 - 金色收获"""
        for node_id in self.current_path:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                self.canvas.itemconfig(node['oval_id'], fill=self.colors['success'])
                if node['line_id']:
                    self.canvas.itemconfig(node['line_id'], 
                        fill=self.colors['line_success'], width=3)
                node['state'] = 'success'
        
        # 绘制成功提示
        if self.nodes:
            width, height = self._get_canvas_size()
            self.canvas.create_text(
                width // 2, height - 20,
                text=f"🌾 探索完成! 共 {len(self.nodes)} 步 🌾",
                fill=THEME["success"],
                font=("Courier New", 10, "bold"),
                tags="success_msg"
            )
    
    def get_current_parent_id(self):
        if self.current_path:
            return self.current_path[-1]
        return None
    
    def get_stats(self):
        """获取搜索树统计信息"""
        if not self.nodes:
            return {"total": 0, "success": 0, "backtrack": 0, "rows": 0}
        
        success_count = sum(1 for n in self.nodes.values() if n['state'] == 'success')
        backtrack_count = sum(1 for n in self.nodes.values() if n['state'] == 'backtrack')
        max_row = max(n.get('display_row', 0) for n in self.nodes.values()) + 1
        
        return {
            "total": len(self.nodes),
            "success": success_count,
            "backtrack": backtrack_count,
            "rows": max_row
        }

# 创建搜索树可视化器实例
search_tree_viz = SearchTreeVisualizer(tree_canvas)

# ==================== 核心功能函数 ====================
def get_speed_params():
    speed_map = {
        "慢": (600, 800),
        "中": (300, 400),
        "快": (100, 150)
    }
    return speed_map.get(speed_var.get(), (300, 400))

def disable_buttons():
    for btn in [clear_btn, fill_btn, solve_btn, compare_btn]:
        btn.config(state="disabled")
    difficulty_menu.config(state="disabled")
    alg_menu.config(state="disabled")
    speed_menu.config(state="disabled")

def enable_buttons():
    for btn in [clear_btn, fill_btn, solve_btn, compare_btn]:
        btn.config(state="normal")
    difficulty_menu.config(state="readonly")
    alg_menu.config(state="readonly")
    speed_menu.config(state="readonly")

def clear_sudoku():
    """清理农田"""
    global original_puzzle
    disable_buttons()
    
    for row in range(9):
        for col in range(9):
            entry = sudoku_entries[row][col]
            entry.config(state="normal")
            entry.delete(0, tk.END)
            block_row, block_col = row // 3, col // 3
            bg_color = THEME["field_light"] if (block_row + block_col) % 2 == 0 else THEME["field_dark"]
            entry.config(bg=bg_color, fg=THEME["text_dark"])
            original_puzzle[row][col] = 0
    
    update_performance(None)
    search_tree_viz.clear()
    enable_buttons()

def read_sudoku():
    sudoku_data = [[0 for _ in range(9)] for _ in range(9)]
    for row in range(9):
        for col in range(9):
            value = sudoku_entries[row][col].get().strip()
            if value.isdigit() and 1 <= int(value) <= 9:
                sudoku_data[row][col] = int(value)
    return sudoku_data

def fill_sudoku(sudoku_data, is_initial=False):
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
                if is_initial or original_puzzle[row][col] != 0:
                    entry.config(fg=THEME["primary"])
                else:
                    entry.config(fg=THEME["text_dark"])
            
            block_row, block_col = row // 3, col // 3
            bg_color = THEME["field_light"] if (block_row + block_col) % 2 == 0 else THEME["field_dark"]
            entry.config(bg=bg_color)

def update_performance(perf_data):
    if perf_data is None:
        perf_labels['algorithm'].config(text="未选择")
        perf_labels['time'].config(text="0.000 秒")
        perf_labels['nodes'].config(text="0")
        perf_labels['backtracks'].config(text="0")
        perf_labels['status'].config(text="等待播种...", fg=THEME["text_dark"])
    else:
        perf_labels['algorithm'].config(text=perf_data.get('algorithm', '未知'))
        perf_labels['time'].config(text=f"{perf_data.get('time', 0):.3f} 秒")
        perf_labels['nodes'].config(text=str(perf_data.get('nodes', 0)))
        perf_labels['backtracks'].config(text=str(perf_data.get('backtracks', 0)))
        
        status = perf_data.get('status', '未知')
        if status == '成功':
            perf_labels['status'].config(text="🌾 丰收啦!", fg=THEME["success"])
        elif status == '失败':
            perf_labels['status'].config(text="💀 歉收...", fg=THEME["error"])
        else:
            perf_labels['status'].config(text=status, fg=THEME["warning"])


# ==================== 生成动画（播种动画）====================
def animate_generation_step(row, col, value, step_type="fill"):
    if not animate_var.get():
        return
    
    entry = sudoku_entries[row][col]
    interval, duration = get_speed_params()
    
    def update():
        entry.config(state="normal")
        
        if step_type == "fill":
            entry.config(bg=THEME["anim_plant"])
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
            entry.config(fg=THEME["text_dark"])
            
            def restore():
                block_row, block_col = row // 3, col // 3
                bg_color = THEME["field_light"] if (block_row + block_col) % 2 == 0 else THEME["field_dark"]
                entry.config(bg=bg_color, fg=THEME["primary"])
            
            root.after(duration, restore)
            
        elif step_type == "try":
            entry.config(bg=THEME["anim_water"])
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
            entry.config(fg=THEME["text_dark"])
            
        elif step_type == "backtrack":
            entry.config(bg=THEME["anim_wither"])
            entry.delete(0, tk.END)
            entry.config(fg=THEME["text_dark"])
            
            def restore():
                block_row, block_col = row // 3, col // 3
                bg_color = THEME["field_light"] if (block_row + block_col) % 2 == 0 else THEME["field_dark"]
                entry.config(bg=bg_color)
            
            root.after(duration // 2, restore)
    
    root.after(0, update)

def fill_with_difficulty():
    """播种 - 生成数独"""
    if SudokuGenerator is None:
        messagebox.showerror("错误", "播种机未加载!")
        return
    
    level = difficulty_var.get()
    difficulty_map = {"简单": "Easy", "中等": "Medium", "困难": "Hard"}
    target_difficulty = difficulty_map.get(level, "Medium")
    
    def generate_with_animation():
        disable_buttons()
        perf_labels['status'].config(text=f"🌱 正在播种{level}作物...", fg=THEME["warning"])
        
        try:
            for row in range(9):
                for col in range(9):
                    entry = sudoku_entries[row][col]
                    entry.config(state="normal")
                    entry.delete(0, tk.END)
            
            generator = SudokuGenerator()
            puzzle, info = generator.generate_puzzle_with_difficulty(
                target_difficulty=target_difficulty,
                symmetric=True,
                max_retries=20
            )
            
            global original_puzzle
            for r in range(9):
                for c in range(9):
                    original_puzzle[r][c] = puzzle[r][c]
            
            if animate_var.get():
                cells = [(r, c, puzzle[r][c]) for r in range(9) for c in range(9) if puzzle[r][c] != 0]
                random.shuffle(cells)
                
                interval, _ = get_speed_params()
                delay = max(interval // 10, 30)
                
                def schedule_animation(idx, row, col, val):
                    root.after(idx * delay, lambda: animate_generation_step(row, col, val, "fill"))
                
                for idx, (r, c, val) in enumerate(cells):
                    schedule_animation(idx, r, c, val)
                
                final_info = info
                root.after(len(cells) * delay + 500, lambda: [
                    perf_labels['status'].config(
                        text=f"🌻 播种完成! 难度:{final_info['level']} 种子:{final_info['clues']}",
                        fg=THEME["success"]),
                    enable_buttons()
                ])
            else:
                fill_sudoku(puzzle, is_initial=True)
                perf_labels['status'].config(
                    text=f"🌻 播种完成! 难度:{info['level']} 种子:{info['clues']}",
                    fg=THEME["success"])
                enable_buttons()
                
        except Exception as e:
            messagebox.showerror("播种失败", str(e))
            enable_buttons()
    
    threading.Thread(target=generate_with_animation, daemon=True).start()

# ==================== 求解动画（收获动画）====================
def animation_fill_cell(row, col, value, is_try=True):
    if not animate_var.get():
        entry = sudoku_entries[row][col]
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, str(value))
        if not is_try:
            entry.config(fg=THEME["text_dark"])
        return
    
    entry = sudoku_entries[row][col]
    interval, duration = get_speed_params()
    
    entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, str(value))
    
    if is_try:
        entry.config(bg=THEME["anim_water"], fg=THEME["text_dark"])
        
        parent_id = search_tree_viz.get_current_parent_id()
        search_tree_viz.add_node(row, col, value, parent_id)
        
        root.update_idletasks()
        time.sleep(interval / 1000.0)
    else:
        entry.config(fg=THEME["text_dark"])
        block_row, block_col = row // 3, col // 3
        bg_color = THEME["field_light"] if (block_row + block_col) % 2 == 0 else THEME["field_dark"]
        entry.config(bg=bg_color)

def animation_backtrack_cell(row, col):
    if not animate_var.get():
        entry = sudoku_entries[row][col]
        entry.config(state="normal")
        entry.delete(0, tk.END)
        return
    
    entry = sudoku_entries[row][col]
    interval, duration = get_speed_params()
    
    entry.config(state="normal", bg=THEME["anim_wither"])
    entry.delete(0, tk.END)
    entry.insert(0, "✗")
    entry.config(fg=THEME["error"])
    
    search_tree_viz.backtrack_node()
    
    root.update_idletasks()
    time.sleep(max(duration / 1000.0, 0.1))
    
    entry.delete(0, tk.END)
    block_row, block_col = row // 3, col // 3
    bg_color = THEME["field_light"] if (block_row + block_col) % 2 == 0 else THEME["field_dark"]
    entry.config(bg=bg_color, fg=THEME["text_dark"])
    root.update_idletasks()

def animation_ac3_prune_cell(row, col, value):
    if not animate_var.get():
        return
    
    entry = sudoku_entries[row][col]
    interval, _ = get_speed_params()
    
    entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, str(value))
    entry.config(fg=THEME["text_red"], font=("Courier New", 10, "italic"))
    root.update_idletasks()
    
    time.sleep(max(interval / 3000.0, 0.05))
    
    entry.delete(0, tk.END)
    entry.config(font=("Courier New", 14, "bold"))
    root.update_idletasks()

def solve_sudoku():
    """开始收获 - 求解数独"""
    global is_animating
    
    selected_alg = algorithm_var.get()
    sudoku_data = read_sudoku()
    
    if all(value == 0 for row in sudoku_data for value in row):
        perf_labels['status'].config(text="🌱 请先播种!", fg=THEME["error"])
        return
    
    disable_buttons()
    is_animating = animate_var.get()
    perf_labels['algorithm'].config(text=selected_alg)
    perf_labels['status'].config(text="🌾 收获中...", fg=THEME["warning"])
    
    search_tree_viz.clear()
    
    def run_solver():
        try:
            puzzle = deepcopy(sudoku_data)
            
            if selected_alg == "基础DFS算法":
                if BasicSolver is None:
                    raise ImportError("基础工具未加载")
                solver = BasicSolver()
                solver.set_animation_callbacks(
                    fill_cb=animation_fill_cell,
                    backtrack_cb=animation_backtrack_cell)
                solution = solver.solve(puzzle)
                
            elif selected_alg == "MRV+LCV算法":
                if MRVLCVSolver is None:
                    raise ImportError("MRV+LCV工具未加载")
                solver = MRVLCVSolver()
                solver.set_animation_callbacks(
                    fill_cb=animation_fill_cell,
                    backtrack_cb=animation_backtrack_cell)
                solution = solver.solve(puzzle)
                
            elif selected_alg == "AC3+MRV+LCV算法":
                if AC3_MRV_LCV_Solver is None:
                    raise ImportError("AC3+MRV+LCV工具未加载")
                solver = AC3_MRV_LCV_Solver()
                solver.set_animation_callbacks(
                    fill_cb=animation_fill_cell,
                    backtrack_cb=animation_backtrack_cell,
                    ac3_prune_cb=animation_ac3_prune_cell)
                solution = solver.solve(puzzle)
            else:
                raise ValueError(f"未知工具: {selected_alg}")
            
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
            root.after(0, lambda: messagebox.showerror("收获失败", str(e)))
            root.after(0, lambda: perf_labels['status'].config(text="💀 出错了!", fg=THEME["error"]))
            root.after(0, enable_buttons)
    
    threading.Thread(target=run_solver, daemon=True).start()

def finish_solve(success, result_board, final_perf):
    global is_animating
    is_animating = False
    
    update_performance(final_perf)
    
    if success:
        search_tree_viz.mark_success_path()
        perf_labels['status'].config(text="🌾 丰收啦!", fg=THEME["success"])
    else:
        perf_labels['status'].config(text="💀 歉收...", fg=THEME["error"])
    
    enable_buttons()


# ==================== 算法对比 ====================
performance_data = {
    "基础DFS": {"time": 0, "nodes": 0, "backtracks": 0},
    "MRV+LCV": {"time": 0, "nodes": 0, "backtracks": 0},
    "AC3+MRV+LCV": {"time": 0, "nodes": 0, "backtracks": 0},
}

def compare_algorithms():
    """工具对比"""
    sudoku_data = read_sudoku()
    
    if all(value == 0 for row in sudoku_data for value in row):
        messagebox.showwarning("提示", "🌱 请先播种!")
        return
    
    disable_buttons()
    perf_labels['status'].config(text="🔧 对比工具中...", fg=THEME["warning"])
    
    def run_comparison():
        try:
            if BasicSolver:
                puzzle = deepcopy(sudoku_data)
                solver = BasicSolver()
                solver.solve(puzzle)
                actual_time = solver.stats.pure_solve_time if hasattr(solver.stats, 'pure_solve_time') else solver.stats.solve_time
                performance_data["基础DFS"]["time"] = actual_time
                performance_data["基础DFS"]["nodes"] = solver.stats.nodes
                performance_data["基础DFS"]["backtracks"] = solver.stats.backtracks
            
            if MRVLCVSolver:
                puzzle = deepcopy(sudoku_data)
                solver = MRVLCVSolver()
                solver.solve(puzzle)
                actual_time = solver.stats.pure_solve_time if hasattr(solver.stats, 'pure_solve_time') else solver.stats.solve_time
                performance_data["MRV+LCV"]["time"] = actual_time
                performance_data["MRV+LCV"]["nodes"] = solver.stats.nodes
                performance_data["MRV+LCV"]["backtracks"] = solver.stats.backtracks
            
            if AC3_MRV_LCV_Solver:
                puzzle = deepcopy(sudoku_data)
                solver = AC3_MRV_LCV_Solver()
                solver.solve(puzzle)
                actual_time = solver.stats.pure_solve_time if hasattr(solver.stats, 'pure_solve_time') else solver.stats.solve_time
                performance_data["AC3+MRV+LCV"]["time"] = actual_time
                performance_data["AC3+MRV+LCV"]["nodes"] = solver.stats.nodes
                performance_data["AC3+MRV+LCV"]["backtracks"] = solver.stats.backtracks
            
            root.after(0, lambda: [
                show_chart(),
                perf_labels['status'].config(text="📊 对比完成!", fg=THEME["success"])
            ])
            
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("对比失败", str(e)))
        finally:
            root.after(0, enable_buttons)
    
    threading.Thread(target=run_comparison, daemon=True).start()

# ==================== 统计图表（农场风格）====================
def show_chart():
    """显示农场风格统计图表"""
    has_data = any(performance_data[alg]["nodes"] > 0 for alg in performance_data)
    
    if not has_data:
        messagebox.showinfo("提示", "请先运行工具对比!")
        return
    
    chart_window = tk.Toplevel(root)
    chart_window.title("农场工具对比报告")
    chart_window.geometry("1000x700")
    chart_window.configure(bg=THEME["bg_panel"])
    
    # 顶部区域（标题 + 说明框）
    top_area = tk.Frame(chart_window, bg=THEME["bg_panel"])
    top_area.pack(fill=tk.X, padx=20, pady=10)
    
    # 标题
    title = tk.Label(top_area,
        text="农场工具效率对比 Tool Comparison",
        font=("Courier New", 16, "bold"),
        bg=THEME["bg_panel"], fg=THEME["primary"])
    title.pack(side=tk.LEFT, padx=20)
    
    # 右上角说明框
    legend_frame = tk.Frame(top_area, bg=THEME["bg_panel_dark"], 
        relief="ridge", bd=2, padx=10, pady=8)
    legend_frame.pack(side=tk.RIGHT, padx=10)
    
    legend_title = tk.Label(legend_frame, text="术语对照",
        font=("Courier New", 9, "bold"),
        bg=THEME["bg_panel_dark"], fg=THEME["primary"])
    legend_title.pack(anchor="w")
    
    legend_items = [
        ("收获时间", "算法实际执行时间"),
        ("种植数", "搜索节点数"),
        ("重种数", "回溯次数")
    ]
    for farm_term, tech_term in legend_items:
        item_frame = tk.Frame(legend_frame, bg=THEME["bg_panel_dark"])
        item_frame.pack(anchor="w", pady=1)
        tk.Label(item_frame, text=f"{farm_term}", 
            font=("Courier New", 8, "bold"),
            bg=THEME["bg_panel_dark"], fg=THEME["text_gold"]).pack(side=tk.LEFT)
        tk.Label(item_frame, text=f" → {tech_term}", 
            font=("Courier New", 8),
            bg=THEME["bg_panel_dark"], fg=THEME["text_dark"]).pack(side=tk.LEFT)
    
    algorithms = ["基础DFS", "MRV+LCV", "AC3+MRV+LCV"]
    times = [performance_data[alg]["time"] for alg in algorithms]
    nodes = [performance_data[alg]["nodes"] for alg in algorithms]
    backtracks = [performance_data[alg]["backtracks"] for alg in algorithms]
    
    # 统一的颜色方案
    bar_colors = ["#8B4513", "#228B22", "#FF6B35"]  # 棕色、绿色、橙色
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor(THEME["bg_panel"])
    
    # 图表1：执行时间对比
    bars1 = ax1.bar(algorithms, times, color=bar_colors, edgecolor=THEME["border_dark"], linewidth=2)
    ax1.set_ylabel('收获时间 (秒)', fontsize=12, color=THEME["text_dark"])
    ax1.set_title('收获时间对比', fontsize=14, fontweight='bold', color=THEME["primary"])
    ax1.tick_params(colors=THEME["text_dark"])
    ax1.set_facecolor(THEME["bg_panel"])
    ax1.grid(axis='y', alpha=0.3, color=THEME["border_light"])
    
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}s', ha='center', va='bottom',
                fontsize=10, fontweight='bold', color=THEME["text_dark"])
    
    # 图表2：种植数和重种数（使用统一颜色）
    x = range(len(algorithms))
    width = 0.35
    bars2 = ax2.bar([i - width/2 for i in x], nodes, width,
                    label='种植数', color=bar_colors)
    bars3 = ax2.bar([i + width/2 for i in x], backtracks, width,
                    label='重种数', color=[c + "80" for c in bar_colors])  # 稍浅的颜色
    
    # 为重种数使用对应的浅色
    for i, bar in enumerate(bars3):
        bar.set_color(bar_colors[i])
        bar.set_alpha(0.5)
    
    ax2.set_ylabel('数量', fontsize=12, color=THEME["text_dark"])
    ax2.set_title('种植统计', fontsize=14, fontweight='bold', color=THEME["primary"])
    ax2.set_xticks(x)
    ax2.set_xticklabels(algorithms)
    ax2.tick_params(colors=THEME["text_dark"])
    ax2.set_facecolor(THEME["bg_panel"])
    ax2.legend(facecolor=THEME["bg_panel"], edgecolor=THEME["border_dark"], 
               labelcolor=THEME["text_dark"])
    ax2.grid(axis='y', alpha=0.3, color=THEME["border_light"])
    
    plt.tight_layout()
    
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    # 底部漂浮装饰区域
    deco_frame = tk.Frame(chart_window, bg=THEME["bg_panel"], height=60)
    deco_frame.pack(fill=tk.X, pady=5)
    deco_frame.pack_propagate(False)
    
    # 创建漂浮的小图标
    floating_icons = ["🐔", "🌻", "🐷", "🌾", "🐮", "🌽", "🐑"]
    icon_labels = []
    
    for i, icon in enumerate(floating_icons):
        label = tk.Label(deco_frame, text=icon, font=("Arial", 18), bg=THEME["bg_panel"])
        # 初始位置分散在底部
        x_pos = 80 + i * 120
        label.place(x=x_pos, y=20)
        icon_labels.append({"label": label, "x": x_pos, "y": 20, "direction": 1 if i % 2 == 0 else -1})
    
    # 漂浮动画函数
    def float_animation():
        if not chart_window.winfo_exists():
            return
        for item in icon_labels:
            # 上下漂浮
            item["y"] += item["direction"] * 2
            if item["y"] > 35:
                item["direction"] = -1
            elif item["y"] < 5:
                item["direction"] = 1
            item["label"].place(x=item["x"], y=item["y"])
        chart_window.after(100, float_animation)
    
    # 启动漂浮动画
    float_animation()

# ==================== 底部装饰栏 ====================
bottom_frame = tk.Frame(root, bg=THEME["bg_dirt"], height=30)
bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
bottom_frame.pack_propagate(False)

# 装饰元素
deco_text = tk.Label(bottom_frame,
    text="🌾🌻🌽🥕🍅🥬🌾  Happy Farming!  🌾🥬🍅🥕🌽🌻🌾",
    font=("Arial", 12),
    bg=THEME["bg_dirt"], fg=THEME["text_dark"])
deco_text.pack(pady=5)

# ==================== 启动应用 ====================
if __name__ == "__main__":
    print("🌾 数独农场启动中... Sudoku Farm Loading...")
    print("🌻 欢迎来到数独农场! Welcome to Sudoku Farm!")
    root.mainloop()
