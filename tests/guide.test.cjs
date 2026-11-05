const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const context = { window: {} };
const source = path.join(__dirname, '../js/guide.js');
if (fs.existsSync(source)) vm.runInNewContext(fs.readFileSync(source, 'utf8'), context);
const guide = context.window.IsaacGuide;

const fixture = {
  data: { unlockRules: [{ id: 'r1', characterId: 'c1', bossIds: ['b1'], achievementId: 1 }] },
  challenges: [{ challengeId: 1, rewardAchievementId: 2 }],
  achievements: {
    main: [{ achievementId: 3 }],
    characters: { normal: [{ achievementId: 1 }, { achievementId: 4 }], tainted: [{ achievementId: 5 }] },
    cumulative: [{ achievementId: 6 }],
    completion: [{ achievementId: 7 }]
  }
};
const allCategories = ['character', 'challenge', 'main', 'character-unlock', 'cumulative', 'completion'];

test('the overview includes every category and merges duplicate achievements', () => {
  assert.ok(guide, 'The overview model must be available');
  const entries = guide.buildEntries(fixture);
  assert.equal(entries.length, 7);
  assert.deepEqual(Array.from(entries.find(x => x.achievementId === 1).categories), ['character', 'character-unlock']);
});

test('category selections form a union, including achievements with multiple categories', () => {
  assert.ok(guide, 'The overview model must be available');
  const entries = guide.buildEntries(fixture);
  const select = categories => Array.from(guide.selectEntries(entries, { categories }), x => x.achievementId);
  assert.deepEqual(select(['character', 'challenge', 'completion']), [1, 2, 7]);
  assert.deepEqual(select(['character-unlock']), [1, 4, 5]);
  assert.deepEqual(select([]), []);
});

test('hiding completed entries requires a save and preserves unknown entries', () => {
  assert.ok(guide, 'The overview model must be available');
  const entries = guide.buildEntries(fixture);
  const options = { categories: allCategories, showUnlocked: false };
  assert.equal(guide.selectEntries(entries, options).length, 7);
  const save = { isAchievementUnlocked: id => id === 2 || id === 4 };
  assert.deepEqual(Array.from(guide.selectEntries(entries, { ...options, save }), x => x.achievementId), [1, 3, 5, 6, 7]);
});

test('priority ordering is global across categories and remains stable for ties', () => {
  assert.ok(guide, 'The overview model must be available');
  const entries = guide.buildEntries(fixture);
  const options = { categories: allCategories, sort: 'priority', priorityFor: row => row.achievementId === 7 ? 3 : 1 };
  assert.deepEqual(Array.from(guide.selectEntries(entries, options), x => x.achievementId), [7, 1, 2, 3, 4, 5, 6]);
  assert.deepEqual(Array.from(guide.selectEntries(entries, { ...options, sort: 'default' }), x => x.achievementId), [1, 2, 3, 4, 5, 6, 7]);
});

test('search is case insensitive and searches an entry only within selected categories', () => {
  assert.ok(guide, 'The overview model must be available');
  const entries = guide.buildEntries(fixture);
  const options = { categories: ['challenge'], query: '  BOSS  ', searchTextFor: row => row.achievementId === 2 ? 'Boss Rush' : '' };
  assert.deepEqual(Array.from(guide.selectEntries(entries, options), x => x.achievementId), [2]);
  assert.equal(guide.selectEntries(entries, { ...options, categories: ['main'] }).length, 0);
});

test('reward type selections combine with target categories and keep mixed rewards once',()=>{
  const rows=[
    {achievementId:1,order:0,categories:['challenge'],types:['rune','collectible']},
    {achievementId:2,order:1,categories:['character'],types:['soulstone']},
    {achievementId:3,order:2,categories:['challenge'],types:['card']}
  ];
  const select=(categories,rewardTypes)=>Array.from(guide.selectEntries(rows,{categories,rewardTypes,rewardTypesFor:row=>row.types}),row=>row.achievementId);
  assert.deepEqual(select(['challenge'],['rune','collectible','soulstone']),[1]);
  assert.deepEqual(select(['character','challenge'],['rune','soulstone']),[1,2]);
  assert.deepEqual(select(['challenge'],[]),[]);
});

test('a hash-prefixed achievement ID is exact, including single-digit IDs', () => {
  const entries = [6,66,116].map((achievementId,order) => ({ achievementId, order, categories:['character'] }));
  const select = query => Array.from(guide.selectEntries(entries, { query }), row => row.achievementId);
  assert.deepEqual(select('#6'), [6]);
  assert.deepEqual(select('6'), [6,66,116]);
  assert.deepEqual(select('#44'), []);
});

test('the actual project catalogue appears once per achievement in the overview', () => {
  assert.ok(guide, 'The overview model must be available');
  const dataContext = { window: {} };
  for (const filename of ['unlocks', 'challenges', 'achievements']) {
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, `../data/${filename}.js`), 'utf8'), dataContext);
  }
  const entries = guide.buildEntries({ data: dataContext.window.ISAAC_UNLOCK_DATA, challenges: dataContext.window.ISAAC_CHALLENGE_DATA.entries, achievements: dataContext.window.ISAAC_ACHIEVEMENT_DATA });
  const ids = entries.map(x => x.achievementId);
  assert.equal(ids.length, new Set(ids).size);
  for (const id of [1, 70, 89, 199, 474, 637, 641]) assert.ok(ids.includes(id), `Missing achievement #${id}`);
  assert.equal(guide.selectEntries(entries, { categories: ['challenge'] }).length, 45);
  assert.equal(guide.selectEntries(entries, { categories: ['character'] }).length, 340);
});
