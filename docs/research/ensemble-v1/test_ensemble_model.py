"""Research model regressions: do not silently turn missingness into losses."""
import copy
import unittest
import numpy as np
import ensemble_model as model
from ensemble_model import assemble_sources, fit_model, objective_gradient, model_scores


def source(sid, levels, **metadata):
    return dict(id=sid, family=sid, basis='strength', quality=1.0,
                relevance=1.0, version=1.0,
                entries=[dict(id=cid, level=level) for cid,level in levels], **metadata)


class EnsembleModelTest(unittest.TestCase):
    def test_one_complete_order_stays_in_order(self):
        c,t,audit = assemble_sources([source('full', [(1,1),(2,2),(3,3),(4,4)])], [1,2,3,4])
        fit = fit_model(c,t)
        self.assertTrue(fit['converged'])
        self.assertLess(fit['gradientMax'], 1e-6)
        self.assertTrue(all(np.diff(fit['theta']) < 0))
        scores = model_scores(fit['theta'])
        self.assertTrue(all(np.diff(scores) < 0))
        self.assertAlmostEqual(float(np.mean(scores)), 50)

    def test_unequal_exposure_does_not_reorder_an_unchallenged_complete_list(self):
        poll=source('poll',[(i,i) for i in range(1,31)])
        for entry in poll['entries']: entry['votes']=1 if entry['id']==1 else 100000
        c,t,_=assemble_sources([poll],list(range(1,31)))
        fit=fit_model(c,t)
        self.assertTrue(fit['converged'])
        self.assertTrue(all(np.diff(fit['theta'])<0))

    def test_a_local_list_has_no_observations_against_unlisted_items(self):
        c,t,audit = assemble_sources([source('angel',[(2,1),(3,2)])], [1,2,3,4])
        self.assertEqual(float(c[0].sum()), 0)
        self.assertEqual(float(c[3].sum()), 0)
        self.assertGreater(t[1,2], 0)
        self.assertEqual(t[2,1], 0)
        self.assertEqual(audit['observedIds'], [2,3])

    def test_partial_coverage_does_not_receive_a_full_global_source_budget(self):
        partial=source('local',[(1,1),(2,2)])
        c,t,audit=assemble_sources([partial],list(range(1,102)))
        self.assertAlmostEqual(float(c[0].sum()),.1)
        self.assertAlmostEqual(audit['sources'][0]['coverageFactor'],.1)

    def test_same_tier_does_not_invent_internal_comparisons(self):
        c,t,audit = assemble_sources([source('tiers',[(1,1),(2,1),(3,2)])], [1,2,3])
        self.assertEqual(c[0,1], 0)
        self.assertGreater(t[0,2], 0)
        self.assertGreater(t[1,2], 0)
        self.assertLessEqual(float(c.sum(axis=1).max()), 1)

    def test_duplicates_in_the_same_source_family_do_not_add_weight(self):
        original = source('original',[(1,1),(2,2),(3,3)])
        repost = copy.deepcopy(original)
        repost['id'] = 'repost'
        a = assemble_sources([original], [1,2,3])
        b = assemble_sources([original,repost], [1,2,3])
        np.testing.assert_array_equal(a[0], b[0])
        np.testing.assert_array_equal(a[1], b[1])
        self.assertEqual(b[2]['familyCount'],1)

    def test_a_derived_sublist_of_the_same_family_is_redundant(self):
        original=source('original',[(1,1),(2,2),(3,3),(4,4),(5,5)])
        subset=source('subset',[(1,1),(2,2)])
        subset['family']='original'
        a=assemble_sources([original],[1,2,3,4,5])
        b=assemble_sources([original,subset],[1,2,3,4,5])
        np.testing.assert_array_equal(a[0],b[0])
        np.testing.assert_array_equal(a[1],b[1])

    def test_ties_keep_a_rank_interval_and_do_not_break_a_grade_boundary_by_input_order(self):
        self.assertTrue(callable(getattr(model,'rank_summary',None)))
        ranks,low,high=model.rank_summary(np.array([3.,2.,2.,1.]))
        np.testing.assert_array_equal(ranks,[1,2.5,2.5,4])
        np.testing.assert_array_equal(low,[1,2,2,4])
        np.testing.assert_array_equal(high,[1,3,3,4])
        self.assertEqual(model.relative_tiers(1,2,20),['S','A'])

    def test_several_lists_from_one_author_share_one_per_item_budget(self):
        first=source('part-a',[(1,1),(2,2)])
        second=source('part-b',[(1,1),(3,2)])
        first['family']=second['family']='one-author'
        c,t,audit=assemble_sources([first,second],[1,2,3])
        self.assertLessEqual(float(c.sum(axis=1).max()),1)

    def test_incompatible_versions_and_unlock_order_do_not_become_strength_votes(self):
        old = source('old',[(1,1),(2,2)])
        old['entries'][0]['version']=0
        c,t,_ = assemble_sources([old], [1,2])
        self.assertEqual(c.sum(), 0)
        route = source('route', [(1,1),(2,2)])
        route['basis']='unlock-order'
        with self.assertRaises(ValueError):
            assemble_sources([route], [1,2])
        route['family']='original'
        with self.assertRaises(ValueError):
            assemble_sources([source('original',[(1,1),(2,2)]),route], [1,2])

    def test_sample_weight_saturates_and_never_counts_a_whole_list_as_independent_people(self):
        low = source('low',[(1,1),(2,2)])
        high = copy.deepcopy(low)
        high['id']=high['family']='high'
        for item in low['entries']: item['votes']=50
        for item in high['entries']: item['votes']=200
        a = assemble_sources([low], [1,2])[0][0,1]
        b = assemble_sources([high], [1,2])[0][0,1]
        self.assertAlmostEqual(b/a, np.sqrt(1.6))

    def test_zero_exposure_is_missing_evidence_rather_than_a_middle_grade(self):
        poll=source('poll',[(1,1),(2,2),(3,3)])
        poll['entries'][0]['votes']=0
        c,t,audit=assemble_sources([poll],[1,2,3])
        self.assertEqual(float(c[0].sum()),0)
        self.assertEqual(audit['observedIds'],[2,3])

    def test_gradient_matches_finite_differences(self):
        c,t,_ = assemble_sources([source('full',[(1,1),(2,2),(3,3)])],[1,2,3])
        theta = np.array([.4,-.3,.1])
        loss, grad = objective_gradient(theta,c,t,.03)
        eps=1e-6
        numerical=[]
        for i in range(3):
            delta=np.zeros(3); delta[i]=eps
            numerical.append((objective_gradient(theta+delta,c,t,.03)[0]-objective_gradient(theta-delta,c,t,.03)[0])/(2*eps))
        np.testing.assert_allclose(grad,numerical,atol=1e-7)


if __name__ == '__main__':
    unittest.main()
