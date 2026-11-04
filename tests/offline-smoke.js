async page => {
  if (!page.url().endsWith('/isaac-unlock-planner-offline.html')) throw new Error('Open the generated single-file HTML before running this check');
  const blocked = [];
  const artifactUrl = page.url();
  await page.route('**/*', route => {
    if (route.request().url() === artifactUrl && route.request().isNavigationRequest()) return route.continue();
    blocked.push(route.request().url());
    return route.abort();
  });
  try {
    // Run in an isolated test profile: the single-file artifact must not depend
    // on a cached save, a cached script, or the optional local API.
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.locator('[data-guide-achievement]').first().waitFor();
    if (await page.locator('[data-guide-achievement]').count() !== 606) throw new Error('The single-file guide did not load all project targets');
    if (await page.locator('script[src], link[rel="stylesheet"][href]').count()) throw new Error('The offline page still requires external code or styles');
    const externalImages = await page.locator('img').evaluateAll(images => images.filter(image => !image.src.startsWith('data:')).map(image => image.src));
    if (externalImages.length) throw new Error(`Images were not embedded: ${externalImages.join(', ')}`);
    await page.getByRole('button', { name: '仅角色', exact: true }).click();
    if (await page.locator('[data-guide-achievement]').count() !== 372) throw new Error('Offline character filtering failed');
    await page.getByRole('button', { name: '仅挑战', exact: true }).click();
    await page.getByRole('checkbox', { name: '主线推进', exact: false }).check();
    if (await page.locator('[data-guide-achievement]').count() !== 53) throw new Error('Offline combined filtering failed');
    await page.getByRole('button', { name:'道具总榜', exact:true }).click();
    if (await page.locator('[data-community-item]').count() !== 719) throw new Error('Offline full community board did not load all719 source entries');
    await page.getByRole('searchbox', { name:'搜索全部道具', exact:true }).fill('Godhead');
    if (await page.locator('[data-community-item]').count() !== 1) throw new Error('Offline community item search failed');
    const externalAssets = blocked.filter(url => !url.endsWith('/api/health'));
    if (externalAssets.length) throw new Error(`The single-file page requested external assets: ${externalAssets.join(', ')}`);
    return { passed: true, targets: 606, characterTargets: 372, combinedCategories: 53, communityItems:719, externalAssets: [] };
  } finally { await page.unroute('**/*'); }
}
