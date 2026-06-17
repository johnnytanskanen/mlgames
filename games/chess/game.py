#!/usr/bin/env python3
"""Play one game between two players and report the result.

A "player" is anything with `select_move(board) -> (move, stats)` — so `ChessAI`
and every class in opponents.py plug in interchangeably. Shared by arena.py
(benchmarking), selfplay.py (training-data generation) and play.py (the viewer).
"""
import chess

from encode import board_to_planes
from heuristics import evaluate

# Games that reach the ply cap are adjudicated by material: a clear edge counts as
# a win, otherwise a draw. Keeps self-play from labelling balanced positions as wins.
ADJUDICATE_CP = 200


def result_white_perspective(board: chess.Board) -> float:
    """+1 White won, -1 Black won, 0 draw. Adjudicates unfinished (ply-capped) games."""
    outcome = board.outcome(claim_draw=True)
    if outcome is not None:
        if outcome.winner is None:
            return 0.0
        return 1.0 if outcome.winner == chess.WHITE else -1.0
    # not over → adjudicate by material (evaluate() is side-to-move relative)
    cp = evaluate(board)
    cp = cp if board.turn == chess.WHITE else -cp
    if cp > ADJUDICATE_CP:
        return 1.0
    if cp < -ADJUDICATE_CP:
        return -1.0
    return 0.0


def play_game(white, black, max_plies=200, record=False, on_move=None):
    """Play white vs black. Returns (board, result_white_perspective, history).

    history (only if record=True) is a list of (planes, side_to_move) for every
    position a move was made from — used to build training targets.
    on_move(board, move, stats) is an optional callback (the viewer uses it).
    """
    board = chess.Board()
    players = {chess.WHITE: white, chess.BLACK: black}
    history = []

    while not board.is_game_over(claim_draw=True) and board.ply() < max_plies:
        move, stats = players[board.turn].select_move(board)
        if move is None:
            break
        if record:
            history.append((board_to_planes(board), board.turn))
        if on_move is not None:
            on_move(board, move, stats)
        board.push(move)

    return board, result_white_perspective(board), history


def labelled_positions(history, result_white):
    """Turn recorded history + final result into (planes, z) training pairs.

    z is the game outcome from each position's side-to-move perspective: +1 if that
    side ultimately won, -1 if it lost, 0 for a draw.
    """
    out = []
    for planes, side in history:
        z = result_white if side == chess.WHITE else -result_white
        out.append((planes, z))
    return out
