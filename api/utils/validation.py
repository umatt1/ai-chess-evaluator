"""Validation utilities for chess operations."""

import chess
from typing import Tuple, Optional, Dict
from dataclasses import dataclass
from rest_framework.exceptions import APIException

class ChessError(APIException):
    """Base exception for chess-related errors."""
    status_code = 400
    default_detail = 'Chess error occurred.'

@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    error: Optional[str] = None
    data: Optional[Dict] = None

def validate_position(fen: str) -> Tuple[chess.Board, Optional[str]]:
    """Validate a chess position.
    
    Args:
        fen: FEN string representing the position
        
    Returns:
        Tuple[chess.Board, Optional[str]]: Board object and error message if any
    """
    try:
        board = chess.Board(fen)
        if not list(board.legal_moves):
            return board, "No legal moves available in this position"
        return board, None
    except ValueError as e:
        return None, f"Invalid FEN: {str(e)}"

def validate_move(move: str, board: chess.Board) -> Optional[str]:
    """Validate a chess move.
    
    Args:
        move: Move in UCI format
        board: Current chess board
        
    Returns:
        Optional[str]: Error message if move is invalid, None if valid
    """
    try:
        chess_move = chess.Move.from_uci(move)
        if chess_move not in board.legal_moves:
            return f"Invalid move {move} for current position"
            
        # Check if move changes position
        test_board = board.copy()
        test_board.push(chess_move)
        if test_board.fen() == board.fen():
            return f"Move {move} doesn't change the position"
            
        return None
    except ValueError:
        return f"Invalid move format: {move}"
