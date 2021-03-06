import copy
import curses
import math
import random

from pieces import *


NUM_COLUMNS = 10
NUM_ROWS = 20

STARTING_COLUMN = 4
STARTING_ROW = 0

PREVIEW_COLUMN = 12
PREVIEW_ROW = 1

BLOCK_WIDTH = 2
BORDER_WIDTH = 1

POINTS_PER_LINE = [0, 40, 100, 300, 1200] # [0,1,2,3,4]

class Board(object):
    """Maintains the entire state of the game."""
    def __init__(self, columns=None, rows=None, pieceLimit=-1):
        self.pieceLimit = pieceLimit
        self.num_rows = rows or NUM_ROWS
        self.num_columns = columns or NUM_COLUMNS
        self.array = [[None for _ in range(self.num_columns)] for _ in range(self.num_rows)]
        self.falling_shape = None
        self.next_shape = None
        self.score = 0
        self.bag = [SquareShape(PREVIEW_COLUMN, PREVIEW_ROW, 6, 0), 
                    LineShape(PREVIEW_COLUMN, PREVIEW_ROW, 5, 1),
                    SShape(PREVIEW_COLUMN, PREVIEW_ROW, 3, 1),
                    LShape(PREVIEW_COLUMN, PREVIEW_ROW, 6, 3),
                    TShape(PREVIEW_COLUMN, PREVIEW_ROW, 4, 0),
                    ZShape(PREVIEW_COLUMN, PREVIEW_ROW, 1, 1),
                    JShape(PREVIEW_COLUMN, PREVIEW_ROW, 2, 1)] # bag of tetrominos
        self.shuffle_bag()
        self.bagNextIndex = 0


    def deepBoardCopy(self):
        newBoard = Board(pieceLimit=self.pieceLimit)
        newBoard.falling_shape = self.falling_shape
        newBoard.next_shape = self.next_shape
        for r in range(self.num_rows):
            for c in range(self.num_columns):
                if self.array[r][c] is not None:
                    newBoard.array[r][c] = self.array[r][c].getDeepCopy()
        return newBoard

    def printSelf(self):
        for row in self.array:
            for cell in row:
                if cell:
                    print("[]", end='')
                else:
                    print("__", end='')
            print()


    def shuffle_bag(self):
        random.shuffle(self.bag)

    def next_tetromino(self):

        if type(self.bag[self.bagNextIndex]) is SquareShape:
            self.next_shape = SquareShape(PREVIEW_COLUMN, PREVIEW_ROW, 6, 0)
        if type(self.bag[self.bagNextIndex]) is LineShape:
            self.next_shape = LineShape(PREVIEW_COLUMN, PREVIEW_ROW, 5, 1)
        if type(self.bag[self.bagNextIndex]) is SShape:
            self.next_shape = SShape(PREVIEW_COLUMN, PREVIEW_ROW, 3, 1)
        if type(self.bag[self.bagNextIndex]) is LShape:
            self.next_shape = LShape(PREVIEW_COLUMN, PREVIEW_ROW, 6, 3)
        if type(self.bag[self.bagNextIndex]) is TShape:
            self.next_shape = TShape(PREVIEW_COLUMN, PREVIEW_ROW, 4, 0)
        if type(self.bag[self.bagNextIndex]) is ZShape:
            self.next_shape = ZShape(PREVIEW_COLUMN, PREVIEW_ROW, 1, 1)
        if type(self.bag[self.bagNextIndex]) is JShape:
            self.next_shape = JShape(PREVIEW_COLUMN, PREVIEW_ROW, 2, 1)
        
        self.bagNextIndex += 1
        if self.bagNextIndex == 7:
            self.bagNextIndex = 0
            self.shuffle_bag()

    def start_game(self):
        self.score = 0
        if self.next_shape is None:
            self.next_tetromino()
            self.new_shape()

    def end_game(self):
        raise GameOverError(score=self.score)

    def new_shape(self):
        self.falling_shape = self.next_shape
        self.falling_shape.move_to(STARTING_COLUMN, STARTING_ROW)
        self.next_tetromino()
        if self.shape_cannot_be_placed(self.falling_shape) or self.pieceLimit == 0:
            self.next_shape = self.falling_shape
            self.falling_shape = None
            self.next_shape.move_to(PREVIEW_COLUMN, PREVIEW_ROW)
            self.end_game()
        self.pieceLimit -= 1

    def remove_completed_lines(self):
        rows_removed = []
        lowest_row_removed = 0
        for row in self.array:
            if all(row):
                lowest_row_removed = max(lowest_row_removed, row[0].row_position)
                removedRow = []
                for block in row:
                    removedRow.append(block.getDeepCopy())
                rows_removed.append(removedRow)
                #rows_removed.append(copy.deepcopy(row))
                for block in row:
                    self.array[block.row_position][block.column_position] = None
        if len(rows_removed) > 0:
            self.score += POINTS_PER_LINE[len(rows_removed)]

            for column_index in range(0, NUM_COLUMNS):
                for row_index in range(lowest_row_removed, 0, -1):
                    block = self.array[row_index][column_index]
                    if block:
                        # number of rows removed that were below this one
                        distance_to_drop = len(
                            [row for row in rows_removed if
                             row[0].row_position > block.row_position]
                        )
                        new_row_index = row_index + distance_to_drop
                        self.array[row_index][column_index] = None
                        self.array[new_row_index][column_index] = block
                        block.row_position = new_row_index

    def settle_falilng_shape(self):
        """Resolves the current falling shape."""
        if self.falling_shape:
            self._settle_shape(self.falling_shape)
            self.falling_shape = None
            self.new_shape()

    def _settle_shape(self, shape):
        """Adds shape to settled pieces array."""
        if shape:
            for block in shape.blocks:
                self.array[block.row_position][block.column_position] = block
        self.remove_completed_lines()

    def _settle_shape_no_clear(self, shape):
        """Adds shape to settled pieces array. does not remove completed lines"""
        if shape:
            for block in shape.blocks:
                self.array[block.row_position][block.column_position] = block

    def move_shape_left(self):
        """When the user hits the left arrow."""
        if self.falling_shape:
            self.falling_shape.shift_shape_left_by_one_column()
            if self.shape_cannot_be_placed(self.falling_shape):
                self.falling_shape.shift_shape_right_by_one_column()
                return False
            return True

    def move_shape_right(self):
        """When the user hits the right arrow."""
        if self.falling_shape:
            self.falling_shape.shift_shape_right_by_one_column()
            if self.shape_cannot_be_placed(self.falling_shape):
                self.falling_shape.shift_shape_left_by_one_column()
                return False
            return True

    def rotate_shape(self):
        """When the user hits the up arrow."""
        if self.falling_shape:
            self.falling_shape.rotate_clockwise()
            if self.shape_cannot_be_placed(self.falling_shape):
                self.falling_shape.rotate_counterclockwise()
                return False
            return True

    def let_shape_fall(self):
        """What happens during every `tick`. Also what happens when the user hits down arrow."""
        if self.falling_shape:
            self.falling_shape.lower_shape_by_one_row()
            if self.shape_cannot_be_placed(self.falling_shape):
                self.falling_shape.raise_shape_by_one_row()
                if self.shape_cannot_be_placed(self.falling_shape):
                    self.end_game()
                else:
                    self.settle_falilng_shape()
            return True

    def drop_shape(self):
        """When you hit the enter arrow and the piece goes all the way down."""
        if self.falling_shape:
            while not self.shape_cannot_be_placed(self.falling_shape):
                self.falling_shape.lower_shape_by_one_row()
            self.falling_shape.raise_shape_by_one_row()
            if self.shape_cannot_be_placed(self.falling_shape):
                self.end_game()
            else:
                self.settle_falilng_shape()
            return True

    def shape_cannot_be_placed(self, shape):
        for block in shape.blocks:
            if (block.column_position < 0 or
                    block.column_position >= NUM_COLUMNS or
                    block.row_position < 0 or
                    block.row_position >= NUM_ROWS or
                    self.array[block.row_position][block.column_position] is not None):
                return True
        return False


