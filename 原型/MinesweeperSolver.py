from MinesweeperGenerate import MinesweeperOperator, CellStatus
from enum import Enum
from abc import abstractmethod, abstractproperty, ABCMeta
import time

class CheckState(Enum):
    error = 0
    flag = 1
    space = 2
    flag_or_space = 3

class MinesweeperSaverInterface(metaclass=ABCMeta):
    @abstractmethod
    def run(self, debug_print=False):
        pass

    @abstractproperty
    def is_guess(self):
        pass

class MinesweeperSolverBase(MinesweeperSaverInterface):
    def __init__(self, msOp: MinesweeperOperator):
        self._cells = msOp.all_cells
        assert all([len(self._cells[0]) == len(self._cells[i]) for i in range(1, len(self._cells))])
        self._width = len(self._cells)
        self._height = len(self._cells[0])
        self.__remain_mines = msOp.remain_mines
        self.__results = []
        self.__probability = None
        self.__runCount = 0

    @property
    def is_guess(self):
        return False

    @property
    def probability(self):
        return self.__probability

    @abstractmethod
    def _i2xy(self, index: int):
        pass

    @abstractproperty
    def _size(self):
        pass

    @abstractmethod
    def _append_convert(self, cells, count):
        pass

    @abstractmethod
    def _in_count(self, count, other: bool):
        pass

    def __run(self, index: int, count):
        self.__runCount += 1
        if index > self._size:
            return
        if index == self._size:
            t = self._append_convert(self._cells, count)
            if t is not None:
                self.__results.append(t)
            return
        x, y = self._i2xy(index)
        if self._cells[x][y] != CellStatus.Unknown:
            self.__run(index + 1, count)
            return
        cs = self._check(x, y)
        if cs == CheckState.space:
            t, self._cells[x][y] = self._cells[x][y], CellStatus.ToSpace
            self.__run(index + 1, count)
            self._cells[x][y] = t
        elif cs == CheckState.flag:
            if count > 0:
                t, self._cells[x][y] = self._cells[x][y], CellStatus.ToFlag
                self.__run(index + 1, count - 1)
                self._cells[x][y] = t
        elif cs == CheckState.flag_or_space:
            t = self._cells[x][y]
            if count > 0:
                self._cells[x][y] = CellStatus.ToFlag
                self.__run(index + 1, count - 1)
            self._cells[x][y] = CellStatus.ToSpace
            self.__run(index + 1, count)
            self._cells[x][y] = t

    def run(self, debug_print=False):
        flags = set()
        spaces = set()
        s = 0
        if debug_print:
            s=time.time()
        self.__run(0, self.__remain_mines)
        if debug_print:
            print(f'run count: {self.__runCount}')
            print(f'self.__run time: {time.time() - s}s')
            s = time.time()
        allCount = sum([self._in_count(_count, False) for _, _count in self.__results])
        if allCount < 1:
            return (flags, spaces)
        if debug_print:
            print(f'allCount time: {time.time() - s}s')
            s = time.time()
        self.__probability = [[None for _ in range(self._height)] for _ in range(self._width)]
        def prob_add(x, y, val):
            if self.__probability[x][y] is None:
                self.__probability[x][y] = val
            else:
                self.__probability[x][y] += val
        for __cells, _count in self.__results:
            for i in range(self._width):
                for j in range(self._height):
                    if __cells[i][j] == CellStatus.ToFlagOrSpace:
                        self._cells[i][j] = CellStatus.ToFlagOrSpace
                        prob_add(i, j, self._in_count(_count, True))
                    elif __cells[i][j] == CellStatus.ToFlag:
                        if self._cells[i][j] == CellStatus.Unknown:
                            self._cells[i][j] = CellStatus.ToFlag
                        elif self._cells[i][j] == CellStatus.ToSpace:
                            self._cells[i][j] = CellStatus.ToFlagOrSpace
                        prob_add(i, j, self._in_count(_count, False))
                    elif __cells[i][j] == CellStatus.ToSpace:
                        if self._cells[i][j] == CellStatus.Unknown:
                            self._cells[i][j] = CellStatus.ToSpace
                        elif self._cells[i][j] == CellStatus.ToFlag:
                            self._cells[i][j] = CellStatus.ToFlagOrSpace
                        prob_add(i, j, 0)
        if debug_print:
            print(f'for for time: {time.time() - s}s')
            s = time.time()
        for i in range(self._width):
            for j in range(self._height):
                if self._cells[i][j] == CellStatus.ToFlag:
                    flags.add((i, j))
                elif self._cells[i][j] == CellStatus.ToSpace:
                    spaces.add((i, j))
                if self.__probability[i][j] is not None:
                    self.__probability[i][j] /= allCount
        if debug_print:
            print(f'for for 2 time: {time.time() - s}s')
        return (flags, spaces)

    def __xycheck(self, x, y):
        assert x >= 0
        assert x < self._width
        assert y >= 0
        assert y < self._height

    def _neighbours(self, x, y):
        '生成邻居列表'
        self.__xycheck(x, y)
        return [ 
            (i, j)
            for i in range(max(0, x-1), min(self._width, x+2))
                for j in range(max(0, y-1), min(self._height, y+2))
        ]

    def _check(self, x: int, y: int):
        '通过检测周围空白数来判断指定格是否是雷'
        self.__xycheck(x, y)
        assert self._cells[x][y] == CellStatus.Unknown

        state = CheckState.flag_or_space
        for i, j in self._neighbours(x, y):
            if state == CheckState.error:
                break
            if self._cells[i][j].value > 8:
                continue
            cmin, cmax = 0, 0
            for ii, jj in self._neighbours(i, j):
                if self._cells[ii][jj] in [CellStatus.Flagged, CellStatus.ToFlag]:
                    cmin += 1
                    cmax += 1
                elif self._cells[ii][jj] == CellStatus.Unknown:
                    cmax += 1
            if cmin > self._cells[i][j].value:
                return CheckState.error
            if cmax < self._cells[i][j].value:
                return CheckState.error
            if cmin == self._cells[i][j].value:
                state = CheckState(state.value & CheckState.space.value)
            if cmax == self._cells[i][j].value:
                state = CheckState(state.value & CheckState.flag.value)
        return state

