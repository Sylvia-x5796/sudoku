# -*- coding: utf-8 -*-
"""
sudoku_generator.py (改进版)
新增:根据目标难度生成题目
"""

import random
from copy import deepcopy
from typing import List, Tuple, Optional, Dict
from src.algorithms.solver_mrv_lcv import MRVLCVSolver

Board = List[List[int]]


class SudokuGenerator:
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

        # 难度阈值配置(可根据实际调整)
        self.difficulty_ranges = {
            "Easy": (0, 100),
            "Medium": (100, 250),
            "Hard": (250, 1000)
        }

    @staticmethod
    def print_board(board: Board):
        for r in range(9):
            row_str = ""
            for c in range(9):
                v = board[r][c]
                row_str += (str(v) if v != 0 else ".") + " "
                if c % 3 == 2 and c < 8:
                    row_str += "| "
            print(row_str)
            if r % 3 == 2 and r < 8:
                print("-" * 21)
        print()

    # 生成完整终盘
    def generate_full_solution(self) -> Board:
        board = [[0 for _ in range(9)] for _ in range(9)]
        self._fill_board_randomly(board)
        return board

    def _fill_board_randomly(self, board: Board) -> bool:
        empty = self._find_empty(board)
        if not empty:
            return True
        row, col = empty

        nums = list(range(1, 10))
        random.shuffle(nums)

        for val in nums:
            if self._is_safe(board, row, col, val):
                board[row][col] = val
                if self._fill_board_randomly(board):
                    return True
                board[row][col] = 0
        return False

    @staticmethod
    def _find_empty(board: Board) -> Optional[Tuple[int, int]]:
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    return r, c
        return None

    @staticmethod
    def _is_safe(board: Board, row: int, col: int, val: int) -> bool:
        for i in range(9):
            if board[row][i] == val or board[i][col] == val:
                return False

        br, bc = (row // 3) * 3, (col // 3) * 3
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if board[r][c] == val:
                    return False
        return True

    # 原有方法:根据提示数生成
    def generate_puzzle(
            self,
            target_clues: int = 30,
            symmetric: bool = True,
            max_attempts: int = 1000
    ) -> Board:
        full = self.generate_full_solution()
        puzzle = deepcopy(full)

        cells = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(cells)

        clues = 81
        attempts = 0

        for (row, col) in cells:
            if attempts >= max_attempts or clues <= target_clues:
                break
            if puzzle[row][col] == 0:
                continue

            backup_val = puzzle[row][col]
            sym_row, sym_col = 8 - row, 8 - col
            backup_sym = puzzle[sym_row][sym_col] if symmetric else backup_val

            puzzle[row][col] = 0
            if symmetric and (row, col) != (sym_row, sym_col):
                puzzle[sym_row][sym_col] = 0

            removed = 1 if (row, col) == (sym_row, sym_col) else 2
            new_clues = clues - removed

            if new_clues >= target_clues and self.has_unique_solution(puzzle):
                clues = new_clues
            else:
                puzzle[row][col] = backup_val
                if symmetric and (row, col) != (sym_row, sym_col):
                    puzzle[sym_row][sym_col] = backup_sym

            attempts += 1

        return puzzle

    # ★ 新增方法:根据目标难度生成题目
    def generate_puzzle_with_difficulty(
            self,
            target_difficulty: str = "Medium",
            symmetric: bool = True,
            max_retries: int = 50,
            clue_range: Tuple[int, int] = (25, 40)
    ) -> Tuple[Board, Dict]:
        """
        根据目标难度生成题目

        参数:
            target_difficulty: "Easy", "Medium" 或 "Hard"
            symmetric: 是否对称挖洞
            max_retries: 最大尝试次数
            clue_range: 提示数范围(min, max)

        返回:
            (puzzle, info) - 题目和统计信息
        """

        if target_difficulty not in self.difficulty_ranges:
            raise ValueError(f"难度必须是: {list(self.difficulty_ranges.keys())}")

        min_nodes, max_nodes = self.difficulty_ranges[target_difficulty]
        min_clues, max_clues = clue_range

        best_puzzle = None
        best_stats = None
        best_diff = float('inf')

        for attempt in range(max_retries):
            # 根据难度动态调整提示数
            if target_difficulty == "Easy":
                target_clues = random.randint(40, 50)
            elif target_difficulty == "Medium":
                target_clues = random.randint(30, 40)
            else:  # Hard
                target_clues = random.randint(22, 32)

            # 生成题目
            puzzle = self.generate_puzzle(
                target_clues=target_clues,
                symmetric=symmetric,
                max_attempts=500
            )

            # 评估难度
            level, stats = self.evaluate_difficulty(puzzle)
            nodes = stats["nodes"]

            # 计算与目标难度的偏差
            if min_nodes <= nodes < max_nodes:
                # 完全符合目标难度
                print(f"✓ 第{attempt + 1}次尝试成功! 节点数:{nodes}, 难度:{level}")
                return puzzle, {"level": level, "stats": stats, "clues": self._count_clues(puzzle)}

            # 记录最接近目标的题目
            if nodes < min_nodes:
                diff = min_nodes - nodes
            else:
                diff = nodes - max_nodes

            if diff < best_diff:
                best_diff = diff
                best_puzzle = puzzle
                best_stats = {"level": level, "stats": stats, "clues": self._count_clues(puzzle)}
                print(f"  第{attempt + 1}次: 节点数={nodes}, 难度={level} (最接近)")

        print(f"⚠ 经过{max_retries}次尝试,返回最接近的题目")
        return best_puzzle, best_stats

    @staticmethod
    def _count_clues(board: Board) -> int:
        """统计提示数"""
        return sum(1 for r in range(9) for c in range(9) if board[r][c] != 0)

    # 唯一性判断
    def has_unique_solution(self, board: Board, solution_limit: int = 2) -> bool:
        count = self._count_solutions(deepcopy(board), limit=solution_limit)
        return count == 1

    def _count_solutions(self, board: Board, limit: int = 2) -> int:
        self._solution_count = 0
        self._solution_limit = limit
        self._dfs_count(board)
        return self._solution_count

    def _dfs_count(self, board: Board):
        if self._solution_count >= self._solution_limit:
            return

        empty = self._find_empty(board)
        if not empty:
            self._solution_count += 1
            return

        row, col = empty
        for val in range(1, 10):
            if self._is_safe(board, row, col, val):
                board[row][col] = val
                self._dfs_count(board)
                board[row][col] = 0
                if self._solution_count >= self._solution_limit:
                    return

    # 难度评估
    def evaluate_difficulty(self, board: Board) -> Tuple[str, Dict]:
        puzzle = deepcopy(board)
        solver = MRVLCVSolver()
        solution = solver.solve(puzzle)

        if solution is None:
            return "Invalid", {"nodes": 0, "backtracks": 0}

        nodes = solver.stats.nodes
        backtracks = solver.stats.backtracks

        # 根据节点数判断难度
        for level, (min_n, max_n) in self.difficulty_ranges.items():
            if min_n <= nodes < max_n:
                return level, {"nodes": nodes, "backtracks": backtracks}

        return "Hard", {"nodes": nodes, "backtracks": backtracks}


# 测试代码
if __name__ == "__main__":
    gen = SudokuGenerator()

    # 生成简单难度
    print("=" * 50)
    print("生成简单难度数独")
    puzzle_easy, info_easy = gen.generate_puzzle_with_difficulty(
        target_difficulty="Easy",
        symmetric=True,
        max_retries=30
    )
    gen.print_board(puzzle_easy)
    print(f"难度: {info_easy['level']}")
    print(f"统计: {info_easy['stats']}")
    print(f"提示数: {info_easy['clues']}\n")

    # 生成中等难度
    print("=" * 50)
    print("生成中等难度数独")
    puzzle_medium, info_medium = gen.generate_puzzle_with_difficulty(
        target_difficulty="Medium",
        symmetric=True,
        max_retries=30
    )
    gen.print_board(puzzle_medium)
    print(f"难度: {info_medium['level']}")
    print(f"统计: {info_medium['stats']}")
    print(f"提示数: {info_medium['clues']}\n")

    # 生成困难难度
    print("=" * 50)
    print("生成困难难度数独")
    puzzle_hard, info_hard = gen.generate_puzzle_with_difficulty(
        target_difficulty="Hard",
        symmetric=True,
        max_retries=30
    )
    gen.print_board(puzzle_hard)
    print(f"难度: {info_hard['level']}")
    print(f"统计: {info_hard['stats']}")
    print(f"提示数: {info_hard['clues']}")