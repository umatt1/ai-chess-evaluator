from django.urls import path
from .views import EvaluatePositionView, ChessGameView, GetBotMoveView, PositionEvaluatorView

urlpatterns = [
    path('evaluate/', EvaluatePositionView.as_view(), name='evaluate-position'),
    path('play/', ChessGameView.as_view(), name='chess-game'),
    path('get_move/', GetBotMoveView.as_view(), name='get-bot-move'),
    path('analyze/', PositionEvaluatorView.as_view(), name='position-evaluator'),
]
