import matplotlib.pyplot as plt
import numpy as np
from itertools import permutations
from typing import List, Set

class Cell:
    def __init__(self, row, col, cage=None):
        self.row = row
        self.col = col
        self.cage = cage
        self.candidates = set(range(1, 10))
        self.solved = False

    def exclude(self, number:int, info):
        if not self.solved :
            if number in self.candidates:
                self.candidates -= {number}
                print(f"Exclude {number} at ({self.row+1},{self.col+1}) {info}")

    def set_cage(self, cage:int):
        self.cage = cage

    def set_candidates(self, candidates:Set):
        self.candidates = candidates

    def __repr__(self):
        if self.solved:
            return f"Cell({self.row+1}, {self.col+1}):{self.candidates}"
        else:
            return f"Cell({self.row+1}, {self.col+1}):{self.candidates}"


class Cage:
    instance_count = 0

    def __init__(self, sum, cells:List[Cell], virtual=False):
        self.ID = Cage.instance_count
        Cage.instance_count += 1
        self.sum = sum
        self.cells = cells
        self.virtual = virtual

        if not virtual:
            for cell in self.cells:
                cell.set_cage(self.ID)

        def set_combinations(sum, count):
            results = set()
            def backtrack(start, path, target):
                if len(path) == count and target == 0:
                    results.add(tuple(path))
                    return
                for i in range(start, 10):
                    if i > target:
                        break
                    backtrack(i + 1, path + [i], target - i)
            backtrack(1, [], sum)
            return results
        self.combinations = set_combinations(self.sum, len(self.cells))  # Cage's possible number combination
        self.number_dict = {num: self.cells for num in range(1, 10)}  # number's possible position in cage
        self.certain_number = set()  # certain number in cage
        self.solved = False
        self.update()

    def split(self, sum, cells):
        return Cage(sum, cells), Cage(self.sum - sum, self.cells - cells)

    @classmethod
    def virtual_cage(cls, sum, cells):
        return cls(sum, cells, virtual=True)

    def update(self):
        def combination_check(combination:Set, cells:List[Cell]):
            appeared_numbers = {cell: set() for cell in cells}
            for number in combination:
                matched = False
                for cell in cells:
                    if number in cell.candidates:
                        matched = True
                        appeared_numbers[cell].add(number)
                        cells -= {cell}
                        break
                if not matched:
                    return False, {cell: set() for cell in cells}
            return True, appeared_numbers

        cell_number = {cell: set() for cell in self.cells}

        for combination in self.combinations.copy():
            combination_is_possible = False
            for perm in permutations(combination):
                valid, appeared_numbers = combination_check(perm, self.cells.copy())
                if valid:
                    combination_is_possible = True
                    for cell in self.cells:
                        cell_number[cell].update(appeared_numbers[cell])
            if not combination_is_possible:
                self.combinations.remove(combination)
                if self.combinations == set():
                    print(f"!!!{self}")

        for cell in self.cells:
            cell.candidates &= cell_number[cell]
        self.number_dict = {number: {cell for cell in self.cells if number in cell.candidates} for number in range(1, 10)}
        self.certain_number = {number for number in range(1, 10) if all(number in combination for combination in self.combinations)}

    def __repr__(self):
        if self.solved:
            return f"Cage(ID={self.ID}, target_sum={self.sum}, cells={self.cells}, solution={self.combinations})"
        else:
            return f"Cage(ID={self.ID}, target_sum={self.sum}, cells={self.cells}, combinations={self.combinations})"


