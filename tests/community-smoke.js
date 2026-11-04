// Use an isolated browser profile; restore its original local storage afterwards.
async page => {
  const storage = await page.evaluate(() => Object.fromEntries(Object.entries(localStorage)));
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/*', route => route.abort());
  const check = (value, message) => { if (!value) throw new Error(message); };
  try {
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    const expected = await page.evaluate(() => {
      const index = IsaacRankings.createIndex(ISAAC_RESEARCH_RANKINGS);
      return [108,54,452,198].map(id => ({ id, rank: index.communityFor(id)[0].rank }));
    });
    for (const { id, rank } of expected) {
      const row = page.locator(`[data-guide-achievement="${id}"]`);
      check((await row.innerText()).includes(`社区 #${rank}/719`), `Achievement ${id} must show its existing full-list rank`);
      check((await row.innerText()).includes('尚未综合复核'), 'Community coverage must not pretend to be an editorial review');
      check(!(await row.innerText()).includes('暂无排名'), 'Known community ranks must not be labelled missing');
    }
    await page.getByRole('button', { name: '社区强度', exact: true }).click();
    const ranked = page.locator('[data-guide-achievement] [data-community-rank]');
    check(await ranked.count() === 271, 'All confirmed collectible-unlock targets must have community coverage');
    const ranks = await ranked.evaluateAll(nodes => nodes.map(node => Number(node.dataset.communityRank)));
    check(ranks.every((rank,i) => !i || rank >= ranks[i-1]), 'Community sort must include unreviewed items in global rank order');
    for (const id of [248,250]) {
      check(await page.locator(`[data-guide-achievement="${id}"] [data-community-rank]`).count() === 0, 'Starting-equipment upgrades must not inherit item-pool unlock ranks');
    }
    await page.getByRole('button', { name: '道具总榜', exact: true }).click();
    const boardRows = page.locator('[data-community-item]');
    check(await boardRows.count() === 719, 'The full 719-entry source must be browsable');
    check(await boardRows.first().getAttribute('data-community-item') === '628', 'Death Certificate must retain source rank 1');
    check((await page.locator('#communitySection').innerText()).includes('Repentance'), 'Source version must be visible');
    check(await page.locator('#profileSelect').isHidden(), 'Unlock-only controls must not imply that they change the full community board');
    const search = page.getByRole('searchbox', { name: '搜索全部道具', exact: true });
    await search.fill('神性');
    check(await boardRows.count() === 1, 'Chinese item names must be searchable');
    const godheadRank = await boardRows.first().getAttribute('data-community-position');
    await search.fill('Godhead');
    check(await boardRows.count() === 1 && await boardRows.first().getAttribute('data-community-position') === godheadRank, 'English search must retain the same global rank');
    await boardRows.first().getByRole('button', { name: /查看解锁目标/ }).click();
    check(await page.locator('[data-guide-achievement="156"]').count() === 1, 'Board links must open the corresponding guide target');
    for (const [item, id] of [['Cube of Meat',6], ['Razor Blade',44]]) {
      await page.getByRole('button', { name: '道具总榜', exact: true }).click();
      await search.fill(item);
      await boardRows.first().getByRole('button', { name: /查看解锁目标/ }).click();
      check(await page.locator('[data-guide-achievement]').count() === 1 && await page.locator(`[data-guide-achievement="${id}"]`).count() === 1,
        `Short achievement #${id} must open exactly one target, rather than a substring search`);
    }
    await page.getByRole('button', { name: '道具总榜', exact: true }).click();
    await search.fill('Tonsil');
    check(await boardRows.count() === 1 && await boardRows.first().getAttribute('data-community-item') === 'legacy-710', 'The obsolete source entry must remain explicit instead of being mapped to the wrong current item');
    check((await boardRows.first().innerText()).includes('旧版条目'), 'Legacy mapping limitation must be visible');
    check(await boardRows.first().locator('[data-open-achievement]').count() === 0, 'Legacy Tonsil must not link to current Glass Cannon unlocks');
    await search.fill('no-such-isaac-item');
    check(await boardRows.count() === 0 && (await page.locator('#tableBody').innerText()).includes('没有匹配的道具'), 'Search must handle an empty result');
    await search.fill('');
    await page.setViewportSize({ width:390, height:844 });
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Full board must fit the narrow page, with scrolling confined to its table');
    await page.setViewportSize({ width:1280, height:900 });
    check(errors.length === 0, `Browser errors: ${errors.join('; ')}`);
    return { passed:true, sourceEntries:719, mappedTargets:271, editorialReviews:65, errors };
  } finally {
    await page.evaluate(values => {
      localStorage.clear();
      for (const [key,value] of Object.entries(values)) localStorage.setItem(key,value);
    }, storage);
    await page.unroute('**/api/*');
    await page.reload();
  }
}
