"""Protect research coverage, provenance and parity with the editable priorities."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_research_rankings import validate


class ResearchRankingsTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "tools/research_rankings.json").read_text("utf-8"))

    def test_public_source_validates(self):
        validate(self.data)

    def test_duplicate_ranks_and_two_positions_are_rejected(self):
        numbered = [x for x in self.data["entries"] if x["unlockRank"]]
        numbered[1]["unlockRank"] = numbered[0]["unlockRank"]
        with self.assertRaisesRegex(RuntimeError, "duplicate numbered"):
            validate(self.data)
        self.setUp()
        self.data["entries"][0]["unlockRank"] = 1
        with self.assertRaisesRegex(RuntimeError, "Exactly one"):
            validate(self.data)

    def test_research_cannot_disagree_with_the_runtime_priority(self):
        entry = next(x for x in self.data["entries"] if x["achievementId"] == 231)
        entry["priority"] = "strong"
        with self.assertRaisesRegex(RuntimeError, "disagree"):
            validate(self.data)

    def test_missing_provenance_and_unsafe_source_links_are_rejected(self):
        for mutation in (lambda data: data["entries"][0].update(sourceIds=["unknown"]),
                         lambda data: data["sources"][0].update(url="javascript:alert(1)")):
            invalid = copy.deepcopy(self.data)
            mutation(invalid)
            with self.assertRaises(RuntimeError):
                validate(invalid)

    def test_a_collectible_only_community_rank_cannot_be_assigned_to_a_trinket(self):
        entry = next(x for x in self.data["entries"] if x["achievementId"] == 336)
        entry["communityReference"] = {"sourceId": "RT1", "rank": 1, "itemVoterCount": 100}
        with self.assertRaisesRegex(RuntimeError, "collectible preference"):
            validate(self.data)


if __name__ == "__main__":
    unittest.main()
