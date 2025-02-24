"""Views for chess game interaction."""

from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..chess.evaluator import ChessEvaluator
from ..utils.validation import validate_position, validate_move
from ..utils.logging import setup_logger
from ..serializers import ChessPositionSerializer

logger = setup_logger(__name__)

class ChessGameView(TemplateView):
    """View for the chess game interface."""
    template_name = 'api/chess_game.html'

class GetBotMoveView(APIView):
    """View for getting the bot's next move."""
    
    def post(self, request):
        """Handle POST request for bot move.
        
        Args:
            request: HTTP request
            
        Returns:
            Response: Bot's move or error
        """
        serializer = ChessPositionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        fen = serializer.validated_data['fen']
        depth = serializer.validated_data['depth']
        api_key = serializer.validated_data['openai_api_key']

        try:
            # Validate position
            board, error = validate_position(fen)
            if error:
                logger.error(f"Position validation failed: {error}")
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Processing move for position: {fen}")
            logger.info(f"Current turn: {'White' if board.turn else 'Black'}")
            logger.debug(f"Legal moves: {[move.uci() for move in board.legal_moves]}")

            # Get move from evaluator
            evaluator = ChessEvaluator(api_key)
            result = evaluator.evaluate_recursive(fen, depth)
            
            if 'error' in result:
                logger.error(f"Evaluation error: {result['error']}")
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not result['best_move']:
                error = "No move was returned by the evaluator"
                logger.error(f"{error}. Full result: {result}")
                return Response(
                    {'error': error},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Validate the chosen move
            error = validate_move(result['best_move'], board)
            if error:
                logger.error(error)
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Best move found: {result['best_move']}")
            logger.info(f"Evaluation: {result['evaluation']}")
            logger.debug(f"All possible lines: {result['all_lines']}")
            
            return Response({
                'best_move': result['best_move'],
                'evaluation': result['evaluation']
            })
            
        except Exception as e:
            logger.exception("Error processing move")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