class MinesweeperSolverByWalkAll(MinesweeperSolverBase):
    def __init__(self, msOp: MinesweeperOperator):
        super().__init__(msOp)

    def _i2xy(self, index: int):
        return (index // self._height, index % self._height)

    @property
    def _size(self):
        return self._width * self._height

    def _append_convert(self, cells, count):
        import copy
        if count != 0:
            return None
        return (copy.deepcopy(cells), 0)

    def _in_count(self, count, other: bool):
        return 1

class MinesweeperSolverByFloodfill(MinesweeperSolverBase):
    def __init__(self, msOp: MinesweeperOperator):
        super().__init__(msOp)
        self.__edges = []
        self.__ins = []
        self.__cns = []
        self.__cn_1s = []

    def __split_cells(self):
        tempCells = []
        def isSpace(i, j):
            assert self._cells[i][j] != CellStatus.ToFlagOrSpace
            return self._cells[i][j].value < 9 or self._cells[i][j] == CellStatus.ToSpace
        self.__edges = []
        self.__ins = []
        for i in range(self._width):
            for j in range(self._height):
                if isSpace(i, j):
                    pass
                elif any([isSpace(ii, jj) for ii, jj in self._neighbours(i, j)]):
                    if self._cells[i][j] == CellStatus.Unknown:
                        self.__edges.append((i, j))
                else:
                    self.__ins.append((i, j))

    def run(self, debug_print=False):
        self.__split_cells()
        flags = set()
        spaces = set()
        for x, y in self.__edges:
            cs = self._check(x, y)
            assert cs != CheckState.error
            if cs == CheckState.space:
                spaces.add((x, y))
            elif cs == CheckState.flag:
                flags.add((x, y))
        if len(flags) + len(spaces) > 0:
            return (flags, spaces)
        import math
        C = lambda n, m: math.factorial(n) // math.factorial(m) // math.factorial(n - m)
        for i in range(len(self.__ins)):
            self.__cn_1s.append(C(len(self.__ins) - 1, i))
        for i in range(len(self.__ins) + 1):
            self.__cns.append(C(len(self.__ins), i))

        return MinesweeperSolverBase.run(self, debug_print)

    def _i2xy(self, index: int):
        assert index >= 0 and index < len(self.__edges)
        return self.__edges[index]

    @property
    def _size(self):
        return len(self.__edges)

    def _append_convert(self, cells, count):
        import copy
        if count > len(self.__ins):
            return None
        tc = copy.deepcopy(cells)
        if count == 0:
            for i, j in self.__ins:
                tc[i][j] = CellStatus.ToSpace
        elif count == len(self.__ins):
            for i, j in self.__ins:
                tc[i][j] = CellStatus.ToFlag
        else:
            for i, j in self.__ins:
                tc[i][j] = CellStatus.ToFlagOrSpace
        return (copy.deepcopy(tc), count)

    def _in_count(self, count, other: bool):
        assert count <= len(self.__ins)
        assert count >= 0
        if other:
            assert count > 0
            return self.__cn_1s[count - 1]
        else:
            return self.__cns[count]

class MinesweeperSolverByFloodfillAndGroup(MinesweeperSolverBase):
    '''
    边界分组
    '''
    def __init__(self, msOp: MinesweeperOperator):
        super().__init__(msOp)
        self.__edges = []
        self.__ins = []
        self.__cns = []
        self.__cn_1s = []
        self.__all_edges = []
        self.__true_ins = []

    def __split_cells(self):
        tempCells = []
        def isSpace(i, j):
            assert self._cells[i][j] != CellStatus.ToFlagOrSpace
            return self._cells[i][j].value < 9 or self._cells[i][j] == CellStatus.ToSpace
        edges = {}
        self.__true_ins = []
        for i in range(self._width):
            for j in range(self._height):
                if isSpace(i, j):
                    pass
                elif any([isSpace(ii, jj) for ii, jj in self._neighbours(i, j)]):
                    if self._cells[i][j] == CellStatus.Unknown:
                        edges[(i, j)]=[]
                else:
                    self.__true_ins.append((i, j))
        for i, j in edges:
            for ii, jj in self._neighbours(i, j):
                if self._cells[ii][jj].value < 9 or (ii, jj) in edges:
                    edges[(i, j)].append((ii, jj))
        group_cells = {}
        for i, j in edges:
            for ii, jj in edges[(i, j)]:
                if (ii, jj) not in group_cells:
                    group_cells[(ii, jj)] = set()
                group_cells[(ii, jj)].add((i, j))
        same_group_cells = {k: set([k]) for k in edges}
        for k in group_cells:
            if k in edges:
                same_group_cells[k] |= group_cells[k]
            else:
                for kk in group_cells[k]:
                    same_group_cells[kk] |= group_cells[k]
        group_id = [[None for _ in range(self._height)] for _ in range(self._width)]
        curId = 0
        def fill_id(k):
            if group_id[k[0]][k[1]] is not None:
                return
            group_id[k[0]][k[1]] = curId
            for v in same_group_cells[k]:
                fill_id(v)
        for i in range(self._width):
            for j in range(self._height):
                if (i, j) in same_group_cells and (i, j) not in group_id:
                    fill_id((i, j))
                    curId += 1
        self.__all_edges = [[] for _ in range(curId)]
        for i in range(self._width):
            for j in range(self._height):
                if group_id[i][j] is not None:
                    self.__all_edges[group_id[i][j]].append((i, j))
        # TODO: edge生成完成， 下一步改run

    def run(self, debug_print=False):
        self.__split_cells()
        flags = set()
        spaces = set()
        for edges in self.__all_edges:
            for x, y in edges:
                cs = self._check(x, y)
                assert cs != CheckState.error
                if cs == CheckState.space:
                    spaces.add((x, y))
                elif cs == CheckState.flag:
                    flags.add((x, y))
        if len(flags) + len(spaces) > 0:
            return (flags, spaces)
        import math
        C = lambda n, m: math.factorial(n) // math.factorial(m) // math.factorial(n - m)

        for k in range(len(self.__all_edges)):
            self.__ins = self.__true_ins + [v for kk in range(len(self.__all_edges)) if kk != k for v in self.__all_edges[kk]]
            for i in range(len(self.__ins)):
                self.__cn_1s.append(C(len(self.__ins) - 1, i))
            for i in range(len(self.__ins) + 1):
                self.__cns.append(C(len(self.__ins), i))

            self.__edges = self.__all_edges[k]
            flags, spaces = MinesweeperSolverBase.run(self, debug_print)
            if len(flags) + len(spaces) > 0:
                return (flags, spaces)

        return (set(), set())

    def _i2xy(self, index: int):
        assert index >= 0 and index < len(self.__edges)
        return self.__edges[index]

    @property
    def _size(self):
        return len(self.__edges)

    def _append_convert(self, cells, count):
        import copy
        if count > len(self.__ins):
            return None
        tc = copy.deepcopy(cells)
        if count == 0:
            for i, j in self.__ins:
                tc[i][j] = CellStatus.ToSpace
        elif count == len(self.__ins):
            for i, j in self.__ins:
                tc[i][j] = CellStatus.ToFlag
        else:
            for i, j in self.__ins:
                tc[i][j] = CellStatus.ToFlagOrSpace
        return (copy.deepcopy(tc), count)

    def _in_count(self, count, other: bool):
        assert count <= len(self.__ins)
        assert count >= 0
        if other:
            assert count > 0
            return self.__cn_1s[count - 1]
        else:
            return self.__cns[count]

class CellInfo:
    def __init__(self, i, j, width, height, cells):
        self.__pos = (i, j)
        self.__x = i
        self.__y = j
        self.__info = cells[i][j]
        self.__neighbours = {CellStatus(i): set() for i in range(11)}
        for ii in range(max(0, i-1), min(width, i+2)):
            for jj in range(max(0, j-1), min(height, j+2)):
                if ii != i or jj != j:
                    self.__neighbours[cells[ii][jj]].add((ii, jj))
        self.__advance_num_neighbours = {
            (ii, jj) : {
                'common': set(),
                'only' : set(),
                'other' : set()
            }
            for ii in range(max(0, i-2), min(width, i+3))
                for jj in range(max(0, j-2), min(height, j+3))
                    if (ii != i or jj != j) and cells[ii][jj].value > 0 and cells[ii][jj].value < 9
        }

    @property
    def pos(self):
        return self.__pos

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def info(self):
        return self.__info

    @property
    def neighbours(self):
        return self.__neighbours

    @property
    def advance_num_neighbours(self):
        return self.__advance_num_neighbours

    def init_advance_num_neighbours(self, cellInfos):
        for pos in self.__advance_num_neighbours:
            self.__advance_num_neighbours[pos]['common'] = self.__neighbours[CellStatus.Unknown] & cellInfos[pos].neighbours[CellStatus.Unknown]
            self.__advance_num_neighbours[pos]['only'] = self.__neighbours[CellStatus.Unknown] - cellInfos[pos].neighbours[CellStatus.Unknown]
            self.__advance_num_neighbours[pos]['other'] = cellInfos[pos].neighbours[CellStatus.Unknown] - self.__neighbours[CellStatus.Unknown]

class MinesweeperSolverByNumber(MinesweeperSaverInterface):
    def __init__(self, msOp: MinesweeperOperator):
        self._cells = msOp.all_cells
        assert all([len(self._cells[0]) == len(self._cells[i]) for i in range(1, len(self._cells))])
        self._width = len(self._cells)
        self._height = len(self._cells[0])
        self.__is_guess = False
        self.is_advance = False
        self._cellInfos = {
            (i, j) :
                CellInfo(i, j, self._width, self._height, self._cells)
                for i in range(self._width)
                    for j in range(self._height)
        }
        for pos in self._cellInfos:
            self._cellInfos[pos].init_advance_num_neighbours(self._cellInfos)
        self._numsWithUnknown = dict(filter(lambda item: item[1].info.value > 0 and item[1].info.value < 9 and len(item[1].neighbours[CellStatus.Unknown]) > 0, self._cellInfos.items()))

    def run(self):
        self.__to_flags = set()
        self.__to_spaces = set()

        self.__basic_solver()
        if len(self.__to_flags) + len(self.__to_spaces) > 0:
            return (self.__to_flags, self.__to_spaces)
        self.__advance_solver()
        if len(self.__to_flags) + len(self.__to_spaces) > 0:
            self.is_advance = True
            return (self.__to_flags, self.__to_spaces)
        self.__guess_solver()
        assert len(self.__to_spaces) > 0
        return (self.__to_flags, self.__to_spaces)

    def __basic_solver(self):
        for k, cellInfo in self._numsWithUnknown.items():
            if cellInfo.info.value == len(cellInfo.neighbours[CellStatus.Flagged]):
                self.__to_spaces |= cellInfo.neighbours[CellStatus.Unknown]
            elif cellInfo.info.value == len(cellInfo.neighbours[CellStatus.Flagged]) + len(cellInfo.neighbours[CellStatus.Unknown]):
                self.__to_flags |= cellInfo.neighbours[CellStatus.Unknown]
            else:
                assert cellInfo.info.value > len(cellInfo.neighbours[CellStatus.Flagged])
                assert cellInfo.info.value < len(cellInfo.neighbours[CellStatus.Flagged]) + len(cellInfo.neighbours[CellStatus.Unknown])

    def __advance_solver(self):
        for pos, cellInfo in self._numsWithUnknown.items():
            for opos, neighbourInfo in self._cellInfos[pos].advance_num_neighbours.items():
                selfVal = cellInfo.info.value - len(cellInfo.neighbours[CellStatus.Flagged])
                otherVal = self._cellInfos[opos].info.value - len(self._cellInfos[opos].neighbours[CellStatus.Flagged])
                if selfVal == otherVal:
                    if len(neighbourInfo['only']) < 1:
                        self.__to_spaces |= neighbourInfo['other']
                elif selfVal > otherVal:
                    assert len(neighbourInfo['only']) >= selfVal - otherVal
                    if len(neighbourInfo['only']) == selfVal - otherVal:
                        self.__to_flags |= neighbourInfo['only']
                        self.__to_spaces |= neighbourInfo['other']
        # TODO:
        '''
        @1
        @21
        x@@

        @1
        @31
        f@@
        '''
        assert len(self.__to_flags & self.__to_spaces) < 1

    def __guess_solver(self):
        unknowns = list(set([cell for pos, cellInfo in self._numsWithUnknown.items() for cell in cellInfo.neighbours[CellStatus.Unknown]]))
        from random import choice
        self.__to_spaces.add(choice(unknowns))
        self.__is_guess = True

    @property
    def is_guess(self):
        return self.__is_guess
