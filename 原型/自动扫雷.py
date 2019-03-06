import sys, pickle
from MinesweeperGenerate import Minesweeper, CellStatus
from MinesweeperSolver import MinesweeperSolverByWalkAll, MinesweeperSolverByFloodfill, CellStatusEx
from enum import Enum
from time import time

class MinesweeperOperator(Enum):
    to_open = 1
    to_flag = 2
    to_open_final = 3

class GameMode(Enum):
    unknown = 0
    new = 1
    load = 2

class AutoRun:
    def __init__(self):
        self.game_mode = GameMode.unknown
        self.win = False
        self.use_time = 0
        self.show_time = False
        self.show_step = False
        self.hide_result = False

    def arg_parse(self):
        import argparse
        parser = argparse.ArgumentParser(description='auto minesweeper')
        parser.add_argument('--show_step', default=False, action='store_true', help='show step info')
        parser.add_argument('--show_time', default=False, action='store_true', help='show time')
        parser.add_argument('--hide_result', default=False, action='store_true', help='show time')

        subparsers = parser.add_subparsers(help='game mode')

        new_game = subparsers.add_parser('new', help='begin a new game')
        new_game.add_argument('width', type=int, help='width of minesweeper board')
        new_game.add_argument('height', type=int, help='height of minesweeper board')
        new_game.add_argument('mineCount', type=int, help='mine count of minesweeper board')
        new_game.add_argument('startx', type=int, help='col for the first click')
        new_game.add_argument('starty', type=int, help='row for the first click')
        new_game.add_argument('-s', '--saveFile', type=str, default=None, help='file path for save')
        new_game.set_defaults(func=self.new_game_func)

        load_game = subparsers.add_parser('load', help='load a game from file')
        load_game.add_argument('recordFile', type=str, help='file path for save')
        load_game.add_argument('-u', '--useOps', action='store_true', default=False, help='use ops (default: not)')
        load_game.set_defaults(func=self.load_game_func)

        args = parser.parse_args()
        self.show_time = args.show_time
        self.show_step = args.show_step
        self.hide_result = args.hide_result
        args.func(args)

    def new_game_func(self, args):
        self.new_game_init(args.width, args.height, args.mineCount, args.startx, args.starty, args.saveFile)

    def load_game_func(self, args):
        self.load_game_init(args.recordFile, args.useOps)

    def new_game_init(self, width, height, mineCount, startx, starty, saveFile = None):
        self.game_mode = GameMode.new
        self.width = width
        self.height = height
        self.mineCount = mineCount
        self.startx = startx
        self.starty = starty
        self.saveFile = saveFile

    def load_game_init(self, recordFile, useOps = False):
        self.game_mode = GameMode.load
        self.recordFile = recordFile
        self.useOps = useOps

        with open(self.recordFile, 'rb') as f:
            recordData = pickle.load(f)

        self.width = recordData['width']
        self.height = recordData['height']
        self.mineCount = recordData['mineCount']
        fop = recordData['ops'][0]
        assert fop['type'].value == MinesweeperOperator.to_open.value
        self.startx = fop['x']
        self.starty = fop['y']
        self.mines = recordData['mines']
        if self.useOps:
            self.ops = recordData['ops']

    def run(self):
        self.ms = Minesweeper(self.width, self.height)
        assert self.game_mode != GameMode.unknown
        if self.game_mode == GameMode.new:
            self.ms.generate(self.mineCount, self.startx, self.starty)
            self.save_game(self.new_game_run())
        else:
            self.ms.mines = self.mines
            if self.useOps:
                self.load_game_run()
            else:
                self.new_game_run()
        return self.win

    def new_game_run(self):
        start_time = time()
        ops = []
        nextops = [{'type': MinesweeperOperator.to_open, 'x': self.startx, 'y': self.starty}]
        die = False
        while not self.ms.is_win():
            if len(nextops) < 1:
                solver = MinesweeperSolverByFloodfill(self.ms)
                toFlags, toSpaces = solver.run()
                needGuess = True
                for x, y in toFlags:
                    needGuess = False
                    nextops.append({'type': MinesweeperOperator.to_flag, 'x': x, 'y': y})
                for x, y in toSpaces:
                    needGuess = False
                    nextops.append({'type': MinesweeperOperator.to_open, 'x': x, 'y': y})
                if needGuess:
                    if self.show_step:
                        print('need guess')
                    probability = solver.probability
                    cells = self.ms.all_cells
                    if self.show_step:
                        self.ms.show(cells)
                    next_point = None
                    for i in range(self.width):
                        for j in range(self.height):
                            if probability[i][j] is not None and cells[i][j] == CellStatus.Unknown:
                                if next_point is None:
                                    next_point = (i, j)
                                elif probability[i][j] < probability[next_point[0]][next_point[1]]:
                                    next_point = (i, j)
                    if next_point is not None:
                        if self.show_step:
                            print(probability[next_point[0]][next_point[1]])
                        nextops.append({'type': MinesweeperOperator.to_open, 'x': next_point[0], 'y': next_point[1]})
            op = nextops.pop(0)
            ops.append(op)
            if op['type'] == MinesweeperOperator.to_open:
                if self.show_step:
                    print(f'open ({op["x"]},{op["y"]})')
                if not self.ms.open(op['x'], op['y']):
                    if not self.hide_result:
                        print(f'die')
                    die = True
                    break
            elif op['type'] == MinesweeperOperator.to_flag:
                if self.show_step:
                    print(f'flag ({op["x"]},{op["y"]})')
                self.ms.flag(op['x'], op['y'])
            elif op['type'] == MinesweeperOperator.to_open_final:
                if self.show_step:
                    print(f'open final ({op["x"]},{op["y"]})')
                if not self.ms.open_final(op['x'], op['y']):
                    if not self.hide_result:
                        print(f'die')
                    die = True
                    break
        if not die:
            if not self.hide_result:
                print('win')
            self.win = True
        self.use_time = time() - start_time
        if self.show_time:
            print(f'time: {self.use_time}s')
        return ops

    def save_game(self, ops):
        if self.saveFile is not None:
            with open(self.saveFile, 'wb') as f:
                pickle.dump({
                    'width': self.width,
                    'height': self.height,
                    'mineCount': self.mineCount,
                    'mines': self.ms.mines,
                    'ops': ops
                }, f)

    def load_game_run(self):
        pass

def main():
    autoRun = AutoRun()
    autoRun.arg_parse()
    if autoRun.run():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
