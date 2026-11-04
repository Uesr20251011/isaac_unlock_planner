(function (root) {
  'use strict';

  const categories = [
    { id: 'character', label: '角色通关' },
    { id: 'challenge', label: '挑战奖励' },
    { id: 'main', label: '主线推进' },
    { id: 'character-unlock', label: '角色解锁' },
    { id: 'cumulative', label: '次数 / 累计' },
    { id: 'completion', label: '完成类成就' }
  ];

  function buildEntries({ data, challenges, achievements }) {
    const entries = new Map();
    function add(achievementId, category, source) {
      const id = Number(achievementId);
      if (!entries.has(id)) entries.set(id, { achievementId: id, categories: [], order: entries.size, ...source });
      const entry = entries.get(id);
      if (!entry.categories.includes(category)) entry.categories.push(category);
      // One achievement can be both a character unlock and a completion mark.
      // Retain the descriptive entry while keeping its existing rule/menu identity.
      if (source.entry) entry.entry = source.entry;
    }
    for (const rule of data.unlockRules) add(rule.achievementId, 'character', { kind: 'rule', rule });
    for (const challenge of challenges) add(challenge.rewardAchievementId, 'challenge', { kind: 'challenge', challenge });
    for (const [category, list] of [
      ['main', achievements.main],
      ['character-unlock', [...achievements.characters.normal, ...achievements.characters.tainted]],
      ['cumulative', achievements.cumulative],
      ['completion', achievements.completion]
    ]) {
      for (const entry of list) add(entry.achievementId, category, { kind: 'achievement', entry });
    }
    return [...entries.values()];
  }

  function selectEntries(entries, {
    categories: selected = categories.map(x => x.id), query = '', showUnlocked = true,
    save = null, sort = 'default', priorityFor = () => 0, searchTextFor = () => '', compareFor = () => 0
  } = {}) {
    const selectedIds = new Set(selected);
    const search = String(query).trim().toLocaleLowerCase();
    const rows = entries.filter(row => (
      row.categories.some(id => selectedIds.has(id)) &&
      (showUnlocked || !save || !save.isAchievementUnlocked(row.achievementId)) &&
      (!search || `${row.achievementId} ${searchTextFor(row)}`.toLocaleLowerCase().includes(search))
    ));
    rows.sort((a, b) => (sort === 'priority' ? priorityFor(b) - priorityFor(a)
      : ['rank', 'community'].includes(sort) ? compareFor(a, b, sort) : 0) || a.order - b.order);
    return rows;
  }

  root.IsaacGuide = { categories, buildEntries, selectEntries };
})(typeof window !== 'undefined' ? window : globalThis);
