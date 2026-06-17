#!/usr/bin/env python3
"""The neural chess player: a value network inside an alpha-beta search.

The network (model.py) only answers "how good is this position for the side to
move?". Turning that into strong play is the job of classic **alpha-beta
(negamax) search**: we look a few plies ahead, assume best play from both sides,
and evaluate the quiet leaf positions with the net.

    select_move(board, depth=2)  →  (best_move, stats)

Move ordering (captures first, MVV-LVA) makes the alpha-beta pruning effective. A
small transposition cache avoids re-evaluating positions reached by different move
orders. Terminal positions (mate/draw) are scored directly, so the net never has to
learn that a checkmate is good.
"""
import math
import random

import numpy as np
import torch
import chess
import chess.polyglot

from encode import board_to_planes
import model as model_mod

INF = float('inf')
# Mate score sits well above the value net's tanh range (±1), so a forced mate
# always dominates any heuristic eval; the ply term prefers quicker mates.
MATE_SCORE = 100.0

# MVV-LVA-ish piece weights for capture ordering.
_ORDER_VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
              chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


class ChessAI:
    def __init__(self, model=None, device=None, depth=2, name='neural'):
        self.device = device or model_mod.pick_device('cpu')  # cpu = low search latency
        if model is None:
            model, _meta, _trained = model_mod.load_or_new(device=self.device)
        self.model = model.to(self.device).eval()
        self.depth = depth
        self.name = name
        self._cache = {}          # zobrist hash -> nn value (side-to-move perspective)
        self.nodes = 0
        self.last_stats = {}

    # ---- network evaluation -------------------------------------------------

    def _nn_value(self, board: chess.Board) -> float:
        """Value in [-1, 1] from the side-to-move's perspective (cached)."""
        key = chess.polyglot.zobrist_hash(board)
        v = self._cache.get(key)
        if v is None:
            x = torch.from_numpy(board_to_planes(board)[None]).to(self.device)
            with torch.no_grad():
                v = float(self.model(x).item())
            self._cache[key] = v
        return v

    def _eval_children_batched(self, board, moves):
        """Score each root move by one network call over all (non-terminal) children.

        Returns scores from the *root* side-to-move's perspective. Used at depth 1
        (and for self-play) — one batched forward pass instead of N.
        """
        scores = [None] * len(moves)
        pending, planes = [], []
        for i, mv in enumerate(moves):
            board.push(mv)
            if board.is_checkmate():
                scores[i] = MATE_SCORE          # we just mated them
            elif board.is_game_over(claim_draw=False) or board.is_insufficient_material():
                scores[i] = 0.0
            else:
                pending.append(i)
                planes.append(board_to_planes(board))
            board.pop()
        if pending:
            x = torch.from_numpy(np.stack(planes)).to(self.device)
            with torch.no_grad():
                vals = self.model(x).cpu().numpy()
            # child value is from the opponent's perspective → negate for us
            for i, v in zip(pending, vals):
                scores[i] = -float(v)
        self.nodes += len(moves)
        return scores

    # ---- alpha-beta ---------------------------------------------------------

    def _ordered(self, board):
        """Legal moves, captures first (MVV-LVA), for better pruning."""
        def key(mv):
            if board.is_capture(mv):
                victim = board.piece_type_at(mv.to_square) or chess.PAWN  # en passant
                attacker = board.piece_type_at(mv.from_square)
                return 100 + _ORDER_VAL[victim] * 10 - _ORDER_VAL[attacker]
            return 0
        return sorted(board.legal_moves, key=key, reverse=True)

    def _negamax(self, board, depth, alpha, beta, ply):
        self.nodes += 1
        if board.is_checkmate():
            return -(MATE_SCORE - ply * 0.01)          # side to move is mated
        if board.is_stalemate() or board.is_insufficient_material() or \
           board.is_seventyfive_moves() or board.is_fivefold_repetition():
            return 0.0
        if depth == 0:
            return self._nn_value(board)

        best = -INF
        for mv in self._ordered(board):
            board.push(mv)
            val = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    # ---- public API ---------------------------------------------------------

    def root_scores(self, board, depth):
        """Score every legal move from the root side's perspective."""
        moves = list(board.legal_moves)
        if not moves:
            return moves, []
        if depth <= 1:
            return moves, self._eval_children_batched(board, moves)
        moves = self._ordered(board)
        scores = []
        for mv in moves:
            board.push(mv)
            scores.append(-self._negamax(board, depth - 1, -INF, INF, 1))
            board.pop()
        return moves, scores

    def select_move(self, board, depth=None, temperature=0.0, rng=random):
        """Return (move, stats). temperature>0 samples for self-play exploration."""
        depth = self.depth if depth is None else depth
        self.nodes = 0
        self._cache.clear()
        moves, scores = self.root_scores(board, depth)
        if not moves:
            return None, {'nodes': 0, 'eval': 0.0, 'depth': depth}

        if temperature and temperature > 0:
            s = np.array(scores, dtype=np.float64) / max(temperature, 1e-6)
            s -= s.max()
            p = np.exp(s); p /= p.sum()
            idx = rng.choices(range(len(moves)), weights=p, k=1)[0]
        else:
            idx = int(np.argmax(scores))

        best_eval = float(scores[idx])
        self.last_stats = {
            'nodes': self.nodes,
            'eval': best_eval,                 # root side-to-move perspective, [-1,1]-ish
            'depth': depth,
            'move': moves[idx],
            'n_moves': len(moves),
        }
        return moves[idx], self.last_stats


def material_eval_cp(board):
    """Convenience re-export used by callers wanting a quick static read."""
    from heuristics import evaluate
    return evaluate(board)
