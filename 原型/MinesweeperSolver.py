from MinesweeperGenerate import MinesweeperOperator, CellStatus
from enum import Enum
from abc import abstractmethod, abstractproperty, ABCMeta

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

class RunForWalk(metaclass=ABCMeta):
    def __init__(self, cells):
        self.__results = []
        self.__walk_cells = cells
        self.__probability = None

    @property
    def probability(self):
        return self.__probability

    @abstractmethod
    def _i2xy(self, index: int):
        pass

    @abstractproperty
    def _size(self):
        pass

    @abstractproperty
    def width(self):
        pass

    @abstractproperty
    def height(self):
        pass

    @abstractmethod
    def _append_convert(self, cells, count):
        pass

    @abstractmethod
    def _walk_check(self, x, y):
        pass

    @abstractproperty
    def _remain_mines(self):
        pass

    @abstractmethod
    def _in_count(self, count, other: bool):
        pass

    def __run(self, index: int, count):
        if index > self._size:
            return
        if index == self._size:
            t = self._append_convert(self.__walk_cells, count)
            if t is not None:
                self.__results.append(t)
            return
        x, y = self._i2xy(index)
        if self.__walk_cells[x][y] != CellStatus.Unknown:
            self.__run(index + 1, count)
            return
        cs = self._walk_check(x, y)
        if cs == CheckState.space:
            t, self.__walk_cells[x][y] = self.__walk_cells[x][y], CellStatusEx.ToSpace
            self.__run(index + 1, count)
            self.__walk_cells[x][y] = t
        elif cs == CheckState.flag:
            if count > 0:
                t, self.__walk_cells[x][y] = self.__walk_cells[x][y], CellStatusEx.ToFlag
                self.__run(index + 1, count - 1)
                self.__walk_cells[x][y] = t
        elif cs == CheckState.flag_or_space:
            t = self.__walk_cells[x][y]
            if count > 0:
                self.__walk_cells[x][y] = CellStatusEx.ToFlag
                self.__run(index + 1, count - 1)
            self.__walk_cells[x][y] = CellStatusEx.ToSpace
            self.__run(index + 1, count)
            self.__walk_cells[x][y] = t

    def run(self):
        flags = set()
        spaces = set()
        self.__run(0, self._remain_mines)
        allCount = sum([self._in_count(_count, False) for _, _count in self.__results])
        if allCount < 1:
            return (flags, spaces)
        self.__probability = [[None for _ in range(self.height)] for _ in range(self.width)]
        def prob_add(x, y, val):
            if self.__probability[x][y] is None:
                self.__probability[x][y] = val
            else:
                self.__probability[x][y] += val
        for _cells, _count in self.__results:
            for i in range(self.width):
                for j in range(self.height):
                    if _cells[i][j] == CellStatusEx.ToFlagOrSpace:
                        self.__walk_cells[i][j] = CellStatusEx.ToFlagOrSpace
                        prob_add(i, j, self._in_count(_count, True))
                    elif _cells[i][j] == CellStatusEx.ToFlag:
                        if self.__walk_cells[i][j] == CellStatus.Unknown:
                            self.__walk_cells[i][j] = CellStatusEx.ToFlag
                        elif self.__walk_cells[i][j] == CellStatusEx.ToSpace:
                            self.__walk_cells[i][j] = CellStatusEx.ToFlagOrSpace
                        prob_add(i, j, self._in_count(_count, False))
                    elif _cells[i][j] == CellStatusEx.ToSpace:
                        if self.__walk_cells[i][j] == CellStatus.Unknown:
                            self.__walk_cells[i][j] = CellStatusEx.ToSpace
                        elif self.__walk_cells[i][j] == CellStatusEx.ToFlag:
                            self.__walk_cells[i][j] = CellStatusEx.ToFlagOrSpace
                        prob_add(i, j, 0)
        for i in range(self.width):
            for j in range(self.height):
                if self.__walk_cells[i][j] == CellStatusEx.ToFlag:
                    flags.add((i, j))
                elif self.__walk_cells[i][j] == CellStatusEx.ToSpace:
                    spaces.add((i, j))
                if self.__probability[i][j] is not None:
                    self.__probability[i][j] /= allCount
        return (flags, spaces)

class MinesweeperSolverBase(metaclass=ABCMeta):
    def __init__(self, msOp: MinesweeperOperator):
        self._msOp = msOp
        self._cells = msOp.all_cells
        assert all([len(self._cells[0]) == len(self._cells[i]) for i in range(1, len(self._cells))])
        self._width = len(self._cells)
        self._height = len(self._cells[0])

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

class MinesweeperSolverByWalkAll(MinesweeperSolverBase, RunForWalk):
    def __init__(self, msOp: MinesweeperOperator):
        MinesweeperSolverBase.__init__(self, msOp)
        RunForWalk.__init__(self, self._cells)
        self.__remain_mines = msOp.remain_mines

    def _i2xy(self, index: int):
        return (index // self._height, index % self._height)

    @property
    def _size(self):
        return self._width * self._height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self.height

    def _append_convert(self, cells, count):
        import copy
        if count != 0:
            return None
        return (copy.deepcopy(cells), 0)

    def _walk_check(self, x, y):
        return self._check(x, y)

    @property
    def _remain_mines(self):
        return self.remain_mines

    def _in_count(self, count, other: bool):
        return 1

class MinesweeperSolverByFloodfill(MinesweeperSolverBase, RunForWalk):
    def __init__(self, msOp: MinesweeperOperator):
        MinesweeperSolverBase.__init__(self, msOp)
        RunForWalk.__init__(self, self._cells)
        self.__edges = []
        self.__ins = []
        self.__remain_mines = msOp.remain_mines

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
        import ipdb
        if self._msOp.debug:
            ipdb.set_trace()
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
        return RunForWalk.run(self)

    def _i2xy(self, index: int):
        assert index >= 0 and index < len(self.__edges)
        return self.__edges[index]

    @property
    def _size(self):
        return len(self.__edges)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

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

    def _walk_check(self, x, y):
        return self._check(x, y)

    @property
    def _remain_mines(self):
        return self.__remain_mines

    def _in_count(self, count, other: bool):
        import math
        C = lambda n, m: math.factorial(n) // math.factorial(m) // math.factorial(n - m)
        if other:
            return C(len(self.__ins) - 1, count - 1)
        else:
            return C(len(self.__ins), count)
