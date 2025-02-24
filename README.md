# LLM Chess

A chess engine that uses GPT to evaluate positions and play chess at a high level.

## Features

- Position evaluation using GPT-3.5
- Recursive search with alpha-beta pruning
- Web interface for playing against the engine
- Detailed position analysis and move explanation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/llm-chess.git
cd llm-chess
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

5. Run migrations:
```bash
python manage.py migrate
```

## Usage

1. Start the development server:
```bash
python manage.py runserver
```

2. Open `http://localhost:8000/api/play/` in your browser
3. Start a new game and play against the engine!

## API Documentation

### Evaluate Position
```
POST /api/evaluate/
{
    "fen": "<FEN string>",
    "depth": <search depth>,
    "openai_api_key": "<your API key>"
}
```

### Get Bot Move
```
POST /api/move/
{
    "fen": "<FEN string>",
    "depth": <search depth>,
    "openai_api_key": "<your API key>"
}
```

## Development

### Project Structure
```
llm-chess/
├── api/
│   ├── chess/          # Chess logic
│   ├── views/          # API views
│   ├── utils/          # Utilities
│   └── templates/      # HTML templates
├── tests/              # Test suite
└── requirements.txt    # Dependencies
```

### Running Tests
```bash
python manage.py test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
