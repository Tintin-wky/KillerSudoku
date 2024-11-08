import matplotlib.pyplot as plt
from itertools import permutations


def find_combinations(sum, count):
    results = set()

    def backtrack(start, path, target):
        # 当路径长度等于count且目标为0时，找到一个有效组合
        if len(path) == count and target == 0:
            results.add(tuple(path))
            return
        # 遍历1到9的数字
        for i in range(start, 10):
            # 如果当前数字大于目标，不再继续尝试更大的数字
            if i > target:
                break
            # 尝试添加当前数字，并递归搜索
            backtrack(i + 1, path + [i], target - i)

    backtrack(1, [], sum)
    return results


def find_impossible_numbers(possible_combinations):
    all_numbers = set(range(1, 10))
    used_numbers = set()
    for combination in possible_combinations:
        used_numbers.update(combination)
    impossible_numbers = all_numbers - used_numbers
    return impossible_numbers


def get_cells_in_same_box(row, col):
    start_row = (row - 1) // 3 * 3 + 1
    start_col = (col - 1) // 3 * 3 + 1
    cells = [(r, c) for r in range(start_row, start_row + 3)
             for c in range(start_col, start_col + 3)]
    return cells


cell_dict = {}


class Cell:
    def __init__(self, row, col, cage):
        self.row = row
        self.col = col
        self.cage = cage
        self.candidates = set(range(1, 10))
        self.solved = False
        global cell_dict
        cell_dict[(row, col)] = self

    def exclude(self, number):
        self.candidates -= number
        if self.candidates == set():
            print(f"!!!{self}")

    def set_number(self, number):
        self.candidates = {number}

    def __repr__(self):
        if self.solved:
            return f"Cell(row={self.row}, col={self.col}, solution={self.candidates}, Cage={self.cage})"
        else:
            return f"Cell(row={self.row}, col={self.col}, candidates={self.candidates}, Cage={self.cage})"


class Cage:
    instance_count = -1

    def __init__(self, cage_constraint, cells=None):
        Cage.instance_count += 1
        self.sum = cage_constraint[0]
        self.ID = Cage.instance_count
        self.cells = set()
        if cells is None:
            for row, col in cage_constraint[1]:
                self.cells.add(Cell(row + 1, col + 1, self.ID))
        else:
            self.cells = cells
        self.combinations = find_combinations(self.sum, len(self.cells))
        self.number_dict = {i: self.cells for i in range(1, 10)}
        self.exact_number = set()
        self.update()
        self.solved = False
        # for cell in self.cells:
        #     cell.exclude(find_impossible_numbers(self.combinations))

    def split(self, sum, cells):
        cage_constraint1 = [sum, [[cell.row - 1, cell.col - 1] for cell in cells]]
        cage_constraint2 = [self.sum - sum, [[cell.row - 1, cell.col - 1] for cell in self.cells - cells]]
        return Cage(cage_constraint1, cells), Cage(cage_constraint2, self.cells - cells)

    @classmethod
    def virtual_cage(cls, sum, cells):
        cage_constraint = [sum, [[cell.row - 1, cell.col - 1] for cell in cells]]
        return Cage(cage_constraint, cells)

    def update(self):
        def combination_check(combination, cells):
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

        number_dict = {number: set() for number in range(1, 10)}
        for number in range(1, 10):
            for cell in self.cells:
                if number in cell.candidates:
                    number_dict[number].update({cell})
        self.number_dict = number_dict

        for number in range(1, 10):
            if all(number in combination for combination in self.combinations):
                self.exact_number.update({number})

    def __repr__(self):
        if self.solved:
            return f"Cage(ID={self.ID}, target_sum={self.sum}, cells={self.cells}, solution={self.combinations})"
        else:
            return f"Cage(ID={self.ID}, target_sum={self.sum}, cells={self.cells}, combinations={self.combinations})"


