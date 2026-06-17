#!/usr/bin/env python3
"""Board → tensor encoding for the chess value network.

A position is encoded as a stack of 8x8 binary planes, **always from the side-to-
move's perspective** (the board is mirrored when it's Black's turn). That symmetry
lets a single value head answer one question — "how good is this for the player about
to move?" — regardless of color, so the net never has to learn White and Black
separately.

Planes (17 total):
    0-5    our pieces      (pawn, knight, bishop, rook, queen, king)
    6-11   their pieces    (same order)
    12     our  kingside castling right   (whole plane on/off)
    13     our  queenside castling right
    14     their kingside castling right
    15     their queenside castling right
    16     en-passant target square
"""
import numpy as np
import chess

N_PLANES = 17
PIECE_ORDER = [chess.PAWN, chess.KNIGHT, chess.BISHOP,
               chess.ROOK, chess.QUEEN, chess.KING]
_PIECE_IDX = {pt: i for i, pt in enumerate(PIECE_ORDER)}


def board_to_planes(board: chess.Board) -> np.ndarray:
    """Return a (17, 8, 8) float32 array from the side-to-move's perspective."""
    planes = np.zeros((N_PLANES, 8, 8), dtype=np.float32)
    us = board.turn

    for sq, piece in board.piece_map().items():
        # orient so our back rank is row 0
        osq = sq if us == chess.WHITE else chess.square_mirror(sq)
        r, f = chess.square_rank(osq), chess.square_file(osq)
        idx = _PIECE_IDX[piece.piece_type] + (0 if piece.color == us else 6)
        planes[idx, r, f] = 1.0

    if board.has_kingside_castling_rights(us):
        planes[12, :, :] = 1.0
    if board.has_queenside_castling_rights(us):
        planes[13, :, :] = 1.0
    if board.has_kingside_castling_rights(not us):
        planes[14, :, :] = 1.0
    if board.has_queenside_castling_rights(not us):
        planes[15, :, :] = 1.0

    if board.ep_square is not None:
        esq = board.ep_square if us == chess.WHITE else chess.square_mirror(board.ep_square)
        planes[16, chess.square_rank(esq), chess.square_file(esq)] = 1.0

    return planes


def boards_to_batch(boards) -> np.ndarray:
    """Stack several boards into a (N, 17, 8, 8) float32 array."""
    return np.stack([board_to_planes(b) for b in boards], axis=0)
