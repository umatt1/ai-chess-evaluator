from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView
from .serializers import ChessPositionSerializer
from .chess_evaluator import ChessEvaluator
import chess

class ChessGameView(TemplateView):
    template_name = 'api/chess_game.html'

class PositionEvaluatorView(TemplateView):
    template_name = 'api/position_evaluator.html'

class GetBotMoveView(APIView):
    def post(self, request):
        serializer = ChessPositionSerializer(data=request.data)
        if serializer.is_valid():
            fen = serializer.validated_data['fen']
            depth = serializer.validated_data['depth']
            api_key = serializer.validated_data['openai_api_key']

            try:
                # Initial validation of the position
                board = chess.Board(fen)
                print(f"\nProcessing move for position: {fen}")
                print(f"Current turn: {'White' if board.turn else 'Black'}")
                print(f"Legal moves: {[move.uci() for move in board.legal_moves]}")

                if not list(board.legal_moves):
                    error_msg = "No legal moves available in this position"
                    print(error_msg)
                    return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

                # Get move from evaluator
                evaluator = ChessEvaluator(api_key)
                result = evaluator.evaluate_recursive(fen, depth)
                
                if 'error' in result:
                    print(f"Error in evaluation: {result['error']}")
                    return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
                
                if not result['best_move']:
                    error_msg = "No move was returned by the evaluator"
                    print(error_msg)
                    print(f"Full result: {result}")
                    return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                print(f"Best move found: {result['best_move']}")
                print(f"Evaluation: {result['evaluation']}")
                print(f"All possible lines: {result['all_lines']}")
                
                # Validate the move
                try:
                    move = chess.Move.from_uci(result['best_move'])
                    if move not in board.legal_moves:
                        error_msg = f"Invalid move {result['best_move']} for position {fen}"
                        print(error_msg)
                        print(f"Legal moves were: {[m.uci() for m in board.legal_moves]}")
                        return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
                except ValueError as e:
                    error_msg = f"Invalid move format: {result['best_move']}"
                    print(error_msg)
                    return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
                
                # Make sure the move actually changes the position
                test_board = board.copy()
                test_board.push(move)
                if test_board.fen() == fen:
                    error_msg = f"Move {result['best_move']} doesn't change the position"
                    print(error_msg)
                    return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'best_move': result['best_move'],
                    'evaluation': result['evaluation']
                })
            except Exception as e:
                print(f"Error processing move: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
