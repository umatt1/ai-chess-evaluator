"""Constants used in chess evaluation and gameplay."""

import chess

# Piece values for basic evaluation
PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.0,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
}

# Important squares
CENTER_SQUARES = [chess.E4, chess.E5, chess.D4, chess.D5]

# Position evaluation constants
MAX_EVAL = 10.0
MIN_EVAL = -10.0
TURN_BONUS = 0.2
CENTER_CONTROL_BONUS = 0.1
DEVELOPMENT_BONUS = 0.2

# Game phase thresholds
OPENING_MOVES = 10
MIDDLEGAME_PIECES = 20

# Search parameters
DEFAULT_DEPTH = 2
MIN_DEPTH = 1
