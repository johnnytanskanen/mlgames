#!/usr/bin/env python3
"""Opponents to play (and benchmark) the neural net against — "existing AI algorithms".

All opponents share one tiny interface:

    move, stats = opponent.select_move(board)

so they're drop-in interchangeable with `ChessAI` in arena.py / play.py / selfplay.py.

    RandomOpponent   — picks a uniformly random legal move (the noise floor).
    MaterialOpponent — greedy 1-ply: grab the move that maximizes material (+PST).
    MinimaxOpponent  — classic alpha-beta over the material+PST heuristic. A real,
                       non-ML chess algorithm — the main yardstick for "did the net
                       actually learn to play?".
    UCIEngineOpponent — wraps any UCI engine (e.g. Stockfish) via python-chess.
                        Auto-detected; absent → find_stockfish() returns None and
                        callers simply skip it.
"""
import random
import shutil

import chess
import chess.engine

from heuristics import evaluate, MATE

INF = float('inf')


class RandomOpponent:
    name = 'random'

    def __init__(self, rng=None):
        self.rng = rng or random.Random()

    def select_move(self, board):
        moves = list(board.legal_moves)
        return (self.rng.choice(moves) if moves else None), {}


class MaterialOpponent:
    """Greedy: choose the move with the best immediate static evaluation (1-ply)."""
    name = 'material'

    def __init__(self, rng=None):
        self.rng = rng or random.Random()

    def select_move(self, board):
        best, best_moves = -INF, []
        for mv in board.legal_moves:
            board.push(mv)
            val = -evaluate(board)            # eval is from the mover's side; negate
            board.pop()
            if val > best:
                best, best_moves = val, [mv]
            elif val == best:
                best_moves.append(mv)
        if not best_moves:
            return None, {}
        return self.rng.choice(best_moves), {'eval': best / 100.0}


class MinimaxOpponent:
    """Classic alpha-beta search over the hand-crafted material+PST evaluation."""

    def __init__(self, depth=2, rng=None):
        self.depth = depth
        self.rng = rng or random.Random()
        self.name = f'minimax{depth}'
        self.nodes = 0

    def _search(self, board, depth, alpha, beta):
        self.nodes += 1
        if board.is_checkmate():
            return -MATE
        if board.is_game_over(claim_draw=False) or board.is_insufficient_material():
            return 0
        if depth == 0:
            return evaluate(board)
        best = -INF
        for mv in self._ordered(board):
            board.push(mv)
            best = max(best, -self._search(board, depth - 1, -beta, -alpha))
            board.pop()
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best

    @staticmethod
    def _ordered(board):
        return sorted(board.legal_moves, key=board.is_capture, reverse=True)

    def select_move(self, board):
        self.nodes = 0
        best, best_moves = -INF, []
        for mv in self._ordered(board):
            board.push(mv)
            val = -self._search(board, self.depth - 1, -INF, INF)
            board.pop()
            if val > best:
                best, best_moves = val, [mv]
            elif val == best:
                best_moves.append(mv)
        if not best_moves:
            return None, {}
        return self.rng.choice(best_moves), {'eval': best / 100.0, 'nodes': self.nodes}


def find_stockfish():
    """Return a path to a Stockfish/UCI binary if one is on PATH, else None."""
    for name in ('stockfish', 'stockfish.exe'):
        path = shutil.which(name)
        if path:
            return path
    return None


class UCIEngineOpponent:
    """Adapter for any UCI engine (Stockfish). Optional — needs the binary installed."""

    def __init__(self, path=None, movetime=0.1, skill=None):
        path = path or find_stockfish()
        if not path:
            raise FileNotFoundError("no UCI engine found (install Stockfish or pass a path)")
        self.engine = chess.engine.SimpleEngine.popen_uci(path)
        self.limit = chess.engine.Limit(time=movetime)
        if skill is not None:
            try:
                self.engine.configure({'Skill Level': skill})
            except chess.engine.EngineError:
                pass
        self.name = 'stockfish'

    def select_move(self, board):
        result = self.engine.play(board, self.limit)
        return result.move, {}

    def close(self):
        try:
            self.engine.quit()
        except Exception:
            pass


def make_opponent(kind, depth=2, rng=None):
    """Factory used by the CLIs. Returns an opponent or raises for unknown/missing kinds."""
    kind = kind.lower()
    if kind == 'random':
        return RandomOpponent(rng)
    if kind == 'material':
        return MaterialOpponent(rng)
    if kind.startswith('minimax'):
        d = int(kind[7:]) if kind[7:].isdigit() else depth
        return MinimaxOpponent(d, rng)
    if kind in ('stockfish', 'uci'):
        return UCIEngineOpponent()
    raise ValueError(f"unknown opponent '{kind}' "
                     "(choose: random, material, minimax, minimax3, stockfish)")
