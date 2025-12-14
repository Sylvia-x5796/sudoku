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

plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置为黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
# ---------------------- 修复导入路径 ----------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------------------- 导入算法和生成器 ----------------------
try:
    from src.algorithms.solver_basic_v1 import SudokuSolver as BasicSolver
    from src.algorithms.solver_mrv_lcv import MRVLCVSolver
    from src.algorithms.solver_ac3_mrv_lcv import AC3_MRV_LCV_Solver
    from src.generator.sudoku_generator import SudokuGenerator

    print("✓ 算法和生成器加载成功")
except ImportError as e:
    print(f"✗ 警告：导入算法或生成器失败 - {e}")
    BasicSolver = None
    MRVLCVSolver = None
    AC3_MRV_LCV_Solver = None
    SudokuGenerator = None

# ---------------------- 1. 初始化主窗口 + 全局样式配置（核心修复）----------------------
root = tk.Tk()
root.title("数独求解可视化工具 - V5.0（布局优化版）")
root.geometry("1200x800")
root.resizable(False, False)

# 统一配置所有ttk组件样式（解决font参数报错问题）
style = ttk.Style(root)

# 1. 大按钮样式（功能按钮）
style.configure(
    "Large.TButton",
    font=("Arial", 12, "bold"),
    padding=(15, 8)  # 按钮内边距：左右15px，上下8px
)

# 2. 普通标签样式（难度/算法标签、统计项标签）
style.configure(
    "Normal.TLabel",
    font=("Arial", 11)
)

# 3. 复选框样式（动态填数动画开关）
style.configure(
    "Normal.TCheckbutton",
    font=("Arial", 11)
)

# 4. 下拉框样式（难度/算法选择）
style.configure(
    "Normal.TCombobox",
    font=("Arial", 11)
)

# 5. 标签框架样式（搜索树、统计区标题）
style.configure(
    "Title.TLabelframe",
    font=("Arial", 11)
)
style.configure(
    "Title.TLabelframe.Label",
    font=("Arial", 11)  # LabelFrame标题文字样式
)

# ---------------------- 2. 顶部功能栏（拆分为两排）----------------------
# 顶部总容器
top_container = ttk.Frame(root, padding="10")
top_container.pack(fill=tk.X, side=tk.TOP)

# 第一排：难度选择、算法选择、动画开关
top_frame1 = ttk.Frame(top_container)
top_frame1.pack(fill=tk.X, side=tk.TOP, pady=(0, 8))

# 难度选择（使用样式替代直接font参数）
difficulty_label = ttk.Label(top_frame1, text="难度：", style="Normal.TLabel")
difficulty_label.pack(side=tk.LEFT, padx=8)
difficulty_var = tk.StringVar(value="中等")
difficulty_options = ["简单", "中等", "困难"]
difficulty_menu = ttk.Combobox(
    top_frame1,
    textvariable=difficulty_var,
    values=difficulty_options,
    state="readonly",
    width=10,
    style="Normal.TCombobox"  # 应用下拉框样式
)
difficulty_menu.pack(side=tk.LEFT, padx=8)

# 算法选择（使用样式替代直接font参数）
alg_label = ttk.Label(top_frame1, text="算法：", style="Normal.TLabel")
alg_label.pack(side=tk.LEFT, padx=8)
algorithm_var = tk.StringVar(value="请选择算法")
alg_options = ["基础DFS算法", "MRV+LCV算法", "AC3+MRV+LCV算法"]
alg_menu = ttk.Combobox(
    top_frame1,
    textvariable=algorithm_var,
    values=alg_options,
    state="readonly",
    width=18,
    style="Normal.TCombobox"  # 应用下拉框样式
)
alg_menu.pack(side=tk.LEFT, padx=8)

# 动态填数动画开关（核心修复：移除font参数，改用style）
animate_var = tk.BooleanVar(value=True)
animate_check = ttk.Checkbutton(
    top_frame1,
    text="动态填数动画",
    variable=animate_var,
    style="Normal.TCheckbutton"  # 应用复选框样式
)
animate_check.pack(side=tk.LEFT, padx=15)

# 第二排：功能按钮（超大尺寸，应用自定义样式）
top_frame2 = ttk.Frame(top_container)
top_frame2.pack(fill=tk.X, side=tk.TOP)

