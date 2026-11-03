async page => {
  let releaseHealth;
  let markHealthStarted;
  const gate = new Promise(resolve => { releaseHealth = resolve; });
  const healthStarted = new Promise(resolve => { markHealthStarted = resolve; });
  await page.route('**/api/health', async route => {
    markHealthStarted();
    await gate;
    await route.continue();
  });
  try {
    await page.reload();
    await healthStarted;
    await page.getByRole('button', { name: '清除本地缓存', exact: true }).click();
    const healthResponse = page.waitForResponse(response => response.url().endsWith('/api/health'));
    releaseHealth();
    await healthResponse;
    await page.locator('#localSaveControls').waitFor({ state: 'visible' });
    if (await page.locator('#pauseLocalSaveBtn').innerText() !== '恢复自动同步') throw new Error('Clearing the cache while health detection is pending must pause automatic synchronization');
    if (!(await page.locator('#saveStatus').innerText()).includes('尚未读取存档')) throw new Error('A cleared save must not be silently restored by delayed binding detection');
    await page.reload();
    await page.locator('#localSaveControls').waitFor({ state: 'visible' });
    if (await page.locator('#pauseLocalSaveBtn').innerText() !== '恢复自动同步') throw new Error('An explicit pause should survive reopening');
    await page.getByRole('button', { name: '立即同步', exact: true }).click();
    await page.waitForFunction(() => document.getElementById('saveStatus').innerText.includes('已解锁'));
    return { passed: true, clearDuringInitialDetection: true, pausePersists: true, resumeReadsBoundSave: true };
  } finally {
    releaseHealth();
    await page.unroute('**/api/health');
  }
}
