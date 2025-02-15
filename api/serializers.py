from rest_framework import serializers

class ChessPositionSerializer(serializers.Serializer):
    fen = serializers.CharField(required=True, help_text="FEN string representing the chess position")
    depth = serializers.IntegerField(required=True, min_value=1, max_value=3, help_text="Depth of recursive position analysis")
    openai_api_key = serializers.CharField(required=True, help_text="OpenAI API key for GPT analysis")
