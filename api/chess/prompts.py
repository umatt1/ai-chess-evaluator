"""GPT prompts for chess evaluation."""

def get_evaluation_prompt(fen: str, board_analysis: dict) -> str:
    """Generate the evaluation prompt for GPT.
    
    Args:
        fen: Current position FEN string
        board_analysis: Dict containing position analysis
        
    Returns:
        str: Formatted prompt for GPT
    """
    return f"""You are a chess position evaluator. Return ONLY a single decimal number between -10.0 and 10.0 representing the position evaluation.

Rules for evaluation:
1. Return ONLY the number, no text or explanation
2. Positive numbers favor White, negative favor Black
3. Use decimal points (e.g. 0.5 not 1/2)
4. Typical values: 0.0 (equal), 0.5 (slight White advantage), -0.5 (slight Black advantage)

Position Analysis:
FEN: {fen}

1. Material Count
   White: {board_analysis['white_material']}
   Black: {board_analysis['black_material']}

2. Position Details
   - Turn: {board_analysis['turn']}
   - Center Control: White={board_analysis['white_center']}, Black={board_analysis['black_center']}
   - Castling: White={board_analysis['white_castling']}, Black={board_analysis['black_castling']}
   - Phase: {board_analysis['phase']}
   - Legal Moves: {board_analysis['legal_moves']}

Guidelines:
1. Consider material values: pawn=1, knight/bishop=3, rook=5, queen=9
2. Factor in:
   - Center control and piece activity
   - King safety and pawn structure
   - Development and mobility
   - Current turn advantage (+0.2 for side to move)

Return ONLY a decimal number between -10.0 and 10.0 (e.g. 0.5, -1.2, 3.0).
Evaluation:"""
