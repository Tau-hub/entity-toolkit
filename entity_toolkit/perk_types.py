"""What a perk does, in plain words ("Generator slowdown", "Aura reading", "Healing"...), so perks can be searched by type.

A perk gets a type when the wiki tagged it with one of the type's tags (the wiki tags every perk with the mechanics it touches) or when its
text matches the type's pattern. The rules below are a best effort: `data/perk_types.json` holds your own corrections, which replace the
automatic types of the perks they name ({"Perk name": ["type id", ...]}).
"""
import json
import re

from . import paths

# id, label, group, sides ("K" killer perks, "S" survivor perks), wiki tags, text pattern (case-insensitive, on the description)
TYPES = [
    # ---- generators
    ("gen-slowdown", "Generator slowdown", "Generators", "K", {"Regression", "GenBlocker", "ProgressionPenalty", "RepairingProficiency"},
     r"regress|(blocked|block|blocks|blocking)\b[^.]{0,70}generator|generator[^.]{0,70}\bblocked|(lose|loses|lost)\b[^.]{0,40}(repair|progress)|repair(ing)? (speed|progress)[^.]{0,40}(reduc|decreas|slow)"),
    ("gen-speed", "Repairing generators", "Generators", "S", {"RepairingProficiency", "BonusProgression"},
     r"repair(ing)? (speed|progress)|generator[^.]{0,40}(faster|speed|progress)|repairs? a generator"),
    ("gen-skillcheck", "Skill checks", "Generators", "KS", {"SkillChecks"}, r"skill check"),
    # ---- information
    ("aura", "Aura reading", "Information", "KS", {"Auras"}, r"\baura"),
    ("tracking", "Tracking", "Information", "KS", {"ScratchMarks", "PoolsOfBlood"}, r"scratch mark|pools? of blood|footprint"),
    ("notifications", "Notifications & noise", "Information", "KS", {"LoudNoiseNotifications", "Screams", "GruntsOfPain", "ActionNoise", "ConspicuousActions", "Warning", "Crows"},
     r"notification|loud noise|\bscream|grunt"),
    ("mindgames", "Mind games & deception", "Information", "KS", {"Deception"}, r"false|illusion|decoy"),
    # ---- chase and movement
    ("chase", "Chase & speed boosts", "Chase & movement", "KS", {"Haste", "Chase"}, r"\bhaste\b|movement speed"),
    ("exhaustion", "Exhaustion & endurance", "Chase & movement", "KS", {"Exhausted", "Endurance"}, r"exhaust|endurance"),
    ("terror", "Terror radius", "Chase & movement", "KS", {"TerrorRadius"}, r"terror radius"),
    ("attacks", "Attacks & lunges", "Chase & movement", "K", {"AttackCooldown", "Lunge", "ActionPause"}, r"lunge|basic attack"),
    ("loops", "Pallets & windows", "Chase & movement", "KS", {"Pallets", "Windows", "WindowBlocker", "Vaulting", "BreakableWalls", "VaultLocations"},
     r"\bpallet|window|vault"),
    ("action-speed", "Action speed", "Chase & movement", "KS", {"ActionSpeed"}, r"action speed"),
    ("stuns", "Stuns & blinds", "Chase & movement", "S", {"KillerStun", "KillerBlind"}, r"\bstun|blind(ed|s)? the killer"),
    ("stun-resist", "Stun & blind resistance", "Chase & movement", "K", {"KillerStun", "KillerBlind"}, r"\bstun|blind"),
    ("escape", "Escaping a carry or a hook", "Chase & movement", "S", {"Wiggle", "Carrying"}, r"wiggle|being carried|struggle"),
    # ---- healing and injuries
    ("carry", "Carrying & wiggling", "Hooks & rescue", "K", {"Carrying", "Wiggle"}, r"carry|carrying|wiggle"),
    ("healing", "Healing", "Healing & injuries", "S", {"Healing", "HealingProficiency", "Recovering"}, r"\bheal"),
    ("anti-heal", "Anti-healing & injuries", "Healing & injuries", "K", {"Healing", "HealingProficiency", "Broken", "DeepWound", "InjuredState", "Recovering"},
     r"\bheal|deep wound|injur"),
    # ---- hooks and rescue
    ("hooks", "Hooks & sacrifice", "Hooks & rescue", "K", {"Hooks", "ScourgeHooks", "Basement"}, r"\bhook"),
    ("unhook", "Unhooking & rescue", "Hooks & rescue", "S", {"Hooks"}, r"unhook|rescue"),
    # ---- status effects
    ("exposed", "Exposed", "Status effects", "KS", {"Exposed"}, r"\bexposed"),
    ("hindered", "Hindered", "Status effects", "KS", {"Hindered"}, r"\bhindered"),
    ("oblivious", "Oblivious", "Status effects", "KS", {"Oblivious"}, r"\boblivious"),
    ("blindness", "Blindness", "Status effects", "KS", {"Blindness"}, r"blindness"),
    ("status-resist", "Status resistance", "Status effects", "S", set(), ""),  # perks that shorten negative statuses: only by your own correction
    ("broken", "Broken", "Status effects", "KS", {"Broken"}, r"\bbroken"),
    ("undetectable", "Stealth & undetectable", "Status effects", "KS", {"Stealth", "Undetectable", "Elusive"}, r"undetectable|stealth|elusive|terror radius"),
    # ---- totems and hexes
    ("hex", "Hexes", "Totems", "K", {"Hex"}, r"\bhex\b"),
    ("totems", "Totems & boons", "Totems", "S", {"Totems", "Boon", "Blessing", "Cleansing"}, r"totem|boon|cleans|bless"),
    # ---- the rest
    ("endgame", "Endgame", "Other", "KS", {"ExitGates"}, r"exit gate|endgame"),
    ("items", "Items & chests", "Other", "KS", {"Items", "Chests"}, r"\bitem|\bchest|toolbox|med-?kit"),
    ("teamwork", "Teamwork", "Other", "S", {"Teamwork"}, r"other survivors?"),
    ("obsession", "The Obsession", "Other", "KS", {"Obsession"}, r"obsession"),
    ("tokens", "Tokens & stacking", "Other", "KS", {"Tokens"}, r"\btokens?\b"),
    ("lockers", "Lockers", "Other", "KS", {"Lockers"}, r"\blocker"),
]
_BY_ID = {t[0]: t for t in TYPES}