class KillerSudokuSolver:
    def __init__(self, cage_constraints):      
        self.cell = [[Cell(row, col) for col in range(9)] for row in range(9)]
        self.cells = {cell for row in self.cell for cell in row}
        self.rows = [[self.cell[row][col] for col in range(9)] for row in range(9)]
        self.cols = [[self.cell[row][col] for row in range(9)] for col in range(9)]
        self.boxes = [[self.cell[r][c] 
                       for r in range(box_row * 3, box_row * 3 + 3) 
                       for c in range(box_col * 3, box_col * 3 + 3)] 
                      for box_row in range(3) for box_col in range(3)]
        self.cages = [Cage(sum,{self.cell[row][col] for row, col in cells}) for sum, cells in cage_constraints]
        self.step = 0
        self.updated = False

    def get_box(self, row, col):
        return (row // 3) * 3 + (col // 3)

    def is_solved(self):
        return all(cell.solved for cell in self.cells)

    def solve(self, visualize=False):
        loop = 0
        loop_max = 3
        while not self.is_solved():
            self.update()
            loop += 1
            if loop > loop_max:
                break
        if visualize:
            self.visualization()  
        return self.solution()

    def solution(self):
        solution_matrix = [[0 for _ in range(9)] for _ in range(9)] 

        for row in range(9):
            for col in range(9):
                cell = self.cell[row][col]
                if cell.solved and len(cell.candidates) == 1:
                    solution_matrix[row][col] = list(cell.candidates)[0]
                else:
                    solution_matrix[row][col] = 0

        return solution_matrix

    def update(self):
        self.updated = False

        # 45法则
        self.rule45()

        # 裸对检查
        for cells in self.rows:
            self.find_naked_pairs(cells)
        for cells in self.cols:
            self.find_naked_pairs(cells)
        for cells in self.boxes:   
            self.find_naked_pairs(cells) 
        for cage in self.cages:
            self.find_naked_pairs(cage.cells) 

        # 唯一性检查
        for cells in self.rows:
            for number in range(1, 10):
                self.reduce_in_row(cells,number)
        for cells in self.cols:
            for number in range(1, 10):
                self.reduce_in_column(cells,number)
        for cells in self.boxes:
            for number in range(1, 10):
                self.reduce_in_box(cells,number)
        for cage in self.cages:
            if cage.solved and all(cell.solved for cell in cage.cells):
                continue
            if (not cage.solved) and len(cage.combinations) == 1:
                cage.solved = True
            cage.update()
            if cage.certain_number != set():
                for number in cage.certain_number:
                    self.reduce_in_cage(cage.cells, number)

        if self.updated:
            self.update()

    def set_number(self, cell:Cell, number:int, info):
        if cell.solved:
            return
        cell.set_candidates({number})
        cell.solved = True
        self.step += 1
        self.updated = True
        print(f"[{self.step}]Solved cell at ({cell.row+1}, {cell.col+1}): {number} {info}")

        row, col, cage_id = cell.row, cell.col, cell.cage
        for peer in self.rows[row]:
            if not peer.solved and number in peer.candidates:
                peer.exclude(number,info=f"[update]Same row of {cell}")
        for peer in self.cols[col]:
            if not peer.solved and number in peer.candidates:
                peer.exclude(number,info=f"[update]Same col of {cell}")
        for peer in self.boxes[self.get_box(row, col)]:
            if not peer.solved and number in peer.candidates:
                peer.exclude(number,info=f"[update]Same box of {cell}")
        cage = self.cages[cage_id]
        for peer in cage.cells:
            if not peer.solved and number in peer.candidates:
                peer.exclude(number,info=f"[update]Same cage of {cell}")

    def visualization(self):
        """绘制数独棋盘，并在未解的单元格中显示可能的候选数字"""
        cell_size = 1
        fig, ax = plt.subplots(figsize=(9, 9))
        
        # 绘制单元格
        for i in range(9):
            for j in range(9):
                x, y = j * cell_size, 8 - i * cell_size
                
                # 绘制单元格边框
                ax.add_patch(plt.Rectangle((x, y), cell_size, cell_size, fill=False))
                
                # 填充数字或候选数字
                candidates = self.cell[i][j].candidates
                candidate_text = " ".join(str(num) for num in candidates)
                if len(candidates) == 1:
                    candidate = candidates.pop()
                    # 已确定的数字，使用较大字体居中显示
                    ax.text(x + 0.5, y + 0.5, candidate_text, fontsize=24, ha='center', va='center')
                else:
                    # 未确定的格子，显示候选数字
                    # 将候选数字按 3x3 排列在单元格内
                    for idx, candidate in enumerate(candidates):
                        cx = x + (idx % 3) * 0.3 + 0.2
                        cy = y + (idx // 3) * 0.3 + 0.2
                        ax.text(cx, cy, str(candidate), fontsize=10, ha='center', va='center', color='blue')
        
        # 绘制粗线条分隔 3x3 宫
        for i in range(0, 10, 3):
            ax.plot([0, 9], [i, i], 'k-', linewidth=3)
            ax.plot([i, i], [0, 9], 'k-', linewidth=3)
        
        # 设置坐标轴
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(0, 9)
        ax.set_ylim(0, 9)
        ax.set_aspect('equal')
        
        plt.show()

    def reduce_in_box(self, box_cells, number):
        # 找出该数字在当前宫格内的候选单元格
        candidates = [cell for cell in box_cells if number in cell.candidates]

        # 如果数字只在一个单元格内出现，则确定其值
        if len(candidates) == 1:
            candidate = candidates.pop()
            self.set_number(candidate, number, info=f"[info]Only candidate in box({box_cells[0].row//3+1},{box_cells[0].col//3+1})")
            return

        # 如果候选单元格全在同一行, 从该行的其他宫格中排除该数字
        rows = {cell.row for cell in candidates}
        if len(rows) == 1:
            row = rows.pop()
            for cell in self.rows[row]:
                if cell not in box_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_box]Same row of {candidates}")

        # 如果候选单元格全在同一列, 从该列的其他宫格中排除该数字
        cols = {cell.col for cell in candidates}
        if len(cols) == 1:
            col = cols.pop()
            for cell in self.cols[col]:
                if cell not in box_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_box]Same col of {candidates}")

        # 如果候选单元格全在同一笼, 从该笼的其他宫格中排除该数字
        cages = {cell.cage for cell in candidates}
        if len(cages) == 1:
            cage = cages.pop()
            for cell in self.cages[cage].cells:
                if cell not in box_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_box]Same cage of {candidates}")

    def reduce_in_row(self, row_cells, number):
        # 找出该数字在当前宫格内的候选单元格
        candidates = [cell for cell in row_cells if number in cell.candidates]
        
        # 如果数字只在一个单元格内出现，则确定其值
        if len(candidates) == 1:
            candidate = candidates.pop()
            self.set_number(candidate, number, info=f"[info]Only candidate in row[{row_cells[0].row+1}]")
            return
        
        # 如果候选单元格全部在同一个宫格, 从该宫格内的其他行中排除该数字
        box_ids = {self.get_box(cell.row, cell.col) for cell in candidates}
        if len(box_ids) == 1:
            box_id = box_ids.pop()
            for cell in self.boxes[box_id]:
                if cell not in row_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_row]Same box of {candidates}")
        
        # 如果候选单元格全在同一笼, 从该笼的其他宫格中排除该数字
        cages = {cell.cage for cell in candidates}
        if len(cages) == 1:
            cage = cages.pop()
            for cell in self.cages[cage].cells:
                if cell not in row_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_row]Same cage of {candidates}")

    def reduce_in_column(self, col_cells, number):
        # 找出该数字在当前宫格内的候选单元格
        candidates = [cell for cell in col_cells if number in cell.candidates]

        # 如果数字只在一个单元格内出现，则确定其值
        if len(candidates) == 1:
            candidate = candidates.pop()
            self.set_number(candidate, number, info=f"[info]Only candidate in col[{col_cells[0].col+1}]")
            return
        
        # 如果候选单元格全部在同一个宫格, 从该宫格内的其他行中排除该数字
        box_ids = {self.get_box(cell.row, cell.col) for cell in candidates}
        if len(box_ids) == 1:
            box_id = box_ids.pop()
            for cell in self.boxes[box_id]:
                if cell not in col_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_column]Same box of {candidates}")

        # 如果候选单元格全在同一笼, 从该笼的其他宫格中排除该数字
        cages = {cell.cage for cell in candidates}
        if len(cages) == 1:
            cage = cages.pop()
            for cell in self.cages[cage].cells:
                if cell not in col_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_column]Same cage of {candidates}")

    def reduce_in_cage(self, cage_cells, number):
        # 找出该数字在当前宫格内的候选单元格
        candidates = [cell for cell in cage_cells if number in cell.candidates]

        # 如果数字只在一个单元格内出现，则确定其值
        if len(candidates) == 1:
            candidate = candidates.pop()
            self.set_number(candidate, number, info=f"[info]Only candidate in cage[{cage_cells}]")
            return
        
        # 如果候选单元格全在同一行, 从该行的其他宫格中排除该数字
        rows = {cell.row for cell in candidates}
        if len(rows) == 1:
            row = rows.pop()
            for cell in self.rows[row]:
                if cell not in cage_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_cage]Same row of {candidates}")

        # 如果候选单元格全在同一列, 从该列的其他宫格中排除该数字
        cols = {cell.col for cell in candidates}
        if len(cols) == 1:
            col = cols.pop()
            for cell in self.cols[col]:
                if cell not in cage_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_cage]Same col of {candidates}")
        
        # 如果候选单元格全部在同一个宫格, 从该宫格内的其他行中排除该数字
        box_ids = {self.get_box(cell.row, cell.col) for cell in candidates}
        if len(box_ids) == 1:
            box_id = box_ids.pop()
            for cell in self.boxes[box_id]:
                if cell not in cage_cells and number in cell.candidates:
                    cell.exclude(number,info=f"[reduce_in_cage]Same box of {candidates}")

    def find_naked_pairs(self, cells):
        """
        检查给定的单元格列表（行、列或宫格）中的“裸对”情况，
        并从其他单元格的候选解中排除“裸对”数字。
        """
        candidates_count = {}
        # 统计候选数字为2的单元格
        for cell in cells:
            if len(cell.candidates) == 2:
                candidates_key = tuple(sorted(cell.candidates))
                candidates_count[candidates_key] = candidates_count.get(candidates_key, 0) + 1

        # 筛选出“裸对”
        naked_pairs = [pair for pair, count in candidates_count.items() if count == 2]
        
        # 从其他单元格中排除“裸对”数字
        for naked_pair in naked_pairs:
            for cell in cells:
                if cell.candidates != set(naked_pair):
                    for number in set(naked_pair):
                        cell.exclude(number, info=f"[naked_pairs] {naked_pair}")        

    def rule45(self, cage_max=3):
        # 内
        for row1 in range(9):
            for row2 in range(row1, 9):
                cells = set()
                cages = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = 45 * (row2 - row1 + 1)
                for row in range(row1, row2 + 1):
                    for col in range(9):
                        cells.add(self.cell[row][col])
                        cells_count += 1
                cage_cells = cells.copy()
                for cell in cells:
                    cages.add(self.cages[cell.cage])
                for cage in cages:
                    if all(cell in cells for cell in cage.cells):
                        known_cells_count += len(cage.cells)
                        cage_sum -= cage.sum
                        cage_cells -= {cell for cell in cage.cells}
                for cell in cage_cells.copy():
                    if cell.solved:
                        known_cells_count += 1
                        cage_sum -= list(cell.candidates)[0]
                        cage_cells -= {cell}
                if abs(known_cells_count - cells_count) <= cage_max and known_cells_count != cells_count:
                    cell_ = list(cage_cells)[0]
                    if all(cell.cage == cell_.cage for cell in cage_cells):
                        self.cages.extend(self.cages[cell_.cage].split(cage_sum, cage_cells))
                    elif all(cell.row == cell_.row for cell in cage_cells) or all(
                            cell.col == cell_.col for cell in cage_cells) or all(
                        cell in self.boxes[self.get_box(cell_.row, cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))  
                        # print(f"{row1} to {row2}: {cells_count} cages:{[cage.ID for cage in cages]} known_cells_count:{known_cells_count}")
        for col1 in range(9):
            for col2 in range(col1, 9):
                cells = set()
                cages = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = 45 * (col2 - col1 + 1)
                for col in range(col1, col2 + 1):
                    for row in range(9):
                        cells.add(self.cell[row][col])
                        cells_count += 1
                cage_cells = cells.copy()
                for cell in cells:
                    cages.add(self.cages[cell.cage])
                for cage in cages:
                    if all(cell in cells for cell in cage.cells):
                        known_cells_count += len(cage.cells)
                        cage_sum -= cage.sum
                        cage_cells -= {cell for cell in cage.cells}
                for cell in cage_cells.copy():
                    if cell.solved:
                        known_cells_count += 1
                        cage_sum -= list(cell.candidates)[0]
                        cage_cells -= {cell}
                if abs(known_cells_count - cells_count) <= cage_max and known_cells_count != cells_count:  # cage_constraint = [cage_sum, [[cell.row - 1, cell.col - 1] for cell in cage_cells]]
                    cell_ = list(cage_cells)[0]
                    if all(cell.cage == cell_.cage for cell in cage_cells):
                        self.cages.extend(self.cages[cell_.cage].split(cage_sum, cage_cells))
                    elif all(cell.row == cell_.row for cell in cage_cells) or all(
                            cell.col == cell_.col for cell in cage_cells) or all(
                        cell in self.boxes[self.get_box(cell_.row,cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum,
                                                            cage_cells))  # print(f"{col1} to {col2}: {cells_count} cages:{[cage.ID for cage in cages]} known_cells_count:{known_cells_count}")
        for box_index in range(9):
            cells = set(self.boxes[box_index])
            cages = set()
            cells_count = 9
            known_cells_count = 0
            cage_sum = 45
            cage_cells = cells.copy()
            for cell in cells:
                cages.add(self.cages[cell.cage])
            for cage in cages:
                if all(cell in cells for cell in cage.cells):
                    known_cells_count += len(cage.cells)
                    cage_sum -= cage.sum
                    cage_cells -= {cell for cell in cage.cells}
            for cell in cage_cells.copy():
                if cell.solved:
                    known_cells_count += 1
                    cage_sum -= list(cell.candidates)[0]
                    cage_cells -= {cell}
            if abs(known_cells_count - cells_count) <= cage_max and known_cells_count != cells_count:
                cell_ = list(cage_cells)[0]
                if all(cell.cage == cell_.cage for cell in cage_cells):
                    self.cages.extend(self.cages[cell_.cage].split(cage_sum, cage_cells))
                elif all(cell.row == cell_.row for cell in cage_cells) or all(
                        cell.col == cell_.col for cell in cage_cells) or all(
                    cell in self.boxes[self.get_box(cell_.row,cell_.col)] for cell in cage_cells):
                    self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))
        # 外
        for row1 in range(9):
            for row2 in range(row1, 9):
                cells = set()
                cages = set()
                cage_cells = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = - 45 * (row2 - row1 + 1)
                for col in range(row1, row2 + 1):
                    for row in range(9):
                        cells.add(self.cell[row][col])
                        cells_count += 1
                for cell in cells:
                    cages.add(self.cages[cell.cage])
                for cage in cages:
                    known_cells_count += len(cage.cells)
                    cage_sum += cage.sum
                    cage_cells.update(cage.cells)
                cage_cells -= cells
                for cell in cage_cells.copy():
                    if cell.solved:
                        known_cells_count -= 1
                        cage_sum -= list(cell.candidates)[0]
                        cage_cells -= {cell}
                if abs(known_cells_count - cells_count) <= cage_max and known_cells_count != cells_count:  # cage_constraint = [cage_sum, [[cell.row - 1, cell.col - 1] for cell in cage_cells]]
                    cell_ = list(cage_cells)[0]
                    if all(cell.cage == cell_.cage for cell in cage_cells):
                        self.cages.extend(self.cages[cell_.cage].split(cage_sum, cage_cells))
                    elif all(cell.row == cell_.row for cell in cage_cells) or all(
                            cell.col == cell_.col for cell in cage_cells) or all(
                        cell in self.boxes[self.get_box(cell_.row,cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))
        for col1 in range(9):
            for col2 in range(col1, 9):
                cells = set()
                cages = set()
                cage_cells = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = - 45 * (col2 - col1 + 1)
                for col in range(col1, col2 + 1):
                    for row in range(9):
                        cells.add(self.cell[row][col])
                        cells_count += 1
                for cell in cells:
                    cages.add(self.cages[cell.cage])
                for cage in cages:
                    known_cells_count += len(cage.cells)
                    cage_sum += cage.sum
                    cage_cells.update(cage.cells)
                cage_cells -= cells
                for cell in cage_cells.copy():
                    if cell.solved:
                        known_cells_count -= 1
                        cage_sum -= list(cell.candidates)[0]
                        cage_cells -= {cell}
                if abs(known_cells_count - cells_count) <= cage_max and known_cells_count != cells_count:  # cage_constraint = [cage_sum, [[cell.row - 1, cell.col - 1] for cell in cage_cells]]
                    cell_ = list(cage_cells)[0]
                    if all(cell.cage == cell_.cage for cell in cage_cells):
                        self.cages.extend(self.cages[cell_.cage].split(cage_sum, cage_cells))
                    elif all(cell.row == cell_.row for cell in cage_cells) or all(
                            cell.col == cell_.col for cell in cage_cells) or all(
                        cell in self.boxes[self.get_box(cell_.row,cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))
        for box_index in range(9):
            cells = set(self.boxes[box_index])
            cages = set()
            cells_count = 9
            known_cells_count = 0
            cage_sum = -45
            cage_cells = cells.copy()
            for cell in cells:
                cages.add(self.cages[cell.cage])
            for cage in cages:
                known_cells_count += len(cage.cells)
                cage_sum += cage.sum
                cage_cells.update(cage.cells)
            cage_cells -= cells
            for cell in cage_cells.copy():
                if cell.solved:
                    known_cells_count -= 1
                    cage_sum -= list(cell.candidates)[0]
                    cage_cells -= {cell}
            if abs(known_cells_count - cells_count) <= cage_max and known_cells_count != cells_count:
                cell_ = list(cage_cells)[0]
                if all(cell.cage == cell_.cage for cell in cage_cells):
                    self.cages.extend(self.cages[cell_.cage].split(cage_sum, cage_cells))
                elif all(cell.row == cell_.row for cell in cage_cells) or all(
                        cell.col == cell_.col for cell in cage_cells) or all(
                    cell in self.boxes[self.get_box(cell_.row,cell_.col)] for cell in cage_cells):
                    self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))


