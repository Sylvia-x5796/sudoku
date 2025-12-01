# -*- coding: utf-8 -*-
"""
Basic Sudoku Solver using DFS Backtracking.

This version adds initial board validation to ensure the input is legal.
"""

from typing import List, Optional

Board = List[List[int]]  # 9x9 Sudoku board, where 0 means empty


class SudokuSolver:
    def __init__(self):
        pass

    def solve(self, board: Board) -> Optional[Board]:
        """Solve the Sudoku board. Returns the solved board or None if unsolvable."""
        # 1. First, validate the initial board (no duplicates in rows/columns/boxes)
        if not self._is_board_valid(board):
            print("Initial board is invalid (duplicates exist).")
            return None
        # 2. Proceed with backtracking only if the initial board is legal
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
                # Iterate through each cell in the 3x3 box
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

        for num in range(1, 10):
            if self._is_valid(board, row, col, num):
                print(f"Placing {num} at ({row}, {col})")
                board[row][col] = num
                if self._backtrack(board):
                    return True
                board[row][col] = 0  # Backtrack
                print(f"Backtracking at ({row}, {col})")

        print(f"No valid number for ({row}, {col}).")
        return False

    def _find_empty_cell(self, board: Board) -> Optional[tuple]:
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    return r, c
        return None

    def _is_valid(self, board: Board, row: int, col: int, num: int) -> bool:
        """Check if placing `num` at (row, col) is valid (for backtracking steps)."""
        # Check row (we can optimize by not checking the entire row, but this is clear)
        if num in board[row]:
            return False

        # Check column
        for r in range(9):
            if board[r][col] == num:
                return False

        # Check box
        box_row_start = (row // 3) * 3
        box_col_start = (col // 3) * 3
        for r in range(box_row_start, box_row_start + 3):
            for c in range(box_col_start, box_col_start + 3):
                if board[r][c] == num:
                    return False

        return True


# ---------------- Test Cases ----------------
if __name__ == "__main__":
    # Test Case 1: Initial board with duplicate (should be invalid)
    invalid_board = [
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
    # Modify the board to create a duplicate in column 8
    invalid_board[2][8] = 6  # Adding duplicate 6 in column 8

    print("Testing invalid board (has duplicate in column 8):")
    solver = SudokuSolver()
    solution = solver.solve(invalid_board)
    if not solution:
        print("Correctly detected no solution (initial board invalid).")

    # Test Case 2: Valid but unsolvable board (hypothetical, but your code will handle it via backtracking)
    # Test Case 3: Valid and solvable board
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
    print("Testing valid and solvable board: ")
    solution = solver.solve(solvable_board)
    if solution:
        print("Solved board:")
        for row in solution:
            print(row)
    else:
        print("No solution found.")

