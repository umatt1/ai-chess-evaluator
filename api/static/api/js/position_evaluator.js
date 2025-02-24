// Global variables
let board = null;
let game = new Chess();
let apiKey = '';
let isPlacingPieces = false;

function setApiKey() {
    apiKey = document.getElementById('api-key').value;
    document.getElementById('status').innerText = 'API Key set. You can now evaluate positions!';
    document.getElementById('evaluateBtn').disabled = false;
}

function onDrop(source, target, piece, newPos, oldPos, orientation) {
    if (isPlacingPieces) {
        updateGameFromPosition(newPos);
        return;
    }

    // Prevent regular drops when not in placing mode
    return 'snapback';
}

function onDragStart(source, piece, position, orientation) {
    if (!isPlacingPieces) {
        return false;
    }
}

function updateGameFromPosition(position) {
    // Create a new game with the current position
    let newFen = Chessboard.objToFen(position);
    let turn = document.getElementById('turn').value;
    
    // Add turn, castling rights, and other FEN components
    newFen += ` ${turn} KQkq - 0 1`;
    
    try {
        let tempGame = new Chess(newFen);
        game = tempGame;
        updateFenDisplay();
    } catch (e) {
        console.error('Invalid position:', e);
        document.getElementById('status').innerText = 'Invalid position! Please check piece placement.';
    }
}

function togglePlacePieces() {
    isPlacingPieces = !isPlacingPieces;
    const btn = document.getElementById('placePiecesBtn');
    btn.style.backgroundColor = isPlacingPieces ? '#dc3545' : '#007bff';
    btn.innerText = isPlacingPieces ? 'Stop Placing' : 'Place Pieces';
    
    if (isPlacingPieces) {
        document.getElementById('status').innerText = 'Click squares to place the selected piece type';
    } else {
        document.getElementById('status').innerText = 'Piece placement mode disabled';
    }
}

function clearBoard() {
    board.position('8/8/8/8/8/8/8/8');
    game = new Chess('8/8/8/8/8/8/8/8 w KQkq - 0 1');
    updateFenDisplay();
}

function startingPosition() {
    board.start();
    game = new Chess();
    updateFenDisplay();
}

function updateFenDisplay() {
    document.getElementById('fen-string').innerText = game.fen();
}

async function evaluatePosition() {
    const statusElement = document.getElementById('status');
    const evaluationElement = document.getElementById('evaluation-results');
    const depth = document.getElementById('depth').value;

    statusElement.innerText = 'Evaluating position...';
    document.getElementById('evaluateBtn').disabled = true;

    try {
        const response = await fetch('/api/evaluate/', {
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
        
        if (data.error) {
            throw new Error(data.error);
        }

        // Display evaluation results
        let resultsHtml = '';
        
        // Display best move and evaluation
        if (data.best_move) {
            const evalText = data.evaluation > 0 ? `+${data.evaluation.toFixed(2)}` : 
                           data.evaluation < 0 ? data.evaluation.toFixed(2) : '0.00';
            resultsHtml += `
                <div class="evaluation-line">
                    <h3>Best Line</h3>
                    <p>Evaluation: <span class="evaluation-score">${evalText}</span></p>
                    <p>Best move: <span class="evaluation-move">${data.best_move}</span></p>
                </div>`;
        }

        // Display all analyzed lines
        if (data.all_lines) {
            resultsHtml += '<h3>All Analyzed Lines</h3>';
            for (const line of data.all_lines) {
                const evalText = line.evaluation > 0 ? `+${line.evaluation.toFixed(2)}` : 
                               line.evaluation < 0 ? line.evaluation.toFixed(2) : '0.00';
                resultsHtml += `
                    <div class="evaluation-line">
                        <p>Move: <span class="evaluation-move">${line.move}</span></p>
                        <p>Evaluation: <span class="evaluation-score">${evalText}</span></p>
                    </div>`;
            }
        }

        evaluationElement.innerHTML = resultsHtml;
        statusElement.innerText = 'Evaluation complete!';

    } catch (error) {
        console.error('Error in evaluatePosition:', error);
        statusElement.innerText = 'Error: ' + error.message;
        evaluationElement.innerHTML = '<p>Failed to evaluate position. Please try again.</p>';
    } finally {
        document.getElementById('evaluateBtn').disabled = false;
    }
}

// Handle square clicks for piece placement
function onSquareClick(square) {
    if (!isPlacingPieces) return;
    
    const piece = document.getElementById('pieceToPlace').value;
    const position = board.position();
    
    // Remove any existing piece on the square
    if (position[square]) {
        delete position[square];
    } else {
        // Place the selected piece
        position[square] = piece;
    }
    
    board.position(position);
    updateGameFromPosition(position);
}

// Initialize the board when the page loads
window.onload = function() {
    const config = {
        draggable: true,
        position: 'start',
        pieceTheme: '/static/api/img/chesspieces/wikipedia/{piece}.png',
        onDragStart: onDragStart,
        onDrop: onDrop,
        onSnapEnd: () => board.position(game.fen()),
        onSquareClick: onSquareClick
    };
    board = Chessboard('board', config);
    updateFenDisplay();
};
