# Full community ranking coverage

The user correctly identified that the collected 719-entry source was only exposed through 36 community references inside 65 editorial reviews. Community coverage must be independent of editorial review status and acquisition advice.

- [x] Add failing regressions for unreviewed screenshot examples and all source entries.
- [x] Preserve all719 source entries, their original ranks and vote counts. Map718 distinct collectible IDs; explicitly retain the legacy Tonsil row without assigning a current entity.
- [x] Associate271 confirmed collectible-unlock targets independently of65 editorial reviews. Exclude starting-equipment upgrades; show each item in multi-reward targets and sort by the best source position.
- [x] Show community ranks in all existing views, with a separate unreviewed acquisition label.
- [x] Add the searchable 道具总榜 tab, matching the original visual style, with links to guide targets and save progress.
- [x] Document full source provenance, mapping exceptions and the difference between community positions and editorial unlock advice.
- [x] Rebuild the offline artifact; verify normal/offline UI, save sync, category filters, ranking order and custom profiles.
- [x] Obtain independent read-only review and address findings; prepare the reviewed change for publication to the same fork branch.

Keep project/runtime artifacts on E:, user saves read-only, personal configuration ignored, and editorial priority choices unchanged by the newly imported community positions.

Validation:17 Node tests,11 Python tests, priorities validation, normal/offline full-board browser checks, ranking/guide/profile regression checks and bound-save synchronization passed. Independent review verified every source UUID/rank/vote against the original719-row snapshot and718 entity mappings against EID. A short-ID jump issue found during review was fixed with explicit `#ID` matching and regressions for #6/#44.

Publication verification: after committing and uploading, require a matching local/remote tree and a clean working tree before reporting completion. No PR or direct changes to the upstream default branch.
