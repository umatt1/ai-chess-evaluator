import chess
import openai
from typing import Dict, List, Tuple
import json

class ChessEvaluator:
    def __init__(self, api_key: str):
        openai.api_key = api_key

    def _evaluate_position_with_gpt(self, fen: str) -> float:
        """
        Use GPT-3.5-turbo-instruct to evaluate a chess position and return a numerical score.
        Positive scores favor white, negative scores favor black.
        """
        prompt = f"""Analyze this chess position in FEN notation: {fen}
        
        Consider material balance, piece positions, king safety, and pawn structure.
        Return ONLY a single number between -10 and 10 representing the position evaluation.
        Positive numbers favor white, negative numbers favor black.
        0 means equal position.
        10 means white is winning decisively.
        -10 means black is winning decisively.
        
        Evaluation:"""

        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=10,
            temperature=0.3
        )

        try:
            evaluation = float(response['choices'][0]['text'].strip())
            return max(min(evaluation, 10), -10)  # Ensure within bounds
        except ValueError:
            return 0.0  # Default to neutral if parsing fails

    def _get_moves_and_resulting_positions(self, board: chess.Board) -> List[Tuple[chess.Move, str]]:
        """Get all legal moves and their resulting positions."""
        moves_and_positions = []
        for move in board.legal_moves:
            board_copy = board.copy()
            board_copy.push(move)
            moves_and_positions.append((move, board_copy.fen()))
        return moves_and_positions

    def evaluate_recursive(self, fen: str, depth: int) -> Dict:
        """
        Recursively evaluate chess positions up to the specified depth.
        Returns the best move and evaluation at each level.
        """
        try:
            board = chess.Board(fen)
        except ValueError as e:
            return {"error": f"Invalid FEN: {str(e)}"}

        if depth < 1:
            return {"error": "Depth must be at least 1"}

        def evaluate_at_depth(current_fen: str, current_depth: int) -> Tuple[float, List[Dict]]:
            if current_depth == 0:
                return self._evaluate_position_with_gpt(current_fen), []

            current_board = chess.Board(current_fen)
            if current_board.is_game_over():
                if current_board.is_checkmate():
                    return -10 if current_board.turn else 10, []
                return 0, []  # Draw

            moves_and_positions = self._get_moves_and_resulting_positions(current_board)
            evaluations = []

            for move, resulting_fen in moves_and_positions:
                eval_score, child_lines = evaluate_at_depth(resulting_fen, current_depth - 1)
                # Negate the evaluation because it's from the opponent's perspective
                evaluations.append({
                    "move": move.uci(),
                    "evaluation": -eval_score,
                    "lines": child_lines
                })

            # Find the best move (highest evaluation)
            best_eval = max(evaluations, key=lambda x: x["evaluation"])
            return best_eval["evaluation"], evaluations

        final_eval, move_lines = evaluate_at_depth(fen, depth)
        
        return {
            "evaluation": final_eval,
            "best_move": max(move_lines, key=lambda x: x["evaluation"])["move"] if move_lines else None,
            "all_lines": move_lines,
            "depth": depth,
            "original_position": fen
        }
