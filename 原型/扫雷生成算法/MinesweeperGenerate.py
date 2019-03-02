from enum import Enum
from abc import abstractmethod, ABCMeta

class CellStatus(Enum):
    '''
    每个格子的状态

    Space = 0: 已被点开的空的无数字的格子
    _1 = 1: 已被点开的标着数字1的格子
    _2 = 2: 已被点开的标着数字2的格子
    _3 = 3: 已被点开的标着数字3的格子
    _4 = 4: 已被点开的标着数字4的格子
    _5 = 5: 已被点开的标着数字5的格子
    _6 = 6: 已被点开的标着数字6的格子
    _7 = 7: 已被点开的标着数字7的格子
    _8 = 8: 已被点开的标着数字8的格子
    Unknown = 9: 未被点开的未标旗子的格子
    Flagged = 10: 未被点开的已标旗子的格子

    用于扫雷AI的状态
    ToFlag = 11: Unknown状态下的格子,已计算出此格子必然是雷,准备标旗子
    ToSpace = 12: Unknown状态下的格子,已计算出此格子必然不是雷,准备点开
    ToFlagOrSpace = 13: Unknown状态下的格子,已计算出此格子不确定是否有雷
    '''
    Space = 0
    _1 = 1
    _2 = 2
    _3 = 3
    _4 = 4
    _5 = 5
    _6 = 6
    _7 = 7
    _8 = 8
    Unknown = 9
    Flagged = 10
    ToFlag = 11
    ToSpace = 12
    ToFlagOrSpace = 13

class BoardSizeError(Exception):
    '''
    异常:
        生成的棋盘太小
    '''
    def __init__(self, msg):
        self.message = msg

class XYCheckError(Exception):
    '''
    异常:
        点坐标不合法
    '''
    def __init__(self, msg):
        self.message = msg

class MineCountError(Exception):
    '''
    异常:
        雷数太多, 或雷数小于1
    '''
    def __init__(self, msg):
        self.message = msg

class BoardInfo:
    '''
    棋盘信息

    Width: 棋盘的宽
    Height: 棋盘的高
    '''
    def __init__(self, width = None, height = None):
        self.Width = width
        self.Height = height

        if width < 4 or height < 4:
            raise BoardSizeError('宽度、高度太小')

    def MaxMineCount(self):
        '棋盘最大雷数，用于棋盘生成'
        return self.Width * self.Height - 9

    def xycheck(self, x, y):
        '''
        检测一个点的坐标是否合法

        参数:
            x: 横坐标 ∈[0,Width)
            y: 纵坐标 ∈[0,Height)

        返回值:
            无

        异常:
            XYCheckError
        '''
        if x < 0 or x >= self.Width or y < 0 or y >= self.Height:
            raise XYCheckError('坐标 ({}, {}) 不合法, 棋盘宽: {}, 棋盘高: {}'.format(x, y, self.Width, self.Height))

class MinesweeperGenerator(metaclass=ABCMeta):
    '用于生成扫雷棋盘的接口类'
    @abstractmethod
    def generate(self, mineCount, x, y):
        '''
        生成扫雷棋盘

        参数:
            x: 初始点击点的横坐标 ∈[0,Width)
            y: 初始点击点的纵坐标 ∈[0,Height)

        返回值:
            生成的棋盘, list[list[bool]], 其中True为雷, False为空
        '''
        pass

class MinesweeperOperator(metaclass=ABCMeta):
    '用于操作扫雷的接口类'
    @abstractmethod
    def cell(self, x, y):
        '''
        获取一个扫雷棋盘中的格子的状态

        参数:
            x: 横坐标 ∈[0,Width)
            y: 纵坐标 ∈[0,Height)

        返回值:
            指定格子的状态, CellStatus
        '''
        pass

    @abstractmethod
    def open(self, x, y):
        '''
        点开一个扫雷棋盘中的格子
        只能点CellStatus.Unknown状态的格子

        参数:
            x: 横坐标 ∈[0,Width)
            y: 纵坐标 ∈[0,Height)

        返回值:
            无
        '''
        pass

    @abstractmethod
    def flag(self, x, y):
        '''
        对一个扫雷棋盘中的格子标旗
        只能标旗CellStatus.Unknown状态的格子

        参数:
            x: 横坐标 ∈[0,Width)
            y: 纵坐标 ∈[0,Height)

        返回值:
            无
        '''
        pass

