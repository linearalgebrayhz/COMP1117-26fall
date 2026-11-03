"""Draw the string-operation diagrams for Tutorial 7 and build T7_illustrated.ipynb.

Run from anywhere:  python3 make_diagrams.py
Writes the PNGs next to this script, then copies ../T7.ipynb to
../T7_illustrated.ipynb with each picture embedded (as a cell attachment) in the
explanation cell that follows the matching demo. T7.ipynb itself is not touched.
"""

import base64
import copy
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = Path(__file__).resolve().parent
NB_IN = HERE.parent / "T7.ipynb"
NB_OUT = HERE.parent / "T7_illustrated.ipynb"

S = 0.42  # inches per diagram unit (one character cell is 1 x 1)
DPI = 150
MONO = "DejaVu Sans Mono"
SANS = "DejaVu Sans"

INK = "#1f2937"
MUTED = "#6b7280"
CODE = "#5b3cc4"
ARROW = "#4b5563"

# style name -> (fill, edge, text colour)
STY = {
    "str": ("#e3edff", "#3b6fd8", INK),
    "ws": ("#f1f2f4", "#a3a9b3", "#7b8290"),
    "hl": ("#ffe9a8", "#d08a00", INK),
    "bad": ("#ffe1e1", "#d63b3b", "#b42318"),
    "good": ("#dcf5e3", "#239a4b", INK),
    "ghost": ("#ffffff", "#c9cdd4", "#a3a9b3"),
    "var": ("#efe7ff", "#7a4fd6", "#3f2a8c"),
    "num": ("#fff4e5", "#c77700", INK),
}
SHOW = {" ": "␣", "\t": "⇥", "\n": "↵"}  # ␣ ⇥ ↵


def mono_w(s, fs):
    return len(s) * 0.602 * fs / 72 / S


def sans_w(s, fs):
    return len(s) * 0.56 * fs / 72 / S


