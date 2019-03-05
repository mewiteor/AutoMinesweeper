import sys, pickle
from MinesweeperGenerate import Minesweeper, CellStatus
from MinesweeperSolver import MinesweeperSolverByWalkAll, MinesweeperSolverByFloodfill, CellStatusEx
from enum import Enum
from time import time

class MinesweeperOperator(Enum):
    to_open = 1
    to_flag = 2
    to_open_final = 3

def main():
    width = None
    height = None
    mineCount = None
    startx = None
    starty = None

    recordFile = None
    recordData = None

    if len(sys.argv) in [6, 7]:
        # python 自动扫雷.py 宽 高 雷数 起点横坐标 起点纵坐标 [保存录像文件]
        width = int(sys.argv[1])
        height = int(sys.argv[2])
        mineCount = int(sys.argv[3])
        startx = int(sys.argv[4])
        starty = int(sys.argv[5])
        saveFile = None
        if len(sys.argv) == 7:
            saveFile = sys.argv[6]
    elif len(sys.argv) == 2:
        # python 自动扫雷.py 录像文件
        recordFile = sys.argv[1]
    else:
        print('usage:')
        print(f'\tpython {sys.argv[0]} 宽 高 雷数 起点横坐标 起点纵坐标')
        print(f'\tpython {sys.argv[0]} 录像文件')
        return

    if recordFile is not None:
        with open(recordFile, 'rb') as f:
            recordData = pickle.load(f)
        width = recordData['width']
        height = recordData['height']
        mineCount = recordData['mineCount']
        fop = recordData['ops'][0]
        assert fop['type'] == MinesweeperOperator.to_open
        startx = fop['x']
        starty = fop['y']
    ms = Minesweeper(width, height)
    if recordFile is None:
        ms.generate(mineCount, startx, starty)
    else:
        ms.mines = recordData['mines']
        return

    # recordFile is None

    start_time = time()
    ops = []
    nextops = [{'type': MinesweeperOperator.to_open, 'x': startx, 'y': starty}]
    die = False
    while not ms.is_win():
        if len(nextops) < 1:
            solver = MinesweeperSolverByFloodfill(ms)
            toFlags, toSpaces = solver.run()
            needGuess = True
            for x, y in toFlags:
                needGuess = False
                nextops.append({'type': MinesweeperOperator.to_flag, 'x': x, 'y': y})
            for x, y in toSpaces:
                needGuess = False
                nextops.append({'type': MinesweeperOperator.to_open, 'x': x, 'y': y})
            if needGuess:
                print('need guess')
                probability = solver.probability
                cells = ms.all_cells
                ms.show(cells)
                n = None
                for i in range(width):
                    for j in range(height):
                        if probability[i][j] is not None and cells[i][j] == CellStatus.Unknown:
                            if n is None:
                                n = (i, j)
                            elif probability[i][j] < probability[n[0]][n[1]]:
                                n = (i, j)
                if n is not None:
                    print(probability[n[0]][n[1]])
                    nextops.append({'type': MinesweeperOperator.to_open, 'x': n[0], 'y': n[1]})
        op = nextops.pop(0)
        ops.append(op)
        if op['type'] == MinesweeperOperator.to_open:
            print(f'open ({op["x"]},{op["y"]})')
            if not ms.open(op['x'], op['y']):
                print(f'die')
                die = True
                break
        elif op['type'] == MinesweeperOperator.to_flag:
            print(f'flag ({op["x"]},{op["y"]})')
            ms.flag(op['x'], op['y'])
        elif op['type'] == MinesweeperOperator.to_open_final:
            print(f'open final ({op["x"]},{op["y"]})')
            if not ms.open_final(op['x'], op['y']):
                print(f'die')
                die = True
                break
    if not die:
        print('win')
    print(f'time: {time() - start_time}s')
    if saveFile is not None:
        with open(saveFile, 'wb') as f:
            pickle.dump({
                'width': width,
                'height': height,
                'mineCount': mineCount,
                'mines': ms.mines,
                'ops': ops
            })

if __name__ == "__main__":
    main()