class KillerSudokuSolver:
    step = 0

    def __init__(self, cage_constraints):
        """
        Args:
            cage_constraints (list): Lists of tuples 'cage constraints'
                e.g. if cells [0,0], [0,1], and [0,2] sum to 12 would be
                (12, [[0,0],[0,1],[0,2]])
        """
        print(cage_constraints)
        self.cages = [Cage(cage_constraint) for cage_constraint in cage_constraints]

    def update(self):
        updated = False

        # 唯一性检查
        for row in range(1, 10):
            candidate_counts = {number: set() for number in range(1, 10)}
            for cell in [cell_dict.get((row, col)) for col in range(1, 10)]:
                for candidate in cell.candidates:
                    candidate_counts[candidate].update({cell.col})
            for number in range(1, 10):
                if len(candidate_counts[number]) == 1 and cell_dict.get(
                        (row, list(candidate_counts[number])[0])).solved is False:
                    self.set_number(row, list(candidate_counts[number])[0], number)
            for number in range(1, 10):
                if len(candidate_counts[number]) != 1:
                    row_ = row
                    cols = list(candidate_counts[number])
                    col_ = cols[0]
                    cell_ = cell_dict.get((row_, col_))
                    cage_ = self.cages[cell_.cage]
                    same_box = all((col - 1) // 3 == (col_ - 1) // 3 for col in cols)
                    if same_box:
                        for cell in [cell_dict.get((row, col)) for row, col in
                                     get_cells_in_same_box(row_, col_)]:
                            if cell.row != row_:
                                cell.exclude({number})
                    same_cage = all(cell_dict.get((row_, col)).cage == cell_.cage for col in cols)
                    if same_cage:
                        for cell in cage_.cells:
                            if cell.row != cell_.row:
                                cell.exclude({number})
                        cage_.combinations = {combination for combination in cage_.combinations if
                                              number in set(combination)}
                        cage_.update()
        for col in range(1, 10):
            candidate_counts = {number: set() for number in range(1, 10)}
            for cell in [cell_dict.get((row, col)) for row in range(1, 10)]:
                for candidate in cell.candidates:
                    candidate_counts[candidate].update({cell.row})
            for number in range(1, 10):
                if len(candidate_counts[number]) == 1 and cell_dict.get(
                        (list(candidate_counts[number])[0], col)).solved is False:
                    self.set_number(list(candidate_counts[number])[0], col, number)
            for number in range(1, 10):
                if len(candidate_counts[number]) != 1:
                    col_ = col
                    rows = list(candidate_counts[number])
                    row_ = rows[0]
                    cell_ = cell_dict.get((row_, col_))
                    cage_ = self.cages[cell_.cage]
                    same_box = all((row - 1) // 3 == (row_ - 1) // 3 for row in rows)
                    if same_box:
                        for cell in [cell_dict.get((row, col)) for row, col in
                                     get_cells_in_same_box(row_, col_)]:
                            if cell.col != col_:
                                cell.exclude({number})
                    same_cage = all(cell_dict.get((row, col_)).cage == cell_.cage for row in rows)
                    if same_cage:
                        for cell in cage_.cells:
                            if cell.col != cell_.col:
                                cell.exclude({number})
                        cage_.combinations = {combination for combination in cage_.combinations if
                                              number in set(combination)}
                        cage_.update()
        box_size = 3
        for box_row in range(1, 10, box_size):
            for box_col in range(1, 10, box_size):
                box_cells = set()
                for row in range(box_row, box_row + box_size):
                    for col in range(box_col, box_col + box_size):
                        box_cells.add(cell_dict.get((row, col)))
                candidate_counts = {number: set() for number in range(1, 10)}
                for cell in box_cells:
                    for candidate in cell.candidates:
                        candidate_counts[candidate].update({(cell.row, cell.col)})
                for number in range(1, 10):
                    if len(candidate_counts[number]) == 1 and cell_dict.get(
                            list(candidate_counts[number])[0]).solved is False:
                        self.set_number(list(candidate_counts[number])[0][0], list(candidate_counts[number])[0][1],
                                        number)
                for number in range(1, 10):
                    if len(candidate_counts[number]) != 1:
                        cells = candidate_counts[number]
                        row_, col_ = list(cells)[0]
                        cell_ = cell_dict.get((row_, col_))
                        cage_ = self.cages[cell_.cage]
                        same_row = all(cell_dict.get(cell).row == cell_.row for cell in cells)
                        same_col = all(cell_dict.get(cell).col == cell_.col for cell in cells)
                        same_cage = all(cell_dict.get(cell).cage == cell_.cage for cell in cells)
                        if same_row:
                            for cell in [cell_dict.get((row_, col)) for col in range(1, 10)]:
                                if cell not in [cell_dict.get((row, col)) for row, col in
                                                get_cells_in_same_box(row_, col_)]:
                                    cell.exclude({number})
                        if same_col:
                            for cell in [cell_dict.get((row, col_)) for row in range(1, 10)]:
                                if cell not in [cell_dict.get((row, col)) for row, col in
                                                get_cells_in_same_box(row_, col_)]:
                                    cell.exclude({number})
                        if same_cage:
                            for cell in cage_.cells:
                                if cell not in [cell_dict.get((row, col)) for row, col in
                                                get_cells_in_same_box(row_, col_)]:
                                    cell.exclude({number})
                            cage_.combinations = {combination for combination in cage_.combinations if
                                                  number in set(combination)}
                            cage_.update()

        # 检查裸对
        for row in range(1, 10):
            candidates_count = {}
            for cell in [cell_dict.get((row, col)) for col in range(1, 10)]:
                if len(cell.candidates) == 2:
                    candidates_key = tuple(sorted(cell.candidates))
                    candidates_count[candidates_key] = candidates_count.get(candidates_key, 0) + 1
            naked_pairs = [pair for pair, count in candidates_count.items() if count == 2]
            for naked_pair in naked_pairs:
                for cell in [cell_dict.get((row, col)) for col in range(1, 10)]:
                    if cell.candidates != set(naked_pair):
                        cell.exclude(set(naked_pair))
        for col in range(1, 10):
            candidates_count = {}
            for cell in [cell_dict.get((row, col)) for row in range(1, 10)]:
                if len(cell.candidates) == 2:
                    candidates_key = tuple(sorted(cell.candidates))
                    candidates_count[candidates_key] = candidates_count.get(candidates_key, 0) + 1
            naked_pairs = [pair for pair, count in candidates_count.items() if count == 2]
            for naked_pair in naked_pairs:
                for cell in [cell_dict.get((row, col)) for row in range(1, 10)]:
                    if cell.candidates != set(naked_pair):
                        cell.exclude(set(naked_pair))
        box_size = 3
        for box_row in range(1, 10, box_size):
            for box_col in range(1, 10, box_size):
                box_cells = set()
                for row in range(box_row, box_row + box_size):
                    for col in range(box_col, box_col + box_size):
                        box_cells.add(cell_dict.get((row, col)))
                candidates_count = {}
                for cell in box_cells:
                    if len(cell.candidates) == 2:
                        candidates_key = tuple(sorted(cell.candidates))
                        candidates_count[candidates_key] = candidates_count.get(candidates_key, 0) + 1
                naked_pairs = [pair for pair, count in candidates_count.items() if count == 2]
                for naked_pair in naked_pairs:
                    for cell in box_cells:
                        if cell.candidates != set(naked_pair):
                            cell.exclude(set(naked_pair))

        # 更新每个笼子
        for cage in self.cages:
            cage.update()

        # # 检查互斥
        # for row in range(1, 10):
        #     cells = set()
        #     cages = set()
        #     for col in range(1, 10):
        #         cells.add(cell_dict.get((row, col)))
        #     for cell in cells:
        #         cages.add(self.cages[cell.cage])
        #     for cage in cages.copy():
        #         if any(cell not in cells for cell in cage.cells):
        #             cages -= {cage}
        #         if cage.solved:
        #             cages -= {cage}
        #     if len(cages) >= 2:
        #         for cage in cages:
        #             for combination in cage.combinations.copy():
        #                 conflict = True
        #                 for cage_ in cages:
        #                     if cage_ != cage:
        #                         combinations_ = cage_.combinations.copy()
        #                         for combination_ in combinations_.copy():
        #                             if not set(combination_).intersection(combination):
        #                                 conflict = False
        #                                 break
        #                 if conflict:
        #                     cage.combinations -= {combination}
        # for col in range(1, 10):
        #     cells = set()
        #     cages = set()
        #     for row in range(1, 10):
        #         cells.add(cell_dict.get((row, col)))
        #     for cell in cells:
        #         cages.add(self.cages[cell.cage])
        #     for cage in cages.copy():
        #         if any(cell not in cells for cell in cage.cells):
        #             cages -= {cage}
        #         if cage.solved:
        #             cages -= {cage}
        #     if len(cages) >= 2:
        #         for cage in cages:
        #             for combination in cage.combinations.copy():
        #                 conflict = True
        #                 for cage_ in cages:
        #                     if cage_ != cage:
        #                         combinations_ = cage_.combinations.copy()
        #                         for combination_ in combinations_.copy():
        #                             if not set(combination_).intersection(combination):
        #                                 conflict = False
        #                                 break
        #                 if conflict:
        #                     cage.combinations -= {combination}
        # for box_row in range(1, 10, box_size):
        #     for box_col in range(1, 10, box_size):
        #         cells = set()
        #         cages = set()
        #         for row in range(box_row, box_row + box_size):
        #             for col in range(box_col, box_col + box_size):
        #                 cells.add(cell_dict.get((row, col)))
        #         for cell in cells:
        #             cages.add(self.cages[cell.cage])
        #         for cage in cages.copy():
        #             if any(cell not in cells for cell in cage.cells):
        #                 cages -= {cage}
        #             if cage.solved:
        #                 cages -= {cage}
        #         if len(cages) >= 2:
        #             for cage in cages:
        #                 for combination in cage.combinations.copy():
        #                     conflict = True
        #                     for cage_ in cages:
        #                         if cage_ != cage:
        #                             combinations_ = cage_.combinations.copy()
        #                             for combination_ in combinations_.copy():
        #                                 if not set(combination_).intersection(combination):
        #                                     conflict = False
        #                                     break
        #                     if conflict:
        #                         cage.combinations -= {combination}

        # self.visualization()
        for cage_ in self.cages:
            # 检查每个笼子是否仅一种可能
            if (not cage_.solved) and len(cage_.combinations) == 1:
                cage_.solved = True
            # 检查每个笼子是否有确定数字
            if (not cage_.solved) and cage_.exact_number != set():
                for number in cage_.exact_number:
                    rows = [cell.row for cell in cage_.number_dict[number]]
                    cols = [cell.col for cell in cage_.number_dict[number]]
                    same_row = all(row == rows[0] for row in rows)
                    same_col = all(col == cols[0] for col in cols)
                    box_identifiers = {(row - 1) // 3 * 3 + (col - 1) // 3 for row, col in zip(rows, cols)}
                    same_box = len(box_identifiers) == 1
                    if same_row:
                        for cell in [cell_dict.get((rows[0], col)) for col in range(1, 10)]:
                            if cell not in cage_.cells:
                                cell.exclude({number})
                    if same_col:
                        for cell in [cell_dict.get((row, cols[0])) for row in range(1, 10)]:
                            if cell not in cage_.cells:
                                cell.exclude({number})
                    if same_box:
                        for cell in [cell_dict.get((row, col)) for row, col in
                                     get_cells_in_same_box(rows[0], cols[0])]:
                            if cell not in cage_.cells:
                                cell.exclude({number})
            # 检查每个格子是否仅一种可能
            for cell_ in cage_.cells:
                if (not cell_.solved) and len(cell_.candidates) == 1:
                    cell_.solved = True
                    self.step += 1
                    print(f'[{self.step}] row: {cell_.row}, col: {cell_.col}, solution: {list(cell_.candidates)[0]}')
                    for cell in self.cages[cell_.cage].cells:
                        if cell != cell_:
                            cell.exclude(cell_.candidates)
                    for cell in [cell_dict.get((cell_.row, col)) for col in range(1, 10)]:
                        if cell != cell_:
                            cell.exclude(cell_.candidates)
                    for cell in [cell_dict.get((row, cell_.col)) for row in range(1, 10)]:
                        if cell != cell_:
                            cell.exclude(cell_.candidates)
                    for cell in [cell_dict.get((row, col)) for row, col in
                                 get_cells_in_same_box(cell_.row, cell_.col)]:
                        if cell != cell_:
                            cell.exclude(cell_.candidates)
                    updated = True
            # 检查笼内分布
            if cage_.solved and any(not cell_.solved for cell_ in cage_.cells):
                for number in range(1, 10):
                    if len(cage_.number_dict[number]) > 1:
                        rows = [cell.row for cell in cage_.number_dict[number]]
                        cols = [cell.col for cell in cage_.number_dict[number]]
                        same_row = all(row == rows[0] for row in rows)
                        same_col = all(col == cols[0] for col in cols)
                        box_identifiers = {(row - 1) // 3 * 3 + (col - 1) // 3 for row, col in zip(rows, cols)}
                        same_box = len(box_identifiers) == 1
                        if same_row:
                            for cell in [cell_dict.get((rows[0], col)) for col in range(1, 10)]:
                                if cell not in cage_.cells:
                                    cell.exclude({number})
                        if same_col:
                            for cell in [cell_dict.get((row, cols[0])) for row in range(1, 10)]:
                                if cell not in cage_.cells:
                                    cell.exclude({number})
                        if same_box:
                            for cell in [cell_dict.get((row, col)) for row, col in
                                         get_cells_in_same_box(rows[0], cols[0])]:
                                if cell not in cage_.cells:
                                    cell.exclude({number})

        if updated:
            self.update()

    def rule45(self, cage_max=3):
        # 内
        for row1 in range(1, 10):
            for row2 in range(row1, 10):
                cells = set()
                cages = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = 45 * (row2 - row1 + 1)
                for row in range(row1, row2 + 1):
                    for col in range(1, 10):
                        cells.add(cell_dict.get((row, col)))
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
                        cell in [cell_dict.get((row, col)) for row, col in
                                 get_cells_in_same_box(cell_.row, cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum,
                                                            cage_cells))  # print(f"{row1} to {row2}: {cells_count} cages:{[cage.ID for cage in cages]} known_cells_count:{known_cells_count}")
        for col1 in range(1, 10):
            for col2 in range(col1, 10):
                cells = set()
                cages = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = 45 * (col2 - col1 + 1)
                for col in range(col1, col2 + 1):
                    for row in range(1, 10):
                        cells.add(cell_dict.get((row, col)))
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
                        cell in [cell_dict.get((row, col)) for row, col in
                                 get_cells_in_same_box(cell_.row, cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum,
                                                            cage_cells))  # print(f"{col1} to {col2}: {cells_count} cages:{[cage.ID for cage in cages]} known_cells_count:{known_cells_count}")
        box_size = 3
        for box_row in range(1, 10, box_size):
            for box_col in range(1, 10, box_size):
                cells = set()
                cages = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = 45
                for row in range(box_row, box_row + box_size):
                    for col in range(box_col, box_col + box_size):
                        cells.add(cell_dict.get((row, col)))
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
                        cell in [cell_dict.get((row, col)) for row, col in
                                 get_cells_in_same_box(cell_.row, cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))
        # 外
        for row1 in range(1, 10):
            for row2 in range(row1, 10):
                cells = set()
                cages = set()
                cage_cells = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = - 45 * (row2 - row1 + 1)
                for col in range(row1, row2 + 1):
                    for row in range(1, 10):
                        cells.add(cell_dict.get((row, col)))
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
                        cell in [cell_dict.get((row, col)) for row, col in
                                 get_cells_in_same_box(cell_.row, cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))
        for col1 in range(1, 10):
            for col2 in range(col1, 10):
                cells = set()
                cages = set()
                cage_cells = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = - 45 * (col2 - col1 + 1)
                for col in range(col1, col2 + 1):
                    for row in range(1, 10):
                        cells.add(cell_dict.get((row, col)))
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
                        cell in [cell_dict.get((row, col)) for row, col in
                                 get_cells_in_same_box(cell_.row, cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))
        box_size = 3
        for box_row in range(1, 10, box_size):
            for box_col in range(1, 10, box_size):
                cells = set()
                cages = set()
                cage_cells = set()
                cells_count = 0
                known_cells_count = 0
                cage_sum = -45
                for row in range(box_row, box_row + box_size):
                    for col in range(box_col, box_col + box_size):
                        cells.add(cell_dict.get((row, col)))
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
                if abs(known_cells_count - cells_count) <= cage_max and known_cells_count != cells_count:
                    cell_ = list(cage_cells)[0]
                    if all(cell.cage == cell_.cage for cell in cage_cells):
                        self.cages.extend(self.cages[cell_.cage].split(cage_sum, cage_cells))
                    elif all(cell.row == cell_.row for cell in cage_cells) or all(
                            cell.col == cell_.col for cell in cage_cells) or all(
                        cell in [cell_dict.get((row, col)) for row, col in
                                 get_cells_in_same_box(cell_.row, cell_.col)] for cell in cage_cells):
                        self.cages.append(Cage.virtual_cage(cage_sum, cage_cells))

    def set_number(self, row_, col_, number):
        cell_dict.get((row_, col_)).set_number(number)

    def is_solved(self):
        return all(cell.solved for cell in cell_dict.values())
        # return all(cell.solved for cell in [cell_dict.get((row, col)) for row, col in zip(range(1,10),range(1,10))])

    def visualization(self):
        fig, ax = plt.subplots(figsize=(18, 18))
        for x in range(10):
            ax.axhline(x, color='black', linewidth=1 if x % 3 else 3)
            ax.axvline(x, color='black', linewidth=1 if x % 3 else 3)
        ax.axis('off')

        for i in range(9):
            for j in range(9):
                text = ','.join(str(num) for num in cell_dict.get((i + 1, j + 1)).candidates)
                ax.text(j + 0.5, 8.5 - i, text, va='center', ha='center')

        # plt.savefig(f''step{self.step}'')
        # plt.close()
        plt.show()

    def solve(self):
        loop = 0
        loop_max = 5
        self.update()
        cell_dict.get((4,4)).exclude({2,3,4})
        while not self.is_solved():
            self.rule45()
            self.update()
            loop += 1
            if loop > loop_max:
                break
        print(f"loop:{loop}")
        self.visualization()


if __name__ == "__main__":
    # 27049
    # cage_constraints = [(11, [[0, 1], [0, 2]]), (15, [[0, 3], [0, 4], [1, 4]]), (16, [[0, 5], [0, 6], [1, 5], [1, 6]]),
    #                     (10, [[0, 0], [1, 0], [2, 0]]), (19, [[1, 2], [1, 3], [2, 3]]),
    #                     (20, [[0, 7], [0, 8], [1, 7], [1, 8]]), (11, [[1, 1], [2, 1]]),
    #                     (22, [[2, 7], [2, 8], [3, 7], [3, 8]]), (20, [[3, 0], [3, 1], [4, 0], [5, 0]]),
    #                     (6, [[2, 2], [3, 2]]), (22, [[3, 3], [3, 4], [4, 4], [4, 5], [5, 5]]),
    #                     (31, [[2, 4], [2, 5], [2, 6], [3, 5], [3, 6], [4, 6]]), (10, [[4, 2], [4, 3]]),
    #                     (15, [[4, 7], [4, 8], [5, 8]]), (14, [[4, 1], [5, 1]]), (13, [[5, 4], [6, 4]]),
    #                     (14, [[5, 6], [5, 7], [6, 7]]), (14, [[5, 2], [5, 3], [6, 2], [6, 3]]), (16, [[6, 5], [6, 6]]),
    #                     (5, [[6, 8], [7, 8]]), (43, [[6, 0], [6, 1], [7, 0], [7, 1], [7, 2], [8, 0], [8, 1], [8, 2]]),
    #                     (15, [[7, 3], [7, 4]]), (11, [[7, 5], [8, 3], [8, 4], [8, 5]]), (11, [[7, 6], [7, 7]]),
    #                     (21, [[8, 6], [8, 7], [8, 8]])]

    # 59
    # cage_constraints = [(11, [[5, 7], [6, 6], [6, 7]]), (23, [[0, 3], [0, 4], [1, 4], [1, 5], [2, 4], [2, 5]]),
    #                     (15, [[8, 6], [8, 7], [8, 8]]), (12, [[3, 0], [4, 0], [5, 0]]), (13, [[0, 1], [0, 2], [1, 1]]),
    #                     (13, [[6, 8], [7, 7], [7, 8]]), (19, [[1, 6], [1, 7], [2, 6], [2, 7]]),
    #                     (26, [[3, 6], [3, 7], [4, 6], [4, 7], [4, 8], [5, 8]]), (13, [[0, 5], [0, 6]]),
    #                     (13, [[7, 3], [7, 4]]), (10, [[2, 8], [3, 8]]), (13, [[4, 1], [5, 1]]),
    #                     (21, [[0, 7], [0, 8], [1, 8]]), (12, [[7, 5], [7, 6]]), (15, [[2, 1], [3, 1]]),
    #                     (14, [[5, 5], [5, 6], [6, 5]]), (17, [[0, 0], [1, 0], [2, 0]]),
    #                     (45, [[6, 0], [6, 1], [6, 2], [7, 0], [7, 1], [7, 2], [8, 0], [8, 1], [8, 2]]),
    #                     (11, [[2, 3], [3, 2], [3, 3]]), (40, [[4, 2], [4, 3], [5, 2], [5, 3], [5, 4], [6, 3], [6, 4]]),
    #                     (15, [[1, 2], [1, 3], [2, 2]]), (19, [[8, 3], [8, 4], [8, 5]]),
    #                     (15, [[3, 4], [3, 5], [4, 4], [4, 5]])]

    # 26274
    # cage_constraints = [(26, [[0, 0], [0, 1], [1, 0], [1, 1]]), (13, [[0, 5], [0, 6]]), (17, [[0, 2], [0, 3], [0, 4], [1, 2]]), (8, [[0, 7], [1, 7]]), (23, [[2, 0], [2, 1], [3, 0], [3, 1], [4, 0]]), (11, [[1, 3], [1, 4], [2, 2], [2, 3]]), (30, [[1, 5], [1, 6], [2, 4], [2, 5], [2, 6], [2, 7]]), (17, [[3, 2], [3, 3]]), (4, [[3, 6], [3, 7]]), (23, [[0, 8], [1, 8], [2, 8], [3, 8]]), (11, [[4, 1], [4, 2]]), (9, [[4, 3], [5, 3]]), (11, [[3, 4], [4, 4], [5, 4]]), (8, [[3, 5], [4, 5]]), (16, [[4, 6], [4, 7]]), (11, [[5, 0], [6, 0], [7, 0], [8, 0]]), (8, [[5, 1], [5, 2]]), (11, [[5, 5], [5, 6]]), (39, [[6, 1], [6, 2], [6, 3], [6, 4], [7, 2], [7, 3]]), (15, [[6, 5], [6, 6], [7, 4], [7, 5]]), (28, [[4, 8], [5, 7], [5, 8], [6, 7], [6, 8]]), (16, [[7, 1], [8, 1]]), (22, [[7, 6], [8, 4], [8, 5], [8, 6]]), (10, [[8, 2], [8, 3]]), (18, [[7, 7], [7, 8], [8, 7], [8, 8]])]

    # 26079
    cage_constraints = [(8, [[0, 0], [0, 1]]), (25, [[0, 2], [0, 3], [0, 4], [0, 5], [0, 6]]), (12, [[0, 7], [0, 8]]),
                        (25, [[1, 0], [1, 1], [2, 0], [3, 0]]), (23, [[1, 7], [1, 8], [2, 8], [3, 8]]),
                        (28, [[1, 2], [2, 1], [2, 2], [3, 2], [4, 2]]), (6, [[1, 3], [2, 3]]), (14, [[1, 4], [2, 4]]),
                        (6, [[1, 5], [2, 5]]), (23, [[1, 6], [2, 6], [2, 7], [3, 6], [4, 6]]),
                        (14, [[3, 3], [3, 4], [3, 5]]), (5, [[3, 1], [4, 1]]), (13, [[4, 3], [4, 4], [4, 5]]),
                        (11, [[3, 7], [4, 7]]), (18, [[4, 0], [5, 0], [6, 0]]), (14, [[4, 8], [5, 8], [6, 8]]),
                        (13, [[5, 1], [6, 1]]), (14, [[5, 2], [6, 2]]), (16, [[5, 3], [6, 3], [7, 3]]),
                        (7, [[5, 4], [6, 4]]), (20, [[5, 5], [6, 5], [7, 5]]), (8, [[5, 6], [6, 6]]),
                        (5, [[5, 7], [6, 7]]), (22, [[7, 1], [7, 2], [8, 2], [8, 3]]),
                        (22, [[7, 6], [7, 7], [8, 5], [8, 6]]), (10, [[7, 0], [8, 0], [8, 1]]), (8, [[7, 4], [8, 4]]),
                        (15, [[7, 8], [8, 7], [8, 8]])]

    killer_solver = KillerSudokuSolver(cage_constraints=cage_constraints)

    killer_solver.solve()

    # with open("solution.txt", "w") as file:
    #     original_stdout = sys.stdout
    #     sys.stdout = file
    #
    #     killer_solver.solve()
    #
    #     sys.stdout = original_stdout
