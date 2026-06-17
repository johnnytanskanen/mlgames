#!/usr/bin/env python3
"""Generate screenshots of the Tetris AI for the README."""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# the engine lives in the terminal/ folder after the web/terminal split
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'terminal'))
import tetris_ai as t

CELL = 24
COLORS = {
    1: (34, 211, 238),   # I - cyan
    2: (250, 204, 21),   # O - yellow
    3: (192, 132, 252),  # T - purple
    4: (74, 222, 128),   # S - green
    5: (244, 63, 94),    # Z - red
    6: (251, 146, 60),   # L - orange
    7: (59, 130, 246),   # J - blue
}
BG = (14, 14, 12)
SURFACE = (34, 34, 32)
BORDER = (51, 51, 48)
TEXT = (184, 184, 168)
DIM = (102, 102, 96)
GREEN = (78, 201, 48)
RED = (224, 48, 48)
CYAN = (32, 184, 200)
YELLOW = (200, 192, 32)
ACCENT = (232, 228, 208)


def draw_cell(draw, x, y, color):
    draw.rectangle([x+1, y+1, x+CELL-2, y+CELL-2], fill=color)
    hi = tuple(min(c+40, 255) for c in color)
    lo = tuple(max(c-40, 0) for c in color)
    draw.rectangle([x+1, y+1, x+CELL-2, y+3], fill=hi)
    draw.rectangle([x+1, y+1, x+3, y+CELL-2], fill=hi)
    draw.rectangle([x+1, y+CELL-4, x+CELL-2, y+CELL-2], fill=lo)
    draw.rectangle([x+CELL-4, y+1, x+CELL-2, y+CELL-2], fill=lo)


def sparkline_img(draw, data, x, y, w, h, color, max_val=None):
    if not data:
        return
    if max_val is None:
        max_val = max(data) if max(data) > 0 else 1
    step = w / len(data)
    points = []
    for i, v in enumerate(data):
        px = x + i * step + step/2
        py = y + h - (v / max_val) * h
        points.append((px, py))
    if len(points) > 1:
        draw.line(points, fill=color, width=2)


