"""Chess position evaluation using GPT and traditional methods."""

import chess
import openai
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ..utils.logging import setup_logger
from .constants import (
    PIECE_VALUES, CENTER_SQUARES, MAX_EVAL, MIN_EVAL,
    TURN_BONUS, CENTER_CONTROL_BONUS, DEVELOPMENT_BONUS,
    OPENING_MOVES, MIDDLEGAME_PIECES
)
from .prompts import get_evaluation_prompt

logger = setup_logger(__name__)

@dataclass
class EvaluationResult:
    """Result of a position evaluation."""
    score: float
    best_move: Optional[str] = None
    all_lines: Optional[List[Dict]] = None
    error: Optional[str] = None

class ChessEvaluator:
    """Evaluates chess positions using GPT and traditional methods."""
    
    def __init__(self, api_key: str):
        """Initialize evaluator with OpenAI API key."""
        openai.api_key = api_key

    def _analyze_board(self, board: chess.Board) -> Dict:
        """Analyze current board state for GPT prompt.
        
        Args:
            board: Current chess board
            
        Returns:
            Dict: Analysis of material, position, and game state
        """
        def piece_str(piece_type: chess.PieceType, color: chess.Color) -> str:
            symbol = chess.piece_symbol(piece_type)
            return symbol.upper() if color else symbol.lower()
            
        white_material = ", ".join(
            f"{len(board.pieces(pt, chess.WHITE))} {piece_str(pt, True)}"
            for pt in PIECE_VALUES
        )
        black_material = ", ".join(
            f"{len(board.pieces(pt, chess.BLACK))} {piece_str(pt, False)}"
            for pt in PIECE_VALUES
        )
        
        white_center = len([sq for sq in CENTER_SQUARES if board.attackers(chess.WHITE, sq)])
        black_center = len([sq for sq in CENTER_SQUARES if board.attackers(chess.BLACK, sq)])
        
        white_castling = "can" if bool(board.castling_rights & (chess.BB_H1 | chess.BB_A1)) else "cannot"
        black_castling = "can" if bool(board.castling_rights & (chess.BB_H8 | chess.BB_A8)) else "cannot"
        
        phase = (
            "Opening" if board.fullmove_number <= OPENING_MOVES
            else "Middlegame" if len(board.piece_map()) > MIDDLEGAME_PIECES
            else "Endgame"
        )
        
        return {
            "white_material": white_material,
            "black_material": black_material,
            "white_center": white_center,
            "black_center": black_center,
            "white_castling": white_castling,
            "black_castling": black_castling,
            "turn": "White" if board.turn else "Black",
            "phase": phase,
            "legal_moves": len(list(board.legal_moves))
        }

    def _evaluate_position_with_gpt(self, fen: str) -> float:
        """Evaluate position using GPT.
        
        Args:
            fen: FEN string of position
            
        Returns:
            float: Evaluation score (-10.0 to 10.0, positive favors white)
        """
        board = chess.Board(fen)
        analysis = self._analyze_board(board)
        prompt = get_evaluation_prompt(fen, analysis)
        
        try:
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            eval_text = response.choices[0].text.strip()
            cleaned_text = ''.join(c for c in eval_text if c.isdigit() or c in '.-')
            
            if not cleaned_text or cleaned_text in ['-', '.', '-.']:
                logger.warning(f"Invalid evaluation text: {cleaned_text}")
                return self._basic_material_evaluation(board)
                
            evaluation = float(cleaned_text)
            
            # Add turn bonus
            if not board.turn:
                evaluation -= TURN_BONUS
                
            return max(min(evaluation, MAX_EVAL), MIN_EVAL)
            
        except Exception as e:
            logger.error(f"GPT evaluation error: {str(e)}")
            return self._basic_material_evaluation(board)

    def _basic_material_evaluation(self, board: chess.Board) -> float:
        """Basic material and positional evaluation.
        
        Args:
            board: Current chess board
            
        Returns:
            float: Basic evaluation score
        """
        score = 0.0
        
        # Material
        for piece_type, value in PIECE_VALUES.items():
            score += len(board.pieces(piece_type, chess.WHITE)) * value
            score -= len(board.pieces(piece_type, chess.BLACK)) * value
        
        # Center control
        for sq in CENTER_SQUARES:
            score += CENTER_CONTROL_BONUS * len(board.attackers(chess.WHITE, sq))
            score -= CENTER_CONTROL_BONUS * len(board.attackers(chess.BLACK, sq))
        
        # Development in opening
        if board.fullmove_number <= OPENING_MOVES:
            for piece in [chess.KNIGHT, chess.BISHOP]:
                score += DEVELOPMENT_BONUS * len(
                    [1 for sq in board.pieces(piece, chess.WHITE) if chess.square_rank(sq) > 1]
                )
                score -= DEVELOPMENT_BONUS * len(
                    [1 for sq in board.pieces(piece, chess.BLACK) if chess.square_rank(sq) < 6]
                )
        
        # Mobility
        legal_moves = len(list(board.legal_moves))
        score += TURN_BONUS * legal_moves if board.turn else -TURN_BONUS * legal_moves
        
        return max(min(score, MAX_EVAL), MIN_EVAL)

    def _get_moves_and_positions(self, board: chess.Board) -> List[Tuple[chess.Move, str]]:
        """Get all legal moves and resulting positions.
        
        Args:
            board: Current chess board
            
        Returns:
            List[Tuple[chess.Move, str]]: List of (move, resulting FEN) pairs
        """
        moves_and_positions = []
        for move in board.legal_moves:
            board_copy = board.copy()
            board_copy.push(move)
            moves_and_positions.append((move, board_copy.fen()))
        return moves_and_positions

    def evaluate_recursive(self, fen: str, depth: int) -> Dict:
        """Recursively evaluate position to find best move.
        
        Args:
            fen: FEN string of position
            depth: Search depth
            
        Returns:
            Dict: Evaluation result with best move and score
        """
        try:
            board = chess.Board(fen)
        except ValueError as e:
            return {"error": f"Invalid FEN: {str(e)}"}

        if depth < 1:
            return {"error": "Depth must be at least 1"}
            
        moves_analyzed = 0
        logger.info(f"Starting evaluation at depth {depth}")

        def evaluate_at_depth(
            current_fen: str,
            current_depth: int,
            alpha: float = float('-inf'),
            beta: float = float('inf')
        ) -> Tuple[float, List[Dict]]:
            """Evaluate position at current depth.
            
            Args:
                current_fen: Current position FEN
                current_depth: Current search depth
                alpha: Alpha bound for pruning
                beta: Beta bound for pruning
                
            Returns:
                Tuple[float, List[Dict]]: (evaluation score, line variations)
            """
            nonlocal moves_analyzed
            logger.debug(f"Depth {current_depth}, positions analyzed: {moves_analyzed}")
            
            current_board = chess.Board(current_fen)
            is_white = current_board.turn

            if current_depth == 0:
                logger.debug("Leaf node reached")
                return self._evaluate_position_with_gpt(current_fen), []

            if current_board.is_game_over():
                if current_board.is_checkmate():
                    return (-MAX_EVAL if is_white else MAX_EVAL), []
                return 0, []  # Draw

            moves_and_positions = self._get_moves_and_positions(current_board)
            evaluations = []
            best_value = float('-inf') if is_white else float('inf')

            # Order moves for better pruning
            moves_and_positions.sort(
                key=lambda x: self._basic_material_evaluation(chess.Board(x[1])),
                reverse=is_white
            )

            for move, resulting_fen in moves_and_positions:
                moves_analyzed += 1
                logger.debug(f"Analyzing {move.uci()} at depth {current_depth}")
                
                child_score, child_lines = evaluate_at_depth(
                    resulting_fen,
                    current_depth - 1,
                    -beta,
                    -alpha
                )
                eval_score = -child_score
                
                evaluations.append({
                    "move": move.uci(),
                    "evaluation": eval_score,
                    "lines": child_lines
                })

                if is_white:
                    best_value = max(best_value, eval_score)
                    alpha = max(alpha, best_value)
                else:
                    best_value = min(best_value, eval_score)
                    beta = min(beta, best_value)

                if beta <= alpha:
                    logger.debug(f"Pruning at depth {current_depth}")
                    break

            evaluations.sort(
                key=lambda x: x["evaluation"],
                reverse=is_white
            )
            
            return (
                evaluations[0]["evaluation"] if evaluations else 0,
                evaluations
            )

        score, variations = evaluate_at_depth(fen, depth)
        logger.info(f"Evaluation complete. Analyzed {moves_analyzed} positions")
        
        if not variations:
            return {"error": "No valid moves found"}
            
        return {
            "best_move": variations[0]["move"],
            "evaluation": variations[0]["evaluation"],
            "all_lines": variations
        }
