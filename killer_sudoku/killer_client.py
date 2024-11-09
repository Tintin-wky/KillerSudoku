from killer_sudoku import KillerSudoku
from man_solver import KillerSudokuSolver
from KillerSudokuApp import KillerSudokuApp
import requests
import re
import argparse
import tkinter as tk


class KillerCient:
    def __init__(self):
        self.baseAddress = "https://www.dailykillersudoku.com"

    def get_killer_sudoku(self, puzzleId):
        response = requests.get("{}/puzzle/{}".format(self.baseAddress, puzzleId))

        content = str(response.content)

        matches = re.findall(
            r'board_base64":"([a-zA-Z\d=]*)","solution_base64":"([a-zA-Z\d=]*)"',
            content,
        )

        boardBase64, solutionBase64 = matches[0]

        killer = KillerSudoku(boardBase64)

        return killer


if __name__ == "__main__":
    # 使用 argparse 读取命令行参数
    parser = argparse.ArgumentParser(description="Solve a Killer Sudoku puzzle by ID.")
    parser.add_argument(
        "--id", type=int, required=True,
        help="The Killer Sudoku puzzle ID"
    )
    args = parser.parse_args()
    sudoku_id = args.id

    client = KillerCient()
    killer = client.get_killer_sudoku(sudoku_id)

    print(f"Pulling Sudoku: {sudoku_id}")

    killer_solver = KillerSudokuSolver(cage_constraints=killer.cages)

    print(f"Solving Sudoku: {sudoku_id}")
    Done, steps = killer_solver.solve()
    if Done:
        print(f"Solved succeed by {len(steps)} steps")
    else:
        print(f"Solved failed by {len(steps)} steps")

    print("Loading Interface")
    root = tk.Tk()
    app = KillerSudokuApp(root, steps)
    root.mainloop()

