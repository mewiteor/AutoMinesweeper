from MinesweeperGenerate import MinesweeperOperator, CellStatus
from enum import Enum
from abc import abstractmethod, abstractproperty, ABCMeta
import time

class CellStatusEx(Enum):
    '''
    扫雷AI中每个格子的状态
    ToFlag = 11: Unknown状态下的格子,已计算出此格子必然是雷,准备标旗子
    ToSpace = 12: Unknown状态下的格子,已计算出此格子必然不是雷,准备点开
    ToFlagOrSpace = 13: Unknown状态下的格子,已计算出此格子不确定是否有雷
    '''
    ToFlag = 11
    ToSpace = 12
    ToFlagOrSpace = 13

class CheckState(Enum):
    error = 0
    flag = 1
    space = 2
    flag_or_space = 3

class MinesweeperSolverBase(metaclass=ABCMeta):
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
            t, self._cells[x][y] = self._cells[x][y], CellStatusEx.ToSpace
            self.__run(index + 1, count)
            self._cells[x][y] = t
        elif cs == CheckState.flag:
            if count > 0:
                t, self._cells[x][y] = self._cells[x][y], CellStatusEx.ToFlag
                self.__run(index + 1, count - 1)
                self._cells[x][y] = t
        elif cs == CheckState.flag_or_space:
            t = self._cells[x][y]
            if count > 0:
                self._cells[x][y] = CellStatusEx.ToFlag
                self.__run(index + 1, count - 1)
            self._cells[x][y] = CellStatusEx.ToSpace
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
                    if __cells[i][j] == CellStatusEx.ToFlagOrSpace:
                        self._cells[i][j] = CellStatusEx.ToFlagOrSpace
                        prob_add(i, j, self._in_count(_count, True))
                    elif __cells[i][j] == CellStatusEx.ToFlag:
                        if self._cells[i][j] == CellStatus.Unknown:
                            self._cells[i][j] = CellStatusEx.ToFlag
                        elif self._cells[i][j] == CellStatusEx.ToSpace:
                            self._cells[i][j] = CellStatusEx.ToFlagOrSpace
                        prob_add(i, j, self._in_count(_count, False))
                    elif __cells[i][j] == CellStatusEx.ToSpace:
                        if self._cells[i][j] == CellStatus.Unknown:
                            self._cells[i][j] = CellStatusEx.ToSpace
                        elif self._cells[i][j] == CellStatusEx.ToFlag:
                            self._cells[i][j] = CellStatusEx.ToFlagOrSpace
                        prob_add(i, j, 0)
        if debug_print:
            print(f'for for time: {time.time() - s}s')
            s = time.time()
        for i in range(self._width):
            for j in range(self._height):
                if self._cells[i][j] == CellStatusEx.ToFlag:
                    flags.add((i, j))
                elif self._cells[i][j] == CellStatusEx.ToSpace:
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
                if self._cells[ii][jj] in [CellStatus.Flagged, CellStatusEx.ToFlag]:
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
            assert self._cells[i][j] != CellStatusEx.ToFlagOrSpace
            return self._cells[i][j].value < 9 or self._cells[i][j] == CellStatusEx.ToSpace
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

    def run(self):
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

        return MinesweeperSolverBase.run(self)

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
                tc[i][j] = CellStatusEx.ToSpace
        elif count == len(self.__ins):
            for i, j in self.__ins:
                tc[i][j] = CellStatusEx.ToFlag
        else:
            for i, j in self.__ins:
                tc[i][j] = CellStatusEx.ToFlagOrSpace
        return (copy.deepcopy(tc), count)

    def _in_count(self, count, other: bool):
        assert count <= len(self.__ins)
        assert count >= 0
        if other:
            assert count > 0
            return self.__cn_1s[count - 1]
        else:
            return self.__cns[count]
