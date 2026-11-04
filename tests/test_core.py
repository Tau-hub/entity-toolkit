"""Logic tests that need neither the game nor the network:  python -m unittest discover -s tests"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# every test works in its own throw-away data folder
_TMP = tempfile.mkdtemp(prefix="entity-toolkit-test-")
os.environ["ENTITY_TOOLKIT_DATA"] = _TMP
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from entity_toolkit import assistant, levels, overlay, paths, winapi  # noqa: E402


def ally(row, survivor, player):
    return {"row": row, "survivor": survivor, "player": player, "perks": []}


class OverlayPlacement(unittest.TestCase):
    def test_waits_until_the_game_list_is_readable(self):
        self.assertIsNone(overlay.place([ally(1, "A", "Alpha"), ally(2, "B", "Bravo")], ["", "", "", ""], 0))

    def test_duplicates_are_matched_by_player_name(self):
        allies = [ally(1, "SAME", "Alpha"), ally(2, "SAME", "Bravo"), ally(3, "SAME", "Charlie")]
        names = ["Me", "Charlie", "Alpha", "Bravo"]  # the game's list is in another order than the menu
        self.assertEqual(overlay.place(allies, names, 0), {1: 2, 2: 3, 3: 1})

    def test_your_row_never_moves(self):
        allies = [ally(0, "A", "Alpha"), ally(2, "B", "Bravo"), ally(3, "C", "Charlie")]
        names = ["Alpha", "Me", "Charlie", "Bravo"]
        out = overlay.place(allies, names, 1)
        self.assertEqual(out, {0: 0, 2: 3, 3: 2})
        self.assertNotIn(1, out.values())


class Levels(unittest.TestCase):
    def setUp(self):
        for p in (paths.LEVELS, paths.LEVELS_HISTORY, paths.KILLERS, paths.SURVIVORS):
            p.unlink(missing_ok=True)
        paths.ensure()
        paths.OWNED.unlink(missing_ok=True)
        paths.KILLERS.write_text(json.dumps({"killers": [
            {"name": "The Trapper", "short": "Trapper", "chapter": "Base Game", "teachables": [{"name": "x"}]},
            {"name": "The Spirit", "short": "Spirit", "chapter": "Demise of the Faithful", "teachables": [{"name": "z"}]}]}), encoding="utf8")
        paths.SURVIVORS.write_text(json.dumps({"killers": [
            {"name": "Dwight Fairfield", "short": "Dwight Fairfield", "chapter": "Base Game", "teachables": [{"name": "y"}]},
            {"name": "Yui Kimura", "short": "Yui Kimura", "chapter": "Demise of the Faithful", "teachables": [{"name": "w"}]}]}), encoding="utf8")

    def test_set_level_clamps_and_logs(self):
        self.assertTrue(levels.set_level("killers", "Trapper", 9))
        self.assertEqual(levels.load()["killers"]["Trapper"], 3)
        self.assertFalse(levels.set_level("killers", "Trapper", 3))  # no change, no history line
        self.assertEqual(len(levels.history()), 1)

    def test_import_matches_names_loosely(self):
        n = levels.import_json(json.dumps({"killers": {"the trapper": 2}, "survivors": {"Dwight Fairfeld": 1}}))
        self.assertEqual(n, 2)
        self.assertEqual(levels.load(), {"killers": {"Trapper": 2}, "survivors": {"Dwight Fairfield": 1}})

    def test_import_flat_dict(self):
        self.assertEqual(levels.import_json(json.dumps({"Trapper": 3})), 1)

    def test_everything_is_owned_by_default(self):
        self.assertTrue(all(c["owned"] for k in levels.KINDS for c in levels.characters(k)))

    def test_ownership_and_base_game(self):
        self.assertEqual(levels.set_owned_many("killers", ["Spirit", "Trapper"], False), 1)  # base game stays owned
        owned = {c["short"]: c["owned"] for c in levels.characters("killers")}
        self.assertEqual(owned, {"Trapper": True, "Spirit": False})
        self.assertTrue(levels.set_owned("killers", "Spirit", True))
        self.assertFalse(levels.set_owned("killers", "Spirit", True))

    def test_chapter_toggle_moves_killer_and_survivor_together(self):
        self.assertEqual(levels.set_chapter_owned("Demise of the Faithful", False), 2)
        ch = {g["label"]: g for g in levels.chapters()}
        self.assertEqual(ch["Demise of the Faithful"]["owned"], "none")
        self.assertEqual(ch["Base Game"]["owned"], "all")
        levels.set_owned("survivors", "Yui Kimura", True)
        self.assertEqual({g["label"]: g for g in levels.chapters()}["Demise of the Faithful"]["owned"], "some")

    def test_unlock_all_and_lock_all(self):
        self.assertEqual(levels.set_all_owned(False), 2)  # the two non-base characters
        self.assertEqual(levels.set_all_owned(True), 2)

    def test_export_round_trip_keeps_ownership(self):
        levels.set_owned("killers", "Spirit", False)
        text = json.dumps({"killers": {"Trapper": 3}, "survivors": {}, "unowned": {"killers": ["Spirit"], "survivors": []}})
        levels.set_all_owned(True)
        levels.import_json(text)
        self.assertEqual({c["short"]: c["owned"] for c in levels.characters("killers")}, {"Trapper": True, "Spirit": False})
        self.assertEqual(levels.load()["killers"]["Trapper"], 3)

    def test_reset(self):
        levels.set_level("killers", "Trapper", 2)
        levels.reset()
        self.assertEqual(levels.load()["killers"], {})


class RosterScan(unittest.TestCase):
    def _card(self, digit=None):
        """A synthetic card: beige badge disc at the bottom left with a white digit (or none)."""
        from PIL import Image, ImageDraw, ImageFont
        card = Image.new("RGB", (210, 254), (60, 20, 30))
        d = ImageDraw.Draw(card)
        d.ellipse((30, 185, 80, 235), fill=(120, 110, 90))
        if digit:
            d.text((44, 190), str(digit), fill=(255, 255, 255), font=ImageFont.truetype("arialbd.ttf", 34))
        return card

    def test_reads_every_digit_and_the_empty_ring(self):
        from entity_toolkit import roster_scan
        self.assertEqual([roster_scan.read_level(self._card(d)) for d in (1, 2, 3)], [1, 2, 3])
        self.assertEqual(roster_scan.read_level(self._card()), 0)


class LivePatch(unittest.TestCase):
    def test_picks_the_newest_live_patch_and_ignores_test_builds(self):
        from entity_toolkit.database import patch
        items = [{"title": "10.3.0 | Terrifier PTB Patch Notes", "date": 30}, {"title": "10.2.2a Backend Bugfix Patch", "date": 20},
                 {"title": "Developer Update | 10.2.0 PTB to Live Changes", "date": 25}, {"title": "10.2.2 | Bugfix Patch", "date": 10}]
        self.assertEqual(patch.pick(items)[0], "10.2.2a")
        with self.assertRaises(RuntimeError):
            patch.pick([{"title": "Sale", "date": 1}])


class Matching(unittest.TestCase):
    def test_same_match(self):
        self.assertTrue(assistant.same_match(["a", "b", "c"], ["a", "b"]))
        self.assertFalse(assistant.same_match(["a", "b", "c"], ["x", "y", "z"]))
        self.assertIsNone(assistant.same_match([], ["a"]))


class OneInstance(unittest.TestCase):
    def test_a_second_copy_is_refused(self):
        import uuid
        name = "EntityToolkitTest" + uuid.uuid4().hex
        self.assertTrue(winapi.single_instance(name))
        self.assertFalse(winapi.single_instance(name))


class Hotkeys(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(winapi.parse_combo("alt+numpad7"), [0x12, 0x67])
        self.assertEqual(winapi.parse_combo("Ctrl + Shift + N"), [0x11, 0x10, ord("N")])
        with self.assertRaises(ValueError):
            winapi.parse_combo("alt+nonsense")


if __name__ == "__main__":
    unittest.main()
