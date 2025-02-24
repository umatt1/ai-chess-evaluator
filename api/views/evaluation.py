"""Views for chess position evaluation."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..chess.evaluator import ChessEvaluator
from ..utils.validation import validate_position
from ..utils.logging import setup_logger
from ..serializers import ChessPositionSerializer

logger = setup_logger(__name__)

class EvaluatePositionView(APIView):
    """View for evaluating chess positions."""
    
    def post(self, request):
        """Handle POST request for position evaluation.
        
        Args:
            request: HTTP request
            
        Returns:
            Response: Position evaluation or error
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

            logger.info(f"Evaluating position: {fen}")
            
            # Get evaluation
            evaluator = ChessEvaluator(api_key)
            result = evaluator.evaluate_recursive(fen, depth)
            
            if 'error' in result:
                logger.error(f"Evaluation error: {result['error']}")
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Evaluation complete: {result['evaluation']}")
            return Response(result)
            
        except Exception as e:
            logger.exception("Error evaluating position")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
