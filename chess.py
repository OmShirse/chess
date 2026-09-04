"""
Lightweight 2D Chess — Tkinter, no external dependencies
Controls:
  - Click a piece to select it (valid moves highlighted)
  - Click a destination to move
  - Press R to restart
  - Press Escape to quit
Features: full rules, castling, en passant, pawn promotion (auto-queen),
          check / checkmate / stalemate detection
"""

import tkinter as tk
from tkinter import font as tkfont
import copy, sys

# ── Board geometry ────────────────────────────────────────────────────────────
SQ   = 80          # square size in pixels
GAP  = 36          # info bar height
WIN  = SQ * 8

# ── Colours ───────────────────────────────────────────────────────────────────
LIGHT    = "#F0D9B5"
DARK     = "#B58863"
SEL_COL  = "#F6F669"
MOVE_COL = "#CDD16E"
CAP_COL  = "#E44032"
CHK_COL  = "#FF2222"
DOT_COL  = "#444444"

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
        self.turn   = 'w'          # 'w' or 'b'
        self.ep     = None         # en-passant target square (r,c) or None
        self.castle = {'K':True,'Q':True,'k':True,'q':True}
        self.status = "White's turn"
        self.over   = False

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def color(p): return 'w' if p and p.isupper() else ('b' if p else None)

    def enemy(self, p, turn): return p and Chess.color(p) != turn

    def friendly(self, p, turn): return p and Chess.color(p) == turn

    def find_king(self, turn, board):
        k = 'K' if turn == 'w' else 'k'
        for r in range(8):
            for c in range(8):
                if board[r][c] == k:
                    return r, c
        return None

    # ── Raw move generation (no legality filter) ──────────────────────────────
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
            d = -1 if turn == 'w' else 1
            sr = 6 if turn == 'w' else 1
            # push
            if 0 <= r+d < 8 and board[r+d][c] is None:
                moves.append((r+d, c))
                if r == sr and board[r+2*d][c] is None:
                    moves.append((r+2*d, c))
            # captures
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
            # castling
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
        """Is square (r,c) attacked by the opponent of 'defender'?"""
        atk = 'b' if defender == 'w' else 'w'
        for ar in range(8):
            for ac in range(8):
                p = board[ar][ac]
                if not p or Chess.color(p) != atk:
                    continue
                P = p.upper()
                if P == 'K':
                    if max(abs(ar-r), abs(ac-c)) == 1:
                        return True
                    continue
                if (r, c) in self.raw_moves(ar, ac, board, atk, ep):
                    return True
        return False

    def in_check(self, turn, board, ep=None):
        kr = self.find_king(turn, board)
        return kr and self.attacked(kr[0], kr[1], turn, board, ep)

    def apply(self, board, fr, fc, tr, tc, turn, ep, castle):
        """Return new board after move; doesn't mutate inputs."""
        b = copy.deepcopy(board)
        p = b[fr][fc]
        P = p.upper() if p else None
        b[tr][tc] = p
        b[fr][fc] = None

        # en passant capture
        if P == 'P' and (tr, tc) == ep:
            d = 1 if turn == 'w' else -1
            b[tr+d][tc] = None

        # castling rook
        if P == 'K' and abs(tc - fc) == 2:
            br = 7 if turn == 'w' else 0
            if tc == 6:
                b[br][5] = b[br][7]; b[br][7] = None
            else:
                b[br][3] = b[br][0]; b[br][0] = None

        # promotion → queen
        if P == 'P' and (tr == 0 or tr == 7):
            b[tr][tc] = 'Q' if turn == 'w' else 'q'

        return b

    def legal_moves(self, r, c):
        moves = self.raw_moves(r, c, self.board, self.turn, self.ep)
        result = []
        for (tr, tc) in moves:
            nb = self.apply(self.board, r, c, tr, tc, self.turn, self.ep, self.castle)
            if not self.in_check(self.turn, nb, self.ep):
                result.append((tr, tc))
        return result

    def push(self, fr, fc, tr, tc):
        p  = self.board[fr][fc]
        P  = p.upper()

        new_ep = None
        if P == 'P' and abs(tr - fr) == 2:
            new_ep = ((fr + tr) // 2, fc)

        # update castling rights
        if p == 'K': self.castle['K'] = self.castle['Q'] = False
        if p == 'k': self.castle['k'] = self.castle['q'] = False
        if p == 'R':
            if fc == 0: self.castle['Q'] = False
            if fc == 7: self.castle['K'] = False
        if p == 'r':
            if fc == 0: self.castle['q'] = False
            if fc == 7: self.castle['k'] = False

        self.board = self.apply(self.board, fr, fc, tr, tc, self.turn, self.ep, self.castle)
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
                self.status = f"Checkmate! {winner} wins! (R = restart)"
            else:
                self.status = "Stalemate — Draw! (R = restart)"
            self.over = True
        elif chk:
            self.status = f"{side} is in Check!"
        else:
            self.status = f"{side}'s turn"


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

        # Canvas
        self.cv = tk.Canvas(self, width=WIN, height=WIN+GAP, bg="#1e1e1e",
                            highlightthickness=0)
        self.cv.pack()

        # Fonts — try to pick one that renders chess symbols
        self.piece_font  = self._best_font(int(SQ * 0.72))
        self.coord_font  = tkfont.Font(family="Arial", size=9)
        self.status_font = tkfont.Font(family="Arial", size=13, weight="bold")

        self.cv.bind("<Button-1>", self.on_click)
        self.bind("<Key>", self.on_key)

        self.draw()

    # ── Font selection ─────────────────────────────────────────────────────────
    def _best_font(self, size):
        candidates = ["Segoe UI Symbol","DejaVu Sans","FreeSerif",
                      "Symbola","Noto Sans Symbols2","Arial Unicode MS","TkDefaultFont"]
        for name in candidates:
            try:
                f = tkfont.Font(family=name, size=size)
                if f.measure("♔") > 4:      # non-zero width → supports chess glyphs
                    return f
            except Exception:
                pass
        return tkfont.Font(size=size)

    # ── Drawing ────────────────────────────────────────────────────────────────
    def draw(self):
        cv = self.cv
        cv.delete("all")
        g  = self.game
        chk_sq = None
        if g.in_check(g.turn, g.board):
            chk_sq = g.find_king(g.turn, g.board)

        for row in range(8):
            for col in range(8):
                x1, y1 = col*SQ, row*SQ
                x2, y2 = x1+SQ, y1+SQ
                base = LIGHT if (row+col)%2 == 0 else DARK

                # background
                cv.create_rectangle(x1, y1, x2, y2, fill=base, outline="")

                # overlays
                if chk_sq and (row, col) == chk_sq:
                    cv.create_rectangle(x1, y1, x2, y2, fill=CHK_COL, outline="")
                elif self.selected and (row, col) == self.selected:
                    cv.create_rectangle(x1, y1, x2, y2, fill=SEL_COL, outline="")
                elif (row, col) in self.moves:
                    p = g.board[row][col]
                    if p:
                        # Capture: solid red tint over the square
                        cv.create_rectangle(x1, y1, x2, y2, fill=CAP_COL, outline="")
                    else:
                        # Empty move: small dark dot
                        r = SQ // 5
                        cx, cy = x1 + SQ//2, y1 + SQ//2
                        cv.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#444444", outline="")

        # Board coordinates
        for i in range(8):
            fg = DARK if i%2==0 else LIGHT
            cv.create_text(4, i*SQ+10, text=str(8-i), fill=fg,
                           font=self.coord_font, anchor="nw")
            fg = DARK if i%2==1 else LIGHT
            cv.create_text(i*SQ+SQ-6, WIN-14, text=FILES[i], fill=fg,
                           font=self.coord_font, anchor="se")

        # Pieces
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
                    cv.create_text(cx+dx, cy+dy, text=sym, fill=out,
                                   font=self.piece_font)
                cv.create_text(cx, cy, text=sym, fill=fill,
                               font=self.piece_font)

        # Info bar
        cv.create_rectangle(0, WIN, WIN, WIN+GAP, fill="#111111", outline="")
        cv.create_line(0, WIN, WIN, WIN, fill="#444", width=1)
        txt_col = "#ff6b6b" if "Check" in g.status or "Checkmate" in g.status else "#e0e0e0"
        cv.create_text(WIN//2, WIN + GAP//2, text=g.status,
                       fill=txt_col, font=self.status_font)

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
            self.selected = None
            self.moves    = []
            self.draw()
        elif event.keysym == 'Escape':
            self.destroy()
            sys.exit()


if __name__ == "__main__":
    app = App()
    app.mainloop()
