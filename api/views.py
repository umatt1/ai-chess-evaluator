from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChessPositionSerializer
from .chess_evaluator import ChessEvaluator

class EvaluatePositionView(APIView):
    def post(self, request):
        serializer = ChessPositionSerializer(data=request.data)
        if serializer.is_valid():
            fen = serializer.validated_data['fen']
            depth = serializer.validated_data['depth']
            api_key = serializer.validated_data['openai_api_key']

            try:
                evaluator = ChessEvaluator(api_key)
                result = evaluator.evaluate_recursive(fen, depth)
                
                if 'error' in result:
                    return Response(
                        {'error': result['error']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                return Response(result)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