class Diagram:
    def __init__(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.axis("off")
        self.box = [1e9, -1e9, 1e9, -1e9]

    def grow(self, x0, y0, x1, y1):
        b = self.box
        b[0], b[1] = min(b[0], x0, x1), max(b[1], x0, x1)
        b[2], b[3] = min(b[2], y0, y1), max(b[3], y0, y1)

    # ---- primitives -------------------------------------------------
    def text(self, x, y, s, fs=11, color=INK, ha="left", va="center",
             mono=False, weight="normal", style="normal"):
        self.ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va=va,
                     family=MONO if mono else SANS, weight=weight, fontstyle=style)
        lines = s.split("\n")
        w = max((mono_w if mono else sans_w)(ln, fs) for ln in lines)
        h = len(lines) * fs * 1.25 / 72 / S
        x0 = {"left": x, "center": x - w / 2, "right": x - w}[ha]
        y0 = {"center": y - h / 2, "top": y - h, "bottom": y, "baseline": y}[va]
        self.grow(x0, y0, x0 + w, y0 + h)
        return x0 + w

    def note(self, x, y, s, fs=10, color=MUTED, ha="left", va="center"):
        return self.text(x, y, s, fs=fs, color=color, ha=ha, va=va, style="italic")

    def code(self, x, y, s, fs=12, color=CODE, ha="left", va="center", weight="bold"):
        return self.text(x, y, s, fs=fs, color=color, ha=ha, va=va, mono=True, weight=weight)

    def box_(self, x, y, w, h, style, ls="-", lw=1.5, r=0.14):
        fc, ec, _ = STY[style]
        self.ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
            fc=fc, ec=ec, lw=lw, ls=ls))
        self.grow(x, y, x + w, y + h)

    def cells(self, x, y, s, style="str", styles=None, top=None, bottom=None,
              fs=15, top_color=MUTED, bottom_color=MUTED, ls="-"):
        """One box per character. Whitespace is drawn as a visible symbol."""
        styles = styles or {}
        for i, ch in enumerate(s):
            st = styles.get(i, "ws" if ch in SHOW and style == "str" else style)
            self.box_(x + i + 0.05, y + 0.05, 0.9, 0.9, st, ls=ls)
            self.ax.text(x + i + 0.5, y + 0.5, SHOW.get(ch, ch), ha="center",
                         va="center", family=MONO, fontsize=fs, color=STY[st][2])
            if top is not None:
                self.ax.text(x + i + 0.5, y + 1.3, str(top[i]), ha="center",
                             va="center", family=MONO, fontsize=9.5, color=top_color)
            if bottom is not None:
                self.ax.text(x + i + 0.5, y - 0.3, str(bottom[i]), ha="center",
                             va="center", family=MONO, fontsize=9.5, color=bottom_color)
        self.grow(x, y - (0.6 if bottom is not None else 0),
                  x + len(s), y + 1 + (0.6 if top is not None else 0))
        return x + len(s)

    def chip(self, x, y, s, style="str", fs=13, ls="-"):
        w = mono_w(s, fs) + 0.6
        self.box_(x, y + 0.05, w, 0.9, style, ls=ls, r=0.2)
        self.ax.text(x + w / 2, y + 0.5, s, ha="center", va="center",
                     family=MONO, fontsize=fs, color=STY[style][2])
        return x + w

    def pylist(self, x, y, items, styles=None, fs=13):
        """Draw a Python list as it would print: ['a', 'b']."""
        styles = styles or {}
        x = self.text(x, y + 0.5, "[", fs=fs + 3, mono=True, color=MUTED) + 0.1
        for i, item in enumerate(items):
            x = self.chip(x, y, repr(item), styles.get(i, "str"), fs=fs)
            if i < len(items) - 1:
                x = self.text(x + 0.05, y + 0.35, ",", fs=fs, mono=True, color=MUTED) + 0.2
        return self.text(x + 0.1, y + 0.5, "]", fs=fs + 3, mono=True, color=MUTED)

    def var(self, x, y, name, dashed=False):
        w = mono_w(name, 12) + 0.7
        self.box_(x, y + 0.1, w, 0.8, "var" if not dashed else "ghost",
                  ls="--" if dashed else "-", r=0.25)
        self.ax.text(x + w / 2, y + 0.5, name, ha="center", va="center", family=MONO,
                     fontsize=12, color=STY["var"][2] if not dashed else MUTED,
                     weight="bold" if not dashed else "normal")
        return x + w

    def arrow(self, p, q, rad=0.0, color=ARROW, lw=1.6, ls="-", label=None,
              label_xy=None, label_fs=11, label_ha="center"):
        self.ax.add_patch(FancyArrowPatch(
            p, q, arrowstyle="-|>", mutation_scale=14, color=color, lw=lw, ls=ls,
            connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
        self.grow(*p, *q)
        if label:
            lx, ly = label_xy or ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.35)
            self.code(lx, ly, label, fs=label_fs, ha=label_ha)

    def rarrow(self, x, y, length=1.2, label=None):
        """Short right-pointing arrow centred on a row at height y..y+1."""
        self.arrow((x + 0.15, y + 0.5), (x + length, y + 0.5), label=label,
                   label_xy=(x + length / 2 + 0.1, y + 1.25) if label else None)
        return x + length + 0.2

    def tick(self, x, y, ok, fs=15):
        self.text(x, y, "✓" if ok else "✗", fs=fs, weight="bold",
                  color=STY["good"][1] if ok else STY["bad"][1], ha="center")

    def save(self, name, pad=0.45):
        x0, x1, y0, y1 = self.box
        x0, x1, y0, y1 = x0 - pad, x1 + pad, y0 - pad, y1 + pad
        self.ax.set_xlim(x0, x1)
        self.ax.set_ylim(y0, y1)
        self.fig.set_size_inches((x1 - x0) * S, (y1 - y0) * S)
        path = HERE / name
        self.fig.savefig(path, dpi=DPI, facecolor="white")
        plt.close(self.fig)
        return path


def diff_styles(before, after):
    return {i: "hl" for i, (a, b) in enumerate(zip(before, after)) if a != b}


def ws_styles(s, style):
    return {i: style for i, ch in enumerate(s) if ch in SHOW}


# ====================================================================
# Concept diagrams
# ====================================================================

def fig_immutable():
    d = Diagram()
    for col, (title, saved) in enumerate([
            ("message.lower()", False),
            ("quiet = message.lower()", True)]):
        x0 = col * 15.5
        d.code(x0, 1.2, title, fs=13, color=INK)
        d.note(x0, 0.45, "result thrown away" if not saved else "result saved in a new variable",
               color=STY["bad"][1] if not saved else STY["good"][1])
        # row 1: message -> 'Hello!'
        xe = d.var(x0, -1.3, "message")
        d.arrow((xe + 0.1, -0.8), (x0 + 3.9, -0.8))
        d.cells(x0 + 4, -1.3, "Hello!")
        # row 2: new string, named or not
        if saved:
            xe = d.var(x0, -3.6, "quiet")
            d.arrow((xe + 0.1, -3.1), (x0 + 3.9, -3.1))
            d.cells(x0 + 4, -3.6, "hello!", style="good")
        else:
            d.var(x0, -3.6, "(no name)", dashed=True)
            d.cells(x0 + 4, -3.6, "hello!", style="ghost", ls="--")
        d.arrow((x0 + 10.2, -0.8), (x0 + 10.2, -3.1), rad=-0.6, label=".lower()",
                label_xy=(x0 + 11.0, -1.95), label_ha="left")
        d.note(x0 + 11.0, -2.6, "makes a NEW string")
        # outcome
        d.code(x0, -5.1, "print(message)", fs=11, color=INK, weight="normal")
        d.chip(x0 + 4.0, -5.6, "Hello!", "str", fs=11)
        if saved:
            d.code(x0, -6.3, "print(quiet)", fs=11, color=INK, weight="normal")
            d.chip(x0 + 4.0, -6.8, "hello!", "good", fs=11)
        else:
            d.note(x0, -6.3, "the lowercase copy is lost: nothing refers to it")
    d.ax.plot([14.6, 14.6], [-7, 1.6], color="#e5e7eb", lw=1.2)
    return d.save("01_methods_return_new_strings.png")


def fig_split_join():
    d = Diagram()
    text = "  red\tblue  "
    L = 4.6  # labels end here; content starts at L + 0.5
    X = L + 0.5

    d.code(L, 0.5, "text", ha="right")
    d.cells(X, 0, text, top=range(len(text)))
    d.note(X + len(text) + 0.4, 0.5, "␣ space    ⇥ tab")

    # split()
    y = -2.6
    d.code(L, y + 0.5, "text.split()", ha="right")
    d.cells(X, y, text, styles={**ws_styles(text, "bad")})
    xe = d.rarrow(X + len(text), y)
    d.pylist(xe, y, ["red", "blue"], styles={0: "good", 1: "good"})
    d.note(X, y - 0.45, "every RUN of whitespace (spaces, tabs, newlines) is one cut; "
                        "nothing is kept from the ends", va="center")

    # split(' ')
    y = -5.6
    d.code(L, y + 0.5, "text.split(' ')", ha="right")
    d.cells(X, y, text, styles={i: "bad" for i, ch in enumerate(text) if ch == " "})
    for i, ch in enumerate(text):  # a red cut line through every single space
        if ch == " ":
            d.ax.plot([X + i + 0.5] * 2, [y - 0.15, y + 1.15], color=STY["bad"][1], lw=1.4, ls=":")
    xe = d.rarrow(X + len(text), y)
    d.pylist(xe, y, ["", "", "red\tblue", "", ""],
             styles={0: "bad", 1: "bad", 3: "bad", 4: "bad"}, fs=12)
    d.note(X, y - 0.45, "cuts at each single ' ' only: the tab survives, and two cuts side by side "
                        "leave an empty string ''")

    # join
    y = -8.6
    d.code(L, y + 0.5, "' '.join(words)", ha="right")
    xe = d.pylist(X, y, ["red", "blue"])
    xe = d.rarrow(xe + 0.1, y)
    d.cells(xe, y, "red blue", styles={3: "hl"})
    d.note(X, y - 0.45, "the separator string goes BETWEEN the items, never at the ends")
    return d.save("02_split_and_join.png")


def fig_index_slice():
    d = Diagram()
    word = "Python"
    # indexing
    d.code(0, 2.4, "word = 'Python'", fs=13, color=INK)
    d.note(0, 1.7, "positive index from the left, negative index from the right")
    d.text(-0.3, 0.5 + 0.8, "index", fs=9.5, color=MUTED, ha="right")
    d.text(-0.3, -0.3, "negative", fs=9.5, color=MUTED, ha="right")
    d.cells(0, -0.3 + 0.3 - 0.0, word, styles={0: "hl", 5: "hl"},
            top=range(6), bottom=range(-6, 0), top_color="#3b6fd8", bottom_color="#7a4fd6")
    d.code(7.2, 0.95, "word[0]  → 'P'", fs=12)
    d.code(7.2, 0.05, "word[-1] → 'n'", fs=12)

    # slicing with fence posts
    y = -4.2
    d.code(0, y + 2.3, "word[1:4]", fs=13, color=INK)
    d.note(2.7, y + 2.3, "slice numbers sit on the GAPS between characters", va="center")
    d.cells(0, y, word, styles={0: "ghost", 1: "hl", 2: "hl", 3: "hl", 4: "ghost", 5: "ghost"})
    for g in range(7):
        col = STY["hl"][1] if g in (1, 4) else "#c9cdd4"
        d.ax.plot([g, g], [y - 0.1, y + 1.25], color=col, lw=2.2 if g in (1, 4) else 1.1)
        d.text(g, y + 1.55, str(g), fs=10.5, mono=True, ha="center",
               color=col if g in (1, 4) else MUTED, weight="bold" if g in (1, 4) else "normal")
    d.ax.annotate("", xy=(4, y - 0.45), xytext=(1, y - 0.45),
                  arrowprops=dict(arrowstyle="|-|", color=STY["hl"][1], lw=1.6,
                                  mutation_scale=4))
    d.text(2.5, y - 0.95, "3 characters", fs=9.5, color=STY["hl"][1], ha="center")
    d.code(7.2, y + 0.5, "→ 'yth'", fs=12)
    d.note(7.2, y - 0.3, "start 1 is included, stop 4 is not")
    return d.save("03_indexing_and_slicing.png")


def fig_reverse_repeat():
    d = Diagram()
    word = "Python"
    d.code(-0.4, 0.5, "word", ha="right")
    d.cells(0, 0, word, top=range(6))
    d.code(-0.4, -2.5, "word[::-1]", ha="right")
    d.cells(0, -3, word[::-1], style="good", top=None)
    colors = ["#3b6fd8", "#7a4fd6", "#c4458f", "#d08a00", "#239a4b", "#0e8fa3"]
    for i in range(6):
        d.ax.plot([i + 0.5, 5 - i + 0.5], [-0.05, -1.95], color=colors[i], lw=1.4, alpha=0.85)
    d.note(6.6, -1.0, "step -1: walk from the last\ncharacter back to the first", va="center")

    x0 = 15.0
    d.code(x0, 0.5, "'*' * 3", ha="left")
    d.chip(x0, -1.3, "'*'", "str", fs=12)
    d.text(x0 + 2.0, -0.8, "× 3", fs=13, mono=True, color=INK)
    d.arrow((x0 + 3.4, -0.8), (x0 + 4.4, -0.8))
    d.cells(x0 + 4.6, -1.3, "***", style="good")
    d.note(x0, -2.5, "repeat and join copies:\na NEW string of length 3")
    return d.save("04_reverse_and_repeat.png")


def fig_fstring():
    d = Diagram()
    L = 8.6
    X = L + 0.5
    d.code(L, 0.5, "average = total / count", ha="right")
    d.chip(X, 0, "3.3333333333333335", "num")
    d.note(X, -0.45, "a float, not text")

    y = -2.2
    d.code(L, y + 0.5, "f'Average: {average:.1f}'", ha="right")
    s = "Average: 3.3"
    d.cells(X, y, s, styles={9: "hl", 10: "hl", 11: "hl"})
    d.note(X + 9, y - 0.45, ".1f → 1 decimal place")

    y = -4.4
    d.code(L, y + 0.5, "average   # afterwards", ha="right")
    d.chip(X, y, "3.3333333333333335", "num")
    d.note(X + 8.0, y + 0.5, "unchanged: formatting only builds the text")

    y = -6.9
    d.code(L, y + 0.5, "f'Words: {count}\\nTotal: {total}'", ha="right")
    s = "Words: 3\nTotal: 10"
    d.cells(X, y, s, styles={7: "hl", 8: "hl", 16: "hl", 17: "hl"})
    d.note(X, y - 0.45, "\\n is ONE character (↵): a line break")
    # printed output
    tx, ty = X + 9.5, y - 3.1
    d.ax.add_patch(Rectangle((tx, ty), 6.4, 2.1, fc="#1f2937", ec="#1f2937"))
    d.grow(tx, ty, tx + 6.4, ty + 2.1)
    d.text(tx + 0.4, ty + 1.45, "Words: 3", fs=12, mono=True, color="#e5e7eb")
    d.text(tx + 0.4, ty + 0.6, "Total: 10", fs=12, mono=True, color="#e5e7eb")
    d.note(tx - 0.3, ty + 1.05, "print(...) shows", ha="right")
    return d.save("05_fstrings.png")


def fig_pipeline():
    d = Diagram()
    L = 5.6
    X = L + 0.5
    original = "  Hi\tTHERE  ! "
    lower = original.lower()
    no_bang = lower.replace("!", "")
    pieces = no_bang.split()
    joined = " ".join(pieces)
    rows = [
        ("original", "cells", original, {}, ""),
        (".lower()", "cells", lower, diff_styles(original, lower), "letters lowercased"),
        (".replace('!', '')", "cells", no_bang, {}, "'!' deleted, nothing put in its place"),
        (".split()", "list", pieces, {}, "whitespace runs cut away"),
        ("' '.join(pieces)", "cells", joined, {2: "hl"}, "one space between words"),
    ]
    y = 0
    for i, (label, kind, val, styles, msg) in enumerate(rows):
        d.code(L, y + 0.5, label, ha="right", color=CODE if i else INK)
        if kind == "cells":
            xe = d.cells(X, y, val, styles=styles, style="good" if i == 4 else "str")
        else:
            xe = d.pylist(X, y, val, styles={0: "good", 1: "good"})
        if msg:
            d.note(X + len(original) + 0.6, y + 0.5, msg)
        if i < len(rows) - 1:
            d.arrow((X + 0.5, y - 0.1), (X + 0.5, y - 0.95))
        y -= 2.0
    if True:  # the original is untouched
        y -= 0.4
        d.ax.plot([0, 26], [y + 1.55, y + 1.55], color="#e5e7eb", lw=1.2)
        d.code(L, y + 0.5, "original", ha="right", color=INK)
        d.cells(X, y, original)
        d.note(X + len(original) + 0.6, y + 0.5, "still the same: every step made a NEW string")
    return d.save("06_method_chain.png")


# ====================================================================
# Task diagrams
# ====================================================================

def fig_task1():
    d = Diagram()
    sample = " A ! B "
    d.code(0, 0.5, "sample", color=INK)
    d.cells(2.4, 0, sample)

    y = -1.9
    d.tick(-0.6, y + 0.5, True)
    d.code(0, y + 0.5, "sample.lower().replace('!', '')", color=CODE)
    cleaned = sample.lower().replace("!", "")
    xe = d.cells(0, y - 1.5, cleaned)
    xe = d.rarrow(xe, y - 1.5, length=1.6, label=".split()")
    d.pylist(xe, y - 1.5, cleaned.split(), styles={0: "good", 1: "good"})
    d.note(0, y - 2.0, "remove ! first, then make the word list")

    y = -6.3
    d.tick(-0.6, y + 0.5, False)
    d.code(0, y + 0.5, "sample.lower()", color=CODE)
    low = sample.lower()
    xe = d.cells(0, y - 1.5, low, styles={3: "bad"})
    xe = d.rarrow(xe, y - 1.5, length=1.6, label=".split()")
    d.pylist(xe, y - 1.5, low.split(), styles={1: "bad"})
    d.note(0, y - 2.0, "split first and the lone ! becomes a 'word'")
    return d.save("t1_remove_before_split.png")


def fig_task2():
    d = Diagram()
    d.code(0, 0.5, "longest_seen = ''", color=INK)
    d.text(0.0, -0.8, "candidate", fs=10, color=MUTED, weight="bold")
    d.text(4.0, -0.8, "len(candidate) > len(longest_seen) ?", fs=10, color=MUTED, weight="bold")
    d.text(15.4, -0.8, "longest_seen after", fs=10, color=MUTED, weight="bold")
    longest = ""
    y = -2.4
    for w in "red blue gold".split():
        better = len(w) > len(longest)
        d.chip(0, y, repr(w))
        d.code(4.0, y + 0.5, f"{len(w)} > {len(longest)}", color=INK, weight="normal")
        d.tick(7.0, y + 0.5, better)
        d.note(7.6, y + 0.5, "longer: replace" if better else "a tie is NOT longer: keep the first")
        if better:
            longest = w
        d.chip(15.4, y, repr(longest), "good" if better else "hl")
        y -= 1.5
    d.code(0, y + 0.2, "word_summary('red blue gold')  →  (3, 'blue')", fs=11, color=CODE)
    return d.save("t2_longest_word_trace.png")


def fig_task3():
    d = Diagram()
    cleaned = "python is fun"
    words = cleaned.split()
    L = 3.6
    X = L + 0.5
    d.code(L, 0.5, "cleaned", ha="right", color=INK)
    d.cells(X, 0, cleaned, styles=ws_styles(cleaned, "bad"))
    d.tick(X + len(cleaned) + 0.7, 0.5, False)
    d.note(X + len(cleaned) + 1.2, 0.5, "len(cleaned) = 13\ncounts the 2 spaces")

    y = -2.6
    d.code(L, y + 0.5, "words", ha="right", color=INK)
    x = X
    for w in words:
        d.cells(x, y, w, style="good")
        d.text(x + len(w) / 2, y - 0.45, f"len = {len(w)}", fs=10, color=STY["good"][1],
               ha="center", mono=True)
        x += len(w) + 1.0
    d.tick(X + len(cleaned) + 0.7, y + 0.5, True)
    d.note(X + len(cleaned) + 1.2, y + 0.5, "6 + 2 + 3 = 11\nletters only")

    y = -5.0
    d.code(L, y + 0.5, "average", ha="right", color=INK)
    xe = d.code(X, y + 0.5, "11 / 3", color=INK, weight="normal")
    d.arrow((xe + 0.3, y + 0.5), (xe + 1.3, y + 0.5))
    xe = d.chip(xe + 1.5, y, "3.6666666666666665", "num", fs=12)
    d.arrow((xe + 0.2, y + 0.5), (xe + 1.2, y + 0.5))
    d.code(xe + 0.7, y + 1.3, ":.1f", fs=10, ha="center")
    d.chip(xe + 1.4, y, "'3.7'", "good", fs=12)
    d.note(X, y - 0.5, "no words? skip the division: show 0.0 and (none)")
    return d.save("t3_average_length.png")


def fig_task4():
    d = Diagram()
    name = "  alan\tturing "
    L = 3.6
    X = L + 0.5
    d.code(L, 0.5, "name", ha="right", color=INK)
    d.cells(X, 0, name)

    y = -2.2
    d.code(L, y + 0.5, ".split()", ha="right")
    d.cells(X, y, "alan", styles={0: "hl"})
    d.cells(X + 5.2, y, "turing", styles={0: "hl"})
    d.text(X + 2, y - 0.4, "part 1", fs=9.5, color=MUTED, ha="center")
    d.text(X + 8.2, y - 0.4, "part 2", fs=9.5, color=MUTED, ha="center")
    d.note(X + 12, y + 0.5, "part[0] is safe: split() never\ngives an empty part")

    y = -4.6
    d.code(L, y + 0.5, "upper + '.'", ha="right")
    for px, letter in [(X, "a"), (X + 5.2, "t")]:
        d.arrow((px + 0.5, y + 1.8), (px + 0.5, y + 1.05))
        d.cells(px, y, letter.upper() + ".", style="good")
    y = -6.6
    d.code(L, y + 0.5, "result", ha="right")
    xs = X
    for i, val in enumerate(["''", "'A.'", "'A.T.'"]):
        xs = d.chip(xs, y, val, "good" if i == 2 else "str", fs=12)
        if i < 2:
            xs = d.rarrow(xs, y, length=1.0)
    d.note(X, y - 0.45, "add each initial and its full stop to the result")
    return d.save("t4_initials.png")


def fig_task5():
    d = Diagram()
    text = "Banana"
    L = 5.6
    X = L + 0.5
    d.code(L, 0.5, "'Banana'.lower()", ha="right")
    hits = [i for i, c in enumerate(text.lower()) if c == "a"]
    d.cells(X, 0, text.lower(), styles={i: "hl" for i in hits})
    for n, i in enumerate(hits, 1):
        d.text(X + i + 0.5, -0.45, f"+1", fs=10, color=STY["hl"][1], ha="center",
               mono=True, weight="bold")
    d.code(L, -2.0 + 0.5, "'A'.lower()", ha="right")
    d.cells(X, -2.0, "a", style="hl")
    d.note(X + 1.5, -1.5, "compare each character with the lowercase target")
    d.code(X, -3.0, "counter → 3", fs=13, color=INK)
    return d.save("t5_count_character.png")


def fig_task6():
    d = Diagram()

    def block(y, raw, label):
        cleaned = "".join(raw.lower().split())
        rev = cleaned[::-1]
        L = 4.3
        X = L + 0.5
        d.code(0, y + 1.9, label, color=INK)
        d.code(L, y + 0.5, "cleaned", ha="right")
        d.cells(X, y, cleaned)
        d.code(L, y - 1.0, "cleaned[::-1]", ha="right")
        styles = {i: ("good" if a == b else "bad") for i, (a, b) in enumerate(zip(cleaned, rev))}
        d.cells(X, y - 1.5, rev, styles=styles)
        same = cleaned == rev
        d.tick(X + len(cleaned) + 0.8, y - 0.25, same, fs=17)
        d.code(X + len(cleaned) + 1.4, y - 0.25, str(same), color=INK)

    block(0, "Never odd or even", "is_palindrome('Never odd or even')")
    d.note(0, -2.5, "lowercase + drop all whitespace, then compare with the reverse")
    block(-6.2, "ab,ba!", "is_palindrome('ab,ba!')")
    d.note(0, -8.7, "punctuation is kept, so ! must match too")
    return d.save("t6_palindrome.png")


def fig_task7():
    d = Diagram()
    email = "alice@example.com"
    L = 4.4
    X = L + 0.5
    d.code(L, 0.5, "email", ha="right", color=INK)
    d.cells(X, 0, email, styles={5: "hl"})

    y = -2.4
    d.code(L, y + 0.5, ".split('@')", ha="right")
    d.pylist(X, y, email.split("@"))
    d.note(X, y - 0.45, "username, domain")

    y = -5.0
    d.code(L, y + 0.5, "build", ha="right")
    parts = [("'a'", "good", "username[0]"),
             ("'****'", "hl", "'*' * (5 - 1)"),
             ("'@'", "str", ""),
             ("'example.com'", "str", "domain")]
    x = X
    for i, (val, st, cap) in enumerate(parts):
        slot = max(mono_w(val, 12) + 0.6, mono_w(cap, 9.5))
        cx = x + slot / 2  # centre chip and caption in a slot wide enough for both
        d.chip(cx - (mono_w(val, 12) + 0.6) / 2, y, val, st, fs=12)
        if cap:
            d.text(cx, y - 0.45, cap, fs=9.5, color=MUTED, ha="center", mono=True)
        x += slot
        if i < len(parts) - 1:
            x = d.text(x + 0.25, y + 0.5, "+", fs=14, mono=True, color=INK) + 0.25

    y = -7.6
    d.code(L, y + 0.5, "result", ha="right", color=INK)
    d.cells(X, y, "a****@example.com", styles={i: "hl" for i in range(1, 5)} | {0: "good"})
    d.note(X, y - 0.45, "one-character username: '*' * 0 is '' so nothing is hidden")
    return d.save("t7_mask_email.png")


# ====================================================================
# Notebook: insert each picture into the cell that starts with a key
# ====================================================================

PLACEMENT = [
    ("Calling lower() does not change message", ["01_methods_return_new_strings.png"]),
    ("With no argument, split() groups whitespace", ["02_split_and_join.png"]),
    ("The stop index in [1:4] is excluded", ["03_indexing_and_slicing.png", "04_reverse_and_repeat.png"]),
    ("Use .1f for one decimal place", ["05_fstrings.png"]),
    ("lower() returns lowercase text; replace() removes !", ["06_method_chain.png"]),
    ("### Follow the text through the steps", ["t1_remove_before_split.png"]),
    ("### Keep the best word seen so far", ["t2_longest_word_trace.png"]),
    ("### Separate calculation from formatting", ["t3_average_length.png"]),
    ("### Build the initials one part at a time", ["t4_initials.png"]),
    ("### Use the same case for both arguments", ["t5_count_character.png"]),
    ("### Choose what to ignore before reversing", ["t6_palindrome.png"]),
    ("### Split the address into two jobs", ["t7_mask_email.png"]),
]

ALT = {
    "01_methods_return_new_strings.png": "lower() returns a new string; message is unchanged",
    "02_split_and_join.png": "split() vs split(' ') and join()",
    "03_indexing_and_slicing.png": "Indexing and slicing 'Python'",
    "04_reverse_and_repeat.png": "Reversing with [::-1] and repeating with *",
    "05_fstrings.png": "Formatting with f-strings",
    "06_method_chain.png": "Tracing a chain of string methods",
    "t1_remove_before_split.png": "Remove ! before splitting",
    "t2_longest_word_trace.png": "Trace of the longest-word loop",
    "t3_average_length.png": "Average word length",
    "t4_initials.png": "Building initials",
    "t5_count_character.png": "Counting a character, ignoring case",
    "t6_palindrome.png": "Comparing the cleaned text with its reverse",
    "t7_mask_email.png": "Masking the username of an email",
}


def build_notebook():
    nb = json.loads(NB_IN.read_text())
    out = copy.deepcopy(nb)
    used = set()
    for cell in out["cells"]:
        if cell["cell_type"] != "markdown":
            continue
        src = "".join(cell["source"])
        for key, images in PLACEMENT:
            if not src.startswith(key):
                continue
            used.add(key)
            md = "\n\n".join(f"![{ALT[img]}](attachment:{img})" for img in images)
            if "**Discuss:**" in src:  # picture goes before the discussion question
                head, tail = src.split("**Discuss:**", 1)
                src = head.rstrip() + "\n\n" + md + "\n\n**Discuss:**" + tail
            else:
                src = src.rstrip() + "\n\n" + md
            cell["source"] = src.splitlines(keepends=True)
            cell["attachments"] = {
                img: {"image/png": base64.b64encode((HERE / img).read_bytes()).decode()}
                for img in images}
    missing = [k for k, _ in PLACEMENT if k not in used]
    assert not missing, f"cells not found: {missing}"
    NB_OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    return NB_OUT


if __name__ == "__main__":
    for f in [fig_immutable, fig_split_join, fig_index_slice, fig_reverse_repeat,
              fig_fstring, fig_pipeline, fig_task1, fig_task2, fig_task3, fig_task4,
              fig_task5, fig_task6, fig_task7]:
        print("wrote", f().name)
    print("wrote", build_notebook())
