# Research rankings implementation plan

> **For agentic workers:** Execute inline, with a read-only reviewer before publishing. Steps use checkbox syntax for tracking.

**Goal:** Add visible, sortable research rankings and revise existing priorities for efficient all-character completion, using the already reviewed evidence.

**Architecture:** Keep the dependency-free app, existing data builders and profile storage. Add a public research data file and a pure ranking model. Rankings stay independent of editable priority colors; untouched built-ins refresh and custom profiles remain intact.

**Tech Stack:** Plain JavaScript, Python standard library builders/tests, Node built-in tests, Playwright CLI.

**Spec:** The user's 2026-11-04 requests in this chat authorize rankings and corrections to original priorities, using the prior research and all-character completion objective.

## Constraints

- Keep all project/runtime artifacts on E: and reuse the current feature branch.
- Preserve the original visual style, category combinations, save binding and offline use.
- Cover the 65 reviewed targets, with 55 numbered unlock suggestions and 10 parallel tasks. Do not invent ranks for the remaining 541 targets.
- Numbered suggestions express acquisition priority, not a dependency-complete walkthrough or statistical optimum. Parallel tasks are not prerequisites for starting the numbered list.
- Community rankings retain source, denominator, snapshot date, version and vote count. They measure preference, not win rate or multi-source consensus.
- Keep personal custom profiles and saves intact. Publish to the existing fork branch without opening a PR.

## Steps

- [x] Add failing model tests for numbered vs parallel vs unreviewed sorting, null handling, community ranking, stable filtering and static rank labels.
- [x] Build editable `tools/research_rankings.json` from the reviewed research, add validated compilation in `tools/build_research_rankings.py`, and generate `data/research_rankings.js`.
- [x] Revise reviewed priorities in the existing character, challenge and other-achievement sources. Record old/new values and justifications with the research; compile profiles.
- [x] Implement `js/rankings.js` and extend `js/guide.js` with a comparator for ranking modes. Integrate both sorts, compact rank/strength labels and expandable evidence into every existing list.
- [x] Add browser regression coverage for ranking order, combinable categories, fixed rank labels after filtering, custom priority preservation and both normal/offline pages.
- [x] Run builders and validations, Node/Python tests, targeted browser checks and the existing guide/offline checks. Obtain a read-only final review before committing and pushing to the existing fork branch.

## Result

Validated 65 reviewed targets, 55 numbered suggestions, 10 parallel tasks, 36 original community references and 18 priority corrections. Independent review found no critical or important issues; generated data and the offline artifact match their sources. Publication uses the existing `feat/complete-guide-local-save` fork branch and requires a matching local/remote SHA after push.

## Verification commands

```powershell
node --test tests/guide.test.cjs tests/rankings.test.cjs tests/local-server.test.cjs
python -m unittest discover -s tests -p test_recommendation_profiles.py
python tools/validate_priorities.py
python tools/build_research_rankings.py
python tools/build_recommendation_profiles.py
python tools/prepare_publish.py 20261104-rankings1
```

Use an isolated Edge profile with Playwright CLI for `tests/rankings-smoke.js`, `tests/browser-smoke.js`, `tests/ratings-smoke.js` and `tests/offline-smoke.js`. Confirm no external asset requests in the offline artifact and no personal data in the commit.
