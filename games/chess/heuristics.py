#!/usr/bin/env python3
"""A classic hand-crafted evaluation: material + piece-square tables.

This is intentionally *not* machine learning — it's the well-known
material-and-position heuristic used by countless classical chess engines. It
serves two roles here:

1. the evaluation behind `MinimaxOpponent` (a real "existing algorithm" to play
   against), and
2. the **bootstrap target** for the value network: before any self-play, the net
   is trained to imitate this heuristic so it starts out playing sensibly instead
   of randomly (see train.py).

Scores are in centipawns, from the **side-to-move's** perspective (positive = good
for the player to move), matching the value network's convention.
"""
import math
import chess

PIECE_VALUE = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0,
}

# Piece-square tables (White's view, a1 = index 0 ... h8 = index 63).
# Source: the widely-used "Simplified Evaluation Function" tables.
_PAWN = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]
_KNIGHT = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
_BISHOP = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
_ROOK = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]
_QUEEN = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
      0,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
_KING = [
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]
_PST = {chess.PAWN: _PAWN, chess.KNIGHT: _KNIGHT, chess.BISHOP: _BISHOP,
        chess.ROOK: _ROOK, chess.QUEEN: _QUEEN, chess.KING: _KING}

# Decisive score returned for mate (kept far outside the heuristic's normal range).
MATE = 1_000_000


def evaluate(board: chess.Board) -> int:
    """Static centipawn evaluation from the side-to-move's perspective.

    Handles terminal positions (mate/draw) directly.
    """
    if board.is_checkmate():
        return -MATE                      # side to move has been mated
    if board.is_stalemate() or board.is_insufficient_material() or \
       board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return 0

    score = 0
    for sq, piece in board.piece_map().items():
        val = PIECE_VALUE[piece.piece_type]
        pst = _PST[piece.piece_type]
        # PST is from White's view; mirror the square for Black pieces.
        psq = sq if piece.color == chess.WHITE else chess.square_mirror(sq)
        val += pst[psq]
        score += val if piece.color == chess.WHITE else -val

    return score if board.turn == chess.WHITE else -score


# Scale used to squash centipawns into the value net's [-1, 1] target range.
# ~600 cp ≈ a winning advantage → tanh(600/600)=0.76; 100cp (a pawn) ≈ 0.17.
VALUE_SCALE = 600.0


def normalized_value(board: chess.Board) -> float:
    """The heuristic squashed into [-1, 1] — the bootstrap target for the value net."""
    cp = evaluate(board)
    if cp >= MATE:
        return 1.0
    if cp <= -MATE:
        return -1.0
    return math.tanh(cp / VALUE_SCALE)
