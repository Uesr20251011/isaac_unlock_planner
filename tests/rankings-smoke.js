// Run in an isolated browser profile. It temporarily replaces that profile's storage.
async page => {
  const originalStorage = await page.evaluate(() => Object.fromEntries(Object.entries(localStorage)));
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/*', route => route.abort());
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  try {
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.getByRole('button', { name: '解锁排名', exact: true }).click();
    const rows = page.locator('[data-guide-achievement]');
    check(await rows.count() === 606, 'Rank mode must preserve the full catalogue');
    const order = await rows.evaluateAll(rows => rows.map(row => ({
      id: Number(row.dataset.guideAchievement),
      rank: Number(row.querySelector('[data-unlock-rank]')?.dataset.unlockRank) || null,
      parallel: Boolean(row.querySelector('[data-parallel-task]')),
      community: Number(row.querySelector('[data-community-rank]')?.dataset.communityRank) || null
    })));
    check(order.slice(0,10).every(x => x.parallel), 'Parallel reminders must be distinct from numbered prerequisites');
    check(order.slice(10,65).map(x => x.rank).join(',') === Array.from({length:55}, (_,i) => i+1).join(','), 'Reviewed unlock ranks must be exact and ordered');
    check(order.slice(65).every(x => x.rank === null && !x.parallel), 'Unreviewed rows must not receive invented ranks');
    const godhead = page.locator('[data-guide-achievement="156"]');
    const godheadRank = await godhead.locator('[data-unlock-rank]').textContent();
    check((await godhead.innerText()).includes('强度 S'), 'Godhead strength must be separate from its acquisition priority');
    const d8 = page.locator('[data-guide-achievement="231"]');
    check(await d8.locator('[data-current-priority]').getAttribute('data-current-priority') === 'normal', 'D8 must receive its researched correction');
    await d8.getByText('评级依据', { exact: true }).click();
    check((await d8.innerText()).includes('强烈推荐 → 普通'), 'Corrections must show the previous and revised values');
    check(await d8.locator('.research-sources a').count() >= 3, 'Evidence sources must be accessible');
    await page.getByRole('searchbox', { name: '搜索目标' }).fill('156');
    check(await godhead.locator('[data-unlock-rank]').textContent() === godheadRank, 'Search must not renumber ranks');
    await page.getByRole('searchbox', { name: '搜索目标' }).fill('');
    await page.getByRole('button', { name: '社区强度', exact: true }).click();
    check(await rows.first().getAttribute('data-guide-achievement') === '636', 'Community sort must rank Death Certificate first');
    const communityOrder = await rows.locator('[data-community-rank]').evaluateAll(nodes => nodes.map(node => Number(node.dataset.communityRank)));
    check(communityOrder.every((value,i) => !i || value >= communityOrder[i-1]), 'Community ranks must sort independently of unlock cost');
    check((await page.locator('#rankingNote').innerText()).includes('Repentance'), 'Community source version must be visible');
    await page.getByRole('button', { name: '仅挑战', exact: true }).click();
    check(await rows.count() === 45, 'Ranking must work with challenge-only filtering');
    await page.getByRole('button', { name: '解锁排名', exact: true }).click();
    await page.getByRole('button', { name: '按角色', exact: true }).click();
    check(await page.locator('#tableBody [data-research-achievement]').first().getAttribute('data-research-achievement') === '43', 'Original character view must sort by the same global unlock ranks');
    await page.getByRole('button', { name: '挑战解锁', exact: true }).click();
    check(await page.locator('#tableBody [data-research-achievement]').first().getAttribute('data-research-achievement') === '103', 'Original challenge view must sort by the same global unlock ranks');
    await page.getByRole('button', { name: '其他成就', exact: true }).click();
    check((await page.locator('#achievementResults [data-research-achievement="156"]').innerText()).includes('强度 S'), 'Original achievement view must show the researched strength');
    await page.getByRole('button', { name: '总攻略', exact: true }).click();
    await page.getByRole('button', { name: '全部', exact: true }).click();
    await page.getByRole('button', { name: '解锁排名', exact: true }).click();
    await d8.getByRole('button', { name: '修改优先级' }).click();
    await page.locator('#priorityMenu [data-set-priority="strong"]').click();
    await page.reload();
    check(await d8.locator('[data-current-priority]').getAttribute('data-current-priority') === 'strong', 'Personal color choices must survive the built-in corrections');
    check(await d8.locator('[data-unlock-rank]').count() === 1, 'Research ranking must remain visible for custom profiles');
    check(await page.getByRole('button', { name: '解锁排名', exact: true }).getAttribute('class').then(value => value.includes('active')), 'Ranking mode must survive reopening');
    await page.setViewportSize({ width: 390, height: 844 });
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Ranking controls and evidence must fit narrow screens');
    await page.setViewportSize({ width: 1280, height: 900 });
    check(errors.length === 0, `Browser errors: ${errors.join('; ')}`);
    return { passed: true, reviewed:65, numbered:55, parallel:10, customPreserved:true, errors };
  } finally {
    await page.evaluate(storage => {
      localStorage.clear();
      for (const [key, value] of Object.entries(storage)) localStorage.setItem(key, value);
    }, originalStorage);
    await page.unroute('**/api/*');
    await page.reload();
  }
}
