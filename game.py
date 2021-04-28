#!/usr/bin/env python3

import curses
import datetime
import math
import signal
import sys

from game_board import Board, BoardDrawer, GameOverError
from players import Human, AI


TICK_LENGTH = 600


def main():
    start_new_game()


def start_new_game():
    game = Game()
    game.new_game()
    game.run_game()


class Game(object):
    """Manages the game and updating the screen."""

    def __init__(self, player=None):
        self.last_tick = None
        self.board = None
        self.board_drawer = None
        self.player = player or Human()

        # Game speed management for AI
        self.useTicks = True
        self.displayScreen = True
        if isinstance(self.player, AI):
            self.useTicks = False
            self.displayScreen = True # TODO: make false when sure everything works

    def new_game(self):
        """Initializes a new game."""
        self.last_tick = None
        self.board = Board()
        self.board_drawer = BoardDrawer()
        self.board_drawer.clear_score()
        self.board.start_game()

    def pause_game(self):
        """Pauses or unpauses the game."""
        if self.last_tick:
            self.stop_ticking()
        else:
            self.start_ticking()

    def run_game(self):
        self.start_ticking()
        self._tick()
        while True:
            try:
                if isinstance(self.player, Human):
                    self.process_user_input()
                elif isinstance(self.player, AI):
                    self.process_ai_input()
                self.update()
            except GameOverError:
                self.end_game()
                return self.board.score

    def save_game(self):
        """Writes the state of the game to a file."""
        pass

    def load_game(self):
        """Loads a game from a file."""
        pass

    def end_game(self):
        """Ends the current game."""
        self.board_drawer.return_screen_to_normal()
        print('Game Over! Final Score: {}'.format(int(self.board.score)))
        sys.exit(int(self.board.score))

    def start_ticking(self):
        self.last_tick = datetime.datetime.now()

    def stop_ticking(self):
        self.last_tick = None

    def update(self):
        if self.useTicks:
            current_time = datetime.datetime.now()
            tick_multiplier = 1
            tick_threshold = datetime.timedelta(milliseconds=TICK_LENGTH*tick_multiplier)
            if self.last_tick and current_time - self.last_tick > tick_threshold:
                self.last_tick = current_time
                self._tick()
        else:
            self._tick()

    def _tick(self):
        self.board.let_shape_fall()
        if self.displayScreen:
            if isinstance(self.player, AI):
                self.board_drawer.update(self.board, False)
            else:
                self.board_drawer.update(self.board, True)

    def process_ai_input(self):
        move = self.player.get_moves(self.board, self.board_drawer)
        if move:
            self.board.falling_shape.orientation = move.orientation
            self.board.falling_shape.move_to(move.column_position, move.row_position)
            self.board_drawer.update(self.board)
        else:
            self.end_game()

    def process_user_input(self):
        user_input = self.board_drawer.stdscr.getch()
        moves = {
            curses.KEY_RIGHT: self.board.move_shape_right,
            curses.KEY_LEFT: self.board.move_shape_left,
            curses.KEY_UP: self.board.rotate_shape,
            curses.KEY_DOWN: self.board.let_shape_fall,
            curses.KEY_ENTER: self.board.drop_shape,
            10: self.board.drop_shape,
            13: self.board.drop_shape,
            112: self.pause_game,
            113: self.end_game,
        }
        move_fn = moves.get(user_input)
        if move_fn:
            piece_moved = move_fn()
            if piece_moved:
                self.board_drawer.update(self.board)


def signal_handler(signal, frame):
    BoardDrawer.return_screen_to_normal()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    main()
