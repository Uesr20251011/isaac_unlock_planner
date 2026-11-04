# Third-party data attribution

This project combines several independently maintained data sources at build time.

- **Huiji Wiki / 以撒的结合中文维基**: character × completion-target × achievement-ID matrix, plus the challenge ID × prerequisite-achievement × reward-achievement table, supplied to this project as a saved HTML page by the user.
- **Bilibili unlock recommendation post**: 狐九郎整理的《【以撒的结合】v 9.10 更新版-萌新向人物道具解锁优先顺序（搬运整理）》：`https://www.bilibili.com/opus/1083165871339208713`. 其中 v 9.10 推荐数据来自 @UP主 陈哥1，最初版与 v 9.10 最新修订参考 @UP主 恺恺orz（`https://www.bilibili.com/video/BV11pj7zEEHL`）。本项目还叠加了用户在对话中提供的当前版本修订。
- **IsaacGuru Challenges**: used as an auxiliary English-name cross-check for challenge rewards (`https://isaacguru.com/challenges`).
- **External Item Descriptions (EID)**: Simplified-Chinese effect data used by the build-time effect generator. The effect builder also indexes the English EID packs first when a reward cannot be matched reliably by Chinese name, then resolves the same entity ID back to the Simplified-Chinese description.
- **Unduel item ranking**: the full 719-entry community preference snapshot dated 2026-10-28, labelled Repentance, from [the original ranked list](https://unduel.com/t/the-binding-of-isaac-rebirth/the-binding-of-isaac-items-75IgVOPw3H343hrv6Vh4MP/ranked-list). `tools/community_rankings.json` retains source item UUIDs, global ranks and per-item vote counts; community positions are displayed separately from editorial unlock recommendations. One legacy Tonsil entry remains explicitly unmapped.
- **EID item names**: Chinese/English names and entity-ID cross-checks for the community list use the public AB+, Repentance and Repentance+ language packs in [wofsauge/External-Item-Descriptions](https://github.com/wofsauge/External-Item-Descriptions). Only item names and IDs are added to this snapshot; no new image assets are included.
- **IsaacGuru-hosted image URLs**: some pre-existing character/reward image metadata in `data/unlocks.js`; when both local and remote reward images fail, the app simply hides the image.
- **Boss artwork**: the 13 Boss selector images bundled in the project were supplied directly by the user.
- **Achievement sprite**: the 1280×2112 achievement sprite bundled in `assets/achievement/Achievement_sprite.jpg` was supplied directly by the user; the app treats it as a 20×33 grid of 64×64 cells and uses `achievementId - 1` as the sprite index.

The save parser was implemented from the `Persistentgamedata.js` file supplied by the user. Runtime save parsing is local-only.

Before redistributing or publishing a derived build, review the current upstream terms and attribution requirements for every third-party data/image source you include.
