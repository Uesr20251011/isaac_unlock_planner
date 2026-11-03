async page => {
  const failures = [];
  const check = (condition, message) => { if (!condition) failures.push(message); };
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.reload();
  await page.locator('[data-view="guide"]').waitFor();
  if (!await page.locator('#showUnlocked').isChecked()) await page.getByText('显示已解锁', { exact: true }).click();
  await page.getByRole('button', { name: '全部', exact: true }).click();
  check(await page.locator('[data-guide-achievement]').count() === 606, 'All project achievements should be present');
  await page.getByRole('button', { name: '仅角色', exact: true }).click();
  check(await page.locator('[data-guide-achievement]').count() === 372, 'Character targets and unlocks should merge duplicates');
  await page.getByRole('button', { name: '仅挑战', exact: true }).click();
  check(await page.locator('[data-guide-achievement]').count() === 45, 'All 45 challenges should be listed');
  check(await page.locator('[data-guide-achievement] .priority-pill').count() === 45, 'Every challenge should show its priority label');
  await page.getByRole('checkbox', { name: '主线推进', exact: false }).check();
  check(await page.locator('[data-guide-achievement]').count() === 53, 'Challenge and main-story categories should combine');
  await page.getByRole('button', { name: '全部', exact: true }).click();
  await page.getByRole('searchbox', { name: '搜索目标' }).fill('199');
  check(await page.locator('[data-guide-achievement="199"]').count() === 1, 'An achievement belonging to two categories must appear once');
  await page.getByRole('searchbox', { name: '搜索目标' }).fill('不存在的搜索结果');
  check(await page.locator('[data-guide-achievement]').count() === 0, 'Search should filter the guide');
  check(await page.getByText('没有匹配的目标', { exact: true }).isVisible(), 'Empty search should explain how to recover');
  await page.getByRole('searchbox', { name: '搜索目标' }).fill('');
  await page.getByRole('button', { name: '清空分类', exact: true }).click();
  check(await page.getByText('选择想要查看的分类', { exact: true }).isVisible(), 'No categories should produce a useful empty state');
  await page.getByRole('checkbox', { name: '次数 / 累计', exact: false }).check();
  await page.getByRole('checkbox', { name: '完成类成就', exact: false }).check();
  check(await page.locator('[data-guide-achievement]').count() === 181, 'Other achievement categories should combine');
  await page.reload();
  check(await page.locator('[data-guide-achievement]').count() === 181, 'Category selection should survive reopening');

  await page.getByRole('button', { name: '按角色', exact: true }).click();
  check(await page.getByRole('heading', { name: '选择角色', exact: true }).isVisible(), 'Original character selector should remain available');
  await page.getByRole('button', { name: '按 Boss', exact: true }).click();
  check(await page.getByRole('heading', { name: '选择 Boss', exact: true }).isVisible(), 'Original Boss selector should remain available');
  await page.getByRole('button', { name: '挑战解锁', exact: true }).click();
  check(await page.locator('#tableBody > tr').count() === 45, 'Original challenge view should remain available');
  await page.getByRole('button', { name: '其他成就', exact: true }).click();
  check(await page.getByRole('heading', { name: '主线成就', exact: true }).isVisible(), 'Original achievement view should remain available');
  await page.getByRole('button', { name: '总攻略', exact: true }).click();
  await page.getByRole('button', { name: '全部', exact: true }).click();

  const target = page.locator('[data-guide-achievement="70"]');
  const oldPriority = await target.locator('[data-current-priority]').getAttribute('data-current-priority');
  await target.getByRole('button', { name: '修改优先级' }).click();
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  check(await page.locator('#priorityMenu').isVisible(), 'Scrolling a long guide into view must not immediately close its menu');
  await page.locator('#priorityMenu [data-set-priority="discouraged"]').click();
  check((await target.getAttribute('class')).includes('priority-discouraged'), 'Overview priorities should be editable');
  await page.getByRole('button', { name: '按角色', exact: true }).click();
  check(await page.locator('#tableBody [data-priority-id="c00-isaac-a70"]').getAttribute('data-current-priority') === 'discouraged', 'The overview and original views must share priorities');
  await page.getByRole('button', { name: '总攻略', exact: true }).click();
  await target.getByRole('button', { name: '修改优先级' }).click();
  await page.locator(`#priorityMenu [data-set-priority="${oldPriority}"]`).click();

  const overlap = page.locator('[data-guide-achievement="199"]');
  const overlapPriority = await overlap.locator('[data-current-priority]').getAttribute('data-current-priority');
  await overlap.getByRole('button', { name: '修改优先级' }).click();
  await page.locator('#priorityMenu [data-set-priority="discouraged"]').click();
  await page.getByRole('button', { name: '其他成就', exact: true }).click();
  const originalOverlapMenu = page.locator('#achievementResults [data-priority-id="199"]');
  check(await originalOverlapMenu.getAttribute('data-current-priority') === 'discouraged', 'A duplicated character-unlock achievement must share its guide priority');
  await originalOverlapMenu.click();
  await page.locator('#priorityMenu [data-set-priority="recommended"]').click();
  await page.getByRole('button', { name: '总攻略', exact: true }).click();
  check(await overlap.locator('[data-current-priority]').getAttribute('data-current-priority') === 'recommended', 'Editing the original character-unlock achievement must update the guide');
  await overlap.getByRole('button', { name: '修改优先级' }).click();
  await page.locator(`#priorityMenu [data-set-priority="${overlapPriority}"]`).click();
  await page.getByRole('button', { name: '默认顺序', exact: true }).click();
  check(await page.locator('[data-guide-achievement]').first().getAttribute('data-guide-achievement') === '70', 'Default order should preserve the original character / Boss order');
  await page.getByRole('button', { name: '重要度顺序', exact: true }).click();
  check((await page.locator('[data-guide-achievement]').first().getAttribute('class')).includes('priority-strong'), 'Priority order should include all categories');

  const hasSave = (await page.locator('#saveStatus').innerText()).includes('已解锁');
  if (hasSave) {
    await page.getByText('显示已解锁', { exact: true }).click();
    check(await page.locator('[data-guide-achievement] > td > .status-badge.unlocked').count() === 0, 'Completed reward targets should be hidden');
    check(await page.locator('[data-guide-achievement]').count() < 606, 'Save filtering should reduce the guide');
  }
  await page.setViewportSize({ width: 390, height: 844 });
  check(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'The mobile page should not overflow horizontally');
  await page.screenshot({ path: '.local/guide-mobile.png' });
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.screenshot({ path: '.local/guide-desktop.png' });
  check(errors.length === 0, `No browser errors expected: ${errors.join('; ')}`);
  if (failures.length) throw new Error(failures.join('\n'));
  return { passed: true, allTargets: 606, characterTargets: 372, challenges: 45, saveFiltering: hasSave, browserErrors: errors };
}
