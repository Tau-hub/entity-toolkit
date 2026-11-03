"""Reads the in-game players menu: allies' perks, character names, player names and the map."""
import difflib
import json
import re
import time

import numpy as np

from . import ocr, paths, recognize as rc
from .log import log

MIN_SCORE = 0.78   # below: the perk is flagged "to check"
EMPTY_ROW = 0.60   # every perk of a row below this score: empty row (no player)

# Survivors that may be missing from the wiki data (recent chapters): completed here when needed
EXTRA_SURVIVORS = ["Claire Redfield", "Daryl Dixon", "Jonathan Byers", "James Sunderland", "Maria", "Sienna Shaw", "Aestri Yazar", "Baermar Uraz"]


def survivor_names():
    try:
        data = json.loads(paths.SURVIVORS.read_text(encoding="utf8"))
        names = [s["name"] for s in data["killers"] if s["name"] != "The Troupe"]  # (the "killers" key holds the survivors too)
    except Exception:
        names = []
    return names + [n for n in EXTRA_SURVIVORS if n not in names]


class Analyzer:
    def __init__(self):
        if not paths.LOADOUT.exists():
            raise FileNotFoundError("Perk database missing: run `python -m entity_toolkit update-db` (or use the Setup page).")
        self.data = json.loads(paths.LOADOUT.read_text(encoding="utf8"))
        self.refs = rc.load_refs(self.data)
        self.by_name = {p["name"]: p for p in self.data["perks"]["S"]}
        by_icon = {}
        for p in self.data["perks"]["S"]:
            by_icon.setdefault(p["icon"], []).append(p)
        self.by_icon = by_icon
        self.names = survivor_names()

    def perk(self, score, name):
        p = self.by_name[name]
        same = list(self.by_icon[p["icon"]])  # perks sharing the same icon cannot be told apart on screen
        return {"score": score, "perks": same, "icon": p["icon"], "uncertain": score < MIN_SCORE}

    @staticmethod
    def me_row(img):
        """Row of the players menu that is yours (0 to 3, top to bottom): its background is yellow-olive, the allies' is blue-grey. None if nothing stands out."""
        s = img.height / rc.REF_H
        score = []
        for y in rc.ROWS_Y:
            px = list(img.crop((int(rc.cx_of(img, 600)), int((y - 60) * s), int(rc.cx_of(img, 640)), int(y * s))).getdata())
            score.append(sum(p[0] - p[2] for p in px) / len(px))  # red - blue: positive on your row's yellow background
        best = max(range(4), key=lambda i: score[i])
        return best if score[best] > 3 and score[best] - sorted(score)[-2] > 8 else None

    def menu_visible(self, img):
        """Guard: is the survivor players menu on screen? (the first ally's first perk must look like a real icon)"""
        res, _ = rc.recognize(img, self.refs, top=1, rows=[1])
        return max(r[0][0] for r in res[1]) >= EMPTY_ROW

    def analyze(self, img):
        me = self.me_row(img)
        me = 0 if me is None else me
        ally_rows = [r for r in range(4) if r != me]
        res, _ = rc.recognize(img, self.refs, top=1, rows=ally_rows)
        allies = []
        for ri in ally_rows:
            row = res[ri]
            if row is None or max(r[0][0] for r in row) < EMPTY_ROW:
                continue
            survivor, player = self.row_name(img, ri)
            raw = survivor
            survivor = self.resolve_survivor(survivor) if survivor else survivor
            if survivor and not player and survivor != survivor.upper():
                survivor, player = "", survivor  # mixed case = a player name: the character name line was not read (e.g. a short name like "A2")
            log(f"Ally {ri}: '{raw}' -> {survivor} · player '{player}'")
            allies.append({"row": ri, "survivor": survivor, "player": player, "perks": [self.perk(*r[0]) for r in row]})
        try:
            m = rc.recognize_map(img)
        except Exception as e:
            log(f"Map not read: {e}")
            m = {"maps": None, "realms": None}
        return {"me_row": me, "allies": allies, "map": m["maps"][1] if m["maps"] else None, "realm": m["realms"][1] if m["realms"] else None,
                "time": time.strftime("%H:%M:%S")}

    def resolve_survivor(self, text):
        """Full name of the survivor closest to the text read (first or last name sometimes cut: 'KARLSSON' -> Nea Karlsson). Raw text if nothing fits."""
        norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
        truncated = text.rstrip().endswith(("...", "…"))  # the game cuts long names with "…": compare with the start of the name then
        t = norm(text)
        if len(t) < 3 or text != text.upper():  # character names are upper-case: mixed case means a player name (name line unreadable)
            return text
        best, score = None, 0
        for name in self.names:
            n = norm(name)
            parts = [norm(w) for w in name.split()]
            cands = [difflib.SequenceMatcher(None, t, n).ratio()]
            cands += [difflib.SequenceMatcher(None, t, p).ratio() * 0.9 for p in parts if len(p) >= 3]
            if len(t) >= 4 and (n.endswith(t) or n.startswith(t) or t.endswith(parts[-1])):
                cands.append(0.9)
            if truncated and len(t) >= 4:
                cands.append(difflib.SequenceMatcher(None, t, n[:len(t)]).ratio())
            sc = max(cands)
            if sc > score:
                best, score = name, sc
        return best.upper() if best and score >= 0.5 else text

    @staticmethod
    def row_name(img, ri):
        """(survivor, player name) read on the title line by OCR; empty strings if unreadable.
        The character name (white, bold) is on the first recognised line, the player name (grey) on the next."""
        try:
            s = img.height / rc.REF_H
            y = rc.ROWS_Y[ri]
            box = (int(rc.cx_of(img, 800)), int((y - 78) * s), int(rc.cx_of(img, 1240)), int((y - 34) * s))  # starts after the player / globe icon
            crop = img.crop(box)
            lines = sorted(ocr.read_words(crop, 3), key=lambda ln: ln[0][1])
            try:  # the character name is white (255), the player name grey (~125): more reliable than letter case (names may be upper-case, with digits or "_")
                g = np.asarray(crop.convert("L"), dtype=float)
                bright, dim = [], []
                for ln in lines:
                    for t, x, y0, w, h in ln:
                        if t.isdigit() or t.lower() == "ms":
                            continue  # ping
                        reg = g[int(max(y0, 0)):int(y0 + h) + 1, int(max(x, 0)):int(x + w) + 1]
                        if reg.size:
                            (bright if np.percentile(reg, 95) >= 190 else dim).append((x, t))
                if bright:
                    return " ".join(t for _, t in sorted(bright)), " ".join(t for _, t in sorted(dim))
            except Exception:
                pass
            texts = [" ".join(w[0] for w in ln if not (w[0].isdigit() or w[0].lower() == "ms")) for ln in lines]
            texts = [t for t in texts if t]
            if not texts:
                return "", ""
            words = texts[0].split()  # name (upper-case) and player name (mixed case) sometimes read on one line: split them
            k = 0
            while k < len(words) and (words[k].isupper() or words[k].endswith(("...", "…")) and words[k][:-3].isupper()):
                k += 1
            if 0 < k < len(words):
                return " ".join(words[:k]), " ".join(words[k:]) + (" " + texts[1] if len(texts) > 1 and not texts[1][:1].isdigit() else "")
            return texts[0], (texts[1] if len(texts) > 1 else "")
        except Exception:
            return "", ""
