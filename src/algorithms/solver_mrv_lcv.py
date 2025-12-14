# -*- coding: utf-8 -*-
"""
Sudoku solver using MRV + LCV heuristics.

- MRV (Minimum Remaining Values): choose the empty cell with the fewest candidates.
- LCV (Least Constraining Value): order candidate values so that the value that
  rules out the fewest choices for neighboring cells is tried first.

You can integrate this class into your project as member C's part.
"""

from dataclasses import dataclass
from copy import deepcopy
from typing import List, Optional, Tuple, Set
import time

Board = List[List[int]]  # 9x9, 0 means empty


@dataclass
class SolveStats:
    """统计信息，用于难度评估和性能对比。"""
    nodes: int = 0  # 搜索节点数（尝试赋值次数）
    backtracks: int = 0  # 回溯次数
    solve_time: float = 0.0  # 求解时间（秒，包含动画）
    pure_solve_time: float = 0.0  # 纯算法时间（秒，不包含动画）


class MRVLCVSolver:
    def __init__(self):
        self.stats = SolveStats()
        self._solution: Optional[Board] = None
        # 动画回调函数
        self._fill_cb = None
        self._backtrack_cb = None
        # 纯算法时间累计
        self._pure_time_start = 0.0

    def set_animation_callbacks(self, fill_cb=None, backtrack_cb=None, ac3_prune_cb=None):
        """设置动画回调函数"""
        self._fill_cb = fill_cb
        self._backtrack_cb = backtrack_cb

    # ---------- 外部主接口 ----------

    def solve(self, board: Board) -> Optional[Board]:
        """
        对给定盘面求解数独。
        :param board: 9x9 的二维列表，0 表示空格
        :return: 若有解，返回一个新的已填满的 9x9 棋盘；否则返回 None
        """
        self.stats = SolveStats()
        self._solution = None

        start_time = time.time()
        self._pure_time_start = start_time
        work_board = deepcopy(board)
        success = self._backtrack(work_board)
        self.stats.solve_time = time.time() - start_time
        self.stats.pure_solve_time = self.stats.solve_time  # 默认相同

        if success:
            return self._solution
        return None

    # ---------- 核心回溯 + MRV + LCV ----------

    def _backtrack(self, board: Board) -> bool:
        """
        回溯求解，结合 MRV + LCV。
        """
        # 选择 MRV 格子：候选数最少的空格
        mrv_info = self._find_mrv_cell(board)
        if mrv_info is None:
            # 没有空格了，说明已经找到解
            self._solution = deepcopy(board)
            # 不再重新填充所有数字，因为在回溯过程中已经填充了
            return True

        (row, col, candidates) = mrv_info

        # 如果某个空格没有候选，提前失败（剪枝）
        if not candidates:
            return False

        # 使用 LCV 对候选值排序
        ordered_values = self._order_values_lcv(board, row, col, candidates)

        for val in ordered_values:
            self.stats.nodes += 1

            board[row][col] = val
            
            # 动画：尝试填入（蓝色）
            if self._fill_cb:
                anim_start = time.time()
                self._fill_cb(row, col, val, is_try=True)
                self.stats.pure_solve_time -= (time.time() - anim_start)
            
            # 递归求解
            if self._backtrack(board):
                return True

            # 回溯
            board[row][col] = 0
            self.stats.backtracks += 1
            
            # 动画：回溯撤销（红色闪烁）
            if self._backtrack_cb:
                anim_start = time.time()
                self._backtrack_cb(row, col)
                self.stats.pure_solve_time -= (time.time() - anim_start)

        return False

    # ---------- MRV：选择候选数最少的格子 ----------

    def _find_mrv_cell(self, board: Board) -> Optional[Tuple[int, int, Set[int]]]:
        """
        在当前盘面中找到一个空格，使其候选数字数量最少（MRV）。
        若没有空格（已经填满），返回 None。
        若存在空格候选集为空，那么在上层会剪枝。
        """
        best_row, best_col = -1, -1
        best_candidates: Optional[Set[int]] = None

        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    cand = self._get_candidates(board, r, c)
                    if best_candidates is None or len(cand) < len(best_candidates):
                        best_row, best_col = r, c
                        best_candidates = cand
                        # 如果已经发现只有 1 个候选，MRV 最优，直接返回
                        if len(best_candidates) == 1:
                            return best_row, best_col, best_candidates

        if best_candidates is None:
            # 没有空格了
            return None
        return best_row, best_col, best_candidates

    # ---------- LCV：对候选值进行排序 ----------

    def _order_values_lcv(
            self,
            board: Board,
            row: int,
            col: int,
            candidates: Set[int],
    ) -> List[int]:
        """
        根据 LCV（Least Constraining Value）对候选数值排序：
        尝试那些对相邻格子"约束最小"的值，即在邻居候选中出现次数更少的值。
        """

        def count_constraint(value: int) -> int:
            """
            估计把 board[row][col] 设置为 value 之后，会对邻居候选造成多大约束。
            简单做法：
              - 统计同一行、同一列、同一宫中，有多少空格把 value 作为候选；
                这个数字越大，说明这个 value 使用得越"抢占资源"（约束更大）。
            """
            count = 0

            # 行和列上的邻居
            for i in range(9):
                if board[row][i] == 0 and i != col:
                    if value in self._get_candidates(board, row, i):
                        count += 1
                if board[i][col] == 0 and i != row:
                    if value in self._get_candidates(board, i, col):
                        count += 1

            # 宫内邻居
            br = (row // 3) * 3
            bc = (col // 3) * 3
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    if (r == row and c == col) or board[r][c] != 0:
                        continue
                    if value in self._get_candidates(board, r, c):
                        count += 1

            return count

        # 为每个候选值计算"约束度"，然后按从小到大排序
        value_constraint_pairs = [
            (v, count_constraint(v)) for v in candidates
        ]
        value_constraint_pairs.sort(key=lambda x: x[1])

        ordered = [v for (v, _) in value_constraint_pairs]
        return ordered

    # ---------- 候选集计算 ----------

    def _get_candidates(self, board: Board, row: int, col: int) -> Set[int]:
        """
        计算某个空格 (row, col) 的合法候选集合。
        """
        if board[row][col] != 0:
            # 如果已经有数字，就没有候选（正常情况下不会调用到这里）
            return set()

        used = set()

        # 行
        for c in range(9):
            if board[row][c] != 0:
                used.add(board[row][c])

        # 列
        for r in range(9):
            if board[r][col] != 0:
                used.add(board[r][col])

        # 宫
        br = (row // 3) * 3
        bc = (col // 3) * 3
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if board[r][c] != 0:
                    used.add(board[r][c])

        return {v for v in range(1, 10) if v not in used}


# ---------------- 示例使用 ----------------

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
    print("Testing MRV + LCV Solver")
    print("=" * 60)

    # 测试简单数独
    print("\n[Easy Sudoku]")
    solver1 = MRVLCVSolver()
    solution1 = solver1.solve(easy_board)

    if solution1:
        print("✓ Solved!")
        print(f"  Nodes: {solver1.stats.nodes}")
        print(f"  Backtracks: {solver1.stats.backtracks}")
        print(f"  Time: {solver1.stats.solve_time:.6f}s")
    else:
        print("✗ No solution found")

    # 测试困难数独
    print("\n[Hard Sudoku]")
    solver2 = MRVLCVSolver()
    solution2 = solver2.solve(hard_board)

    if solution2:
        print("✓ Solved!")
        print(f"  Nodes: {solver2.stats.nodes}")
        print(f"  Backtracks: {solver2.stats.backtracks}")
        print(f"  Time: {solver2.stats.solve_time:.6f}s")
        print("\nSolution:")
        for row in solution2:
            print(row)
    else:
        print("✗ No solution found")