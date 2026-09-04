"""
Lightweight 2D Chess — Tkinter, no external dependencies

Controls:
  Click piece → click destination to move
  R  = restart    Escape = quit

Features:
  Full chess rules (castling, en passant, pawn→queen promotion,
  check / checkmate / stalemate)

Scoring / Timed mode:
  Each captured piece awards points to the capturer:
    Pawn=1  Knight=3  Bishop=3  Rook=5  Queen=9
  A countdown timer runs (default 10 minutes).
  When time is up, the player with more points wins.
  If equal → Draw.
"""

import tkinter as tk
from tkinter import font as tkfont
import copy, sys, time

# ── Config ────────────────────────────────────────────────────────────────────
GAME_MINUTES = 10          # change this to set a different time limit

# ── Board geometry ────────────────────────────────────────────────────────────
SQ      = 80               # square size in pixels
WIN     = SQ * 8           # board area (640)
SIDE_W  = 200              # right panel width
BAR_H   = 44               # bottom status bar height
TOT_W   = WIN + SIDE_W
TOT_H   = WIN + BAR_H

# ── Colours ───────────────────────────────────────────────────────────────────
LIGHT   = "#F0D9B5"
DARK    = "#B58863"
SEL_COL = "#F6F669"
CAP_COL = "#E44032"
CHK_COL = "#FF4444"
BG      = "#1e1e1e"
PANEL   = "#161616"
ACCENT  = "#e0a458"

# ── Piece point values ────────────────────────────────────────────────────────
POINTS = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

# ── Unicode pieces ────────────────────────────────────────────────────────────
SYMBOLS = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
}

FILES = "abcdefgh"

