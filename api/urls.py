from django.urls import path
from .views import EvaluatePositionView, ChessGameView, GetBotMoveView

urlpatterns = [
    path('evaluate/', EvaluatePositionView.as_view(), name='evaluate-position'),
    path('play/', ChessGameView.as_view(), name='chess-game'),
    path('get_move/', GetBotMoveView.as_view(), name='get-bot-move'),
]
