#!/usr/bin/env python3
"""Validate and compile the public research snapshot; no network or save access."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit
from build_recommendation_profiles import read_data, read_json, ALLOWED
from crawl_effects import MULTI_REWARD_BUNDLES

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/research_rankings.json"
OUT = ROOT / "data/research_rankings.js"
COMMUNITY = ROOT / "tools/community_rankings.json"


def build_community(source: dict, research: dict) -> tuple[list, list]:
    items = source["entries"]
    if len(items) != source["total"] or sorted(x["rank"] for x in items) != list(range(1, source["total"] + 1)):
        raise RuntimeError("Community snapshot has missing or duplicate ranks")
    ids, source_ids = set(), set()
    for item in items:
        cid = item["collectibleId"]
        if cid is None:
            if not item.get("mappingNote"):
                raise RuntimeError("Unmapped community item needs an explanation")
        elif type(cid) is not int or cid < 1 or cid in ids:
            raise RuntimeError(f"Invalid or duplicate community collectible: {cid}")
        else:
            ids.add(cid)
        if item["sourceItemId"] in source_ids or not item["name"] or not item["nameZh"]:
            raise RuntimeError("Invalid community item identity")
        source_ids.add(item["sourceItemId"])
        if type(item["itemVoterCount"]) is not int or item["itemVoterCount"] < 1:
            raise RuntimeError("Invalid community vote count")
    if (source["total"] != research["community"]["total"] or
            source["snapshotDate"] != research["community"]["snapshotDate"] or
            source["gameVersion"] != research["community"]["version"]):
        raise RuntimeError("Community source metadata disagrees with research")
    by_item = {item["collectibleId"]: item for item in items if item["collectibleId"] is not None}
    for entry in research["entries"]:
        reference = entry.get("communityReference")
        if reference:
            item = by_item.get(entry["entityId"])
            if not item or any(item[key] != reference[key] for key in ("rank", "itemVoterCount")):
                raise RuntimeError(f"Reviewed community reference disagrees with snapshot: {entry['achievementId']}")

    effects = read_data("effects.js")["entries"]
    targets = {}
    excluded = {(x["achievementId"], x["collectibleId"]) for x in source.get("excludedAssociations", [])}
    def add(aid, cids):
        if aid in source.get("excludedTargets", []):
            return
        for cid in cids:
            if (aid, cid) in excluded:
                continue
            if cid not in by_item:
                raise RuntimeError(f"Project collectible {cid} for achievement {aid} has no community mapping")
            targets.setdefault(aid, set()).add(cid)
    def effect_ids(aid, value):
        if value.get("entityType") == "collectible" and type(value.get("entityId")) is int:
            return [value["entityId"]]
        return [cid for _, category, cid in MULTI_REWARD_BUNDLES.get(str(aid), {}).get("parts", []) if category == "collectible"]
    for rule in read_data("unlocks.js")["unlockRules"]:
        aid = rule["achievementId"]
        add(aid, effect_ids(aid, effects.get(str(aid), {})))
    for challenge in read_data("challenges.js")["entries"]:
        aid = challenge["rewardAchievementId"]
        add(aid, effect_ids(aid, challenge))
    achievements = read_data("achievements.js")
    lists = [achievements["main"], achievements["characters"]["normal"], achievements["characters"]["tainted"],
             achievements["cumulative"], achievements["completion"]]
    for group in lists:
        for entry in group:
            add(entry["achievementId"], entry.get("collectibleIds", []))
    associations = [{"achievementId": aid, "collectibleIds": sorted(cids)} for aid, cids in sorted(targets.items())]
    return items, associations


def validate(data: dict) -> None:
    unlocks, challenges, achievements = (read_data(name + ".js") for name in ("unlocks", "challenges", "achievements"))
    rules = {x["achievementId"]: x for x in unlocks["unlockRules"]}
    challenge_by_id = {x["rewardAchievementId"]: x for x in challenges["entries"]}
    lists = [achievements["main"], achievements["characters"]["normal"], achievements["characters"]["tainted"],
             achievements["cumulative"], achievements["completion"]]
    valid_ids = set(rules) | set(challenge_by_id) | {x["achievementId"] for group in lists for x in group}
    pairs = {(x["characterId"], x["bossId"]): x["priority"] for x in read_json(ROOT / "tools/recommendation_seed.json")["entries"]}
    challenge_priority = {x["challengeId"]: x["priority"] for x in read_json(ROOT / "tools/challenge_priority.json")["entries"]}
    other_priority = {x["achievementId"]: x["priority"] for x in read_json(ROOT / "tools/achievement_priority.json")["entries"]}
    source_ids = set()
    for source in data["sources"]:
        if source["id"] in source_ids or urlsplit(source["url"]).scheme not in {"http", "https"}:
            raise RuntimeError(f"Invalid or duplicate research source: {source}")
        source_ids.add(source["id"])
    seen, numbered, parallel = set(), [], []
    for entry in data["entries"]:
        aid = entry["achievementId"]
        if type(aid) is not int or aid not in valid_ids or aid in seen:
            raise RuntimeError(f"Invalid or duplicate researched achievement: {aid}")
        seen.add(aid)
        rank, concurrent = entry.get("unlockRank"), entry.get("parallelOrder")
        if (rank is None) == (concurrent is None):
            raise RuntimeError(f"Exactly one numbered/parallel position is required: {aid}")
        position = concurrent if rank is None else rank
        if type(position) is not int or position < 1:
            raise RuntimeError(f"Invalid research rank: {aid}")
        (parallel if rank is None else numbered).append(position)
        if not entry["sourceIds"] or not set(entry["sourceIds"]) <= source_ids:
            raise RuntimeError(f"Unknown research source for: {aid}")
        if entry["phase"] not in {"P0", "P1", "P2", "P3", "P4"}:
            raise RuntimeError(f"Invalid phase: {aid}")
        if any(not entry.get(field) for field in ("strength", "confidence", "condition", "reason", "caveat")):
            raise RuntimeError(f"Missing research explanation: {aid}")
        if entry["priority"] not in ALLOWED or entry["previousPriority"] not in ALLOWED:
            raise RuntimeError(f"Invalid priority: {aid}")
        if entry["priority"] != entry["previousPriority"] and not entry.get("correctionReason"):
            raise RuntimeError(f"Missing correction explanation: {aid}")
        rule = rules.get(aid)
        challenge = challenge_by_id.get(aid)
        actual = {pairs.get((rule["characterId"], boss), "normal") for boss in rule["bossIds"]} if rule else {
            challenge_priority.get(challenge["challengeId"], "normal") if challenge else other_priority.get(aid, "normal")}
        if actual != {entry["priority"]}:
            raise RuntimeError(f"Research and runtime priorities disagree for #{aid}: {actual}")
        community = entry.get("communityReference")
        if community:
            if (entry["entityType"] != "collectible" or entry["strength"] == "—" or
                    community["sourceId"] not in source_ids or type(community["rank"]) is not int or
                    not 1 <= community["rank"] <= data["community"]["total"] or
                    type(community["itemVoterCount"]) is not int or community["itemVoterCount"] < 1):
                raise RuntimeError(f"Invalid collectible preference reference: {aid}")
    for name, ranks in [("numbered", numbered), ("parallel", parallel)]:
        if sorted(ranks) != list(range(1, len(ranks) + 1)):
            raise RuntimeError(f"Non-contiguous or duplicate {name} ranks")


def main() -> None:
    data = read_json(SOURCE)
    validate(data)
    data["communityItems"], data["communityTargets"] = build_community(read_json(COMMUNITY), data)
    OUT.write_text("// Generated by tools/build_research_rankings.py. Do not edit by hand.\n"
                   "window.ISAAC_RESEARCH_RANKINGS = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", "utf-8")
    print(json.dumps({"reviewed": len(data["entries"]),
                      "numbered": sum(x["unlockRank"] is not None for x in data["entries"]),
                      "parallel": sum(x["parallelOrder"] is not None for x in data["entries"]),
                      "priorityCorrections": sum(x["priority"] != x["previousPriority"] for x in data["entries"]),
                      "communityItems": len(data["communityItems"]),
                      "communityTargets": len(data["communityTargets"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
