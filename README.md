# Chess Position Evaluator API

A Django REST API for evaluating chess positions using FEN notation and GPT-3.5-turbo-instruct for position analysis.

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Evaluate Position

**Endpoint**: `POST /api/evaluate/`

Evaluates a chess position using GPT-3.5-turbo-instruct with recursive depth analysis.

**Request Body**:
```json
{
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "depth": 2,
    "openai_api_key": "your-api-key-here"
}
```

**Parameters**:
- `fen`: FEN string representing the chess position
- `depth`: Depth of recursive analysis (1-3)
  - depth=1: Evaluates only the current position
  - depth=2: Evaluates current position and all possible moves
  - depth=3: Evaluates current position, all possible moves, and opponent's responses
- `openai_api_key`: Your OpenAI API key

**Response**:
```json
{
    "evaluation": 0.2,
    "best_move": "e2e4",
    "all_lines": [
        {
            "move": "e2e4",
            "evaluation": 0.2,
            "lines": [
                {
                    "move": "e7e5",
                    "evaluation": -0.1,
                    "lines": []
                }
            ]
        }
    ],
    "depth": 2,
    "original_position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

**Evaluation Scale**:
- Range: -10 to 10
- Positive values favor white
- Negative values favor black
- 0 indicates an equal position
- ±10 indicates a decisive advantage

## Error Handling

- Invalid FEN string: 400 Bad Request
- Invalid depth: 400 Bad Request
- Invalid or missing API key: 400 Bad Request
- Server errors: 500 Internal Server Error