class BoardDrawer(object):
    def __init__(self):
        stdscr = curses.initscr()
        stdscr.nodelay(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_CYAN)
        curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(10, 10, 10)
        curses.cbreak()
        stdscr.keypad(1)
        curses.nonl()
        curses.curs_set(0)
        curses.noecho()
        self.stdscr = stdscr

    def update_falling_piece(self, board):
        """Adds the currently falling pieces to the next stdscr to be drawn."""
        # actual game board: falling piece
        if board.falling_shape:
            for block in board.falling_shape.blocks:
                self.stdscr.addstr(
                    block.row_position+BORDER_WIDTH,
                    BLOCK_WIDTH*block.column_position+BORDER_WIDTH,
                    ' '*BLOCK_WIDTH,
                    curses.color_pair(block.color)
                )

    def update_settled_pieces(self, board):
        """Adds the already settled pieces to the next stdscr to be drawn."""
        # actual game board: settled pieces
        for (r_index, row) in enumerate(board.array):
            for (c_index, value) in enumerate(row):
                block = value
                if block:
                    color_pair = block.color
                else:
                    color_pair = 0
                self.stdscr.addstr(
                    r_index+BORDER_WIDTH,
                    c_index*BLOCK_WIDTH+BORDER_WIDTH,
                    ' '*BLOCK_WIDTH,
                    curses.color_pair(color_pair)
                )

    def update_shadow(self, board):
        """Adds the 'shadow' of the falling piece to the next stdscr to be drawn."""
        # where this piece will land
        shadow = copy.deepcopy(board.falling_shape) # deepcopy is no problem here, because only used for graphics
        if shadow:
            while not board.shape_cannot_be_placed(shadow):
                shadow.lower_shape_by_one_row()
            shadow.raise_shape_by_one_row()
            for block in shadow.blocks:
                self.stdscr.addstr(
                    block.row_position+BORDER_WIDTH,
                    BLOCK_WIDTH*block.column_position+BORDER_WIDTH,
                    ' '*BLOCK_WIDTH,
                    curses.color_pair(8))

    def update_next_piece(self, board):
        """Adds the next piece to the next stdscr to be drawn."""
        # next piece
        if board.next_shape:
            for preview_row_offset in range(4):
                self.stdscr.addstr(
                    PREVIEW_ROW+preview_row_offset+BORDER_WIDTH,
                    (PREVIEW_COLUMN-1)*BLOCK_WIDTH+BORDER_WIDTH*2,
                    '    '*BLOCK_WIDTH,
                    curses.color_pair(0)
                )
            for block in board.next_shape.blocks:
                self.stdscr.addstr(
                    block.row_position+BORDER_WIDTH,
                    block.column_position*BLOCK_WIDTH+BORDER_WIDTH*2,
                    ' '*BLOCK_WIDTH,
                    curses.color_pair(block.color)
                )

    def update_score(self, board):
        """Adds the score to the next stdscr to be drawn."""
        # score
        self.stdscr.addstr(
            6+BORDER_WIDTH,
            PREVIEW_COLUMN*BLOCK_WIDTH-2+BORDER_WIDTH,
            'GAME SCORE: %d' % board.score,
            curses.color_pair(7)
        )

    def clear_score(self):
        # score
        self.stdscr.addstr(
            6+BORDER_WIDTH,
            PREVIEW_COLUMN*BLOCK_WIDTH-2+BORDER_WIDTH,
            'GAME SCORE:              ',
            curses.color_pair(7)
        )

    def update_border(self):
        """Adds the border to the next stdscr to be drawn."""
        # side borders
        for row_position in range(NUM_ROWS+BORDER_WIDTH*2):
            self.stdscr.addstr(row_position, 0, '|', curses.color_pair(7))
            self.stdscr.addstr(row_position, NUM_COLUMNS*BLOCK_WIDTH+1, '|', curses.color_pair(7))
        # top and bottom borders
        for column_position in range(NUM_COLUMNS*BLOCK_WIDTH+BORDER_WIDTH*2):
            self.stdscr.addstr(0, column_position, '-', curses.color_pair(7))
            self.stdscr.addstr(NUM_ROWS+1, column_position, '-', curses.color_pair(7))

    def update(self, board, shadows = True):
        """Updates all visual board elements and then refreshes the screen."""
        self.update_border()
        self.update_score(board)
        self.update_next_piece(board)

        self.update_settled_pieces(board)

        if shadows:
            self.update_shadow(board)

        self.update_falling_piece(board)

        

        self.refresh_screen()

    def refresh_screen(self):
        """Re-draws the current screen."""
        stdscr = self.stdscr
        stdscr.refresh()

    @staticmethod
    def return_screen_to_normal():
        """Undoes the weird settings to the terminal isn't screwed up when the game is over"""
        curses.endwin()


class GameOverError(Exception):
    def __init__(self, score):
        super(GameOverError).__init__(GameOverError)
        self.score = score
