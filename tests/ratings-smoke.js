// Run in an isolated browser profile: this check simulates old and custom profiles.
async page => {
  const key = 'isaac_unlock_planner.current_profile.v1';
  const originalStorage = await page.evaluate(() => Object.fromEntries(Object.entries(localStorage)));
  const expected = { 135: 'strong', 136: 'recommended', 138: 'strong', 156: 'recommended',
    250: 'strong', 325: 'normal', 336: 'recommended', 354: 'strong', 360: 'normal',
    547: 'normal', 636: 'normal' };
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/*', route => route.abort());
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const readProfile = () => page.evaluate(key => JSON.parse(localStorage.getItem(key)), key);
  const loadProfile = async profile => {
    await page.evaluate(({ key, profile }) => {
      localStorage.clear();
      if (profile) localStorage.setItem(key, JSON.stringify(profile));
    }, { key, profile });
    await page.reload();
    await page.locator('[data-guide-achievement="354"]').waitFor();
  };
  try {
    await loadProfile(null);
    for (const [id, priority] of Object.entries(expected)) {
      const actual = await page.locator(`[data-guide-achievement="${id}"] [data-current-priority]`).getAttribute('data-current-priority');
      check(actual === priority, `New profile #${id}: expected ${priority}, got ${actual}`);
    }
    const fresh = await readProfile();
    const legacy = { ...fresh, achievements: fresh.achievements.map(entry => ({ ...entry, priority: 'normal' })) };
    await loadProfile(legacy);
    let current = await readProfile();
    check(current.achievements.find(x => x.achievementId === 354).priority === 'strong', 'Old unmodified built-in profiles must refresh');
    check(JSON.stringify(current.characterBoss) === JSON.stringify(fresh.characterBoss), 'Existing character ratings must stay intact');
    check(JSON.stringify(current.challenges) === JSON.stringify(fresh.challenges), 'Existing challenge ratings must stay intact');

    const custom = { ...legacy, customized: true, name: '保留我的配置' };
    custom.achievements.find(x => x.achievementId === 354).priority = 'discouraged';
    await loadProfile(custom);
    current = await readProfile();
    check(JSON.stringify(current) === JSON.stringify(custom), 'Custom profiles, including explicit normal entries, must remain unchanged');
    check(await page.locator('[data-guide-achievement="354"] [data-current-priority]').getAttribute('data-current-priority') === 'discouraged', 'Custom rating must render');
    check(await page.locator('[data-guide-achievement="135"] [data-current-priority]').getAttribute('data-current-priority') === 'normal', 'Do not replace a custom normal rating');
    await loadProfile(null);
    await page.getByRole('button', { name: '其他成就', exact: true }).click();
    check(await page.locator('#achievementResults [data-priority-id="354"]').getAttribute('data-current-priority') === 'strong', 'Legacy achievement view must use the same researched rating');
    check(errors.length === 0, `Browser errors: ${errors.join('; ')}`);
    return { passed: true, researchedAchievements: Object.keys(expected).length, legacyUpgrade: true, customPreserved: true };
  } finally {
    await page.evaluate(storage => {
      localStorage.clear();
      for (const [key, value] of Object.entries(storage)) localStorage.setItem(key, value);
    }, originalStorage);
    await page.unroute('**/api/*');
    await page.reload();
  }
}
