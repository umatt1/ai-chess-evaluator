from django.urls import path
from .views import EvaluatePositionView

urlpatterns = [
    path('evaluate/', EvaluatePositionView.as_view(), name='evaluate-position'),
]
