import tkinter as tk
from tkinter import ttk
import time
import random
import threading

# ---------------------- 导入成员A的DFS算法（需确保A的文件在同一目录）----------------------
# 注：需成员A提供改造后的 dfs_solver.py，内容见模块1的算法模板
try:
    from dfs_solver import DFSSudokuSolver
except ImportError:
    print("警告：未找到A的算法文件，请确保 dfs_solver.py 与当前文件在同一目录")

# ---------------------- 1. 初始化主窗口 ----------------------
root = tk.Tk()
root.title("数独求解可视化工具 - V4.0（算法驱动版）")
root.geometry("500x780")
root.resizable(False, False)

# ---------------------- 2. 创建9×9网格容器 ----------------------
grid_frame = ttk.Frame(root, padding="20")
grid_frame.pack(expand=True, fill=tk.BOTH)

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

# ---------------------- 3. 核心数据处理函数 ----------------------
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
            entry.config(state="readonly" if is_animating else "normal")
    enable_buttons()

def clear_sudoku():
    disable_buttons()
    empty_data = [[0 for _ in range(9)] for _ in range(9)]
    fill_sudoku(empty_data)
    update_performance(None)
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

# ---------------------- 数独题库（复用你的代码）----------------------
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

# ---------------------- 4. 动画模块（恢复阶段2优化版）----------------------
def animate_cell_color(entry, start_color, end_color, duration=200):
    steps = 20
    step_duration = duration // steps

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
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
            entry.config(state="readonly" if is_animating else "normal")
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
    animate_cell_color(entry, original_color, "#ffb6c1", duration=duration//2)
    
    def clear_after_highlight():
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.config(state="readonly" if is_animating else "normal")
        animate_cell_color(entry, "#ffb6c1", original_color, duration=duration//2)
    
    entry.after(duration//2, clear_after_highlight)

# ---------------------- 5. 核心动画接口（供A调用）----------------------
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

# ---------------------- 6. 动画队列 ----------------------
animation_queue = []
is_animating = False

def add_animation_to_queue(anim_func, *args):
    animation_queue.append((anim_func, args))
    if not is_animating:
        run_next_animation()

def run_next_animation():
    global is_animating
    if not animation_queue:
        is_animating = False
        return
    is_animating = True
    anim_func, args = animation_queue.pop(0)
    anim_func(*args)
    root.after(350, run_next_animation)

# ---------------------- 7. 按钮状态控制 ----------------------
def disable_buttons():
    fill_btn.config(state="disabled")
    clear_btn.config(state="disabled")
    test_fill_btn.config(state="disabled")
    test_backtrack_btn.config(state="disabled")
    test_single_btn.config(state="disabled")
    solve_btn.config(state="disabled")
    compare_btn.config(state="disabled")
    difficulty_menu.config(state="disabled")
    alg_menu.config(state="disabled")  # 🔸 新增：禁用算法下拉框
    for row in range(9):
        for col in range(9):
            sudoku_entries[row][col].config(state="readonly")

def enable_buttons():
    fill_btn.config(state="normal")
    clear_btn.config(state="normal")
    test_fill_btn.config(state="normal")
    test_backtrack_btn.config(state="normal")
    test_single_btn.config(state="normal")
    solve_btn.config(state="normal")
    compare_btn.config(state="normal")
    difficulty_menu.config(state="readonly")
    alg_menu.config(state="readonly")  # 🔸 新增：恢复算法下拉框
    for row in range(9):
        for col in range(9):
            sudoku_entries[row][col].config(state="normal")

# ---------------------- 8. 难度选择区 ----------------------
difficulty_frame = ttk.Frame(root, padding="0 10 0 0")
difficulty_frame.pack(fill=tk.X, padx=20)

difficulty_label = ttk.Label(difficulty_frame, text="选择数独难度：")
difficulty_label.pack(side=tk.LEFT, padx=5)

difficulty_var = tk.StringVar(value="中等")
difficulty_options = ["简单", "中等", "困难"]
difficulty_menu = ttk.Combobox(
    difficulty_frame,
    textvariable=difficulty_var,
    values=difficulty_options,
    state="readonly",
    width=10
)
difficulty_menu.pack(side=tk.LEFT, padx=5)

# ---------------------- 9. 功能按钮区 ----------------------
button_frame = ttk.Frame(root, padding="0 10 0 10")
button_frame.pack(fill=tk.X, padx=20)

def fill_with_difficulty():
    level = difficulty_var.get()
    sudoku_data = get_puzzle_by_difficulty(level)
    fill_sudoku(sudoku_data)

fill_btn = ttk.Button(button_frame, text="生成数独（按难度）", command=fill_with_difficulty)
fill_btn.pack(side=tk.LEFT, padx=5)

clear_btn = ttk.Button(button_frame, text="清空网格", command=clear_sudoku)
clear_btn.pack(side=tk.LEFT, padx=5)

# 动画测试按钮
test_frame = ttk.Frame(root, padding="0 0 0 10")
test_frame.pack(fill=tk.X, padx=20)

def test_fill_animation():
    clear_sudoku()
    root.after(500, animation_fill_cell, 0, 0, 5)

test_fill_btn = ttk.Button(test_frame, text="测试填数高亮动画", command=test_fill_animation)
test_fill_btn.pack(side=tk.LEFT, padx=5)

def test_backtrack_animation():
    animation_fill_cell(1, 1, 3)
    root.after(1000, animation_backtrack_cell, 1, 1)

test_backtrack_btn = ttk.Button(test_frame, text="测试回溯撤销动画", command=test_backtrack_animation)
test_backtrack_btn.pack(side=tk.LEFT, padx=5)

def test_single_fill_animation():
    clear_sudoku()
    add_animation_to_queue(animation_single_fill, 2, 2, 7)
    add_animation_to_queue(animation_single_fill, 3, 3, 9)
    add_animation_to_queue(animation_single_fill, 4, 4, 2)

test_single_btn = ttk.Button(test_frame, text="测试单步填数过渡", command=test_single_fill_animation)
test_single_btn.pack(side=tk.LEFT, padx=5)

# ---------------------- 10. 算法选择区 ----------------------
algorithm_frame = ttk.Frame(root, padding="0 0 0 10")
algorithm_frame.pack(fill=tk.X, padx=20)

alg_label = ttk.Label(algorithm_frame, text="选择求解算法：")
alg_label.pack(side=tk.LEFT, padx=5)

algorithm_var = tk.StringVar(value="请选择算法")
alg_options = ["基础DFS算法（成员A）", "进阶CSP算法（成员C）"]
alg_menu = ttk.Combobox(algorithm_frame, textvariable=algorithm_var, values=alg_options, state="readonly")
alg_menu.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

# ---------------------- 11. 性能统计板块 ----------------------
performance_frame = ttk.LabelFrame(root, text="算法性能统计", padding="10")
performance_frame.pack(fill=tk.BOTH, padx=20, pady=10, expand=True)

perf_labels = {}
metrics = [
    ("algorithm", "算法名称：", "未运行"),
    ("time", "执行时间：", "0.000 秒"),
    ("nodes", "搜索节点数：", "0"),
    ("backtracks", "回溯次数：", "0"),
    ("status", "求解状态：", "待求解")
]

for i, (key, label_text, default_value) in enumerate(metrics):
    row_frame = ttk.Frame(performance_frame)
    row_frame.pack(fill=tk.X, pady=3)
    label = ttk.Label(row_frame, text=label_text, font=("Arial", 10))
    label.pack(side=tk.LEFT)
    value_label = ttk.Label(row_frame, text=default_value, font=("Arial", 10, "bold"), foreground="#0066cc")
    value_label.pack(side=tk.LEFT, padx=5)
    perf_labels[key] = value_label

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

# ---------------------- 新增：实时性能更新函数 ----------------------
def update_perf_real_time(nodes, backtracks):
    perf_labels['nodes'].config(text=str(nodes))
    perf_labels['backtracks'].config(text=str(backtracks))
    if 'solve_start_time' in globals():
        elapsed_time = time.time() - solve_start_time
        perf_labels['time'].config(text=f"{elapsed_time:.3f} 秒")

# ---------------------- 12. 求解按钮区（真实算法调用）----------------------
solve_frame = ttk.Frame(root, padding="0 0 0 20")
solve_frame.pack(fill=tk.X, padx=20)

def solve_sudoku():
    global solve_start_time, is_animating
    selected_alg = algorithm_var.get()
    
    # 前置校验
    if selected_alg == "请选择算法":
        perf_labels['status'].config(text="请先选择算法", foreground="#cc0000")
        return
    sudoku_data = read_sudoku()
    if all(value == 0 for row in sudoku_data for value in row):
        perf_labels['status'].config(text="请输入或生成数独", foreground="#cc0000")
        return
    
    # 初始化状态
    disable_buttons()
    is_animating = True
    animation_queue.clear()
    perf_labels['algorithm'].config(text=selected_alg)
    perf_labels['nodes'].config(text="0")
    perf_labels['backtracks'].config(text="0")
    perf_labels['time'].config(text="0.000 秒")
    perf_labels['status'].config(text="求解中...", foreground="#ff9900")
    
    # 启动算法
    solve_start_time = time.time()
    try:
        if selected_alg == "基础DFS算法（成员A）":
            if 'DFSSudokuSolver' not in globals():
                raise ImportError("未找到A的DFS算法")
            solver = DFSSudokuSolver(
                animate_fill=animation_fill_cell,
                animate_backtrack=animation_backtrack_cell,
                update_perf=update_perf_real_time
            )
            # 线程运行算法，避免UI阻塞
            def run_solver():
                success, result_board, final_perf = solver.run(sudoku_data)
                root.after(0, finish_solve, success, result_board, final_perf)
            threading.Thread(target=run_solver, daemon=True).start()
        
        elif selected_alg == "进阶CSP算法（成员C）":
            perf_labels['status'].config(text="CSP算法待接入", foreground="#ff9900")
            root.after(1000, enable_buttons)
            is_animating = False
    
    except Exception as e:
        root.after(0, lambda: perf_labels['status'].config(text=f"出错：{str(e)[:20]}", foreground="#cc0000"))
        root.after(0, enable_buttons)
        is_animating = False

def finish_solve(success, result_board, final_perf):
    global is_animating
    is_animating = False
    # 更新最终性能
    perf_labels['time'].config(text=f"{final_perf['time']:.3f} 秒")
    perf_labels['nodes'].config(text=str(final_perf['nodes']))
    perf_labels['backtracks'].config(text=str(final_perf['backtracks']))
    # 更新结果状态
    if success:
        perf_labels['status'].config(text="求解成功", foreground="#00aa00")
        fill_sudoku(result_board)
    else:
        perf_labels['status'].config(text="求解失败（无解）", foreground="#cc0000")
    # 启用按钮
    enable_buttons()

solve_btn = ttk.Button(solve_frame, text="开始求解", command=solve_sudoku)
solve_btn.pack(side=tk.LEFT, padx=5)

compare_btn = ttk.Button(solve_frame, text="对比所有算法", command=lambda: perf_labels['status'].config(text="对比功能待实现", foreground="#ff9900"))
compare_btn.pack(side=tk.LEFT, padx=5)

# ---------------------- 13. 启动主循环 ----------------------
root.mainloop()