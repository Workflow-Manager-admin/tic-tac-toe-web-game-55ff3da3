from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

app = FastAPI(
    title="Tic Tac Toe Backend",
    version="1.0.0",
    description="Backend API for the Tic Tac Toe web game. Provides endpoints to create/reset game, make moves, and query game state.",
    openapi_tags=[
        {"name": "Game", "description": "Endpoints for Tic Tac Toe gameplay"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUBLIC_INTERFACE
class BoardModel(BaseModel):
    """
    Represents the Tic Tac Toe board as a 3x3 grid.
    """
    board: List[List[Optional[Literal['X', 'O']]]] = Field(
        ...,
        description="A 3x3 matrix representing the board with cells as 'X', 'O', or null (empty)"
    )


# PUBLIC_INTERFACE
class MoveModel(BaseModel):
    """
    Represents a move request from client.
    """
    row: int = Field(..., ge=0, le=2, description="Zero-based row index for the move (0-2)")
    col: int = Field(..., ge=0, le=2, description="Zero-based column index for the move (0-2)")
    player: Literal['X', 'O'] = Field(..., description="The symbol of the player making the move ('X' or 'O')")


# PUBLIC_INTERFACE
class GameResultModel(BaseModel):
    """
    Represents the result state of the current game.
    """
    status: Literal["in_progress", "won", "draw"] = Field(..., description="Game status: in progress, won, or draw")
    winner: Optional[Literal['X', 'O']] = Field(None, description="Winner symbol if there is a winner, otherwise null")


# PUBLIC_INTERFACE
class GameStateModel(BaseModel):
    """
    Represents the entire current state of the game.
    """
    board: List[List[Optional[Literal['X', 'O']]]] = Field(..., description="Current board state")
    current_player: Literal['X', 'O'] = Field(..., description="Which player's turn it is")
    result: GameResultModel = Field(..., description="Current game result and winner if any")

# PUBLIC_INTERFACE
class MoveResponseModel(BaseModel):
    """
    Response after making a move.
    """
    board: List[List[Optional[Literal['X', 'O']]]] = Field(..., description="Updated board state after move")
    current_player: Literal['X', 'O'] = Field(..., description="Next player's turn")
    result: GameResultModel = Field(..., description="Game result after the move")

#######################################
# API Endpoints for the Game Logic with actual logic implementation
#######################################

from threading import Lock

# In-memory game state (single game for simplicity)
_game_state = {
    "board": [[None for _ in range(3)] for _ in range(3)],  # 3x3 board
    "current_player": "X",  # 'X' starts first
    "result": {"status": "in_progress", "winner": None}
}
_game_lock = Lock()

def _init_board():
    """Create new empty 3x3 board"""
    return [[None for _ in range(3)] for _ in range(3)]

def _check_winner(board):
    """Check for winner: returns 'X', 'O', or None"""
    # Check rows and columns
    for i in range(3):
        # Row
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] is not None:
            return board[i][0]
        # Column
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] is not None:
            return board[0][i]
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
        return board[0][0]
    if board[2][0] == board[1][1] == board[0][2] and board[2][0] is not None:
        return board[2][0]
    # No winner
    return None

def _is_draw(board):
    """Check if all cells are filled and there is no winner"""
    for row in board:
        if None in row:
            return False
    return _check_winner(board) is None

def _compute_result(board):
    """Compute GameResultModel for given board"""
    winner = _check_winner(board)
    if winner is not None:
        return GameResultModel(status="won", winner=winner)
    elif _is_draw(board):
        return GameResultModel(status="draw", winner=None)
    else:
        return GameResultModel(status="in_progress", winner=None)

def _get_next_player(current_player):
    return "O" if current_player == "X" else "X"

def _reset_game():
    """Resets in-memory board and state to initial values"""
    _game_state["board"] = _init_board()
    _game_state["current_player"] = "X"
    _game_state["result"] = {"status": "in_progress", "winner": None}

def _export_gamestate():
    """Return GameStateModel based on current memory"""
    return GameStateModel(
        board=[row[:] for row in _game_state["board"]],
        current_player=_game_state["current_player"],
        result=GameResultModel(**_game_state["result"])
    )

def _export_moveresponse():
    """Return MoveResponseModel based on current memory"""
    return MoveResponseModel(
        board=[row[:] for row in _game_state["board"]],
        current_player=_game_state["current_player"],
        result=GameResultModel(**_game_state["result"])
    )

# PUBLIC_INTERFACE
@app.post(
    "/game",
    response_model=GameStateModel,
    summary="Start or reset a game",
    description="Start a new game or reset the current game. Returns the fresh game state.",
    tags=["Game"],
)
def start_or_reset_game():
    """
    Starts a new Tic Tac Toe game or resets the current one.

    Returns:
        GameStateModel: The initial or reset game state, board as empty, current player as 'X', status as 'in_progress'.
    """
    with _game_lock:
        _reset_game()
        # Compose state for API response
        return _export_gamestate()

# PUBLIC_INTERFACE
@app.post(
    "/game/move",
    response_model=MoveResponseModel,
    summary="Make a move",
    description="Apply a move to the current game. Returns the updated game state and result.",
    tags=["Game"],
)
def make_move(move: MoveModel):
    """
    Plays a move for the given player at the specified position.

    Args:
        move (MoveModel): The move details - row, col, and player ('X' or 'O').

    Returns:
        MoveResponseModel: The updated game state after the move.
    """
    with _game_lock:
        # Check if the game is in progress
        if _game_state["result"]["status"] != "in_progress":
            # Cannot play if game is finished, respond with latest state
            return _export_moveresponse()

        # Validate it's the correct player's turn
        if move.player != _game_state["current_player"]:
            raise ValueError(f"It is not {move.player}'s turn.")

        # Validate move: within bounds and cell empty
        if not (0 <= move.row < 3 and 0 <= move.col < 3):
            raise ValueError("Move is out of bounds.")
        if _game_state["board"][move.row][move.col] is not None:
            raise ValueError("Cell already taken.")

        # Make the move
        _game_state["board"][move.row][move.col] = move.player

        # Recompute result: win, draw, or still playing
        result_model = _compute_result(_game_state["board"])
        _game_state["result"] = result_model.model_dump()

        # Advance player if game still in progress, else leave winner's turn
        if _game_state["result"]["status"] == "in_progress":
            _game_state["current_player"] = _get_next_player(move.player)
        # else: do not change player, game is over

        return _export_moveresponse()

# PUBLIC_INTERFACE
@app.get(
    "/game",
    response_model=GameStateModel,
    summary="Get current game state",
    description="Returns the current board, player turn, and game result.",
    tags=["Game"],
)
def get_game_state():
    """
    Returns the current state of the game, including the board, current player, and game result status.

    Returns:
        GameStateModel: The full state of the current game.
    """
    with _game_lock:
        return _export_gamestate()

@app.get("/")
def health_check():
    return {"message": "Healthy"}