class Minesweeper(MinesweeperOperator, MinesweeperGenerator):
    '''
    扫雷类
    '''
    def __init__(self, width, height):
        self.boardInfo = BoardInfo(width, height)
        self.cells = [[CellStatus.Unknown for _ in range(height)] for _ in range(width)]
        self._3BV = 0
        self.__mineCount = 0

    def generate(self, mineCount, x, y):
        import random, ipdb
        self.boardInfo.xycheck(x, y)
        if mineCount < 1:
            raise MineCountError('雷数小于1')
        elif mineCount > self.boardInfo.MaxMineCount():
            raise MineCountError('雷数大于{}'.format(self.boardInfo.MaxMineCount()))
        self.__mineCount = mineCount
        size = self.boardInfo.Width * self.boardInfo.Height

        if x in [0, self.boardInfo.Width - 1] and y in [0, self.boardInfo.Height - 1]:
            # 在角落
            size -= 4
        elif x in [0, self.boardInfo.Width - 1] or y in [0, self.boardInfo.Height - 1]:
            # 在边上，非角落
            size -= 6
        else:
            # 在中间区域
            size -= 9

        minelist = [True] * mineCount + [False] * (size - mineCount)
        random.shuffle(minelist)
        cI = 0
        self.__mines = []
        for i in range(self.boardInfo.Width):
            col = []
            for j in range(self.boardInfo.Height):
                if abs(x-i) < 2 and abs(y-j) < 2:
                    col.append(False)
                else:
                    assert cI < size
                    col.append(minelist[cI])
                    cI += 1
            self.__mines.append(col)
        assert cI == size

        tempCells = []
        for i in range(self.boardInfo.Width):
            col = []
            for j in range(self.boardInfo.Height):
                if self.__mines[i][j]:
                    col.append(2)
                elif any([self.__mines[ii][jj] for ii, jj in self.__neighbours(i, j)]):
                    col.append(1)
                else:
                    col.append(0)
            tempCells.append(col)
        def floodfill(i, j):
            if tempCells[i][j] == 2:
                return
            b = tempCells[i][j] == 0
            tempCells[i][j] = 2
            if b:
                for ii, jj in self.__neighbours(i, j):
                    floodfill(ii, jj)

        self._3BV = 0
        for i in range(self.boardInfo.Width):
            for j in range(self.boardInfo.Height):
                if tempCells[i][j] == 0:
                    self._3BV += 1
                    floodfill(i, j)
        print(self._3BV)
        for i in range(self.boardInfo.Width):
            for j in range(self.boardInfo.Height):
                assert tempCells[i][j] in [1, 2]
                if tempCells[i][j] != 2:
                    self._3BV += 1

    def cell(self, x, y):
        self.boardInfo.xycheck(x, y)
        return self.cells[x][y]

    def open(self, x, y):
        self.boardInfo.xycheck(x, y)
        if self.__mines[x][y]:
            return False

        self.__open_expand(x, y)
        return True

    def flag(self, x, y):
        self.boardInfo.xycheck(x, y)
        if self.cells[x][y] == CellStatus.Flagged:
            self.cells[x][y] = CellStatus.Unknown
        elif self.cells[x][y] == CellStatus.Unknown:
            self.cells[x][y] = CellStatus.Flagged

    def __open_expand(self, x, y):
        '自动展开空白的周围'
        if self.cells[x][y] != CellStatus.Unknown:
            return

        self.cells[x][y] = CellStatus(sum([1 if self.__mines[i][j] else 0 for i,j in self.__neighbours(x, y)]))
        if self.cells[x][y] == CellStatus.Space:
            for i, j in self.__neighbours(x, y):
                self.__open_expand(i, j)

    def open_final(self, x, y):
        '当数字与其周围的标旗数相同时，自动展开数字周围'
        if self.cells[x][y].value not in range(1, 9):
            return True

        if self.cells[x][y].value == sum([1 if self.cells[i][j] == CellStatus.Flagged else 0 for i, j in self.__neighbours(x, y)]):
            for i, j in self.__neighbours(x, y):
                if self.cells[i][j] == CellStatus.Unknown:
                    if not self.open(i, j):
                        return False
        return True

    def is_win(self):
        for i in range(self.boardInfo.Width):
            for j in range(self.boardInfo.Height):
                if not self.__mines[i][j] and self.cells[i][j].value >= 9:
                    return False
        return True

    def remain_mines(self):
        return self.__mineCount - sum([1 if cell == CellStatus.Flagged else 0 for col in self.cells for cell in col])

    def __neighbours(self, x, y):
        '生成邻居列表'
        return [ 
            (i, j)
            for i in range(max(0, x-1), min(self.boardInfo.Width, x+2))
                for j in range(max(0, y-1), min(self.boardInfo.Height, y+2))
        ]

