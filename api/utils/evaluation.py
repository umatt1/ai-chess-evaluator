"""Utilities for chess position evaluation."""

from dataclasses import dataclass
from typing import List, Dict, Optional
import chess

@dataclass
class EvaluationLine:
    """Represents a single evaluated line in a chess position."""
    move: str
    evaluation: float
    continuation: Optional[List[str]] = None

@dataclass
class EvaluationResult:
    """Result of a position evaluation."""
    best_move: Optional[str] = None
    evaluation: Optional[float] = None
    all_lines: Optional[List[EvaluationLine]] = None
    error: Optional[str] = None

def get_position_details(board: chess.Board) -> Dict:
    """Get detailed information about a chess position.
    
    Args:
        board: Chess board to analyze
        
    Returns:
        Dict containing position details
    """
    # Calculate center control
    white_center = len([sq for sq in [chess.E4, chess.E5, chess.D4, chess.D5] 
                       if board.attackers(chess.WHITE, sq)])
    black_center = len([sq for sq in [chess.E4, chess.E5, chess.D4, chess.D5] 
                       if board.attackers(chess.BLACK, sq)])
    
    # Check castling rights
    white_kingside = bool(board.castling_rights & chess.BB_H1)
    white_queenside = bool(board.castling_rights & chess.BB_A1)
    black_kingside = bool(board.castling_rights & chess.BB_H8)
    black_queenside = bool(board.castling_rights & chess.BB_A8)
    
    # Get material count
    material_count = {
        'white': {
            'P': len(board.pieces(chess.PAWN, chess.WHITE)),
            'N': len(board.pieces(chess.KNIGHT, chess.WHITE)),
            'B': len(board.pieces(chess.BISHOP, chess.WHITE)),
            'R': len(board.pieces(chess.ROOK, chess.WHITE)),
            'Q': len(board.pieces(chess.QUEEN, chess.WHITE))
        },
        'black': {
            'p': len(board.pieces(chess.PAWN, chess.BLACK)),
            'n': len(board.pieces(chess.KNIGHT, chess.BLACK)),
            'b': len(board.pieces(chess.BISHOP, chess.BLACK)),
            'r': len(board.pieces(chess.ROOK, chess.BLACK)),
            'q': len(board.pieces(chess.QUEEN, chess.BLACK))
        }
    }
    
    # Determine game phase
    total_pieces = sum(len(board.pieces(piece_type, color))
                      for color in [chess.WHITE, chess.BLACK]
                      for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
    
    return {
        'turn': 'White' if board.turn else 'Black',
        'center_control': {'white': white_center, 'black': black_center},
        'castling': {
            'white': {'kingside': white_kingside, 'queenside': white_queenside},
            'black': {'kingside': black_kingside, 'queenside': black_queenside}
        },
        'material': material_count,
        'phase': 'Opening' if board.fullmove_number <= 10 else 'Middlegame' if total_pieces > 20 else 'Endgame',
        'legal_moves': len(list(board.legal_moves))
    }

def basic_material_evaluation(board: chess.Board) -> float:
    """Calculate a basic material evaluation of the position.
    
    Args:
        board: Chess board to evaluate
        
    Returns:
        float: Evaluation score (positive favors white, negative favors black)
    """
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }
    
    evaluation = 0.0
    
    for piece_type in piece_values:
        evaluation += (len(board.pieces(piece_type, chess.WHITE)) - 
                     len(board.pieces(piece_type, chess.BLACK))) * piece_values[piece_type]
    
    # Add a small bonus for the side to move
    if not board.turn:  # If it's black's turn
        evaluation -= 0.2
    
    return evaluation