# 功能按钮 - 应用Large.TButton样式，宽度大幅增加，间距加大
clear_btn = ttk.Button(
    top_frame2,
    text="清空",
    command=lambda: clear_sudoku(),
    width=18,
    style="Large.TButton"
)
clear_btn.pack(side=tk.LEFT, padx=10)

fill_btn = ttk.Button(
    top_frame2,
    text="生成数独",
    command=lambda: fill_with_difficulty(),
    width=22,
    style="Large.TButton"
)
fill_btn.pack(side=tk.LEFT, padx=10)

solve_btn = ttk.Button(
    top_frame2,
    text="开始求解",
    command=lambda: solve_sudoku(),
    width=22,
    style="Large.TButton"
)
solve_btn.pack(side=tk.LEFT, padx=10)

compare_btn = ttk.Button(
    top_frame2,
    text="对比所有算法",
    command=lambda: compare_algorithms(),
    width=25,
    style="Large.TButton"
)
compare_btn.pack(side=tk.LEFT, padx=10)

# ---------------------- 3. 中间主体区域（网格+搜索树）----------------------
main_body = ttk.Frame(root, padding="10")
main_body.pack(fill=tk.BOTH, expand=True)

# 数独网格容器（左侧）
grid_frame = ttk.Frame(main_body, padding="10")
grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

sudoku_entries = [[None for _ in range(9)] for _ in range(9)]
cell_colors = []
for row in range(9):
    row_colors = []
    for col in range(9):
        row_colors.append("#f0f0f0" if (row // 3 + col // 3) % 2 == 0 else "#ffffff")
    cell_colors.append(row_colors)

for row in range(9):
    for col in range(9):
        entry = tk.Entry(
            grid_frame,
            width=3,
            font=("Arial", 16, "bold"),
            justify=tk.CENTER,
            state="normal"
        )
        entry.grid(
            row=row, column=col,
            padx=1 if (col + 1) % 3 != 0 else 3,
            pady=1 if (row + 1) % 3 != 0 else 3,
            sticky="nsew"
        )
        entry.config(background=cell_colors[row][col])
        sudoku_entries[row][col] = entry

for row in range(9):
    grid_frame.grid_rowconfigure(row, weight=1)
for col in range(9):
    grid_frame.grid_columnconfigure(col, weight=1)

# 搜索树可视化区域（右侧）- 核心修复：移除font参数，改用style
search_tree_frame = ttk.LabelFrame(
    main_body,
    text="搜索树可视化",
    padding="10",
    style="Title.TLabelframe"  # 应用LabelFrame样式
)
search_tree_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

# 搜索树占位（后续可替换为真实可视化组件）
tree_canvas = tk.Canvas(search_tree_frame, bg="#f8f8f8", bd=1, relief=tk.SUNKEN)
tree_canvas.pack(fill=tk.BOTH, expand=True)
tree_placeholder = ttk.Label(
    search_tree_frame,
    text="搜索过程可视化\n（算法运行时动态更新）",
    style="Normal.TLabel",  # 应用普通标签样式
    foreground="#666"
)
tree_placeholder.pack(expand=True)

# ---------------------- 4. 底部统计区域 ----------------------
# 核心修复：移除font参数，改用style
stats_frame = ttk.LabelFrame(
    root,
    text="算法性能统计",
    padding="10",
    style="Title.TLabelframe"
)
stats_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 10))

# 统计控制栏（图表显示按钮）
stats_control = ttk.Frame(stats_frame)
stats_control.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))
chart_btn = ttk.Button(
    stats_control,
    text="显示统计图表",
    command=lambda: show_chart(),
    style="Large.TButton",
    width=15
)
chart_btn.pack(side=tk.RIGHT, padx=5)

# 统计内容区域（左右分栏：单个算法+对比结果）
stats_content = ttk.Frame(stats_frame)
stats_content.pack(fill=tk.BOTH, expand=True)

# 单个算法统计（左侧）
single_stats = ttk.Frame(stats_content)
single_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

perf_labels = {}
metrics = [
    ("algorithm", "算法名称：", "未运行"),
    ("time", "执行时间：", "0.000 秒"),
    ("nodes", "搜索节点数：", "0"),
    ("backtracks", "回溯次数：", "0"),
    ("status", "求解状态：", "待求解")
]
for i, (key, label_text, default_value) in enumerate(metrics):
    row_frame = ttk.Frame(single_stats)
    row_frame.pack(fill=tk.X, pady=3)
    # 应用普通标签样式
    label = ttk.Label(row_frame, text=label_text, style="Normal.TLabel")
    label.pack(side=tk.LEFT)
    # 自定义值标签字体（tk.Label支持直接font参数）
    value_label = tk.Label(
        row_frame,
        text=default_value,
        font=("Arial", 11, "bold"),
        foreground="#0066cc"
    )
    value_label.pack(side=tk.LEFT, padx=5)
    perf_labels[key] = value_label

