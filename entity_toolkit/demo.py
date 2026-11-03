"""A fake analysis result (made-up players, real perks) to preview the live page without playing:  python -m entity_toolkit serve --demo"""
import time

from . import analyzer

ALLIES = [
    ("MEG THOMAS", "Sample Player 1", ["Sprint Burst", "Lithe", "Adrenaline", "Deliverance"]),
    ("DWIGHT FAIRFIELD", "Sample Player 2", ["Prove Thyself", "Bond", "Leader", "Dead Hard"]),
    ("CLAUDETTE MOREL", "Sample Player 3", ["Self-Care", "Empathy", "Botany Knowledge", "Resilience"]),
]


def result(ana=None):
    ana = ana or analyzer.Analyzer()
    allies = []
    for i, (survivor, player, perks) in enumerate(ALLIES):
        found = [ana.by_name[p] for p in perks if p in ana.by_name] or list(ana.by_name.values())[:4]
        allies.append({"row": i + 1, "survivor": survivor, "player": player, "perks": [ana.perk(0.95, p["name"]) for p in found]})
    return {"me_row": 0, "allies": allies, "map": "Treatment Theatre", "realm": "Léry's Memorial Institute", "time": time.strftime("%H:%M:%S")}
