"""Protect cost-aware unlock suggestions and the non-collectible reward scope."""
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_unlock_plan as planner


class UnlockPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=planner.build_plan()
        cls.entries={row['achievementId']:row for row in cls.plan['entries']}

    def test_every_existing_guide_target_has_a_unique_suggestion_or_parallel_reminder(self):
        self.assertEqual(len(self.entries),606)
        numbers=sorted(row['unlockRank'] for row in self.entries.values() if row['unlockRank'] is not None)
        self.assertEqual(numbers,list(range(1,len(numbers)+1)))
        for row in self.entries.values():
            self.assertNotEqual(row['unlockRank'] is None,row['parallelOrder'] is None)
            self.assertTrue(row['reason'])
            self.assertTrue(row['evidenceKind'])
            self.assertTrue(math.isfinite(row['priorityScore']))

    def test_all_soul_stones_and_interactive_rewards_are_in_the_resource_recommendations(self):
        for aid in range(618,635):
            self.assertIn('soulstone',self.entries[aid]['rewardTypes'])
        for aid in [601,604,607,609,611,612,613,616,617]:
            self.assertTrue(set(self.entries[aid]['rewardTypes']) & {'interactive','pickup'})
            self.assertTrue(self.entries[aid]['sourceIds'])
        self.assertGreaterEqual(self.plan['resourceCount'],180)

    def test_mixed_rewards_keep_every_category_and_separate_entity_namespaces(self):
        for aid,expected in [(233,{'rune','collectible'}),(415,{'card','collectible'}),(542,{'card'})]:
            self.assertTrue(expected<=set(self.entries[aid]['rewardTypes']))
        self.assertEqual(len([e for e in self.entries[542]['rewardEntities'] if e['entityType']=='card']),2)
        self.assertEqual(self.entries[618]['ensembleReferences'],[])

    def test_new_strength_is_used_without_turning_starting_equipment_into_a_pool_unlock(self):
        self.assertEqual(self.entries[156]['ensembleReferences'][0]['rank'],9)
        self.assertEqual(self.entries[156]['ensembleReferences'][0]['relativeTier'],'S')
        for aid in [108,54,452,198]:self.assertTrue(self.entries[aid]['ensembleReferences'])
        for aid in [248,250]:self.assertEqual(self.entries[aid]['ensembleReferences'],[])

    def test_terminal_rewards_and_real_prerequisites_are_not_promoted_by_raw_strength(self):
        self.assertLess(self.entries[29]['unlockRank'],self.entries[156]['unlockRank'])
        self.assertLess(self.entries[156]['unlockRank'],self.entries[636]['unlockRank'])
        self.assertLess(self.entries[29]['unlockRank'],self.entries[635]['unlockRank'])
        self.assertLess(self.entries[156]['unlockRank'],self.entries[205]['unlockRank'])
        self.assertEqual(self.entries[636]['futureFactor'],0)
        for row in self.entries.values():
            for aid in row['prerequisiteAchievementIds']:
                before=self.entries.get(aid)
                if before and before['unlockRank'] and row['unlockRank']:
                    self.assertLess(before['unlockRank'],row['unlockRank'],(aid,row['achievementId']))

    def test_equal_benefit_is_discounted_for_effort_and_terminal_rewards_have_no_early_gain(self):
        score=planner.priority_score
        self.assertGreater(score(85,20),score(85,80))
        self.assertEqual(score(90,100,future=0),0)
        with self.assertRaises(ValueError):score(80,-1)

    def test_functional_rooms_shop_upgrades_and_drops_are_not_misclassified_as_cosmetics(self):
        for aid in [151,152,153,154,341,406,323,242,240]:
            self.assertNotEqual(self.entries[aid]['rewardTypes'],['completion'])
            self.assertGreater(self.entries[aid]['futureFactor'],0)
        self.assertIn(self.entries[154]['priority'],['strong','recommended'])

    def test_parallel_reminders_do_not_make_keeper_the_first_numbered_target(self):
        self.assertLess(self.entries[4]['unlockRank'],self.entries[251]['unlockRank'])
        self.assertGreaterEqual(self.entries[251]['schedulingPhase'],2)

    def test_deep_routes_record_their_actual_opening_gates(self):
        for aid,gate in [(296,341),(440,407),(441,635),(405,407)]:
            self.assertIn(gate,self.entries[aid]['prerequisiteAchievementIds'])
        self.assertEqual(self.entries[90]['nameEn'],'Jera')


if __name__=='__main__':unittest.main()