if __name__ == "__main__":
    # 26274 Difficulty:6 Success
    cage_constraints = [(26, [[0, 0], [0, 1], [1, 0], [1, 1]]), (13, [[0, 5], [0, 6]]), (17, [[0, 2], [0, 3], [0, 4], [1, 2]]), (8, [[0, 7], [1, 7]]), (23, [[2, 0], [2, 1], [3, 0], [3, 1], [4, 0]]), (11, [[1, 3], [1, 4], [2, 2], [2, 3]]), (30, [[1, 5], [1, 6], [2, 4], [2, 5], [2, 6], [2, 7]]), (17, [[3, 2], [3, 3]]), (4, [[3, 6], [3, 7]]), (23, [[0, 8], [1, 8], [2, 8], [3, 8]]), (11, [[4, 1], [4, 2]]), (9, [[4, 3], [5, 3]]), (11, [[3, 4], [4, 4], [5, 4]]), (8, [[3, 5], [4, 5]]), (16, [[4, 6], [4, 7]]), (11, [[5, 0], [6, 0], [7, 0], [8, 0]]), (8, [[5, 1], [5, 2]]), (11, [[5, 5], [5, 6]]), (39, [[6, 1], [6, 2], [6, 3], [6, 4], [7, 2], [7, 3]]), (15, [[6, 5], [6, 6], [7, 4], [7, 5]]), (28, [[4, 8], [5, 7], [5, 8], [6, 7], [6, 8]]), (16, [[7, 1], [8, 1]]), (22, [[7, 6], [8, 4], [8, 5], [8, 6]]), (10, [[8, 2], [8, 3]]), (18, [[7, 7], [7, 8], [8, 7], [8, 8]])]

    # 26079 Difficulty:6 Fail
    # cage_constraints = [(8, [[0, 0], [0, 1]]), (25, [[0, 2], [0, 3], [0, 4], [0, 5], [0, 6]]), (12, [[0, 7], [0, 8]]),
    #                     (25, [[1, 0], [1, 1], [2, 0], [3, 0]]), (23, [[1, 7], [1, 8], [2, 8], [3, 8]]),
    #                     (28, [[1, 2], [2, 1], [2, 2], [3, 2], [4, 2]]), (6, [[1, 3], [2, 3]]), (14, [[1, 4], [2, 4]]),
    #                     (6, [[1, 5], [2, 5]]), (23, [[1, 6], [2, 6], [2, 7], [3, 6], [4, 6]]),
    #                     (14, [[3, 3], [3, 4], [3, 5]]), (5, [[3, 1], [4, 1]]), (13, [[4, 3], [4, 4], [4, 5]]),
    #                     (11, [[3, 7], [4, 7]]), (18, [[4, 0], [5, 0], [6, 0]]), (14, [[4, 8], [5, 8], [6, 8]]),
    #                     (13, [[5, 1], [6, 1]]), (14, [[5, 2], [6, 2]]), (16, [[5, 3], [6, 3], [7, 3]]),
    #                     (7, [[5, 4], [6, 4]]), (20, [[5, 5], [6, 5], [7, 5]]), (8, [[5, 6], [6, 6]]),
    #                     (5, [[5, 7], [6, 7]]), (22, [[7, 1], [7, 2], [8, 2], [8, 3]]),
    #                     (22, [[7, 6], [7, 7], [8, 5], [8, 6]]), (10, [[7, 0], [8, 0], [8, 1]]), (8, [[7, 4], [8, 4]]),
    #                     (15, [[7, 8], [8, 7], [8, 8]])]

    killer_solver = KillerSudokuSolver(cage_constraints=cage_constraints)

    killer_solver.solve(visualize=True)

    # with open("solution.txt", "w") as file:
    #     original_stdout = sys.stdout
    #     sys.stdout = file
    #
    #     killer_solver.solve()
    #
    #     sys.stdout = original_stdout
