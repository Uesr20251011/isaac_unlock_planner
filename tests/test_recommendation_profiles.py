"""Regression checks for adding researched achievements without changing old ratings."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("profiles", ROOT / "tools/build_recommendation_profiles.py")
profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiles)


class AchievementProfilesTest(unittest.TestCase):
    def compile(self, entries=None):
        # Keep temporary output on the project's drive.
        (ROOT / ".local").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as folder:
            folder = Path(folder)
            manifest = json.loads(profiles.MANIFEST.read_text("utf-8"))
            item = manifest["profiles"][0]
            item.pop("achievementFile", None)
            if entries is not None:
                source = folder / "achievements.json"
                source.write_text(json.dumps({"entries": entries}), "utf-8")
                item["achievementFile"] = str(source)
            manifest_path = folder / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), "utf-8")
            output = folder / "profiles.js"
            with patch.object(profiles, "MANIFEST", manifest_path), patch.object(profiles, "OUT", output):
                profiles.main()
            return json.loads(output.read_text("utf-8").split(" = ", 1)[1].rstrip(";\n"))["profiles"][0]

    def test_achievement_file_is_optional_for_existing_profiles(self):
        result = self.compile()
        self.assertEqual(result.get("achievements"), [])
        for key, filename in [("characterBoss", "recommendation_seed.json"), ("challenges", "challenge_priority.json")]:
            expected = json.loads((ROOT / "tools" / filename).read_text("utf-8"))["entries"]
            self.assertEqual(result[key], expected)

    def test_achievement_ratings_reach_the_browser_bundle(self):
        entries = [{"achievementId": 354, "priority": "strong"}, {"achievementId": 336, "priority": "recommended"}]
        self.assertEqual(self.compile(entries).get("achievements"), entries)

    def test_invalid_duplicate_or_already_rated_targets_are_rejected(self):
        for entries in [
            [{"achievementId": 9999, "priority": "strong"}],
            [{"achievementId": 354, "priority": "invalid"}],
            [{"achievementId": 354, "priority": "strong"}] * 2,
            [{"achievementId": 199, "priority": "strong"}],  # Shared character rule.
            [{"achievementId": 103, "priority": "strong"}],  # Existing challenge.
        ]:
            with self.subTest(entries=entries), self.assertRaises(RuntimeError):
                self.compile(entries)

    def test_shipped_ratings_have_research_and_match_the_generated_bundle(self):
        manifest = json.loads(profiles.MANIFEST.read_text("utf-8"))
        bundle = profiles.read_data("recommendation_profiles.js")
        for item, built in zip(manifest["profiles"], bundle["profiles"]):
            source = json.loads((ROOT / "tools" / item["achievementFile"]).read_text("utf-8"))
            self.assertEqual(built["achievements"], source["entries"])
            self.assertEqual({x["achievementId"] for x in source["reviews"]},
                             {x["achievementId"] for x in source["entries"]})
            source_ids = {x["id"] for x in source["sources"]}
            for review in source["reviews"]:
                self.assertTrue(review["strength"] and review["reason"] and review["caveat"])
                self.assertTrue(review["sourceIds"])
                self.assertTrue(set(review["sourceIds"]) <= source_ids)


if __name__ == "__main__":
    unittest.main()