def bar_chart(draw, data, x, y, w, h, color):
    if not data:
        return
    max_val = max(data) if max(data) > 0 else 1
    bw = max(w // len(data) - 2, 3)
    for i, v in enumerate(data):
        bh = int((v / max_val) * h)
        bx = x + i * (bw + 2)
        by = y + h - bh
        draw.rectangle([bx, by, bx+bw, y+h], fill=color)


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _blend(a, b, t_):
    return tuple(int(a[i] + (b[i] - a[i]) * t_) for i in range(3))


def _section(draw, x, y, w, num, label, fonts):
    """Constructivist numbered section header; returns content-start y."""
    draw.text((x, y - 8), num, font=fonts['disp_sec'], fill=PAL['red'])
    draw.text((x + 46, y + 4), label.upper(), font=fonts['lab'], fill=PAL['ink'])
    draw.line([(x, y + 26), (x + w, y + 26)], fill=PAL['ink'], width=3)
    return y + 38


# constructivist palette (warm cream / vermilion / ink)
PAL = {
    'paper': (231, 221, 198), 'ink': (28, 24, 19), 'ink2': (76, 67, 52),
    'red': (214, 55, 43), 'ochre': (176, 122, 30), 'board': (22, 18, 12),
}
IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
HELV = "/System/Library/Fonts/Helvetica.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"


def _masthead(draw, img_w, fonts):
    # skewed red band
    draw.polygon([(-10, 30), (int(img_w * 0.56), 30),
                  (int(img_w * 0.56) - 42, 98), (-10, 98)], fill=PAL['red'])
    draw.text((24, 8), "SELF-LEARNING AGENT", font=fonts['kick'], fill=PAL['ink'])
    # wordmark with hard shadow
    draw.text((27, 39), "TETRIS", font=fonts['disp'], fill=PAL['ink'])
    draw.text((24, 36), "TETRIS", font=fonts['disp'], fill=PAL['paper'])
    wt = draw.textlength("TETRIS", font=fonts['disp'])
    bxp = 24 + wt + 16
    draw.rectangle([bxp, 46, bxp + 52, 86], fill=PAL['ink'])
    draw.text((bxp + 10, 50), "AI", font=fonts['ai'], fill=PAL['paper'])
    draw.text((24, 104), "TETRIS · AI TELEMETRY DASHBOARD", font=fonts['sub'], fill=PAL['ink'])
    # status chip
    draw.rectangle([img_w - 122, 12, img_w - 24, 34], outline=PAL['red'], width=2)
    draw.text((img_w - 112, 16), "RUNNING", font=fonts['mono'], fill=PAL['red'])


def generate_game_screenshot(game, filename):
    board_w = t.BOARD_WIDTH * CELL
    board_h = t.BOARD_HEIGHT * CELL
    panel_w = 440
    margin = 24
    by = 132
    img_w = margin + board_w + 30 + panel_w + margin
    img_h = by + board_h + 100 + margin

    img = Image.new('RGB', (img_w, img_h), PAL['paper'])
    draw = ImageDraw.Draw(img)
    fonts = {
        'disp': _font(IMPACT, 54), 'ai': _font(IMPACT, 30), 'disp_sec': _font(IMPACT, 30),
        'statnum': _font(IMPACT, 28), 'kick': _font(MENLO, 11), 'sub': _font(HELV, 14),
        'lab': _font(HELV, 13), 'mono': _font(MENLO, 10), 'small': _font(MENLO, 9),
    }
    _masthead(draw, img_w, fonts)

    # board window
    bx = margin
    draw.rectangle([bx - 4, by - 4, bx + board_w + 4, by + board_h + 4], fill=PAL['ink'])
    draw.rectangle([bx, by, bx + board_w, by + board_h], fill=PAL['board'])
    for cy in range(t.BOARD_HEIGHT):
        for cx in range(t.BOARD_WIDTH):
            px, py = bx + cx * CELL, by + cy * CELL
            draw.rectangle([px, py, px + CELL, py + CELL], outline=(42, 33, 20))
            if game.board.grid[cy][cx]:
                draw_cell(draw, px, py, COLORS.get(game.board.color_grid[cy][cx], (128,)*3))
    if not game.game_over and game.current_shape:
        col = COLORS.get(t.PIECE_COLORS[game.current_piece], (128,)*3)
        for sy, row in enumerate(game.current_shape):
            for sx, cell in enumerate(row):
                if cell and game.piece_y + sy >= 0:
                    draw_cell(draw, bx + (game.piece_x + sx) * CELL, by + (game.piece_y + sy) * CELL, col)

    # scoreboard (2x2)
    sy = by + board_h + 10
    cells = [("SCORE", f"{game.score:,}", PAL['red']), ("LINES", str(game.lines), PAL['ink']),
             ("LEVEL", str(game.level), PAL['ink']), ("PIECES", str(game.pieces_placed), PAL['ink'])]
    cw = board_w // 2
    ch = 42
    draw.rectangle([bx, sy, bx + cw * 2, sy + ch * 2], fill=PAL['paper'], outline=PAL['ink'], width=3)
    draw.line([(bx + cw, sy), (bx + cw, sy + ch * 2)], fill=PAL['ink'], width=2)
    draw.line([(bx, sy + ch), (bx + cw * 2, sy + ch)], fill=PAL['ink'], width=2)
    for i, (lab, val, c) in enumerate(cells):
        cx = bx + (i % 2) * cw
        cyy = sy + (i // 2) * ch
        draw.text((cx + 8, cyy + 5), lab, font=fonts['small'], fill=PAL['ink2'])
        draw.text((cx + 8, cyy + 14), val, font=fonts['statnum'], fill=c)

    # right panels
    px = margin + board_w + 30
    pw = panel_w
    py = by

    cy0 = _section(draw, px, py, pw, "01", "Decision weights", fonts)
    metrics = game.ai.last_metrics
    if metrics:
        items = [('lines', metrics.get('lines', 0), game.ai.weights['lines_cleared']),
                 ('holes', metrics.get('holes', 0), game.ai.weights['holes']),
                 ('height', metrics.get('height', 0), game.ai.weights['aggregate_height']),
                 ('bumpy', metrics.get('bumpy', 0), game.ai.weights['bumpiness']),
                 ('wells', metrics.get('wells', 0), game.ai.weights['wells']),
                 ('row tr', metrics.get('row_tr', 0), game.ai.weights['row_transitions']),
                 ('col tr', metrics.get('col_tr', 0), game.ai.weights['col_transitions'])]
        mxv = max(abs(r * w) for _, r, w in items) or 1
        bwe = pw // 7
        base = cy0 + 46
        for i, (name, raw, weight) in enumerate(items):
            wv = raw * weight
            xb = px + i * bwe
            bh = int(min(abs(wv) / mxv, 1.0) * 40)
            c = PAL['ink'] if wv >= 0 else PAL['red']
            draw.rectangle([xb, base - bh, xb + bwe - 8, base], fill=c)
            draw.text((xb, base + 4), f"{wv:.0f}", font=fonts['mono'], fill=c)
            draw.text((xb, cy0), name, font=fonts['small'], fill=PAL['ink2'])
        draw.line([(px, base), (px + pw, base)], fill=PAL['ink'], width=2)
    py += 132

    cy0 = _section(draw, px, py, pw, "02", "Candidate placements", fonts)
    if game.ai.last_candidates:
        cands = game.ai.last_candidates
        mx, mn = cands[0], cands[-1]
        rng = mx - mn if mx != mn else 1
        cbw = max(pw // len(cands) - 1, 2)
        base = cy0 + 50
        for i, s in enumerate(cands):
            n = (s - mn) / rng
            h = int(4 + n * 44)
            col = _blend(PAL['paper'], PAL['red'], 0.2 + n * 0.8)
            xb = px + i * (cbw + 1)
            draw.rectangle([xb, base - h, xb + cbw, base], fill=col)
    py += 96

    cy0 = _section(draw, px, py, pw, "03", "Board health", fonts)
    cx2, cyt, cwt, cht = px, cy0 + 4, pw, 74
    mxall = max(max(game.hole_history or [1]), max(game.height_history or [1]),
                max(game.bump_history or [1])) or 1
    draw.line([(cx2, cyt + cht), (cx2 + cwt, cyt + cht)], fill=PAL['ink'], width=2)
    sparkline_img(draw, game.hole_history, cx2, cyt, cwt, cht, PAL['red'], mxall)
    sparkline_img(draw, game.height_history, cx2, cyt, cwt, cht, PAL['ink'], mxall)
    sparkline_img(draw, game.bump_history, cx2, cyt, cwt, cht, PAL['ochre'], mxall)
    draw.text((cx2, cyt + cht + 6), "Holes", font=fonts['small'], fill=PAL['red'])
    draw.text((cx2 + 54, cyt + cht + 6), "Max H", font=fonts['small'], fill=PAL['ink'])
    draw.text((cx2 + 108, cyt + cht + 6), "Bumpy", font=fonts['small'], fill=PAL['ochre'])
    py += 150

    cy0 = _section(draw, px, py, pw, "04", "Pieces", fonts)
    pwe = pw // 7
    for i, name in enumerate(t.PIECE_NAMES):
        col = COLORS[t.PIECE_COLORS[name]]
        xb = px + i * pwe
        draw.rectangle([xb, cy0, xb + pwe - 10, cy0 + 8], fill=col, outline=PAL['ink'])
        draw.text((xb, cy0 + 12), f"{game.stats[name]}", font=fonts['statnum'], fill=PAL['ink'])
        draw.text((xb, cy0 + 46), name, font=fonts['small'], fill=PAL['ink2'])

    os.makedirs('screenshots', exist_ok=True)
    img.save(filename, quality=95)
    print(f"Saved {filename} ({img_w}x{img_h})")


def generate_terminal_screenshot(game, filename):
    char_w = 8
    char_h = 16
    cols = 90
    rows = 30
    img_w = cols * char_w
    img_h = rows * char_h

    img = Image.new('RGB', (img_w, img_h), (10, 10, 10))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 13)
    except Exception:
        font = ImageFont.load_default()

    def put(row, col, text, color=TEXT):
        draw.text((col * char_w, row * char_h), text, fill=color, font=font)

    put(0, 1, "TETRIS AI", CYAN)
    put(0, 11, "RUNNING", GREEN)

    bx, by = 1, 1
    for y in range(t.BOARD_HEIGHT):
        put(by + y, bx - 1, "|", DIM)
        put(by + y, bx + t.BOARD_WIDTH * 2, "|", DIM)
        for x in range(t.BOARD_WIDTH):
            if game.board.grid[y][x]:
                color = COLORS.get(game.board.color_grid[y][x], (128,128,128))
                put(by + y, bx + x * 2, "[]", color)
    put(by + t.BOARD_HEIGHT, bx - 1, "+" + "-" * (t.BOARD_WIDTH * 2) + "+", DIM)

    if not game.game_over and game.current_shape:
        color = COLORS.get(t.PIECE_COLORS[game.current_piece], (128,128,128))
        for y, row in enumerate(game.current_shape):
            for x, cell in enumerate(row):
                if cell and game.piece_y + y >= 0:
                    put(by + game.piece_y + y, bx + (game.piece_x + x) * 2, "[]", color)

    px = 24
    put(1, px, "SCORE", CYAN)
    put(2, px, f" {game.score:,}", YELLOW)
    put(4, px, "LINES", CYAN)
    put(5, px, f" {game.lines}", TEXT)
    put(7, px, "LEVEL", CYAN)
    put(8, px, f" {game.level}", (160, 64, 192))
    put(10, px, "PIECES", CYAN)
    put(11, px, f" {game.pieces_placed}", TEXT)

    gx = 34
    put(1, gx, "─" * 30, DIM)
    put(2, gx, "DECISION WEIGHTS", CYAN)

    metrics = game.ai.last_metrics
    if metrics:
        items = [
            ('lines', metrics.get('lines', 0), game.ai.weights['lines_cleared']),
            ('holes', metrics.get('holes', 0), game.ai.weights['holes']),
            ('height', metrics.get('height', 0), game.ai.weights['aggregate_height']),
            ('bumpy', metrics.get('bumpy', 0), game.ai.weights['bumpiness']),
            ('wells', metrics.get('wells', 0), game.ai.weights['wells']),
            ('row_tr', metrics.get('row_tr', 0), game.ai.weights['row_transitions']),
        ]
        for i, (name, raw, weight) in enumerate(items):
            weighted = raw * weight
            bar_len = min(int(abs(weighted) / 3), 10)
            bar = "█" * bar_len
            col = GREEN if weighted >= 0 else RED
            put(3 + i, gx, f" {name:<7}", TEXT)
            put(3 + i, gx + 8, bar, col)
            put(3 + i, gx + 20, f"{weighted:>6.1f}", col)

    put(10, gx, "─" * 30, DIM)
    put(11, gx, "BOARD HEALTH", CYAN)
    spark = "▁▂▃▄▅▆▇█"
    if game.hole_history:
        mx = max(game.hole_history) or 1
        s = ""
        for v in game.hole_history[-24:]:
            idx = int(min(v / mx, 1.0) * 7)
            s += spark[idx]
        put(12, gx, " holes  " + s, RED)
    if game.height_history:
        mx = max(game.height_history) or 1
        s = ""
        for v in game.height_history[-24:]:
            idx = int(min(v / mx, 1.0) * 7)
            s += spark[idx]
        put(13, gx, " max h  " + s, CYAN)
    if game.bump_history:
        mx = max(game.bump_history) or 1
        s = ""
        for v in game.bump_history[-24:]:
            idx = int(min(v / mx, 1.0) * 7)
            s += spark[idx]
        put(14, gx, " bumpy  " + s, YELLOW)

    put(16, gx, "─" * 30, DIM)
    put(17, gx, "LINES / 10 PIECES", CYAN)
    if game.lines_per_bucket:
        mx = max(game.lines_per_bucket) or 1
        s = ""
        for v in game.lines_per_bucket[-24:]:
            idx = int(min(v / mx, 1.0) * 7)
            s += spark[idx]
        avg = sum(game.lines_per_bucket) / len(game.lines_per_bucket)
        put(18, gx, " " + s, GREEN)
        put(19, gx, f" avg {avg:.1f} lines", DIM)

    put(21, gx, "─" * 30, DIM)
    put(22, gx, "COLUMN HEIGHTS", CYAN)
    heights = game.board.get_heights()
    for i, h in enumerate(heights):
        bar_len = min(h, 14)
        put(23 + i // 5, gx + (i % 5) * 12, f"{i}:", DIM)
        put(23 + i // 5, gx + (i % 5) * 12 + 2, "█" * bar_len, CYAN)

    controls = "+/- speed  SPC reset  p pause  r restart  q quit"
    put(28, 1, controls, DIM)

    os.makedirs('screenshots', exist_ok=True)
    img.save(filename, quality=95)
    print(f"Saved {filename} ({img_w}x{img_h})")


def _candidates_with_cells(board, piece, weights):
    """Enumerate current-piece placements, returning cells + score, sorted best-first."""
    ai = t.TetrisAI(weights=weights)
    out = []
    col = t.PIECE_COLORS[piece]
    for rot in t.get_rotations(t.PIECES[piece]):
        for x in range(-2, t.BOARD_WIDTH + 1):
            if not board.valid_position(rot, x, 0) and not board.valid_position(rot, x, -len(rot)):
                continue
            dy = 0
            while board.valid_position(rot, x, dy + 1):
                dy += 1
            if not board.valid_position(rot, x, dy):
                continue
            tb = board.copy()
            tb.place_piece(rot, x, dy, col)
            lines = tb.clear_lines()
            score, _ = ai.evaluate(tb, lines, t.BOARD_HEIGHT - dy)
            cells = [(x + cx, dy + cy) for cy, row in enumerate(rot)
                     for cx, c in enumerate(row) if c]
            out.append({'cells': cells, 'score': score})
    out.sort(key=lambda c: c['score'], reverse=True)
    return out


def generate_lab_screenshot(board, piece, next_piece, score, lines, level, pieces,
                            weights, filename):
    """Render the 'AI Lab' view: dark board window with the candidate heatmap."""
    cands = _candidates_with_cells(board, piece, weights)
    best = cands[0] if cands else None

    bw = t.BOARD_WIDTH * CELL
    bh = t.BOARD_HEIGHT * CELL
    margin = 24
    panel_x = margin + bw + 30
    panel_w = 440
    img_w = panel_x + panel_w + margin
    by = 78
    img_h = by + bh + 46 + margin

    img = Image.new('RGB', (img_w, img_h), PAL['paper'])
    draw = ImageDraw.Draw(img)
    fonts = {
        'disp': _font(IMPACT, 38), 'ai': _font(IMPACT, 38), 'disp_sec': _font(IMPACT, 30),
        'statnum': _font(IMPACT, 30), 'big': _font(IMPACT, 34), 'kick': _font(MENLO, 11),
        'lab': _font(HELV, 13), 'mono': _font(MENLO, 10), 'small': _font(MENLO, 9),
    }

    # compact masthead
    draw.text((margin, 8), "DECISION LABORATORY · SELF-LEARNING AGENT", font=fonts['kick'], fill=PAL['ink2'])
    draw.text((margin, 24), "TETRIS", font=fonts['disp'], fill=PAL['ink'])
    wt = draw.textlength("TETRIS", font=fonts['disp'])
    draw.text((margin + wt + 12, 24), "AI", font=fonts['ai'], fill=PAL['red'])
    draw.rectangle([img_w - 196, 30, img_w - 24, 54], outline=PAL['red'], width=2)
    draw.text((img_w - 186, 36), "WEIGHTS: LEARNED", font=fonts['mono'], fill=PAL['red'])

    # board window
    bx = margin
    draw.rectangle([bx - 4, by - 4, bx + bw + 4, by + bh + 4], fill=PAL['ink'])
    draw.rectangle([bx, by, bx + bw, by + bh], fill=PAL['board'])
    for cy in range(t.BOARD_HEIGHT):
        for cx in range(t.BOARD_WIDTH):
            draw.rectangle([bx+cx*CELL, by+cy*CELL, bx+cx*CELL+CELL, by+cy*CELL+CELL], outline=(42, 33, 20))
            if board.grid[cy][cx]:
                draw_cell(draw, bx+cx*CELL, by+cy*CELL, COLORS.get(board.color_grid[cy][cx], (128,)*3))

    # candidate heatmap overlay (vermilion)
    top = cands[:9]
    if top:
        mx, mn = top[0]['score'], top[-1]['score']
        rng = (mx - mn) or 1
        for c in reversed(top[1:]):
            norm = (c['score'] - mn) / rng
            alpha = int((0.14 + norm * 0.5) * 255)
            for (cx, cy) in c['cells']:
                if cy >= 0:
                    ov = Image.new('RGBA', (CELL-10, CELL-10), (214, 55, 43, alpha))
                    img.paste(ov, (bx+cx*CELL+5, by+cy*CELL+5), ov)
        if best:
            for (cx, cy) in best['cells']:
                if cy >= 0:
                    draw.rectangle([bx+cx*CELL+2, by+cy*CELL+2, bx+cx*CELL+CELL-2, by+cy*CELL+CELL-2],
                                   outline=PAL['red'], width=2)

    # live piece near top
    pcol = COLORS.get(t.PIECE_COLORS[piece], (128,)*3)
    pshape = t.PIECES[piece]
    spawn_x = t.BOARD_WIDTH // 2 - len(pshape[0]) // 2
    for cy, row in enumerate(pshape):
        for cx, c in enumerate(row):
            if c:
                draw_cell(draw, bx+(spawn_x+cx)*CELL, by+cy*CELL, pcol)

    legend_y = by + bh + 8
    draw.text((bx, legend_y), "considered", font=fonts['small'], fill=PAL['ink2'])
    for i in range(60):
        draw.rectangle([bx+74+i*2, legend_y+1, bx+74+i*2+2, legend_y+9],
                       fill=_blend(PAL['paper'], PAL['red'], i/60))
    draw.text((bx+200, legend_y), "chosen", font=fonts['small'], fill=PAL['red'])

    # ---- right column ----
    px = panel_x
    pw = panel_w
    py = by

    cy0 = _section(draw, px, py, pw, "01", "Search", fonts)
    draw.text((px + pw - 96, py - 4), "2-PLY LOOKAHEAD", font=fonts['small'], fill=PAL['ink2'])
    cols = [("placements scored", str(len(cands)), PAL['red']),
            ("best score", f"{best['score']:.1f}" if best else "—", PAL['ink']),
            ("pieces / sec", "9", PAL['ink'])]
    for i, (lbl, val, c) in enumerate(cols):
        cx = px + i * 150
        draw.text((cx, cy0), val, font=fonts['big'], fill=c)
        draw.text((cx, cy0 + 38), lbl, font=fonts['small'], fill=PAL['ink2'])
    py += 104

    cy0 = _section(draw, px, py, pw, "02", "Why this move", fonts)
    draw.text((px + pw - 104, py - 4), "WEIGHT × FEATURE", font=fonts['small'], fill=PAL['ink2'])
    if best:
        tb = board.copy()
        for (cx, cy) in best['cells']:
            if 0 <= cy < t.BOARD_HEIGHT and 0 <= cx < t.BOARD_WIDTH:
                tb.grid[cy][cx] = 1
        w = t.TetrisAI(weights=weights).weights
        feat = tb.features()
        rows = [('holes', w['holes'] * feat['holes']),
                ('height', w['aggregate_height'] * feat['agg']),
                ('bumpy', w['bumpiness'] * feat['bump']),
                ('wells', w['wells'] * feat['wells']),
                ('row tr', w['row_transitions'] * feat['row_tr']),
                ('col tr', w['col_transitions'] * feat['col_tr']),
                ('max h', w['max_height'] * feat['max_h'])]
        maxv = max(1.0, max(abs(v) for _, v in rows))
        tx = px + 62
        tw = pw - 110
        mid = tx + tw / 2
        ry = cy0
        for name, v in rows:
            draw.text((px, ry + 2), name, font=fonts['mono'], fill=PAL['ink2'])
            draw.rectangle([tx, ry, tx + tw, ry + 15], fill=_blend(PAL['paper'], PAL['ink'], 0.08), outline=PAL['ink2'])
            draw.line([(mid, ry), (mid, ry + 15)], fill=PAL['ink'])
            frac = min(abs(v) / maxv, 1.0) * (tw / 2)
            c = PAL['ink'] if v >= 0 else PAL['red']
            if v >= 0:
                draw.rectangle([mid, ry + 2, mid + frac, ry + 13], fill=c)
            else:
                draw.rectangle([mid - frac, ry + 2, mid, ry + 13], fill=c)
            draw.text((px + pw - 42, ry + 1), f"{v:+.0f}", font=fonts['mono'], fill=c)
            ry += 25
    py += 220

    # stats row
    cells = [("SCORE", f"{score:,}", PAL['red']), ("LINES", str(lines), PAL['ink']),
             ("LEVEL", str(level), PAL['ink']), ("PIECES", str(pieces), PAL['ink'])]
    cw = pw // 4
    draw.rectangle([px, py, px + cw * 4, py + 50], fill=PAL['paper'], outline=PAL['ink'], width=3)
    for i, (lbl, val, c) in enumerate(cells):
        cx = px + i * cw
        if i: draw.line([(cx, py), (cx, py + 50)], fill=PAL['ink'], width=2)
        draw.text((cx + 6, py + 5), lbl, font=fonts['small'], fill=PAL['ink2'])
        draw.text((cx + 6, py + 16), val, font=fonts['statnum'], fill=c)

    os.makedirs('screenshots', exist_ok=True)
    img.save(filename, quality=95)
    print(f"Saved {filename} ({img_w}x{img_h})")


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    weights = t.load_weights()

    game = t.TetrisGame()
    for _ in range(8000):
        if game.game_over:
            break
        game.ai_step()

    generate_game_screenshot(game, 'screenshots/web_ui.png')
    generate_terminal_screenshot(game, 'screenshots/terminal_ui.png')

    # For the Lab view: build a fresh mid-game board, then freeze on a new piece
    # so the candidate-placement overlay is meaningful.
    lab = t.TetrisGame()
    placed = 0
    while placed < 22 and not lab.game_over:
        prev = lab.pieces_placed
        lab.ai_step()
        placed = lab.pieces_placed
    generate_lab_screenshot(lab.board, lab.current_piece, lab.next_piece,
                            lab.score, lab.lines, lab.level, lab.pieces_placed,
                            weights, 'screenshots/lab_ui.png')
    print("Done!")
