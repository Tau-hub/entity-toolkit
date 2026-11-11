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

from entity_toolkit import captures, database, assistant, levels, mybuilds, overlay, paths, perk_types, winapi  # noqa: E402


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


class PlacementWhenDown(unittest.TestCase):
    """A real case: the key was pressed late, with survivors downed, so their portraits on the game's list no longer look like the menu's."""

    ALLIES = [{"row": 1, "survivor": "NEA KARLSSON", "player": "Castax"},
              {"row": 2, "survivor": "RICK GRIMES", "player": "TheSilentGamer08"},
              {"row": 3, "survivor": "JILL VALENTINE", "player": "BuhGaIterOCHEK"}]
    RIGHT = {1: 2, 2: 3, 3: 1}

    def test_noisy_names_alone_give_the_right_placement(self):
        for names in (["Vodlich", "BuhGa1terOCHEK", "Castax", "Th eSilen tGam er 08"], ["Vod/ich", "BuhGa/terOCHEK", "Castax", "TheSi/entGamer08"]):
            self.assertEqual(overlay.place(self.ALLIES, names, 0), self.RIGHT)

    def test_a_confidently_wrong_portrait_match_does_not_beat_clear_names(self):
        from unittest import mock
        names = ["Vodlich", "BuhGa1terOCHEK", "Castax", "Th eSilen tGam er 08"]
        wrong = ({1: 2, 2: 1, 3: 3}, 5.0)  # what the portraits said at that moment: sure of itself, and wrong
        trace = []
        with mock.patch.object(overlay, "_scores", return_value={}), mock.patch.object(overlay, "_best_assign", return_value=wrong):
            out = overlay.place(self.ALLIES, names, 0, menu_img=object(), hud_img=object(), trace=trace)
        self.assertEqual(out, self.RIGHT)
        self.assertTrue(any("clear match" in line for line in trace), trace)

    def test_portraits_still_decide_when_no_name_is_readable(self):
        from unittest import mock
        names = ["Vodlich", "Qwertzuiop", "Castax", "Zz1"]  # only one of the three allies has a clearly matching name
        ok = ({1: 2, 2: 3, 3: 1}, 5.0)
        with mock.patch.object(overlay, "_scores", return_value={}), mock.patch.object(overlay, "_best_assign", return_value=ok):
            out = overlay.place(self.ALLIES, names, 0, menu_img=object(), hud_img=object())
        self.assertEqual(out[1], 2)  # Castax, by name
        self.assertEqual((out[2], out[3]), (3, 1))  # the two unreadable names, by portrait


