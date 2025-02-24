import chess
import openai
from typing import Dict, List, Optional
from .utils.logging import logger
from .utils.validation import validate_position, validate_move
from .utils.evaluation import (
    EvaluationResult, EvaluationLine, get_position_details,
    basic_material_evaluation
)

class ChessEvaluator:
    def __init__(self, api_key: str):
        openai.api_key = api_key

    def _evaluate_position_with_gpt(self, fen: str) -> float:
        """
        Use GPT-3.5-turbo-instruct to evaluate a chess position and return a numerical score.
        Positive scores favor white, negative scores favor black.
        """
        board, error = validate_position(fen)
        if error:
            logger.error(f"Invalid position: {error}")
            return 0.0

        position_details = get_position_details(board)
        
        prompt = f"""You are a chess position evaluator. Return ONLY a single decimal number between -10.0 and 10.0 representing the position evaluation.

Rules for evaluation:
1. Return ONLY the number, no text or explanation
2. Positive numbers favor White, negative favor Black
3. Use decimal points (e.g. 0.5 not 1/2)
4. Typical values: 0.0 (equal), 0.5 (slight White advantage), -0.5 (slight Black advantage)

Position Analysis:
FEN: {fen}

1. Material Count
   White: {position_details['material']['white']['P']} P, {position_details['material']['white']['N']} N, {position_details['material']['white']['B']} B, {position_details['material']['white']['R']} R, {position_details['material']['white']['Q']} Q
   Black: {position_details['material']['black']['p']} p, {position_details['material']['black']['n']} n, {position_details['material']['black']['b']} b, {position_details['material']['black']['r']} r, {position_details['material']['black']['q']} q

2. Position Details
   - Turn: {position_details['turn']}
   - Center Control: White={position_details['center_control']['white']}, Black={position_details['center_control']['black']}
   - Castling: White={'can' if any(position_details['castling']['white'].values()) else 'cannot'}, Black={'can' if any(position_details['castling']['black'].values()) else 'cannot'}
   - Phase: {position_details['phase']}
   - Legal Moves: {position_details['legal_moves']}

Guidelines:
1. Consider material values: pawn=1, knight/bishop=3, rook=5, queen=9
2. Factor in:
   - Center control and piece activity
   - King safety and pawn structure
   - Development and mobility
   - Current turn advantage (+0.2 for side to move)

Return ONLY a decimal number between -10.0 and 10.0 (e.g. 0.5, -1.2, 3.0).
Evaluation:"""

        try:
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=10,
                temperature=0.1  # Lower temperature for more consistent evaluations
            )
            
            eval_text = response.choices[0].text.strip()
            # Clean the response - keep only digits, decimal point, and minus sign
            cleaned_text = ''.join(c for c in eval_text if c.isdigit() or c in '.-')
            
            # Handle edge cases
            if not cleaned_text or cleaned_text in ['-', '.', '-.']:
                logger.warning(f"Invalid evaluation text after cleaning: {cleaned_text}")
                return basic_material_evaluation(board)
                
            # Parse the evaluation
            evaluation = float(cleaned_text)
            
            # Add a small bonus for the side to move
            if not board.turn:  # If it's black's turn
                evaluation -= 0.2  # Subtract from white's perspective
                
            # Ensure the evaluation is within bounds
            evaluation = max(min(evaluation, 10.0), -10.0)
            
            return evaluation
        except Exception as e:
            logger.error(f"GPT evaluation error: {str(e)}. Raw response: {eval_text if 'eval_text' in locals() else 'No response'}")
            return basic_material_evaluation(board)

    def _get_moves_and_resulting_positions(self, board: chess.Board) -> List[tuple[chess.Move, str]]:
        """Get all legal moves and their resulting positions."""
        moves_and_positions = []
        for move in board.legal_moves:
            error = validate_move(move.uci(), board)
            if error:
                logger.warning(f"Invalid move {move.uci()}: {error}")
                continue
                
            board_copy = board.copy()
            board_copy.push(move)
            moves_and_positions.append((move, board_copy.fen()))
        return moves_and_positions

    def _basic_material_evaluation(self, board: chess.Board) -> float:
        """Basic material and position evaluation when GPT fails"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        
        # Material score
        score = 0
        for piece_type in piece_values:
            score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
            score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
        
        # Center control bonus
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        for sq in center_squares:
            score += 0.1 * len(board.attackers(chess.WHITE, sq))
            score -= 0.1 * len(board.attackers(chess.BLACK, sq))
        
        # Development bonus in opening
        if board.fullmove_number <= 10:
            # Bonus for developed pieces
            for piece in [chess.KNIGHT, chess.BISHOP]:
                # White pieces not on back rank
                score += 0.2 * len([1 for sq in board.pieces(piece, chess.WHITE) if chess.square_rank(sq) > 1])
                # Black pieces not on back rank
                score -= 0.2 * len([1 for sq in board.pieces(piece, chess.BLACK) if chess.square_rank(sq) < 6])
        
        # Mobility (number of legal moves)
        legal_moves = len(list(board.legal_moves))
        score += 0.1 * legal_moves if board.turn else -0.1 * legal_moves
        
        return score

    def evaluate_recursive(self, fen: str, depth: int) -> Dict:
        """
        Recursively evaluate chess positions up to the specified depth.
        Returns the best move and evaluation at each level.
        """
        board, error = validate_position(fen)
        if error:
            logger.error(f"Invalid FEN: {error}")
            return EvaluationResult(error=error).__dict__

        if depth < 1:
            logger.error("Depth must be at least 1")
            return EvaluationResult(error="Depth must be at least 1").__dict__
            
        # Counter for tracking number of positions analyzed
        moves_analyzed = 0

        def evaluate_at_depth(current_fen: str, current_depth: int, alpha=-float('inf'), beta=float('inf')) -> tuple[float, List[EvaluationLine]]:
            nonlocal moves_analyzed
            logger.debug(f"Evaluating at depth {current_depth}, moves analyzed so far: {moves_analyzed}")
            
            current_board, error = validate_position(current_fen)
            if error:
                logger.error(f"Invalid position at depth {current_depth}: {error}")
                return 0.0, []
                
            is_white = current_board.turn

            if current_depth == 0:
                logger.debug("Leaf node reached, calling GPT evaluation")
                eval_score = self._evaluate_position_with_gpt(current_fen)
                return eval_score, []

            if current_board.is_game_over():
                if current_board.is_checkmate():
                    return (-10 if is_white else 10), []
                return 0, []  # Draw

            moves_and_positions = self._get_moves_and_resulting_positions(current_board)
            evaluations: List[EvaluationLine] = []
            best_value = -float('inf') if is_white else float('inf')

            # Order moves to improve alpha-beta pruning
            moves_and_positions.sort(key=lambda x: basic_material_evaluation(chess.Board(x[1])), reverse=is_white)

            for move, resulting_fen in moves_and_positions:
                moves_analyzed += 1
                logger.debug(f"Analyzing move {move.uci()} at depth {current_depth}, total positions: {moves_analyzed}")
                
                # Get score from child's perspective
                child_score, child_lines = evaluate_at_depth(resulting_fen, current_depth - 1, -beta, -alpha)
                # Convert score to our perspective
                eval_score = -child_score
                
                line = EvaluationLine(
                    move=move.uci(),
                    evaluation=eval_score,
                    continuation=[line.move for line in child_lines]
                )
                evaluations.append(line)

                # Update best value and alpha/beta bounds
                if is_white:
                    best_value = max(best_value, eval_score)
                    alpha = max(alpha, best_value)
                else:
                    best_value = min(best_value, eval_score)
                    beta = min(beta, best_value)

                # Alpha-beta cutoff
                if beta <= alpha:
                    logger.debug(f"Pruning at depth {current_depth} after move {move.uci()}")
                    break

            # Sort moves by evaluation for better move selection
            evaluations.sort(key=lambda x: x.evaluation, reverse=is_white)
            return best_value, evaluations

        try:
            final_eval, move_lines = evaluate_at_depth(fen, depth)
            
            if not move_lines:
                logger.warning("No valid moves found")
                return EvaluationResult(error="No valid moves found").__dict__

            # Sort moves by evaluation, considering perspective
            sorted_moves = sorted(move_lines, key=lambda x: x.evaluation, reverse=board.turn)
            best_move = sorted_moves[0].move

            # Log move selection process
            logger.info(f"Move selection for {'White' if board.turn else 'Black'}:")
            for i, move in enumerate(sorted_moves[:3]):
                logger.info(f"{i+1}. {move.move} (eval: {move.evaluation:.2f})")

            return EvaluationResult(
                best_move=best_move,
                evaluation=final_eval,
                all_lines=sorted_moves[:5]  # Only return top 5 moves
            ).__dict__

        except Exception as e:
            logger.error(f"Error in evaluate_recursive: {str(e)}")
            return EvaluationResult(error=str(e)).__dict__
