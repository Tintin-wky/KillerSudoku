import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from man_solver import KillerSudokuSolver
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class KillerSudokuApp:
    def __init__(self, root, steps, cage_constraints):
        self.root = root
        self.root.title("Sudoku Solver Visualization")
        self.steps = steps 
        self.step = 0
        self.cage_constraints = cage_constraints
        
        self.prev_button = tk.Button(
            root,
            text="上一步",
            command=self.prev_step,
            font=("Helvetica", 16, "bold"),
            bg="#2ecc71",                # 绿色背景
            fg="white",                  # 白色文本
            activebackground="#27ae60",  # 鼠标悬停时变为深绿色
            activeforeground="white",
            relief="groove",
            borderwidth=2,
            padx=12,
            pady=10
        )
        self.prev_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.next_button = tk.Button(
            root,
            text="下一步",
            command=self.next_step,
            font=("Helvetica", 16, "bold"),
            bg="#2ecc71",                # 绿色背景
            fg="white",                  # 白色文本
            activebackground="#27ae60",  # 鼠标悬停时变为深绿色
            activeforeground="white",
            relief="groove",
            borderwidth=2,
            padx=12,
            pady=10
        )
        self.next_button.grid(row=0, column=1, padx=2, pady=2)
        
        self.prev_10_button = tk.Button(
            root,
            text="上10步",
            command=self.prev_10_steps,
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",                # 深蓝色背景
            fg="white",                  # 白色文本
            activebackground="#34495e",  # 鼠标悬停时变为深灰蓝色
            activeforeground="white",    # 鼠标悬停时文本颜色
            relief="raised",
            borderwidth=3,
            padx=10,
            pady=8
        )
        self.prev_10_button.grid(row=0, column=2, padx=2, pady=2)
        
        self.next_10_button = tk.Button(
            root,
            text="下10步",
            command=self.next_10_steps,
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",                # 深蓝色背景
            fg="white",                  # 白色文本
            activebackground="#34495e",  # 鼠标悬停时变为深灰蓝色
            activeforeground="white",    # 鼠标悬停时文本颜色
            relief="raised",
            borderwidth=3,
            padx=10,
            pady=8
        )
        self.next_10_button.grid(row=0, column=3, padx=2, pady=2)
        
        self.final_button = tk.Button(
            root,
            text="最终解", 
            command=self.show_final_solution,
            font=("Helvetica", 16, "bold"),  # 使用更大的字体和加粗样式
            bg="#007acc",                    # 按钮背景颜色（蓝色）
            fg="white",                      # 按钮文本颜色（白色）
            activebackground="#005f99",      # 鼠标悬停时的背景颜色
            activeforeground="white",        # 鼠标悬停时的文本颜色
            relief="raised",                 # 按钮的立体效果
            borderwidth=3,                   # 边框宽度
            padx=15,                         # 左右内边距
            pady=10                          # 上下内边距
        )
        self.final_button.grid(row=0, column=4, padx=2, pady=2)
        
        # 显示解题过程的操作提示
        self.action_label = tk.Label(
            root,
            text="", 
            font=("Helvetica", 16, "bold"),  # 使用更优雅的字体和较大的字体大小
            wraplength=450,                  # 调整换行长度
            justify="center",                  # 左对齐文本
            bg="#f0f0f0",                    # 设置浅灰色背景
            fg="#333333",                    # 设置深灰色字体颜色
            padx=20,                         # 内部左右填充
            pady=15,                         # 内部上下填充
            relief="groove",                 # 添加凹陷效果的边框
            borderwidth=2                    # 边框宽度
        )
        self.action_label.grid(row=1, column=0, columnspan=5, padx=20, pady=15, sticky="ew")
        
        # 初始化 matplotlib 图表
        self.figure, self.ax = plt.subplots(figsize=(9, 9))
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().grid(row=2, column=0, columnspan=5)
        
        # 绘制初始棋盘
        self.draw_board()
        self.update_action_label()

    def draw_board(self):
        """使用 matplotlib 绘制数独棋盘并添加杀手数独的Cage约束"""
        cell_size = 1
        self.ax.clear()

        # 创建不同的颜色列表，用于区分每个Cage
        colors = plt.cm.tab20.colors

        # 绘制Cage约束
        for cage_index, (target_sum, cells) in enumerate(self.cage_constraints):
            cage_color = colors[cage_index % len(colors)]  # 选择颜色循环使用
            for cell in cells:
                i, j = cell
                x, y = j * cell_size, 8 - i * cell_size
                
                # 绘制Cage的边框和填充颜色
                self.ax.add_patch(plt.Rectangle((x, y), cell_size, cell_size, fill=True, color=cage_color, alpha=0.3))
            
            # 在Cage的第一个单元格内显示目标和约束值
            first_cell_x, first_cell_y = cells[0][1] * cell_size, 8 - cells[0][0] * cell_size
            self.ax.text(first_cell_x + 0.1, first_cell_y + 0.9, str(target_sum), fontsize=12, color='red', ha='left', va='top')

        # 绘制单元格
        for i in range(9):
            for j in range(9):
                x, y = j * cell_size, 8 - i * cell_size
                
                # 绘制单元格边框
                self.ax.add_patch(plt.Rectangle((x, y), cell_size, cell_size, fill=False))
                
                # 填充数字或候选数字
                candidates = self.steps[self.step]['board'][i][j]
                if len(candidates) == 1:
                    # 已确定的数字，使用较大字体居中显示
                    self.ax.text(x + 0.5, y + 0.5, str(list(candidates)[0]), fontsize=24, ha='center', va='center')
                else:
                    # 未确定的格子，显示候选数字
                    # 将候选数字按 3x3 排列在单元格内
                    for idx, candidate in enumerate(candidates):
                        cx = x + (idx % 3) * 0.3 + 0.2
                        cy = y + (idx // 3) * 0.3 + 0.2
                        self.ax.text(cx, cy, str(candidate), fontsize=10, ha='center', va='center', color='blue')

        # 绘制粗线条分隔 3x3 宫
        for i in range(0, 10, 3):
            self.ax.plot([0, 9], [i, i], 'k-', linewidth=3)
            self.ax.plot([i, i], [0, 9], 'k-', linewidth=3)

        # 设置坐标轴
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_xlim(0, 9)
        self.ax.set_ylim(0, 9)
        self.ax.set_aspect('equal')
        self.figure.tight_layout()
        self.canvas.draw()


    def prev_step(self):
        """切换到上一步"""
        if self.step > 0:
            self.step -= 1
        self.update_board()

    def next_step(self):
        """切换到下一步"""
        if self.step < len(self.steps) - 1:
            self.step += 1
        self.update_board()

    def prev_10_steps(self):
        """切换到上10步"""
        self.step = max(0, self.step - 10)
        self.update_board()

    def next_10_steps(self):
        """切换到下10步"""
        self.step = min(len(self.steps) - 1, self.step + 10)
        self.update_board()

    def show_final_solution(self):
        """显示最终解"""
        self.step = len(self.steps) - 1
        self.update_board()

    def update_board(self):
        """更新棋盘和操作提示"""
        self.draw_board()
        self.update_action_label()

    def update_action_label(self):
        """更新操作指令的标签显示"""
        current_action = self.steps[self.step]['action']
        self.action_label.config(text=f"[{self.step}]{current_action}")

if __name__ == "__main__":
    # 26274 Difficulty:6 Success
    cage_constraints = [(26, [[0, 0], [0, 1], [1, 0], [1, 1]]), (13, [[0, 5], [0, 6]]), (17, [[0, 2], [0, 3], [0, 4], [1, 2]]), (8, [[0, 7], [1, 7]]), (23, [[2, 0], [2, 1], [3, 0], [3, 1], [4, 0]]), (11, [[1, 3], [1, 4], [2, 2], [2, 3]]), (30, [[1, 5], [1, 6], [2, 4], [2, 5], [2, 6], [2, 7]]), (17, [[3, 2], [3, 3]]), (4, [[3, 6], [3, 7]]), (23, [[0, 8], [1, 8], [2, 8], [3, 8]]), (11, [[4, 1], [4, 2]]), (9, [[4, 3], [5, 3]]), (11, [[3, 4], [4, 4], [5, 4]]), (8, [[3, 5], [4, 5]]), (16, [[4, 6], [4, 7]]), (11, [[5, 0], [6, 0], [7, 0], [8, 0]]), (8, [[5, 1], [5, 2]]), (11, [[5, 5], [5, 6]]), (39, [[6, 1], [6, 2], [6, 3], [6, 4], [7, 2], [7, 3]]), (15, [[6, 5], [6, 6], [7, 4], [7, 5]]), (28, [[4, 8], [5, 7], [5, 8], [6, 7], [6, 8]]), (16, [[7, 1], [8, 1]]), (22, [[7, 6], [8, 4], [8, 5], [8, 6]]), (10, [[8, 2], [8, 3]]), (18, [[7, 7], [7, 8], [8, 7], [8, 8]])]
    killer_solver = KillerSudokuSolver(cage_constraints=cage_constraints)
    _,steps = killer_solver.solve()

    root = tk.Tk()
    app = KillerSudokuApp(root, steps, cage_constraints)
    root.mainloop()

