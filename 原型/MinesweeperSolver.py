from MinesweeperGenerate import MinesweeperOperator, CellStatus
from enum import Enum

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

class MinesweeperSolver:
    def __init__(self, msOp: MinesweeperOperator):
        self.__msOp = msOp
        self.__cells = msOp.all_cells()
        assert all([len(self.__cells[0]) == len(self.__cells[i]) for i in range(1, len(self.__cells))])
        self.__width = len(self.__cells)
        self.__height = len(self.__cells[0])

    def __xycheck(self, x, y):
        assert x >= 0
        assert x < self.__width
        assert y >= 0
        assert y < self.__height

    def __neighbours(self, x, y):
        '生成邻居列表'
        self.__xycheck(x, y)
        return [ 
            (i, j)
            for i in range(max(0, x-1), min(self.__width, x+2))
                for j in range(max(0, y-1), min(self.__height, y+2))
        ]

    def __check(self, x: int, y: int):
        '通过检测周围空白数来判断指定格是否是雷'
        self.__xycheck(x, y)
        assert self.__cells[x][y] == CellStatus.Unknown

        state = CheckState.flag_or_space
        for i, j in self.__neighbours(x, y):
            if state == CheckState.error:
                break
            if self.__cells[i][j].value > 8:
                continue
            cmin, cmax = 0, 0
            for ii, jj in self.__neighbours(i, j):
                if self.__cells[ii][jj] in [CellStatus.Flagged, CellStatusEx.ToFlag]:
                    cmin += 1
                    cmax += 1
                elif self.__cells[ii][jj] == CellStatus.Unknown:
                    cmax += 1
            if cmin > self.__cells[i][j].value:
                return CheckState.error
            if cmax < self.__cells[i][j].value:
                return CheckState.error
            if cmin == self.__cells[i][j].value:
                state = CheckState(state.value & CheckState.space.value)
            if cmax == self.__cells[i][j].value:
                state = CheckState(state.value & CheckState.flag.value)
        return state

    def walkAll(self):
        results = []
        def i2xy(index: int):
            return (index // self.__height, index % self.__height)
        runCount = 0
        def run(index: int, count):
            import copy
            if index > self.__width * self.__height:
                return
            if index == self.__width * self.__height:
                if count == 0:
                    results.append(copy.deepcopy(self.__cells))
                return
            x, y = i2xy(index)
            if self.__cells[x][y] != CellStatus.Unknown:
                run(index + 1, count)
                return
            cs = self.__check(x, y)
            if cs == CheckState.space:
                t, self.__cells[x][y] = self.__cells[x][y], CellStatusEx.ToSpace
                run(index + 1, count)
                self.__cells[x][y] = t
            elif cs == CheckState.flag:
                if count > 0:
                    t, self.__cells[x][y] = self.__cells[x][y], CellStatusEx.ToFlag
                    run(index + 1, count - 1)
                    self.__cells[x][y] = t
            elif cs == CheckState.flag_or_space:
                t = self.__cells[x][y]
                if count > 0:
                    self.__cells[x][y] = CellStatusEx.ToFlag
                    run(index + 1, count - 1)
                self.__cells[x][y] = CellStatusEx.ToSpace
                run(index + 1, count)
                self.__cells[x][y] = t
        run(0, self.__msOp.remain_mines())
        for _cells in results:
            for i in range(self.__width):
                for j in range(self.__height):
                    if _cells[i][j] == CellStatusEx.ToFlag:
                        if self.__cells[i][j] == CellStatus.Unknown:
                            self.__cells[i][j] = CellStatusEx.ToFlag
                        elif self.__cells[i][j] == CellStatusEx.ToSpace:
                            self.__cells[i][j] = CellStatusEx.ToFlagOrSpace
                    elif _cells[i][j] == CellStatusEx.ToSpace:
                        if self.__cells[i][j] == CellStatus.Unknown:
                            self.__cells[i][j] = CellStatusEx.ToSpace
                        elif self.__cells[i][j] == CellStatusEx.ToFlag:
                            self.__cells[i][j] = CellStatusEx.ToFlagOrSpace
        flags = set()
        spaces = set()
        for i in range(self.__width):
            for j in range(self.__height):
                if self.__cells[i][j] == CellStatusEx.ToFlag:
                    flags.add((i, j))
                elif self.__cells[i][j] == CellStatusEx.ToSpace:
                    spaces.add((i, j))
        return (flags, spaces)

    def walkByFloodfill(self):
        pass