# 算法对比统计（右侧）- 核心修复：移除font参数，改用style
compare_stats = ttk.LabelFrame(
    stats_content,
    text="算法对比结果",
    style="Title.TLabelframe"
)
compare_stats.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

# tk.Text支持直接font参数
compare_text = tk.Text(
    compare_stats,
    font=("Arial", 11),
    width=40,
    height=6
)
compare_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
compare_text.insert(tk.END, "点击「对比所有算法」按钮查看结果...")
compare_text.config(state="disabled")


# ---------------------- 核心数据处理函数（完全不变）----------------------
def fill_sudoku(sudoku_data):
    disable_buttons()
    for row in range(9):
        for col in range(9):
            value = sudoku_data[row][col]
            entry = sudoku_entries[row][col]
            entry.config(state="normal")
            entry.delete(0, tk.END)
            if value != 0:
                entry.insert(0, str(value))
            entry.config(state="readonly" if (is_animating or animate_var.get()) else "normal")
    enable_buttons()


def clear_sudoku():
    disable_buttons()
    empty_data = [[0 for _ in range(9)] for _ in range(9)]
    fill_sudoku(empty_data)
    update_performance(None)
    # 清空对比结果
    compare_text.config(state="normal")
    compare_text.delete(1.0, tk.END)
    compare_text.insert(tk.END, "点击「对比所有算法」按钮查看结果...")
    compare_text.config(state="disabled")
    enable_buttons()


def read_sudoku():
    sudoku_data = [[0 for _ in range(9)] for _ in range(9)]
    for row in range(9):
        for col in range(9):
            value = sudoku_entries[row][col].get().strip()
            if value.isdigit() and 1 <= int(value) <= 9:
                sudoku_data[row][col] = int(value)
            else:
                sudoku_data[row][col] = 0
    return sudoku_data


# ---------------------- 数独题库（完全不变）----------------------
sample_sudoku = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9]
]
easy_puzzles = [
    [
        [0, 0, 0, 2, 6, 0, 7, 0, 1],
        [6, 8, 0, 0, 7, 0, 0, 9, 0],
        [1, 9, 0, 0, 0, 4, 5, 0, 0],
        [8, 2, 0, 1, 0, 0, 0, 4, 0],
        [0, 0, 4, 6, 0, 2, 9, 0, 0],
        [0, 5, 0, 0, 0, 3, 0, 2, 8],
        [0, 0, 9, 3, 0, 0, 0, 7, 4],
        [0, 4, 0, 0, 5, 0, 0, 3, 6],
        [7, 0, 3, 0, 1, 8, 0, 0, 0]
    ],
    [
        [0, 2, 0, 6, 0, 8, 0, 0, 0],
        [5, 8, 0, 0, 0, 9, 7, 0, 0],
        [0, 0, 0, 0, 4, 0, 0, 0, 0],
        [3, 7, 0, 0, 0, 0, 5, 0, 0],
        [6, 0, 0, 0, 0, 0, 0, 0, 4],
        [0, 0, 8, 0, 0, 0, 0, 1, 3],
        [0, 0, 0, 0, 2, 0, 0, 0, 0],
        [0, 0, 9, 8, 0, 0, 0, 3, 6],
        [0, 0, 0, 3, 0, 6, 0, 9, 0]
    ]
]
medium_puzzles = [
    sample_sudoku,
    [
        [0, 0, 6, 0, 0, 0, 0, 3, 0],
        [0, 0, 0, 0, 9, 0, 0, 0, 1],
        [0, 9, 0, 0, 5, 0, 0, 0, 8],
        [0, 0, 0, 2, 0, 0, 6, 0, 0],
        [2, 0, 0, 0, 0, 0, 0, 0, 7],
        [0, 0, 5, 0, 0, 3, 0, 0, 0],
        [6, 0, 0, 0, 1, 0, 0, 5, 0],
        [4, 0, 0, 0, 8, 0, 0, 0, 0],
        [0, 7, 0, 0, 0, 0, 3, 0, 0]
    ]
]
hard_puzzles = [
    [
        [0, 0, 0, 0, 0, 0, 0, 1, 2],
        [0, 0, 0, 0, 3, 5, 0, 0, 0],
        [0, 0, 0, 7, 0, 0, 0, 0, 0],
        [0, 0, 8, 0, 0, 0, 0, 2, 0],
        [0, 7, 0, 0, 0, 0, 0, 8, 0],
        [0, 3, 0, 0, 0, 0, 6, 0, 0],
        [0, 0, 0, 0, 0, 9, 0, 0, 0],
        [0, 0, 0, 4, 6, 0, 0, 0, 0],
        [5, 1, 0, 0, 0, 0, 0, 0, 0]
    ],
    [
        [0, 0, 0, 0, 0, 0, 2, 0, 0],
        [0, 8, 0, 0, 0, 7, 0, 9, 0],
        [6, 0, 2, 0, 0, 0, 0, 0, 0],
        [0, 7, 0, 0, 6, 0, 0, 0, 0],
        [0, 0, 0, 9, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 2, 0, 0, 4, 0],
        [0, 0, 0, 0, 0, 0, 7, 0, 3],
        [0, 5, 0, 1, 0, 0, 0, 2, 0],
        [0, 0, 6, 0, 0, 0, 0, 0, 0]
    ]
]