class PerkHover(unittest.TestCase):
    def _perk(self, name="Bond", desc="Auras are revealed.", note=78, uncertain=False):
        return {"perks": [{"name": name, "desc": desc, "note": note}], "uncertain": uncertain}

    def test_hit_boxes_stay_inside_the_overlay_and_do_not_overlap(self):
        rect = (0, 0, 2560, 1440)
        hits = overlay.hit_rects({1: [self._perk()] * 4, 2: [self._perk()] * 4, 3: [self._perk()] * 4}, rect)
        g = overlay.grid_geometry(rect)
        self.assertEqual(len(hits), 12)
        for x0, y0, x1, y1, _ in hits:
            self.assertTrue(g["x"] <= x0 and x1 <= g["x"] + g["width"] and g["top"] + g["y0"] <= y0 and y1 <= g["top"] + g["y1"])
        boxes = {(h[0], h[1]) for h in hits}
        self.assertEqual(len(boxes), 12)

    def test_the_icon_under_the_mouse_is_found(self):
        hits = overlay.hit_rects({1: [self._perk("A"), self._perk("B"), self._perk("C"), self._perk("D")]}, (0, 0, 2560, 1440))
        x0, y0, x1, y1, pk = hits[2]
        self.assertEqual(overlay.hover_target(hits, (x0 + x1) // 2, (y0 + y1) // 2)[4]["perks"][0]["name"], "C")
        self.assertIsNone(overlay.hover_target(hits, 1500, 700))  # the middle of the screen, where the cursor sits during mouse look

    def test_boxes_follow_the_screen_size(self):
        small = overlay.hit_rects({1: [self._perk()]}, (0, 0, 1920, 1080))[0]
        big = overlay.hit_rects({1: [self._perk()]}, (0, 0, 2560, 1440))[0]
        self.assertAlmostEqual((small[2] - small[0]) / (big[2] - big[0]), 0.75, delta=0.05)

    def test_tooltip_text(self):
        title, body = overlay.tooltip_text(self._perk("Bond", "Auras are revealed.", 78))
        self.assertEqual((title, body), ("Bond   ·   78/100", "Auras are revealed."))
        self.assertIn("(to check)", overlay.tooltip_text(self._perk(uncertain=True))[0])
        long_text = overlay.tooltip_text(self._perk(desc="word " * 400))[1]
        self.assertLess(len(long_text), 720)
        self.assertTrue(long_text.endswith("…"))
        twin = {"perks": [{"name": "X", "desc": "one", "note": None}, {"name": "Y", "desc": "two", "note": 5}], "uncertain": False}
        self.assertEqual(overlay.tooltip_text(twin)[0], "X / Y")


class HoverCost(unittest.TestCase):
    """The mouse must be looked at often ONLY while the game has freed it and it is near the perk icons: nothing while the overlay is hidden,
    one cheap look every half second while you play (cursor hidden / locked to the camera). A fake cursor counts every look."""

    CENTER = (1280, 720)  # where the cursor sits during mouse look

    def _setup(self, showing, pos=None, front=True):
        import time
        perk = {"perks": [{"name": "Bond", "desc": "d", "note": 78}], "uncertain": False}
        state = {"pos": pos or self.CENTER, "showing": showing, "front": front, "calls": 0, "front_calls": 0}

        def cursor():
            state["calls"] += 1
            return (*state["pos"], state["showing"])

        def front(_hwnd):
            state["front_calls"] += 1
            return state["front"]

        logs = []
        ov = overlay.Overlay(log=logs.append, cursor_fn=cursor, front_fn=front, draw=False)  # draw=False: no window in tests
        ov.hits = overlay.hit_rects({1: [perk] * 4}, (0, 0, 2560, 1440))
        ov.hover_on = True
        self.addCleanup(ov.active.clear)
        return ov, state, logs, time

    def _run(self, ov, seconds, time):
        ov.active.set()
        time.sleep(seconds)
        ov.active.clear()
        time.sleep(0.1)

    # --- deterministic: what one look decides
    def test_a_look_while_playing_waits_half_a_second_and_never_shows_anything(self):
        ov, state, logs, _ = self._setup(showing=False)
        self.assertEqual(ov._hover_step(), overlay.HOVER_LOCKED_S)
        self.assertEqual(state["front_calls"], 0)  # not even the foreground window is asked while the cursor is hidden
        self.assertTrue(ov.q.empty())

    def test_a_look_with_the_mouse_free_but_far_waits_a_quarter_second(self):
        ov, state, logs, _ = self._setup(showing=True)
        self.assertEqual(ov._hover_step(), overlay.HOVER_FREE_S)
        self.assertTrue(ov.q.empty())

    def test_fast_looks_start_only_near_the_icons_and_the_text_appears_on_them(self):
        ov, state, logs, _ = self._setup(showing=True)
        x0, y0, x1, y1, _ = ov.hits[0]
        state["pos"] = (x1 + 100, y0)  # near the grid, not on an icon
        self.assertEqual(ov._hover_step(), overlay.HOVER_FAST_S)
        self.assertTrue(ov.q.empty())
        state["pos"] = ((x0 + x1) // 2, (y0 + y1) // 2)  # on an icon
        self.assertEqual(ov._hover_step(), overlay.HOVER_FAST_S)
        self.assertEqual(ov.q.get_nowait()[0], "tip")
        state["pos"] = self.CENTER  # leaves: the text goes away
        ov._hover_step()
        self.assertIsNone(ov.q.get_nowait()[1])

    def test_when_the_game_is_not_in_front_it_is_back_to_slow_looks(self):
        ov, state, logs, _ = self._setup(showing=True, front=False)
        x0, y0, x1, y1, _ = ov.hits[0]
        state["pos"] = ((x0 + x1) // 2, (y0 + y1) // 2)
        self.assertEqual(ov._hover_step(), overlay.HOVER_LOCKED_S)
        self.assertTrue(ov.q.empty())

    # --- measured: how many looks really happen
    def test_no_look_at_all_while_the_overlay_is_not_shown(self):
        ov, state, logs, time = self._setup(showing=True)
        time.sleep(1.0)  # the hover thread is running but blocked
        self.assertEqual(state["calls"], 0)

    def test_playing_with_the_mouse_locked_costs_about_two_looks_a_second(self):
        ov, state, logs, time = self._setup(showing=False)
        self._run(ov, 2.2, time)
        self.assertTrue(3 <= state["calls"] <= 6, state["calls"])
        self.assertEqual(ov.polls["fast"] + ov.polls["free"], 0)

    def test_mouse_free_but_far_from_the_icons_is_four_looks_a_second(self):
        ov, state, logs, time = self._setup(showing=True)
        self._run(ov, 2.0, time)
        self.assertTrue(5 <= state["calls"] <= 11, state["calls"])
        self.assertEqual(ov.polls["fast"], 0)

    def test_fast_looks_happen_only_near_the_icons(self):
        ov, state, logs, time = self._setup(showing=True)
        x0, y0, x1, y1, _ = ov.hits[0]
        state["pos"] = ((x0 + x1) // 2, (y0 + y1) // 2)
        self._run(ov, 1.0, time)
        self.assertGreater(state["calls"], 15)
        self.assertGreater(ov.polls["fast"], 15)

    def test_removing_the_overlay_stops_every_look(self):
        ov, state, logs, time = self._setup(showing=True)
        ov.active.set()
        time.sleep(0.7)
        ov.hide()
        time.sleep(0.4)
        n = state["calls"]
        time.sleep(1.0)
        self.assertLessEqual(state["calls"] - n, 1)  # at most the look that was already under way
        self.assertTrue(any("asleep" in m for m in logs))

    def test_the_log_reports_changes_of_situation_not_every_look(self):
        ov, state, logs, time = self._setup(showing=False)
        for _ in range(10):
            ov._hover_step()
        state["showing"] = True
        for _ in range(10):
            ov._hover_step()
        hover = [m for m in logs if "Overlay hover" in m]
        self.assertEqual(len(hover), 2, hover)  # "locked" once, then "free" once
        self.assertIn("locked", hover[0])
        self.assertIn("free", hover[1])


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


class BuildCreator(unittest.TestCase):
    def test_a_perk_can_have_several_types(self):
        perk = {"name": "X", "desc": "Blocks a generator and reveals the aura of survivors.", "tags": ["GenBlocker", "Auras"]}
        types = perk_types.classify(perk, "K")
        self.assertIn("gen-slowdown", types)
        self.assertIn("aura", types)

    def test_types_depend_on_the_side(self):
        perk = {"name": "X", "desc": "Heal faster.", "tags": ["Healing"]}
        self.assertIn("healing", perk_types.classify(perk, "S"))
        self.assertNotIn("healing", perk_types.classify(perk, "K"))

    def test_your_correction_replaces_the_automatic_types(self):
        perk = {"name": "Corrected perk", "desc": "", "tags": ["Auras"]}
        perk_types.save_override("Corrected perk", ["hex"])
        self.assertEqual(perk_types.perk_types(perk, "K"), ["hex"])
        perk_types.save_override("Corrected perk", None)
        self.assertEqual(perk_types.perk_types(perk, "K"), ["aura"])

    def test_saving_and_deleting_builds(self):
        b = mybuilds.save({"name": "Gen rush", "side": "K", "perks": ["A", "B", "C", "D", "E"], "killers": ["The Trapper"]})
        self.assertEqual(b["perks"], ["A", "B", "C", "D"])
        again = mybuilds.save({**b, "name": "Renamed"})
        self.assertEqual([x["name"] for x in mybuilds.load() if x["id"] == b["id"]], ["Renamed"])
        self.assertEqual(again["id"], b["id"])
        s = mybuilds.save({"name": "Survivor", "side": "S", "perks": ["A"], "killers": ["The Trapper"]})
        self.assertEqual(s["killers"], [])  # survivor builds are not tied to a killer
        with self.assertRaises(ValueError):
            mybuilds.save({"name": "Empty", "perks": []})
        self.assertEqual(mybuilds.delete(b["id"]), 1)
        self.assertEqual(mybuilds.delete(b["id"]), 0)


class UpdateNews(unittest.TestCase):
    def test_new_things_are_described(self):
        from entity_toolkit.database import changes
        before = {"Killer": ["A"], "Survivor perk": ["P1"], "Map": ["M"]}
        after = {"Killer": ["A", "B"], "Survivor perk": ["P1", "P2", "P3"], "Map": ["M"], "Item": ["I"]}
        lines = changes.describe(changes.diff(before, after))
        self.assertEqual(lines, ["New killer: B", "2 new survivor perks: P2, P3"])  # "Item" did not exist before: a first download is not news

    def test_removed_things_are_described(self):
        from entity_toolkit.database import changes
        self.assertEqual(changes.describe(changes.diff({"Perk": ["a", "b"]}, {"Perk": ["a"]})), ["Removed perk: b"])

    def test_automatic_update_is_due_after_the_chosen_delay(self):
        import time
        from entity_toolkit import config
        cfg = config.load()
        cfg.update(auto_update_days=7, last_update=int(time.time()) - 8 * 86400)
        config.save(cfg)
        self.assertTrue(database.due())
        config.save({**cfg, "last_update": int(time.time()) - 86400})
        self.assertFalse(database.due())
        config.save({**cfg, "auto_update_days": 0, "last_update": 1})
        self.assertFalse(database.due())  # switched off
        config.save({**cfg, "last_update": 0})
        self.assertFalse(database.due())  # never before a first download


class LevelBackups(unittest.TestCase):
    def test_a_bulk_change_can_be_undone(self):
        levels.set_level("killers", "Alpha", 3)
        levels.set_level("killers", "Beta", 2)
        before = levels.load()
        t = levels.snapshot("Before resetting the levels")
        levels.reset()
        self.assertEqual(levels.load()["killers"], {})
        levels.restore(t)
        self.assertEqual(levels.load(), before)

    def test_restoring_keeps_the_current_state_as_a_backup(self):
        levels.set_level("killers", "Gamma", 1)
        t = levels.snapshot("one")
        levels.set_level("killers", "Gamma", 3)
        levels.restore(t)
        self.assertEqual(levels.load()["killers"]["Gamma"], 1)
        self.assertTrue(any(b["label"].startswith("Before restoring") for b in levels.backups()))
        with self.assertRaises(ValueError):
            levels.restore(1)


class CaptureRotation(unittest.TestCase):
    def test_only_the_newest_captures_are_kept(self):
        from PIL import Image
        from entity_toolkit import config
        cfg = config.load()
        config.save({**cfg, "keep_captures": 3})
        for d in paths.CAPTURES.glob("*.jpg") if paths.CAPTURES.exists() else []:
            d.unlink()
        paths.CAPTURES.mkdir(parents=True, exist_ok=True)
        for i in range(5):  # older names first, as the real ones start with the date
            Image.new("RGB", (8, 8)).save(paths.CAPTURES / f"2026010{i}_000000_players.jpg")
        captures.prune(3)
        self.assertEqual([f.name[:8] for f in sorted(paths.CAPTURES.glob("*.jpg"))], ["20260102", "20260103", "20260104"])
        self.assertIsNotNone(captures.save(Image.new("RGB", (8, 8)), "end"))
        self.assertEqual(len(list(paths.CAPTURES.glob("*.jpg"))), 3)
        config.save({**cfg, "keep_captures": 0})
        self.assertIsNone(captures.save(Image.new("RGB", (8, 8)), "end"))  # switched off


class SurvivorNames(unittest.TestCase):
    def resolve(self, text):
        from entity_toolkit import analyzer
        a = analyzer.Analyzer.__new__(analyzer.Analyzer)
        a.names = ["Yui Kimura", "Nea Karlsson", "Meg Thomas"]
        return a.resolve_survivor(text)

    def test_a_few_letters_misread_as_lower_case_still_give_the_character(self):
        self.assertEqual(self.resolve("Y Ul KIMURA"), "YUI KIMURA")
        self.assertEqual(self.resolve("KARLSSON"), "NEA KARLSSON")

    def test_a_player_name_is_left_alone(self):
        self.assertEqual(self.resolve("Yui Kimura"), "Yui Kimura")  # mixed case: a player name
        self.assertEqual(self.resolve("XxDARKLORDxX"), "XxDARKLORDxX")  # mostly upper-case but no character looks like it


class TrayMenu(unittest.TestCase):
    def test_lists_the_same_pages_as_the_navigation_bar(self):
        import re
        from entity_toolkit import tray
        js = (Path(__file__).resolve().parent.parent / "web" / "nav.js").read_text(encoding="utf8")
        nav = re.findall(r'^\s*\["([^"]+\.html[^"]*)",\s*"([^"]+)"\]', js, re.M)
        self.assertEqual(tray.PAGES, nav)


class AutomaticMode(unittest.TestCase):
    def test_the_strip_text_tells_the_screen(self):
        from entity_toolkit import auto
        self.assertEqual(auto.kind_of("Match SCOREBOARD"), "end")
        self.assertEqual(auto.kind_of("players quests power"), "players")
        self.assertEqual(auto.kind_of("PLAY QUESTS"), "players")      # PLAYERS read short
        self.assertIsNone(auto.kind_of("PLAY AS KILLER"))             # a lobby button is not the players menu
        self.assertIsNone(auto.kind_of(""))

    def test_the_menu_is_not_read_twice_in_a_row_nor_a_scoreboard_sent_twice(self):
        from entity_toolkit import auto
        self.assertTrue(auto.want_players(None, 1000))
        self.assertFalse(auto.want_players(1000, 1000 + 60))
        self.assertTrue(auto.want_players(1000, 1000 + auto.REREAD_AFTER + 1))
        self.assertTrue(auto.want_end(None, 1000))
        self.assertFalse(auto.want_end(1000, 1000 + 30))
        self.assertTrue(auto.want_end(1000, 1000 + auto.RESEND_AFTER + 1))

    def test_a_survivor_row_without_a_status_icon_is_still_playing(self):
        from PIL import Image, ImageDraw
        from entity_toolkit import auto
        img = Image.new("RGB", (2560, 1440), (20, 24, 28))
        d = ImageDraw.Draw(img)
        for i in (0, 1, 3):  # a white icon left of the name on three rows; the third survivor has none yet
            d.ellipse((222, 342 + 160.5 * i, 248, 368 + 160.5 * i), fill=(255, 255, 255))
        self.assertEqual(auto.survivors_done(img), [True, True, False, True])
        small = img.resize((1920, 1080))  # positions follow the screen's height
        self.assertEqual(auto.survivors_done(small), [True, True, False, True])


class Autostart(unittest.TestCase):
    def test_launcher_starts_the_watcher_with_python_or_with_the_exe(self):
        from entity_toolkit import autostart
        py = autostart.launcher_text([r"C:\Py thon\pythonw.exe", "-m", "entity_toolkit"], r"C:\tool")
        self.assertIn('sh.Run """C:\\Py thon\\pythonw.exe"" -m entity_toolkit watch", 0, False', py)
        exe = autostart.launcher_text([r"C:\My Tools\EntityToolkit.exe"], r"C:\My Tools")
        self.assertIn('sh.Run """C:\\My Tools\\EntityToolkit.exe"" watch", 0, False', exe)
        self.assertIn('sh.CurrentDirectory = "C:\\My Tools"', exe)


class Shrine(unittest.TestCase):
    PERKS = {"K": [{"name": "Blood Warden", "owner": "Nightmare", "note": 54, "icon": "bw.png"}, {"name": "Corrupt Intervention", "owner": "Plague", "note": 90, "icon": "ci.png"}],
             "S": [{"name": "Smash Hit", "owner": "Lee Yun-Jin", "note": 54, "icon": "sh.png"}, {"name": "Kindred", "owner": "", "note": 70, "icon": "k.png"}]}

    def rows(self, names, lv):
        from entity_toolkit import shrine
        return {r["name"]: r for r in shrine.describe({"perks": [{"name": n, "shards": 2000, "character": "?"} for n in names]}, self.PERKS, lv)}

    def test_a_good_perk_you_do_not_have_is_worth_it(self):
        r = self.rows(["corrupt intervention", "Blood Warden", "Smash Hit", "Kindred"], {"killers": {"Nightmare": 0, "Plague": 0}, "survivors": {"Lee Yun-Jin": 2}})
        self.assertTrue(r["Corrupt Intervention"]["worth"])          # not unlocked, rated 90
        self.assertFalse(r["Blood Warden"]["worth"])                  # not unlocked but rated below 60
        self.assertFalse(r["Blood Warden"]["have"])
        self.assertTrue(r["Smash Hit"]["have"])                       # its survivor is levelled
        self.assertTrue(r["Kindred"]["have"])                         # a general perk: everyone has it
        self.assertEqual(r["Smash Hit"]["side"], "S")

    def test_a_perk_missing_from_the_database_is_shown_but_never_flagged(self):
        r = self.rows(["Brand New Perk"], {"killers": {}, "survivors": {}})["Brand New Perk"]
        self.assertEqual((r["side"], r["have"], r["worth"]), (None, False, False))

    def test_dates_are_read_as_utc(self):
        from entity_toolkit import shrine
        self.assertEqual(shrine._utc("1970-01-02T00:00:00"), 86400)
        self.assertEqual(shrine._utc("nonsense"), 0)


class NewVersion(unittest.TestCase):
    def test_only_a_higher_number_is_newer(self):
        from entity_toolkit import version
        self.assertTrue(version.newer("0.10.0", "0.9.3"))
        self.assertFalse(version.newer("0.2.0", "0.2.0"))
        self.assertFalse(version.newer("0.1.9", "0.2.0"))
        self.assertFalse(version.newer(None, "0.2.0"))
        self.assertEqual(version.read('"""doc"""\n__version__ = "1.4.2"\n'), "1.4.2")


class Hotkeys(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(winapi.parse_combo("alt+numpad7"), [0x12, 0x67])
        self.assertEqual(winapi.parse_combo("Ctrl + Shift + N"), [0x11, 0x10, ord("N")])
        with self.assertRaises(ValueError):
            winapi.parse_combo("alt+nonsense")


if __name__ == "__main__":
    unittest.main()
