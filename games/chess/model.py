#!/usr/bin/env python3
"""The chess value network — a small residual CNN.

Input:  (N, 17, 8, 8) position planes (see encode.py)
Output: (N,) scalar value in [-1, 1] via tanh, from the side-to-move's perspective
        (+1 = side to move is winning, -1 = losing, 0 = equal).

The net is deliberately compact (≈ a few hundred KB) so it trains on a laptop CPU/MPS
and the checkpoint can be committed. It is used as the leaf evaluator inside the
alpha-beta search in chess_ai.py.
"""
import os
import torch
import torch.nn as nn

from encode import N_PLANES

CHANNELS = 64
N_BLOCKS = 4
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pt')


def pick_device(name: str = 'auto') -> torch.device:
    """Resolve 'auto' to mps (Apple Silicon) → cuda → cpu, or honor an explicit name."""
    if name and name != 'auto':
        return torch.device(name)
    if torch.backends.mps.is_available():
        return torch.device('mps')
    if torch.cuda.is_available():
        return torch.device('cuda')
    return torch.device('cpu')


class _ResBlock(nn.Module):
    def __init__(self, ch):
        super().__init__()
        self.c1 = nn.Conv2d(ch, ch, 3, padding=1, bias=False)
        self.b1 = nn.BatchNorm2d(ch)
        self.c2 = nn.Conv2d(ch, ch, 3, padding=1, bias=False)
        self.b2 = nn.BatchNorm2d(ch)

    def forward(self, x):
        h = torch.relu(self.b1(self.c1(x)))
        h = self.b2(self.c2(h))
        return torch.relu(x + h)


class ValueNet(nn.Module):
    def __init__(self, channels=CHANNELS, blocks=N_BLOCKS):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(N_PLANES, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
        )
        self.tower = nn.Sequential(*[_ResBlock(channels) for _ in range(blocks)])
        self.head = nn.Sequential(
            nn.Conv2d(channels, 8, 1, bias=False),
            nn.BatchNorm2d(8),
            nn.ReLU(inplace=True),
            nn.Flatten(),
            nn.Linear(8 * 8 * 8, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 1),
        )

    def forward(self, x):
        h = self.tower(self.stem(x))
        return torch.tanh(self.head(h)).squeeze(-1)


def save(model: ValueNet, path=DEFAULT_PATH, meta=None):
    """Atomic checkpoint write (mirrors the tetris weights.json convention)."""
    payload = {'state_dict': model.state_dict(),
               'config': {'channels': CHANNELS, 'blocks': N_BLOCKS},
               'meta': meta or {}}
    tmp = path + '.tmp'
    torch.save(payload, tmp)
    os.replace(tmp, path)


def load(path=DEFAULT_PATH, device=None, strict=True):
    """Load a checkpoint. Returns (model, meta). Raises FileNotFoundError if absent."""
    device = device or pick_device()
    payload = torch.load(path, map_location=device, weights_only=False)
    cfg = payload.get('config', {})
    model = ValueNet(cfg.get('channels', CHANNELS), cfg.get('blocks', N_BLOCKS))
    model.load_state_dict(payload['state_dict'], strict=strict)
    model.to(device).eval()
    return model, payload.get('meta', {})


def load_or_new(path=DEFAULT_PATH, device=None):
    """Load model.pt if it exists, else return a fresh (untrained) net. Returns (model, meta, trained)."""
    device = device or pick_device()
    if os.path.exists(path):
        model, meta = load(path, device)
        return model, meta, True
    model = ValueNet().to(device).eval()
    return model, {}, False