def get_puzzle_by_difficulty(level: str):
    if level == "简单":
        pool = easy_puzzles
    elif level == "中等":
        pool = medium_puzzles
    elif level == "困难":
        pool = hard_puzzles
    else:
        pool = [sample_sudoku]
    return random.choice(pool)


# ---------------------- 动画模块（完全不变）----------------------
def animate_cell_color(entry, start_color, end_color, duration=200):
    steps = 20
    step_duration = duration // steps

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    start_r, start_g, start_b = hex_to_rgb(start_color)
    end_r, end_g, end_b = hex_to_rgb(end_color)

    delta_r = (end_r - start_r) / steps
    delta_g = (end_g - start_g) / steps
    delta_b = (end_b - start_b) / steps

    def update_step(step):
        if step > steps:
            entry.config(background=end_color)
            return
        current_r = int(start_r + delta_r * step)
        current_g = int(start_g + delta_g * step)
        current_b = int(start_b + delta_b * step)
        current_color = f"#{current_r:02x}{current_g:02x}{current_b:02x}"
        entry.config(background=current_color)
        entry.after(step_duration, update_step, step + 1)

    update_step(1)


def animate_number_fill(entry, value, duration=300):
    entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, value)
    entry.config(foreground=entry["background"])

    steps = 15
    step_duration = duration // steps
    start_r, start_g, start_b = 240, 240, 240
    end_r, end_g, end_b = 0, 0, 0

    def update_step(step):
        if step > steps:
            entry.config(foreground="#000000")
            entry.config(state="readonly" if (is_animating or animate_var.get()) else "normal")
            return
        current_r = int(start_r - (start_r - end_r) * (step / steps))
        current_g = int(start_g - (start_g - end_g) * (step / steps))
        current_b = int(start_b - (start_b - end_b) * (step / steps))
        current_color = f"#{current_r:02x}{current_g:02x}{current_b:02x}"
        entry.config(foreground=current_color)
        entry.after(step_duration, update_step, step + 1)

    update_step(1)


