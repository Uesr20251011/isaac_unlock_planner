(function (root) {
  'use strict';

  function createIndex(data = {}) {
    const entries = new Map((data.entries || []).map(entry => [Number(entry.achievementId), entry]));
    const get = id => entries.get(Number(id)) || null;
    const positive = value => Number.isFinite(value) && value > 0 ? value : Infinity;
    const communityItems = data.communityItems || [];
    const itemsById = new Map(communityItems.filter(item => item.collectibleId != null).map(item => [Number(item.collectibleId), item]));
    const communityTargets = new Map((data.communityTargets || []).map(target => [Number(target.achievementId),
      target.collectibleIds.map(id => itemsById.get(Number(id))).filter(Boolean).sort((a,b) => a.rank - b.rank)]));
    function communityFor(id) {
      const items = communityTargets.get(Number(id));
      if (items) return items;
      const reference = get(id)?.communityReference;
      return reference ? [reference] : [];
    }
    function valueFor(id, mode) {
      const entry = get(id);
      if (mode === 'community') return positive(communityFor(id)[0]?.rank);
      if (mode === 'rank') {
        // Parallel tasks are reminders to start alongside the numbered route.
        if (entry?.parallelOrder) return entry.parallelOrder / (entries.size + 1);
        return positive(entry?.unlockRank);
      }
      return Infinity;
    }
    function compare(a, b, mode) {
      const av = valueFor(a, mode), bv = valueFor(b, mode);
      return av === bv ? 0 : av < bv ? -1 : 1;
    }
    return { get, compare, communityFor, communityItems, reviewedCount: entries.size,
      communityTargetCount: communityTargets.size };
  }

  root.IsaacRankings = { createIndex };
})(typeof window !== 'undefined' ? window : globalThis);
