// Global variables
let board = null;
let game = new Chess();
let apiKey = '';
let userColor = 'w';
let isThinking = false;

function setApiKey() {
    apiKey = document.getElementById('api-key').value;
    document.getElementById('status').innerText = 'API Key set. You can start a new game!';
    document.getElementById('newGameBtn').disabled = false;
}

function onDragStart(source, piece, position, orientation) {
    if (isThinking || game.game_over() || 
        (game.turn() !== userColor) || 
        piece.search(userColor) === -1) {
        return false;
    }
}

async function onDrop(source, target) {
    const move = game.move({
        from: source,
        to: target,
        promotion: 'q'
    });

    if (move === null) return 'snapback';

    updateStatus();
    await makeComputerMove();
}

function onSnapEnd() {
    board.position(game.fen());
}

async function makeComputerMove() {
    if (game.game_over()) {
        console.log('Game is over, not making move');
        return;
    }

    isThinking = true;
    const statusElement = document.getElementById('status');
    statusElement.innerText = 'GPT is thinking...';

    try {
        console.log('Current FEN:', game.fen());
        console.log('Current turn:', game.turn());
        console.log('Legal moves:', game.moves({ verbose: true }));

        const depth = document.getElementById('depth').value;
        console.log('Requesting move with depth:', depth);

        const response = await fetch('/api/get_move/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fen: game.fen(),
                depth: parseInt(depth),
                openai_api_key: apiKey
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Received response:', data);
        
        if (data.error) {
            throw new Error(data.error);
        }

        if (!data.best_move) {
            throw new Error('No move received from server');
        }

        // Convert the move string (e.g., 'e2e4') to a move object
        const moveObj = {
            from: data.best_move.substring(0, 2),
            to: data.best_move.substring(2, 4),
            promotion: data.best_move.length > 4 ? data.best_move[4] : undefined
        };

        console.log('Attempting to make move:', moveObj);

        // Make the move
        const move = game.move(moveObj);
        if (move === null) {
            throw new Error('Invalid move received from server: ' + data.best_move);
        }

        console.log('Move made successfully');

        // Update the board
        board.position(game.fen());
        updateStatus();

        // Add evaluation to status
        const evalText = data.evaluation > 0 ? `+${data.evaluation.toFixed(1)}` : 
                        data.evaluation < 0 ? data.evaluation.toFixed(1) : '0.0';
        statusElement.innerText += ` (Evaluation: ${evalText})`;

    } catch (error) {
        console.error('Error in makeComputerMove:', error);
        statusElement.innerText = 'Error: ' + error.message;
        // If there's an error, enable the user to try again
        isThinking = false;
    } finally {
        isThinking = false;
    }
}

function updateStatus() {
    let status = '';

    let moveColor = game.turn() === 'b' ? 'Black' : 'White';

    if (game.in_checkmate()) {
        status = `Game over, ${moveColor} is in checkmate.`;
    } else if (game.in_draw()) {
        status = 'Game over, drawn position';
    } else {
        status = `${moveColor} to move`;
        if (game.in_check()) {
            status += `, ${moveColor} is in check`;
        }
    }

    document.getElementById('status').innerText = status;
}

function newGame() {
    game = new Chess();
    board.position('start');
    updateStatus();
    document.getElementById('undoBtn').disabled = false;
}

function undoMove() {
    game.undo(); // Undo computer's move
    game.undo(); // Undo player's move
    board.position(game.fen());
    updateStatus();
}

// Initialize the board when the page loads
window.onload = function() {
    const config = {
        draggable: true,
        position: 'start',
        pieceTheme: '/static/api/img/chesspieces/wikipedia/{piece}.png',
        onDragStart: onDragStart,
        onDrop: onDrop,
        onSnapEnd: onSnapEnd
    };
    board = Chessboard('board', config);
    document.getElementById('newGameBtn').disabled = !apiKey;
};
