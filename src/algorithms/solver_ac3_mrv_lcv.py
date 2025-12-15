# -*- coding: utf-8 -*-
"""
Sudoku solver using AC-3 + MRV + LCV.

- AC-3: 弧一致性（约束传播），用于提前/局部削减候选集
- MRV: 选候选数最少的格子（变量选择启发式）
- LCV: 选对邻居"限制最小"的数字（值选择启发式）

你可以将这个类集成到项目中，并作为
"AC-3 + MRV + LCV" 算法选项。
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Set, List, Optional
from copy import deepcopy
import time

Board = List[List[int]]  # 9x9, 0 表示空格
Var = Tuple[int, int]  # (row, col)


@dataclass
class SolveStats:
    nodes: int = 0  # 尝试赋值的次数
    backtracks: int = 0  # 回溯次数
    ac3_calls: int = 0  # AC-3 调用次数
    domain_reductions: int = 0  # 候选值削减次数
    solve_time: float = 0.0  # 求解时间（秒，包含动画）
    pure_solve_time: float = 0.0  # 纯算法时间（秒，不包含动画）


class AC3_MRV_LCV_Solver:
    def __init__(self):
        self.stats = SolveStats()
        self._solution: Optional[Board] = None
        # 动画回调函数
        self._fill_cb = None
        self._backtrack_cb = None
        self._ac3_prune_cb = None
        # 纯算法时间累计
        self._pure_time_start = 0.0

    def set_animation_callbacks(self, fill_cb=None, backtrack_cb=None, ac3_prune_cb=None):
        """设置动画回调函数"""
        self._fill_cb = fill_cb
        self._backtrack_cb = backtrack_cb
        self._ac3_prune_cb = ac3_prune_cb

    # ------------ 外部主接口 ------------

    def solve(self, board: Board) -> Optional[Board]:
        """
        使用 AC-3 + MRV + LCV 求解数独。
        :param board: 9x9 棋盘，0 表示空格
        :return: 若有解，返回 9x9 解盘；否则返回 None
        """
        self.stats = SolveStats()
        self._solution = None
        self._animation_time = 0.0  # 累计动画时间

        start_time = time.time()

        # 初始化 domain（每个格子的候选集）
        domains = self._init_domains(board)

        # 先跑一遍全局 AC-3 进行约束传播
        if not self._ac3(board, domains):
            self.stats.solve_time = time.time() - start_time
            self.stats.pure_solve_time = self.stats.solve_time - self._animation_time
            return None

        # 回溯 + MRV + LCV
        work_board = deepcopy(board)
        success = self._backtrack(work_board, domains)
        self.stats.solve_time = time.time() - start_time
        self.stats.pure_solve_time = self.stats.solve_time - self._animation_time

        if success:
            return self._solution
        return None

    # ------------ 初始化候选集 ------------

    def _init_domains(self, board: Board) -> Dict[Var, Set[int]]:
        """
        根据当前棋盘初始化每个格子的候选集合。
        已有数字的格子 domain = {该数字}
        空格的 domain = 去掉行/列/宫中已用数字
        """
        domains: Dict[Var, Set[int]] = {}
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    used = self._used_in_peers(board, r, c)
                    domains[(r, c)] = {v for v in range(1, 10) if v not in used}
                else:
                    domains[(r, c)] = {board[r][c]}
        return domains

    def _used_in_peers(self, board: Board, row: int, col: int) -> Set[int]:
        """
        返回 (row, col) 所在 行/列/宫 中已经用过的数字。
        """
        used = set()

        # 行和列
        for i in range(9):
            if board[row][i] != 0:
                used.add(board[row][i])
            if board[i][col] != 0:
                used.add(board[i][col])

        # 宫
        br = (row // 3) * 3
        bc = (col // 3) * 3
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if board[r][c] != 0:
                    used.add(board[r][c])

        return used

    # ------------ AC-3 约束传播 ------------

    def _ac3(self, board: Board, domains: Dict[Var, Set[int]]) -> bool:
        """
        AC-3 弧一致性算法。
        若发现某变量 domain 为空，则返回 False 表示无解。
        否则返回 True。
        """
        self.stats.ac3_calls += 1

        queue: List[Tuple[Var, Var]] = []

        # 初始化队列：所有有约束关系的变量对 (Xi, Xj)
        vars_list = list(domains.keys())
        for xi in vars_list:
            for xj in self._neighbors(xi):
                if xj in domains:
                    queue.append((xi, xj))

        while queue:
            xi, xj = queue.pop(0)
            if self._revise(domains, xi, xj):
                # 如果修剪后 domain 为空，说明无解
                if len(domains[xi]) == 0:
                    return False
                # 若 Xi 的 domain 被修改，则 Xi 的其他邻居需重新检查
                for xk in self._neighbors(xi):
                    if xk != xj and xk in domains:
                        queue.append((xk, xi))

        return True

    def _neighbors(self, var: Var) -> List[Var]:
        """
        返回与 var 有约束关系的所有变量（同行、同列、同宫）。
        """
        (row, col) = var
        neighs: Set[Var] = set()

        # 行和列
        for i in range(9):
            if i != col:
                neighs.add((row, i))
            if i != row:
                neighs.add((i, col))

        # 宫
        br = (row // 3) * 3
        bc = (col // 3) * 3
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if not (r == row and c == col):
                    neighs.add((r, c))

        return list(neighs)

    def _revise(self, domains: Dict[Var, Set[int]], xi: Var, xj: Var) -> bool:
        """
        尝试修剪变量 xi 的 domain，使之对 xj 弧一致。
        在数独中，约束是 xi != xj。
        若 xi 的某个值在 xj 的 domain 中是唯一可能值且会导致 xi==xj，
        则应从 xi 的 domain 中删掉这个值。
        返回 True 表示 xi 的 domain 被修改。
        """
        revised = False
        to_remove = set()

        for x in domains[xi]:
            # 检查 xj 的 domain 中是否存在 y != x
            # 如果不存在，则 x 不可用（否则 xi=xj 违反约束）
            if not any(y != x for y in domains[xj]):
                to_remove.add(x)

        if to_remove:
            domains[xi] = domains[xi] - to_remove
            revised = True
            self.stats.domain_reductions += len(to_remove)
            # 动画：显示候选数被削减（AC3剪枝效果）
            if self._ac3_prune_cb:
                for value in to_remove:
                    self._ac3_prune_cb(xi[0], xi[1], value)

        return revised

    # ------------ 回溯 + MRV + LCV ------------

    def _backtrack(self, board: Board,
                   domains: Dict[Var, Set[int]]) -> bool:
        """
        在已经经过 AC-3 约束传播后的 domains 上进行
        回溯搜索，使用 MRV + LCV。
        """
        # 选择一个未赋值的变量（空格）——使用 MRV
        mrv_var = self._select_mrv_variable(board, domains)
        if mrv_var is None:
            # 所有格子都有单一值，说明已找到解
            self._solution = deepcopy(board)
            # 不再重新填充所有数字，因为在回溯过程中已经填充了
            return True

        (row, col) = mrv_var
        values = domains[(row, col)]

        if not values:
            return False

        # 按 LCV 对候选值排序
        ordered_values = self._order_values_lcv(board, domains, mrv_var, values)

        for val in ordered_values:
            self.stats.nodes += 1

            # 备份当前 board 与 domains，用于回溯
            board_backup = board[row][col]
            domains_backup = deepcopy(domains)

            # 赋值
            board[row][col] = val
            domains[(row, col)] = {val}
            
            # 动画：尝试填入（蓝色）
            if self._fill_cb:
                anim_start = time.time()
                self._fill_cb(row, col, val, is_try=True)
                self._animation_time += (time.time() - anim_start)

            # 对该赋值执行局部 AC-3 约束传播
            if self._ac3(board, domains):
                # 若未导致冲突，递归求解
                if self._backtrack(board, domains):
                    return True

            # 回溯
            board[row][col] = board_backup
            domains.clear()
            domains.update(domains_backup)
            self.stats.backtracks += 1
            
            # 动画：回溯撤销（红色闪烁）
            if self._backtrack_cb:
                anim_start = time.time()
                self._backtrack_cb(row, col)
                self._animation_time += (time.time() - anim_start)

        return False

    def _select_mrv_variable(
            self,
            board: Board,
            domains: Dict[Var, Set[int]],
    ) -> Optional[Var]:
        """
        MRV: 从所有尚未确定的格子中，选择 domain 大小最小的一个。
        若所有格子都已确定（domain size == 1 且无 0），返回 None。
        """
        best_var: Optional[Var] = None
        best_size = 10  # 大于最大候选数 9

        for (r, c), dom in domains.items():
            if board[r][c] == 0:
                size = len(dom)
                if size < best_size:
                    best_size = size
                    best_var = (r, c)
                    if best_size == 1:  # 已经是最小可能值，提前结束
                        break

        return best_var

    def _order_values_lcv(
            self,
            board: Board,
            domains: Dict[Var, Set[int]],
            var: Var,
            values: Set[int],
    ) -> List[int]:
        """
        LCV: 对候选值进行排序。
        估计每个值对邻居的 domain 有多大"削减"，
        削减越小（越不限制他人）优先级越高。
        """
        (row, col) = var
        neighbors = self._neighbors(var)

        def constraint_count(value: int) -> int:
            """
            计算如果 var 被赋值为 value，会在邻居的 domain 中
            导致多少次"删除 value"的操作。
            """
            count = 0
            for (nr, nc) in neighbors:
                # 只考虑尚未确定的邻居
                if board[nr][nc] == 0:
                    if value in domains[(nr, nc)]:
                        count += 1
            return count

        value_constraint_pairs = [
            (v, constraint_count(v)) for v in values
        ]
        # 削减越小越好，所以按 count 从小到大排序
        value_constraint_pairs.sort(key=lambda x: x[1])

        return [v for (v, _) in value_constraint_pairs]


# ------------------- 示例使用 -------------------

if __name__ == "__main__":
    # 简单示例
    easy_board = [
        [0, 0, 0, 2, 6, 0, 7, 0, 1],
        [6, 8, 0, 0, 7, 0, 0, 9, 0],
        [1, 9, 0, 0, 0, 4, 5, 0, 0],
        [8, 2, 0, 1, 0, 0, 0, 4, 0],
        [0, 0, 4, 6, 0, 2, 9, 0, 0],
        [0, 5, 0, 0, 0, 3, 0, 2, 8],
        [0, 0, 9, 3, 0, 0, 0, 7, 4],
        [0, 4, 0, 0, 5, 0, 0, 3, 6],
        [7, 0, 3, 0, 1, 8, 0, 0, 0],
    ]

    # 极难示例（需要更多回溯）
    hard_board = [
        [8, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 3, 6, 0, 0, 0, 0, 0],
        [0, 7, 0, 0, 9, 0, 2, 0, 0],
        [0, 5, 0, 0, 0, 7, 0, 0, 0],
        [0, 0, 0, 0, 4, 5, 7, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 3, 0],
        [0, 0, 1, 0, 0, 0, 0, 6, 8],
        [0, 0, 8, 5, 0, 0, 0, 1, 0],
        [0, 9, 0, 0, 0, 0, 4, 0, 0],
    ]

    print("=" * 60)
    print("Testing AC-3 + MRV + LCV Solver")
    print("=" * 60)

    # 测试简单数独
    print("\n[Easy Sudoku]")
    solver1 = AC3_MRV_LCV_Solver()
    solution1 = solver1.solve(easy_board)

    if solution1:
        print("✓ Solved!")
        print(f"  Nodes: {solver1.stats.nodes}")
        print(f"  Backtracks: {solver1.stats.backtracks}")
        print(f"  AC-3 Calls: {solver1.stats.ac3_calls}")
        print(f"  Domain Reductions: {solver1.stats.domain_reductions}")
        print(f"  Time: {solver1.stats.solve_time:.6f}s")
    else:
        print("✗ No solution found")

    # 测试困难数独
    print("\n[Hard Sudoku]")
    solver2 = AC3_MRV_LCV_Solver()
    solution2 = solver2.solve(hard_board)

    if solution2:
        print("✓ Solved!")
        print(f"  Nodes: {solver2.stats.nodes}")
        print(f"  Backtracks: {solver2.stats.backtracks}")
        print(f"  AC-3 Calls: {solver2.stats.ac3_calls}")
        print(f"  Domain Reductions: {solver2.stats.domain_reductions}")
        print(f"  Time: {solver2.stats.solve_time:.6f}s")
        print("\nSolution:")
        for row in solution2:
            print(row)
    else:
        print("✗ No solution found")