# other words people use for a type, so that searching "gen regression" or "heal" finds it
ALIASES = {
    "gen-slowdown": "gen regression regress slowdown block blocker kick pressure",
    "gen-speed": "gen repair fast speed progress",
    "gen-skillcheck": "skill check great success",
    "aura": "aura reveal wallhack information see",
    "tracking": "scratch marks pools blood track",
    "notifications": "notification noise scream loud grunt alert",
    "mindgames": "mind game deception fake decoy",
    "chase": "chase speed haste boost movement",
    "exhaustion": "exhausted exhaustion endurance sprint burst",
    "terror": "terror radius heartbeat",
    "attacks": "attack lunge cooldown hit",
    "carry": "carry carrying wiggle strafe",
    "status-resist": "status resistance resist shorten cleanse effects",
    "loops": "pallet window vault loop",
    "action-speed": "action speed vault open cleanse sabotage",
    "stuns": "stun blind pallet flashlight",
    "stun-resist": "stun blind resist",
    "escape": "escape wiggle carry struggle",
    "healing": "heal healing rebirth recover medkit",
    "anti-heal": "anti heal deep wound injured mend",
    "hooks": "hook sacrifice scourge basement",
    "unhook": "unhook rescue save rebirth",
    "exposed": "exposed one shot",
    "hindered": "hindered slow",
    "oblivious": "oblivious terror radius",
    "blindness": "blindness blind",
    "broken": "broken no healing",
    "undetectable": "stealth undetectable terror radius quiet",
    "hex": "hex totem",
    "totems": "totem boon cleanse bless",
    "endgame": "endgame exit gates",
    "items": "item chest toolbox medkit flashlight key map",
    "teamwork": "team others",
    "obsession": "obsession",
    "tokens": "tokens stack",
    "lockers": "locker hide",
}


def applies(t, side):
    return side in t[3]


def classify(perk, side):
    """Type ids of one perk ({"name", "desc", "tags"}) for side 'K' or 'S'."""
    tags = set(perk.get("tags") or [])
    desc = perk.get("desc") or ""
    out = []
    for tid, _label, _group, sides, wiki_tags, pattern in TYPES:
        if side not in sides:
            continue
        if tags & wiki_tags or (pattern and re.search(pattern, desc, re.I) and (not tags or tags & wiki_tags or _text_only_ok(tid))):
            out.append(tid)
    return out


# types whose text pattern alone is reliable enough even when the wiki gave the perk other tags
_TEXT_OK = {"gen-slowdown", "exposed", "hindered", "oblivious", "blindness", "broken", "hex", "tracking", "obsession"}


def _text_only_ok(tid):
    return tid in _TEXT_OK


def overrides():
    try:
        return json.loads(paths.PERK_TYPES.read_text(encoding="utf8"))
    except Exception:
        return {}


def save_override(name, type_ids):
    """Records your own types for a perk (an empty list removes the correction and returns to the automatic types)."""
    data = overrides()
    if type_ids is None:
        data.pop(name, None)
    else:
        data[name] = [t for t in type_ids if t in _BY_ID]
    paths.ensure()
    paths.PERK_TYPES.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf8")


def resolve_copies(perks):
    """Renamed perks are described as "Identical to Other perk.": they get the tags and text of the perk they copy."""
    by_name = {p["name"]: p for p in perks}
    out = []
    for p in perks:
        m = re.match(r"Identical to (.+?)\.?$", (p.get("desc") or "").strip())
        src = by_name.get(m.group(1)) if m else None
        out.append({**p, "desc": src.get("desc", ""), "tags": src.get("tags", [])} if src else p)
    return out


def perk_types(perk, side, over=None):
    over = overrides() if over is None else over
    if perk["name"] in over:
        return [t for t in over[perk["name"]] if t in _BY_ID and applies(_BY_ID[t], side)]
    return classify(perk, side)


def catalog(side, perks, over=None):
    """The types that exist for a side with how many perks have each: [{"id", "label", "group", "count"}], biggest group order kept as in TYPES."""
    over = overrides() if over is None else over
    counts = {}
    for p in perks:
        for t in perk_types(p, side, over):
            counts[t] = counts.get(t, 0) + 1
    return [{"id": t[0], "label": t[1], "group": t[2], "count": counts.get(t[0], 0)} for t in TYPES if applies(t, side) and counts.get(t[0], 0)]
