# -*- coding: utf-8 -*-
"""
Advanced Sudoku Solver using DFS Backtracking with Pruning and Candidate Generation.

This version includes candidate generation, enhanced pruning, and event callbacks for visualization.
"""

from typing import List, Optional, Callable

Board = List[List[int]]  # 9x9 Sudoku board, where 0 means empty


class SudokuSolver:
    def __init__(self):
        pass

    def solve(self, board: Board) -> Optional[Board]:
        """Solve the Sudoku board. Returns the solved board or None if unsolvable."""
        if not self._is_board_valid(board):
            print("Initial board is invalid (duplicates exist).")
            return None
        if self._backtrack(board):
            return board
        print("No solution found.")
        return None

    def _is_board_valid(self, board: Board) -> bool:
        """Check if the initial board follows Sudoku rules (no duplicates in rows/columns/boxes)."""
        # Check rows
        for row in board:
            seen = set()
            for num in row:
                if num != 0:
                    if num in seen:
                        return False
                    seen.add(num)

        # Check columns
        for col in range(9):
            seen = set()
            for row in range(9):
                num = board[row][col]
                if num != 0:
                    if num in seen:
                        return False
                    seen.add(num)

        # Check 3x3 boxes
        for box_row in range(3):  # 0-2 for top/middle/bottom boxes
            for box_col in range(3):  # 0-2 for left/middle/right boxes
                seen = set()
                start_r = box_row * 3
                start_c = box_col * 3
                for r in range(start_r, start_r + 3):
                    for c in range(start_c, start_c + 3):
                        num = board[r][c]
                        if num != 0:
                            if num in seen:
                                return False
                            seen.add(num)
        return True

    def _backtrack(self, board: Board) -> bool:
        empty_cell = self._find_empty_cell(board)
        if not empty_cell:
            return True  # Solved

        row, col = empty_cell
        candidates = self._get_candidates(board, row, col)

        for num in candidates:
            if self._is_valid(board, row, col, num):
                board[row][col] = num

                # Proceed with backtracking
                if self._backtrack(board):
                    return True

                board[row][col] = 0  # Backtrack

        return False

    def _find_empty_cell(self, board: Board) -> Optional[tuple]:
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    return r, c
        return None

    def _is_valid(self, board: Board, row: int, col: int, num: int) -> bool:
        """Check if placing `num` at (row, col) is valid."""
        if num in board[row]:
            return False
        for r in range(9):
            if board[r][col] == num:
                return False
        box_row_start = (row // 3) * 3
        box_col_start = (col // 3) * 3
        for r in range(box_row_start, box_row_start + 3):
            for c in range(box_col_start, box_col_start + 3):
                if board[r][c] == num:
                    return False
        return True

    def _get_candidates(self, board: Board, row: int, col: int) -> set:
        """Generate the list of possible candidates for the given cell."""
        candidates = set(range(1, 10))
        for i in range(9):
            candidates.discard(board[row][i])  # Remove numbers already in the row
            candidates.discard(board[i][col])  # Remove numbers already in the column
        box_row_start = (row // 3) * 3
        box_col_start = (col // 3) * 3
        for r in range(box_row_start, box_row_start + 3):
            for c in range(box_col_start, box_col_start + 3):
                candidates.discard(board[r][c])  # Remove numbers already in the 3x3 box
        return candidates


# ---------------- Advanced Sudoku Solver ----------------
class AdvancedSudokuSolver(SudokuSolver):
    def __init__(self, update_callback: Optional[Callable] = None):
        super().__init__()  # Inherit methods from SudokuSolver
        self.update_callback = update_callback
        self.candidate_map = [[set(range(1, 10)) for _ in range(9)] for _ in range(9)]  # Candidate map for each cell

    def solve_with_callback(self, board: Board) -> Optional[Board]:
        """Solve the Sudoku board with visualization updates."""
        if not self._is_board_valid(board):
            print("Initial board is invalid (duplicates exist).")
            return None
        self._initialize_candidates(board)

        if self._backtrack(board):
            return board
        print("No solution found.")
        return None

    def _initialize_candidates(self, board: Board):
        """Initialize the candidate map for each empty cell."""
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:  # If the cell is empty
                    self.candidate_map[r][c] = self._get_candidates(board, r, c)
                else:
                    self.candidate_map[r][c] = set()  # Remove candidates for filled cells

    def _backtrack(self, board: Board) -> bool:
        empty_cell = self._find_empty_cell(board)
        if not empty_cell:
            return True  # Solved

        row, col = empty_cell
        candidates = self.candidate_map[row][col]

        for num in candidates:
            if self._is_valid(board, row, col, num):
                board[row][col] = num

                # Trigger visualization update (if callback exists)
                if self.update_callback:
                    self.update_callback(board, row, col, num, "fill")

                # Proceed with backtracking
                if self._backtrack(board):
                    return True

                board[row][col] = 0  # Backtrack
                if self.update_callback:
                    self.update_callback(board, row, col, num, "backtrack")

        return False


# ---------------- Test Cases ----------------
if __name__ == "__main__":
    # Define a simple update callback function for testing
    def update_ui(board, row, col, num, action):
        """Callback function to update the UI. This will be called during each backtrack or fill step."""
        print(f"Action: {action} - Placing {num} at ({row}, {col})")
        for row in board:
            print(row)

    # Test Case 1: Valid and solvable board
    solvable_board = [
        [5, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 5, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]

    print("Starting to solve the Sudoku:")
    solver = AdvancedSudokuSolver(update_callback=update_ui)
    solution = solver.solve_with_callback(solvable_board)

    if solution:
        print("Solved board:")
        for row in solution:
            print(row)
    else:
        print("No solution found.")
