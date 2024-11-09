import multiprocessing
import tkinter as tk

# 用于控制数独解题的暂停和继续
pause_event = multiprocessing.Event()
solve_event = multiprocessing.Event()

# 用于在进程之间传递数独棋盘状态
board_queue = multiprocessing.Queue()

# 初始数独棋盘（0 表示空格）
initial_board = [
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

def is_valid(board, row, col, num):
    """检查在数独棋盘中填写数字 num 是否有效"""
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False
    box_row, box_col = row // 3 * 3, col // 3 * 3
    for i in range(3):
        for j in range(3):
            if board[box_row + i][box_col + j] == num:
                return False
    return True

def get_candidates(board, row, col):
    """获取某个空格的候选数字"""
    if board[row][col] != 0:
        return []
    candidates = set(range(1, 10))
    for i in range(9):
        candidates.discard(board[row][i])
        candidates.discard(board[i][col])
    box_row, box_col = row // 3 * 3, col // 3 * 3
    for i in range(3):
        for j in range(3):
            candidates.discard(board[box_row + i][box_col + j])
    return list(candidates)

def solve_sudoku(board, board_queue, pause_event, solve_event):
    """逐步解数独，每次填写一个数字后更新可视化"""
    def backtrack(board):
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    for num in range(1, 10):
                        if is_valid(board, row, col, num):
                            board[row][col] = num
                            board_queue.put(board)
                            
                            if not solve_event.is_set():
                                pause_event.clear()
                                pause_event.wait()

                            if backtrack(board):
                                return True
                            board[row][col] = 0
                            board_queue.put(board)
                            
                            if not solve_event.is_set():
                                pause_event.clear()
                                pause_event.wait()
                    return False
        return True

    backtrack(board)
    print("数独已解完")

class SudokuApp:
    def __init__(self, root, initial_board):
        self.root = root
        self.root.title("数独求解可视化")
        self.board = [row[:] for row in initial_board]
        
        self.canvas = tk.Canvas(root, width=540, height=540)
        self.canvas.grid(row=0, column=0, columnspan=9)
        
        self.next_button = tk.Button(root, text="下一步", command=self.next_step)
        self.next_button.grid(row=1, column=0, columnspan=4, pady=10)

        self.solve_button = tk.Button(root, text="直接求解", command=self.solve_now)
        self.solve_button.grid(row=1, column=5, columnspan=4, pady=10)
        
        pause_event.set()
        self.process = multiprocessing.Process(target=solve_sudoku, args=(self.board, board_queue, pause_event, solve_event))
        self.process.start()
        
        self.update_ui()

    def draw_board(self):
        """绘制数独棋盘"""
        self.canvas.delete("all")
        for i in range(9):
            for j in range(9):
                x1, y1 = j * 60, i * 60
                x2, y2 = x1 + 60, y1 + 60
                
                # 绘制单元格
                self.canvas.create_rectangle(x1, y1, x2, y2)
                
                # 显示数字或候选数字
                if self.board[i][j] != 0:
                    self.canvas.create_text(x1 + 30, y1 + 30, text=str(self.board[i][j]), font=("Arial", 24))
                else:
                    candidates = get_candidates(self.board, i, j)
                    if candidates:
                        candidates_text = " ".join(map(str, candidates))
                        self.canvas.create_text(x1 + 30, y1 + 30, text=candidates_text, font=("Arial", 10))

        # 绘制粗线条分隔 3x3 宫
        for i in range(0, 10, 3):
            self.canvas.create_line(0, i * 60, 540, i * 60, width=3)
            self.canvas.create_line(i * 60, 0, i * 60, 540, width=3)

    def update_ui(self):
        """更新数独棋盘的界面"""
        try:
            if not board_queue.empty():
                self.board = board_queue.get_nowait()
        except:
            pass
        
        self.draw_board()
        self.root.after(100, self.update_ui)

    def next_step(self):
        pause_event.set()

    def solve_now(self):
        solve_event.set()
        pause_event.set()

    def on_close(self):
        self.process.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(root, initial_board)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
