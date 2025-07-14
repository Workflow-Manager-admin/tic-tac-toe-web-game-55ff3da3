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
# API Endpoints for the Game Logic (Contract Only)
#######################################

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
    raise NotImplementedError("Game logic not implemented. This is only the contract.")


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
    raise NotImplementedError("Game logic not implemented. This is only the contract.")


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
    raise NotImplementedError("Game logic not implemented. This is only the contract.")


@app.get("/")
def health_check():
    return {"message": "Healthy"}
