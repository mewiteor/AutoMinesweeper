import pygame
import pygame.locals as pl
import sys
from MinesweeperGenerate import Minesweeper, CellStatus
from MinesweeperSolver import MinesweeperSolverByWalkAll, MinesweeperSolverByFloodfill, CellStatusEx

if len(sys.argv) != 4:
    print('normal usage: {} 宽 高 雷数'.format(sys.argv[0]))
    sys.exit()


width = int(sys.argv[1])
height = int(sys.argv[2])
mineCount = int(sys.argv[3])

ms = Minesweeper(width, height)
isGenerate = False

cellWid = 60
centerFontSize = 20
topFontSize = 16

pygame.init()
screen = pygame.display.set_mode((cellWid * width + width - 1, cellWid * height + height - 1))
probability = None
clk = pygame.time.Clock()

def all_draw():
    screen.fill((255,255,255))

    # 竖线
    for i in range(cellWid, width * (cellWid + 1) - 1, cellWid + 1):
        pygame.draw.line(screen, (0,0,0), (i, 0), (i, cellWid * height + height - 1))
        
    # 横线
    for j in range(cellWid, height * (cellWid + 1) - 1, cellWid + 1):
        pygame.draw.line(screen, (0,0,0), (0, j), (cellWid * width + width - 1, j))

    for i in range(width):
        for j in range(height):
            cell = ms.cells[i][j]
            cellRect = pl.Rect((i * (cellWid + 1), j * (cellWid + 1)), (cellWid, cellWid))
            if cell == CellStatus.Space:
                pass
            elif cell.value in range(1,9):
                pygame.draw.rect(screen, (192, 192, 192), cellRect)
                fontObj = pygame.font.SysFont('Arial', centerFontSize)
                textSurfaceObj = fontObj.render(str(cell.value), True, (0, 0, 0))
                textRectObj = textSurfaceObj.get_rect()
                textRectObj.center = cellRect.center
                screen.blit(textSurfaceObj, textRectObj)
            elif cell == CellStatus.Unknown:
                pygame.draw.rect(screen, (128, 128, 128), cellRect)
            elif cell == CellStatus.Flagged:
                pygame.draw.rect(screen, (128, 128, 128), cellRect)
                fontObj = pygame.font.SysFont('Arial', centerFontSize)
                textSurfaceObj = fontObj.render('F', True, (255, 0, 0))
                textRectObj = textSurfaceObj.get_rect()
                textRectObj.center = cellRect.center
                screen.blit(textSurfaceObj, textRectObj)
    if probability is not None:
        for i in range(width):
            for j in range(height):
                if probability[i][j] is not None:
                    cellRect = pl.Rect((i * (cellWid + 1), j * (cellWid + 1)), (cellWid, cellWid))
                    fontObj = pygame.font.SysFont('Arial', topFontSize)
                    textSurfaceObj = fontObj.render('%4.2f' % (probability[i][j] * 100), True, (0, 0, 0))
                    textRectObj = textSurfaceObj.get_rect()
                    textRectObj.midtop = cellRect.midtop
                    screen.blit(textSurfaceObj, textRectObj)


    pygame.display.update()

all_draw()

while True:
    clk.tick(100)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            left, middle, right = pygame.mouse.get_pressed()
            x, y = pygame.mouse.get_pos()
            x //= cellWid + 1
            y //= cellWid + 1

            if left:
                if not isGenerate:
                    ms.generate(mineCount, x, y)
                    print('3BV: {}'.format(ms._3BV))
                    isGenerate = True
                if not ms.open(x, y):
                    print('die')
                    sys.exit()
            elif middle:
                if isGenerate:
                    if not ms.open_final(x, y):
                        print('die')
                        sys.exit()
            elif right:
                if isGenerate:
                    ms.flag(x, y)
            if left or middle:
                if ms.is_win():
                    print('win')
                    sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pl.K_1:
                solver = MinesweeperSolverByFloodfill(ms)
                print('begin run')
                toFlags, toSpaces = solver.run()
                print('finish run')
                if len(toFlags) + len(toSpaces) < 1:
                    print('need guess')
                probability = solver.probability
                for x, y in toFlags:
                    ms.flag(x, y)
                for x, y in toSpaces:
                    if not ms.open(x, y):
                        print('die')
                        sys.exit()
                if ms.is_win():
                    print('win')
                    sys.exit()

    pygame.display.set_caption('扫雷 - 3BV: {}, 剩余雷数: {}'.format(ms._3BV, ms.remain_mines))
    all_draw()