def animate_backtrack(entry, duration=200):
    original_color = entry["background"]
    animate_cell_color(entry, original_color, "#ffb6c1", duration=duration // 2)

    def clear_after_highlight():
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.config(state="readonly" if (is_animating or animate_var.get()) else "normal")
        animate_cell_color(entry, "#ffb6c1", original_color, duration=duration // 2)

    entry.after(duration // 2, clear_after_highlight)


# ---------------------- 核心动画接口（完全不变）----------------------
def animation_fill_cell(row, col, value):
    if not (0 <= row < 9 and 0 <= col < 9):
        print("无效的单元格坐标")
        return
    entry = sudoku_entries[row][col]
    add_animation_to_queue(animate_number_fill, entry, str(value), 300)


def animation_single_fill(row, col, value):
    if not (0 <= row < 9 and 0 <= col < 9):
        print("无效的单元格坐标")
        return
    entry = sudoku_entries[row][col]
    add_animation_to_queue(animate_number_fill, entry, str(value), 200)


def animation_backtrack_cell(row, col):
    if not (0 <= row < 9 and 0 <= col < 9):
        print("无效的单元格坐标")
        return
    entry = sudoku_entries[row][col]
    add_animation_to_queue(animate_backtrack, entry, 200)


# ---------------------- 动画队列（完全不变）----------------------
animation_queue = []
is_animating = False


def add_animation_to_queue(anim_func, *args):
    animation_queue.append((anim_func, args))
    if not is_animating and animate_var.get():
        run_next_animation()


def run_next_animation():
    global is_animating
    if not animation_queue or not animate_var.get():
        is_animating = False
        return
    is_animating = True
    anim_func, args = animation_queue.pop(0)
    anim_func(*args)
    root.after(350, run_next_animation)


# ---------------------- 按钮状态控制（完全不变）----------------------
def disable_buttons():
    fill_btn.config(state="disabled")
    clear_btn.config(state="disabled")
    solve_btn.config(state="disabled")
    compare_btn.config(state="disabled")
    difficulty_menu.config(state="disabled")
    alg_menu.config(state="disabled")
    animate_check.config(state="disabled")
    chart_btn.config(state="disabled")
    for row in range(9):
        for col in range(9):
            sudoku_entries[row][col].config(state="readonly")


def enable_buttons():
    fill_btn.config(state="normal")
    clear_btn.config(state="normal")
    solve_btn.config(state="normal")
    compare_btn.config(state="normal")
    difficulty_menu.config(state="readonly")
    alg_menu.config(state="readonly")
    animate_check.config(state="normal")
    chart_btn.config(state="normal")
    for row in range(9):
        for col in range(9):
            sudoku_entries[row][col].config(state="normal")


# ---------------------- 生成数独函数（完全不变）----------------------
def fill_with_difficulty():
    if SudokuGenerator is None:
        messagebox.showerror("错误", "数独生成器未加载")
        return

    level = difficulty_var.get()
    difficulty_map = {"简单": "Easy", "中等": "Medium", "困难": "Hard"}
    target_difficulty = difficulty_map.get(level, "Medium")

    def generate_in_thread():
        disable_buttons()
        perf_labels['status'].config(text=f"正在生成{level}数独...", foreground="#ff9900")

        try:
            generator = SudokuGenerator()
            puzzle, info = generator.generate_puzzle_with_difficulty(
                target_difficulty=target_difficulty,
                symmetric=True,
                max_retries=20
            )
            root.after(0, lambda: fill_sudoku(puzzle))
            root.after(0, lambda: perf_labels['status'].config(
                text=f"已生成 {info['level']} 难度（提示数:{info['clues']}）",
                foreground="#0066cc"
            ))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("生成失败", str(e)))
        finally:
            root.after(0, enable_buttons)

    threading.Thread(target=generate_in_thread, daemon=True).start()


# ---------------------- 性能统计更新（微调：适配新布局）----------------------
def update_performance(perf_data):
    if perf_data is None:
        perf_labels['algorithm'].config(text="未运行")
        perf_labels['time'].config(text="0.000 秒")
        perf_labels['nodes'].config(text="0")
        perf_labels['backtracks'].config(text="0")
        perf_labels['status'].config(text="待求解", foreground="#666666")
    else:
        perf_labels['algorithm'].config(text=perf_data.get('algorithm', '未知'))
        perf_labels['time'].config(text=f"{perf_data.get('time', 0):.3f} 秒")
        perf_labels['nodes'].config(text=str(perf_data.get('nodes', 0)))
        perf_labels['backtracks'].config(text=str(perf_data.get('backtracks', 0)))
        status = perf_data.get('status', '未知')
        if status == '成功':
            perf_labels['status'].config(text=status, foreground="#00aa00")
        elif status == '失败':
            perf_labels['status'].config(text=status, foreground="#cc0000")
        else:
            perf_labels['status'].config(text=status, foreground="#666666")


def update_perf_real_time(nodes, backtracks):
    perf_labels['nodes'].config(text=str(nodes))
    perf_labels['backtracks'].config(text=str(backtracks))
    if 'solve_start_time' in globals():
        elapsed_time = time.time() - solve_start_time
        perf_labels['time'].config(text=f"{elapsed_time:.3f} 秒")


# ---------------------- 统计图表显示（占位函数）----------------------
def show_chart():
    messagebox.showinfo("图表功能", "统计图表功能将在后续版本实现\n当前已显示核心统计数据")


# ---------------------- 求解函数（微调：适配动画开关）----------------------
def solve_sudoku():
    global solve_start_time, is_animating
    selected_alg = algorithm_var.get()

    if selected_alg == "请选择算法":
        perf_labels['status'].config(text="请先选择算法", foreground="#cc0000")
        return

    sudoku_data = read_sudoku()
    if all(value == 0 for row in sudoku_data for value in row):
        perf_labels['status'].config(text="请输入或生成数独", foreground="#cc0000")
        return

    disable_buttons()
    is_animating = animate_var.get()
    animation_queue.clear()
    perf_labels['algorithm'].config(text=selected_alg)
    perf_labels['nodes'].config(text="0")
    perf_labels['backtracks'].config(text="0")
    perf_labels['time'].config(text="0.000 秒")
    perf_labels['status'].config(text="求解中...", foreground="#ff9900")

    def run_solver():
        try:
            start_time = time.time()
            puzzle = deepcopy(sudoku_data)

            if selected_alg == "基础DFS算法":
                if BasicSolver is None:
                    raise ImportError("基础DFS算法未加载")
                solver = BasicSolver()
                solution = solver.solve(puzzle)
                final_perf = {
                    'algorithm': selected_alg,
                    'time': solver.stats.solve_time,
                    'nodes': solver.stats.nodes,
                    'backtracks': solver.stats.backtracks,
                    'status': '成功' if solution else '失败'
                }
                root.after(0, finish_solve, solution is not None, solution, final_perf)

            elif selected_alg == "MRV+LCV算法":
                if MRVLCVSolver is None:
                    raise ImportError("MRV+LCV算法未加载")
                solver = MRVLCVSolver()
                solution = solver.solve(puzzle)
                final_perf = {
                    'algorithm': selected_alg,
                    'time': solver.stats.solve_time,
                    'nodes': solver.stats.nodes,
                    'backtracks': solver.stats.backtracks,
                    'status': '成功' if solution else '失败'
                }
                root.after(0, finish_solve, solution is not None, solution, final_perf)

            elif selected_alg == "AC3+MRV+LCV算法":
                if AC3_MRV_LCV_Solver is None:
                    raise ImportError("AC3+MRV+LCV算法未加载")
                solver = AC3_MRV_LCV_Solver()
                solution = solver.solve(puzzle)
                final_perf = {
                    'algorithm': selected_alg,
                    'time': solver.stats.solve_time,
                    'nodes': solver.stats.nodes,
                    'backtracks': solver.stats.backtracks,
                    'status': '成功' if solution else '失败'
                }
                root.after(0, finish_solve, solution is not None, solution, final_perf)

            else:
                raise ValueError(f"未知算法: {selected_alg}")

        except Exception as e:
            root.after(0, lambda: messagebox.showerror("求解错误", str(e)))
            root.after(0, lambda: perf_labels['status'].config(text=f"出错", foreground="#cc0000"))
            root.after(0, enable_buttons)

    threading.Thread(target=run_solver, daemon=True).start()


def finish_solve(success, result_board, final_perf):
    global is_animating
    is_animating = False

    perf_labels['time'].config(text=f"{final_perf['time']:.3f} 秒")
    perf_labels['nodes'].config(text=str(final_perf['nodes']))
    perf_labels['backtracks'].config(text=str(final_perf['backtracks']))

    if success:
        perf_labels['status'].config(text="求解成功", foreground="#00aa00")
        fill_sudoku(result_board)
    else:
        perf_labels['status'].config(text="求解失败（无解）", foreground="#cc0000")

    enable_buttons()


# ---------------------- 算法对比函数（微调：结果显示到文本框）----------------------
def compare_algorithms():
    sudoku_data = read_sudoku()
    if all(value == 0 for row in sudoku_data for value in row):
        messagebox.showwarning("提示", "请先输入或生成数独")
        return

    disable_buttons()
    perf_labels['status'].config(text="正在对比算法...", foreground="#ff9900")
    compare_text.config(state="normal")
    compare_text.delete(1.0, tk.END)
    compare_text.insert(tk.END, "正在运行算法对比，请稍候...\n")
    compare_text.config(state="disabled")

    def run_comparison():
        try:
            results = []

            # 测试基础DFS算法
            if BasicSolver:
                puzzle = deepcopy(sudoku_data)
                solver = BasicSolver()
                solution = solver.solve(puzzle)
                # 保存性能数据
                performance_data["基础DFS"]["time"] = solver.stats.solve_time
                performance_data["基础DFS"]["nodes"] = solver.stats.nodes
                performance_data["基础DFS"]["backtracks"] = solver.stats.backtracks
                results.append(
                    f"基础DFS算法："
                    f"耗时{solver.stats.solve_time:.3f}秒 | "
                    f"节点{solver.stats.nodes} | "
                    f"回溯{solver.stats.backtracks} | "
                    f"{'✓成功' if solution else '✗失败'}"
                )

            # 测试MRV+LCV算法
            if MRVLCVSolver:
                puzzle = deepcopy(sudoku_data)
                solver = MRVLCVSolver()
                solution = solver.solve(puzzle)
                # 保存性能数据
                performance_data["MRV+LCV"]["time"] = solver.stats.solve_time
                performance_data["MRV+LCV"]["nodes"] = solver.stats.nodes
                performance_data["MRV+LCV"]["backtracks"] = solver.stats.backtracks
                results.append(
                    f"MRV+LCV算法："
                    f"耗时{solver.stats.solve_time:.3f}秒 | "
                    f"节点{solver.stats.nodes} | "
                    f"回溯{solver.stats.backtracks} | "
                    f"{'✓成功' if solution else '✗失败'}"
                )

            # 测试AC3+MRV+LCV算法
            if AC3_MRV_LCV_Solver:
                puzzle = deepcopy(sudoku_data)
                solver = AC3_MRV_LCV_Solver()
                solution = solver.solve(puzzle)
                # 保存性能数据
                performance_data["AC3+MRV+LCV"]["time"] = solver.stats.solve_time
                performance_data["AC3+MRV+LCV"]["nodes"] = solver.stats.nodes
                performance_data["AC3+MRV+LCV"]["backtracks"] = solver.stats.backtracks
                results.append(
                    f"AC3+MRV+LCV算法："
                    f"耗时{solver.stats.solve_time:.3f}秒 | "
                    f"节点{solver.stats.nodes} | "
                    f"回溯{solver.stats.backtracks} | "
                    f"{'✓成功' if solution else '✗失败'}"
                )

            # 显示结果到文本框
            result_text = "\n".join(results)
            root.after(0, lambda: [
                compare_text.config(state="normal"),
                compare_text.delete(1.0, tk.END),
                compare_text.insert(tk.END, result_text),
                compare_text.config(state="disabled"),
                perf_labels['status'].config(text="对比完成，可查看图表", foreground="#0066cc")
            ])

        except Exception as e:
            root.after(0, lambda: messagebox.showerror("对比失败", str(e)))
        finally:
            root.after(0, enable_buttons)

    threading.Thread(target=run_comparison, daemon=True).start()


# 用于保存实时性能数据
performance_data = {
    "基础DFS": {"time": 0, "nodes": 0, "backtracks": 0},
    "MRV+LCV": {"time": 0, "nodes": 0, "backtracks": 0},
    "AC3+MRV+LCV": {"time": 0, "nodes": 0, "backtracks": 0},
}


def show_chart():
    """显示专业的统计图表窗口 - 柱状图+折线图组合"""
    # 检查是否有有效数据
    has_data = any(performance_data[alg]["nodes"] > 0 for alg in performance_data)

    if not has_data:
        messagebox.showinfo("提示", "请先运行「对比所有算法」以获取统计数据")
        return

    # 创建弹窗
    chart_window = tk.Toplevel(root)
    chart_window.title("算法性能统计图表")
    chart_window.geometry("900x650")
    chart_window.resizable(True, True)

    # 获取当前统计数据（实时数据）
    algorithms = ["基础DFS", "MRV+LCV", "AC3+MRV+LCV"]
    times = [performance_data[alg]["time"] for alg in performance_data.keys()]
    nodes = [performance_data[alg]["nodes"] for alg in performance_data.keys()]
    backtracks = [performance_data[alg]["backtracks"] for alg in performance_data.keys()]
    
    # 获取当前难度
    current_difficulty = difficulty_var.get()

    # 创建图表 - 双Y轴（左侧柱状图，右侧折线图）
    import numpy as np
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    fig.suptitle(f'算法性能对比 - {current_difficulty}难度',
                 fontsize=15, fontweight='bold', y=0.97)

    # 设置X轴位置
    x = np.arange(len(algorithms))
    
    # 配色方案
    color_time = '#A8D8EA'        # 执行时间：淡蓝色
    color_nodes = '#FFD700'       # 搜索节点：金黄色（折线）
    color_backtracks = '#90EE90'  # 回溯次数：浅绿色（折线）

    # 左侧Y轴：绘制执行时间柱状图
    bars = ax1.bar(x, times, width=0.6, label='执行时间', 
                   color=color_time, alpha=0.85, edgecolor='#4A90A4', linewidth=2)
    ax1.set_xlabel('算法类型', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_ylabel('执行时间 (秒)', fontsize=12, fontweight='bold', color='#4A90A4')
    ax1.set_xticks(x)
    ax1.set_xticklabels(algorithms, fontsize=11)
    ax1.tick_params(axis='y', labelcolor='#4A90A4')
    ax1.grid(axis='y', linestyle='--', alpha=0.3, linewidth=0.7)
    ax1.set_axisbelow(True)
    
    # 在柱子上显示时间数值
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2., height,
                f'{times[i]:.4f}s',
                ha='center', va='bottom', fontsize=10, fontweight='bold', color='#2C5F75')
    
    # 设置左侧Y轴范围
    if max(times) > 0:
        ax1.set_ylim(0, max(times) * 1.25)

    # 右侧Y轴：绘制节点数和回溯次数折线图
    ax2 = ax1.twinx()
    
    # 绘制搜索节点数折线
    line1 = ax2.plot(x, nodes, color='#DAA520', marker='o', markersize=10, 
                     linewidth=3, label='搜索节点数', linestyle='--', alpha=0.9)
    
    # 绘制回溯次数折线
    line2 = ax2.plot(x, backtracks, color='#228B22', marker='s', markersize=10, 
                     linewidth=3, label='回溯次数', linestyle='--', alpha=0.9)
    
    ax2.set_ylabel('节点数 / 回溯次数', fontsize=12, fontweight='bold', color='#666666')
    ax2.tick_params(axis='y', labelcolor='#666666')
    
    # 在折线上显示数值
    for i, (node, backtrack) in enumerate(zip(nodes, backtracks)):
        # 节点数标签
        ax2.text(x[i], node, f'{node}', 
                ha='center', va='bottom', fontsize=10, fontweight='bold', 
                color='#DAA520', bbox=dict(boxstyle='round,pad=0.3', 
                facecolor='white', edgecolor='#DAA520', alpha=0.8))
        # 回溯次数标签
        ax2.text(x[i], backtrack, f'{backtrack}', 
                ha='center', va='top', fontsize=10, fontweight='bold', 
                color='#228B22', bbox=dict(boxstyle='round,pad=0.3', 
                facecolor='white', edgecolor='#228B22', alpha=0.8))
    
    # 设置右侧Y轴范围
    all_line_values = nodes + backtracks
    if max(all_line_values) > 0:
        ax2.set_ylim(0, max(all_line_values) * 1.3)

    # 合并图例，放在右上角
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, 
              loc='upper right', fontsize=10, framealpha=0.95, 
              edgecolor='#CCCCCC', fancybox=True, shadow=True)

    # 调整布局
    plt.tight_layout(rect=[0, 0.02, 1, 0.95])

    # 将图表嵌入到 tkinter 弹窗中
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    # 底部按钮栏
    button_frame = ttk.Frame(chart_window)
    button_frame.pack(fill=tk.X, padx=15, pady=10)
    
    # 保存图表按钮
    save_btn = ttk.Button(
        button_frame,
        text="保存图表",
        command=lambda: save_chart_image(fig),
        style="Large.TButton"
    )
    save_btn.pack(side=tk.LEFT, padx=5)
    
    # 关闭按钮
    close_btn = ttk.Button(
        button_frame,
        text="关闭",
        command=chart_window.destroy,
        style="Large.TButton"
    )
    close_btn.pack(side=tk.RIGHT, padx=5)


def save_chart_image(fig):
    """保存图表为图片"""
    from tkinter import filedialog
    import datetime
    
    # 生成默认文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"数独算法对比_{timestamp}.png"
    
    # 打开保存对话框
    filepath = filedialog.asksaveasfilename(
        defaultextension=".png",
        initialfile=default_name,
        filetypes=[
            ("PNG图片", "*.png"),
            ("JPEG图片", "*.jpg"),
            ("所有文件", "*.*")
        ]
    )
    
    if filepath:
        try:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("成功", f"图表已保存至:\n{filepath}")
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存图表:\n{str(e)}")


# ---------------------- 启动主循环 ----------------------
root.mainloop()