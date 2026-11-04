(function (root) {
  'use strict';

  function createIndex(data = {}) {
    const entries = new Map((data.entries || []).map(entry => [Number(entry.achievementId), entry]));
    const get = id => entries.get(Number(id)) || null;
    const positive = value => Number.isFinite(value) && value > 0 ? value : Infinity;
    function valueFor(id, mode) {
      const entry = get(id);
      if (mode === 'community') return positive(entry?.communityReference?.rank);
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
    return { get, compare, reviewedCount: entries.size };
  }

  root.IsaacRankings = { createIndex };
})(typeof window !== 'undefined' ? window : globalThis);