# ─────────────────────────────────────────────────────────────────────────────
#  Game logic
# ─────────────────────────────────────────────────────────────────────────────
class Chess:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [
            list("rnbqkbnr"),
            list("pppppppp"),
            [None]*8, [None]*8, [None]*8, [None]*8,
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]
        self.turn    = 'w'
        self.ep      = None
        self.castle  = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.status  = "White's turn"
        self.over    = False
        # scoring
        self.score   = {'w': 0, 'b': 0}        # cumulative points
        self.captured= {'w': [], 'b': []}       # pieces captured BY each side

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def color(p): return 'w' if p and p.isupper() else ('b' if p else None)

    def enemy(self, p, turn):    return p and Chess.color(p) != turn
    def friendly(self, p, turn): return p and Chess.color(p) == turn

    def find_king(self, turn, board):
        k = 'K' if turn == 'w' else 'k'
        for r in range(8):
            for c in range(8):
                if board[r][c] == k:
                    return r, c
        return None

    # ── Raw move generation ───────────────────────────────────────────────────
    def raw_moves(self, r, c, board, turn, ep):
        p = board[r][c]
        if not p or Chess.color(p) != turn:
            return []
        moves = []
        P = p.upper()

        def slide(dr, dc):
            nr, nc = r+dr, c+dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                t = board[nr][nc]
                if t is None:
                    moves.append((nr, nc))
                elif self.enemy(t, turn):
                    moves.append((nr, nc)); break
                else:
                    break
                nr += dr; nc += dc

        def step(dr, dc):
            nr, nc = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                t = board[nr][nc]
                if t is None or self.enemy(t, turn):
                    moves.append((nr, nc))

        if P == 'P':
            d  = -1 if turn == 'w' else 1
            sr =  6 if turn == 'w' else 1
            if 0 <= r+d < 8 and board[r+d][c] is None:
                moves.append((r+d, c))
                if r == sr and board[r+2*d][c] is None:
                    moves.append((r+2*d, c))
            for dc in (-1, 1):
                nr, nc = r+d, c+dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    t = board[nr][nc]
                    if self.enemy(t, turn) or (nr, nc) == ep:
                        moves.append((nr, nc))

        elif P == 'N':
            for dr, dc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
                step(dr, dc)
        elif P == 'B':
            for dr, dc in ((-1,-1),(-1,1),(1,-1),(1,1)): slide(dr, dc)
        elif P == 'R':
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)): slide(dr, dc)
        elif P == 'Q':
            for dr, dc in ((-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)):
                slide(dr, dc)
        elif P == 'K':
            for dr, dc in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
                step(dr, dc)
            br = 7 if turn == 'w' else 0
            if r == br and c == 4 and not self.attacked(br, 4, turn, board, ep):
                ks = 'K' if turn == 'w' else 'k'
                qs = 'Q' if turn == 'w' else 'q'
                if self.castle.get(ks) and board[br][5] is None and board[br][6] is None \
                        and not self.attacked(br, 5, turn, board, ep) \
                        and not self.attacked(br, 6, turn, board, ep):
                    moves.append((br, 6))
                if self.castle.get(qs) and board[br][3] is None and board[br][2] is None \
                        and board[br][1] is None \
                        and not self.attacked(br, 3, turn, board, ep) \
                        and not self.attacked(br, 2, turn, board, ep):
                    moves.append((br, 2))
        return moves

    def attacked(self, r, c, defender, board, ep):
        atk = 'b' if defender == 'w' else 'w'
        for ar in range(8):
            for ac in range(8):
                p = board[ar][ac]
                if not p or Chess.color(p) != atk:
                    continue
                if p.upper() == 'K':
                    if max(abs(ar-r), abs(ac-c)) == 1:
                        return True
                    continue
                if (r, c) in self.raw_moves(ar, ac, board, atk, ep):
                    return True
        return False

    def in_check(self, turn, board, ep=None):
        kr = self.find_king(turn, board)
        return kr and self.attacked(kr[0], kr[1], turn, board, ep)

    def apply(self, board, fr, fc, tr, tc, turn, ep):
        b = copy.deepcopy(board)
        p = b[fr][fc]
        P = p.upper() if p else None
        b[tr][tc] = p
        b[fr][fc] = None
        if P == 'P' and (tr, tc) == ep:
            d = 1 if turn == 'w' else -1
            b[tr+d][tc] = None
        if P == 'K' and abs(tc - fc) == 2:
            br = 7 if turn == 'w' else 0
            if tc == 6:
                b[br][5] = b[br][7]; b[br][7] = None
            else:
                b[br][3] = b[br][0]; b[br][0] = None
        if P == 'P' and (tr == 0 or tr == 7):
            b[tr][tc] = 'Q' if turn == 'w' else 'q'
        return b

    def legal_moves(self, r, c):
        raw = self.raw_moves(r, c, self.board, self.turn, self.ep)
        result = []
        for (tr, tc) in raw:
            nb = self.apply(self.board, r, c, tr, tc, self.turn, self.ep)
            if not self.in_check(self.turn, nb, self.ep):
                result.append((tr, tc))
        return result

    def push(self, fr, fc, tr, tc):
        """Execute a validated move and update scores."""
        p   = self.board[fr][fc]
        P   = p.upper()
        victim = self.board[tr][tc]

        # en passant sets a virtual victim
        if P == 'P' and (tr, tc) == self.ep:
            d = 1 if self.turn == 'w' else -1
            victim = self.board[tr+d][tc]

        # award points for capture
        if victim:
            pts = POINTS.get(victim.upper(), 0)
            self.score[self.turn] += pts
            self.captured[self.turn].append(victim.upper())

        new_ep = None
        if P == 'P' and abs(tr - fr) == 2:
            new_ep = ((fr + tr) // 2, fc)

        if p == 'K': self.castle['K'] = self.castle['Q'] = False
        if p == 'k': self.castle['k'] = self.castle['q'] = False
        if p == 'R':
            if fc == 0: self.castle['Q'] = False
            if fc == 7: self.castle['K'] = False
        if p == 'r':
            if fc == 0: self.castle['q'] = False
            if fc == 7: self.castle['k'] = False

        self.board = self.apply(self.board, fr, fc, tr, tc, self.turn, self.ep)
        self.ep    = new_ep
        self.turn  = 'b' if self.turn == 'w' else 'w'
        self._update_status()

    def has_any_legal(self):
        for r in range(8):
            for c in range(8):
                if self.friendly(self.board[r][c], self.turn):
                    if self.legal_moves(r, c):
                        return True
        return False

    def _update_status(self):
        chk  = self.in_check(self.turn, self.board)
        side = "White" if self.turn == 'w' else "Black"
        if not self.has_any_legal():
            if chk:
                winner = "Black" if self.turn == 'w' else "White"
                self.status = f"Checkmate! {winner} wins!  (R=restart)"
            else:
                self.status = "Stalemate — Draw!  (R=restart)"
            self.over = True
        elif chk:
            self.status = f"{side} is in Check!"
        else:
            self.status = f"{side}'s turn"

    def declare_time_winner(self):
        ws, bs = self.score['w'], self.score['b']
        if ws > bs:
            self.status = f"Time's up! White wins on points ({ws} vs {bs})  (R=restart)"
        elif bs > ws:
            self.status = f"Time's up! Black wins on points ({bs} vs {ws})  (R=restart)"
        else:
            self.status = f"Time's up! Draw — equal points ({ws})  (R=restart)"
        self.over = True


# ─────────────────────────────────────────────────────────────────────────────
#  Tkinter GUI
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chess")
        self.resizable(False, False)
        self.game = Chess()
        self.selected = None
        self.moves    = []

        # Timer state
        self.total_secs  = GAME_MINUTES * 60
        self.remain_secs = self.total_secs
        self.start_time  = time.time()

        # Canvas covers board + right panel + bottom bar
        self.cv = tk.Canvas(self, width=TOT_W, height=TOT_H,
                            bg=BG, highlightthickness=0)
        self.cv.pack()

        self.piece_font  = self._best_font(int(SQ * 0.72))
        self.coord_font  = tkfont.Font(family="Arial", size=9)
        self.status_font = tkfont.Font(family="Arial", size=12, weight="bold")
        self.info_font   = tkfont.Font(family="Arial", size=11)
        self.big_font    = tkfont.Font(family="Arial", size=18, weight="bold")
        self.small_font  = tkfont.Font(family="Arial", size=10)

        self.cv.bind("<Button-1>", self.on_click)
        self.bind("<Key>", self.on_key)

        self._tick()
        self.draw()

    # ── Font selection ─────────────────────────────────────────────────────────
    def _best_font(self, size):
        for name in ("Segoe UI Symbol","DejaVu Sans","FreeSerif",
                     "Symbola","Noto Sans Symbols2","Arial Unicode MS","TkDefaultFont"):
            try:
                f = tkfont.Font(family=name, size=size)
                if f.measure("♔") > 4:
                    return f
            except Exception:
                pass
        return tkfont.Font(size=size)

    # ── Timer tick ─────────────────────────────────────────────────────────────
    def _tick(self):
        if not self.game.over:
            elapsed = time.time() - self.start_time
            self.remain_secs = max(0, self.total_secs - int(elapsed))
            if self.remain_secs == 0:
                self.game.declare_time_winner()
            self.draw()
        self.after(1000, self._tick)

    def _reset_timer(self):
        self.remain_secs = self.total_secs
        self.start_time  = time.time()

    # ── Drawing ────────────────────────────────────────────────────────────────
    def draw(self):
        cv = self.cv
        cv.delete("all")
        g  = self.game

        chk_sq = None
        if g.in_check(g.turn, g.board):
            chk_sq = g.find_king(g.turn, g.board)

        # ── Board squares ──────────────────────────────────────────────────────
        for row in range(8):
            for col in range(8):
                x1, y1 = col*SQ, row*SQ
                x2, y2 = x1+SQ, y1+SQ
                base = LIGHT if (row+col)%2 == 0 else DARK
                cv.create_rectangle(x1, y1, x2, y2, fill=base, outline="")

                if chk_sq and (row, col) == chk_sq:
                    cv.create_rectangle(x1, y1, x2, y2, fill=CHK_COL, outline="")
                elif self.selected and (row, col) == self.selected:
                    cv.create_rectangle(x1, y1, x2, y2, fill=SEL_COL, outline="")
                elif (row, col) in self.moves:
                    if g.board[row][col]:
                        cv.create_rectangle(x1, y1, x2, y2, fill=CAP_COL, outline="")
                    else:
                        r  = SQ // 5
                        cx = x1 + SQ//2; cy = y1 + SQ//2
                        cv.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#444444", outline="")

        # ── Coordinates ────────────────────────────────────────────────────────
        for i in range(8):
            fg = DARK if i%2==0 else LIGHT
            cv.create_text(3, i*SQ+10, text=str(8-i), fill=fg,
                           font=self.coord_font, anchor="nw")
            fg = DARK if i%2==1 else LIGHT
            cv.create_text(i*SQ+SQ-5, WIN-14, text=FILES[i], fill=fg,
                           font=self.coord_font, anchor="se")

        # ── Pieces ─────────────────────────────────────────────────────────────
        for row in range(8):
            for col in range(8):
                p = g.board[row][col]
                if not p:
                    continue
                sym  = SYMBOLS[p]
                cx   = col*SQ + SQ//2
                cy   = row*SQ + SQ//2
                fill = "white" if p.isupper() else "#1a1a1a"
                out  = "#1a1a1a" if p.isupper() else "#d0d0d0"
                for dx, dy in ((-1,-1),(1,-1),(-1,1),(1,1),(0,-1),(0,1),(-1,0),(1,0)):
                    cv.create_text(cx+dx, cy+dy, text=sym, fill=out, font=self.piece_font)
                cv.create_text(cx, cy, text=sym, fill=fill, font=self.piece_font)

        # ── Right panel ────────────────────────────────────────────────────────
        px = WIN
        cv.create_rectangle(px, 0, TOT_W, WIN, fill=PANEL, outline="")
        cv.create_line(px, 0, px, WIN, fill="#333", width=2)

        # Timer
        mins, secs = divmod(self.remain_secs, 60)
        timer_str  = f"{mins:02d}:{secs:02d}"
        warn = self.remain_secs <= 60
        tcol = "#ff4444" if warn else ACCENT
        cv.create_text(px + SIDE_W//2, 28, text="⏱ TIME", fill="#888",
                       font=self.small_font)
        cv.create_text(px + SIDE_W//2, 58, text=timer_str, fill=tcol,
                       font=self.big_font)

        # Divider
        cv.create_line(px+10, 78, TOT_W-10, 78, fill="#333", width=1)

        # Score block builder
        def draw_score_block(top_y, label, side, bg_col):
            pts  = g.score[side]
            caps = g.captured[side]
            cv.create_rectangle(px+8, top_y, TOT_W-8, top_y+90,
                                fill=bg_col, outline="#333", width=1)
            cv.create_text(px + SIDE_W//2, top_y+14, text=label, fill="#aaa",
                           font=self.small_font)
            cv.create_text(px + SIDE_W//2, top_y+38, text=str(pts),
                           fill=ACCENT, font=self.big_font)
            cv.create_text(px + SIDE_W//2, top_y+56, text="pts", fill="#666",
                           font=self.small_font)
            # captured piece icons (last 8 max)
            shown = caps[-8:] if len(caps) > 8 else caps
            icon_y = top_y + 76
            total_w = len(shown) * 20
            start_x = px + (SIDE_W - total_w)//2 + 10
            for i, pc in enumerate(shown):
                sym = SYMBOLS[pc.upper()] if side == 'w' else SYMBOLS[pc.lower()]
                cv.create_text(start_x + i*20, icon_y, text=sym,
                               fill="#ccc", font=self.small_font)

        draw_score_block(86,  "WHITE captured", 'w', "#1c1c1c")
        draw_score_block(184, "BLACK captured", 'b', "#1c1c1c")

        # Divider
        cv.create_line(px+10, 282, TOT_W-10, 282, fill="#333", width=1)

        # Point values legend
        cv.create_text(px + SIDE_W//2, 294, text="PIECE VALUES", fill="#555",
                       font=self.small_font)
        legend = [("♙ Pawn","1"), ("♘ Knight","3"), ("♗ Bishop","3"),
                  ("♖ Rook","5"), ("♕ Queen","9")]
        for i, (nm, val) in enumerate(legend):
            ly = 312 + i * 22
            cv.create_text(px+16, ly, text=nm, fill="#777", font=self.small_font, anchor="w")
            cv.create_text(TOT_W-12, ly, text=val+" pt", fill=ACCENT,
                           font=self.small_font, anchor="e")

        # Controls hint
        cv.create_line(px+10, 426, TOT_W-10, 426, fill="#333", width=1)
        cv.create_text(px + SIDE_W//2, 440, text="R = Restart", fill="#444",
                       font=self.small_font)
        cv.create_text(px + SIDE_W//2, 458, text="Esc = Quit", fill="#444",
                       font=self.small_font)

        # ── Bottom status bar ──────────────────────────────────────────────────
        cv.create_rectangle(0, WIN, TOT_W, TOT_H, fill="#111111", outline="")
        cv.create_line(0, WIN, TOT_W, WIN, fill="#333", width=1)
        is_bad = any(w in g.status for w in ("Check","wins","Draw","Time"))
        col = "#ff6b6b" if is_bad else "#e0e0e0"
        cv.create_text(WIN//2, WIN + BAR_H//2, text=g.status,
                       fill=col, font=self.status_font)

    # ── Events ─────────────────────────────────────────────────────────────────
    def on_click(self, event):
        g = self.game
        if g.over:
            return
        col = event.x // SQ
        row = event.y // SQ
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        p = g.board[row][col]

        if self.selected:
            if (row, col) in self.moves:
                g.push(self.selected[0], self.selected[1], row, col)
                self.selected = None
                self.moves    = []
            elif g.friendly(p, g.turn):
                self.selected = (row, col)
                self.moves    = g.legal_moves(row, col)
            else:
                self.selected = None
                self.moves    = []
        else:
            if g.friendly(p, g.turn):
                self.selected = (row, col)
                self.moves    = g.legal_moves(row, col)
        self.draw()

    def on_key(self, event):
        if event.keysym.lower() == 'r':
            self.game.reset()
            self._reset_timer()
            self.selected = None
            self.moves    = []
            self.draw()
        elif event.keysym == 'Escape':
            self.destroy()
            sys.exit()


if __name__ == "__main__":
    app = App()
    app.mainloop()
