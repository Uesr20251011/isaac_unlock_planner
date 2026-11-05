const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = { window: {} };
const model = path.join(__dirname, '../js/rankings.js');
if (fs.existsSync(model)) vm.runInNewContext(fs.readFileSync(model, 'utf8'), context);
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../js/guide.js'), 'utf8'), context);
const Ranking = context.window.IsaacRankings;
const fixture = { entries: [
  { achievementId: 1, unlockRank: 2, communityReference: { rank: 1 } },
  { achievementId: 2, unlockRank: 1, communityReference: { rank: 9 } },
  { achievementId: 3, unlockRank: null, parallelOrder: 1 },
  { achievementId: 4, unlockRank: null, parallelOrder: 2, communityReference: { rank: 192 } }
] };

test('parallel tasks lead unlock suggestions without being numbered as prerequisites', () => {
  assert.ok(Ranking, 'The ranking model must exist');
  const index = Ranking.createIndex(fixture);
  assert.deepEqual([99, 1, 4, 2, 3].sort((a,b) => index.compare(a,b,'rank')), [3,4,2,1,99]);
  assert.equal(index.get(3).unlockRank, null);
  assert.equal(index.get(99), null);
});

test('community preference is independent of unlock priority and missing ranks sort last', () => {
  assert.ok(Ranking);
  const index = Ranking.createIndex(fixture);
  assert.deepEqual([99,3,2,4,1].sort((a,b) => index.compare(a,b,'community')), [1,2,4,99,3]);
  assert.equal(index.compare(99,3,'community'), 0);
  assert.equal(index.compare(1,2,'default'), 0);
});

test('unlock plan uses cost-aware positions and moves blocked targets after available work', () => {
  const index=Ranking.createIndex({unlockPlan:{entries:[
    {achievementId:1,unlockRank:1,parallelOrder:null,prerequisiteAchievementIds:[8],ensembleReferences:[{rank:2}]},
    {achievementId:2,unlockRank:2,parallelOrder:null,prerequisiteAchievementIds:[],ensembleReferences:[{rank:1}]},
    {achievementId:3,unlockRank:null,parallelOrder:1,prerequisiteAchievementIds:[],ensembleReferences:[]}
  ]}});
  assert.deepEqual([2,1,3].sort((a,b)=>index.compare(a,b,'rank')),[3,1,2]);
  assert.deepEqual([2,1,3].sort((a,b)=>index.compare(a,b,'rank',{isAchievementUnlocked:()=>false})),[3,2,1]);
  assert.deepEqual([2,1,3].sort((a,b)=>index.compare(a,b,'ensemble')),[2,1,3]);
  assert.equal(index.recommendationFor(1).unlockRank,1);
});

test('community positions do not require an editorial review or an unlock-suggestion rank', () => {
  assert.ok(Ranking);
  const index = Ranking.createIndex({
    ...fixture,
    communityItems: [{ collectibleId: 699, rank: 31, name: 'Unreviewed item' }],
    communityTargets: [{ achievementId: 99, collectibleIds: [699] }]
  });
  assert.equal(index.get(99), null);
  assert.equal(index.communityFor(99)[0].rank, 31);
  assert.deepEqual([4,99,1].sort((a,b) => index.compare(a,b,'community')), [1,99,4]);
});

test('the whole collected ranking and the screenshot examples reach the generated data', () => {
  const source = path.join(__dirname, '../data/research_rankings.js');
  vm.runInNewContext(fs.readFileSync(source, 'utf8'), context);
  const data = context.window.ISAAC_RESEARCH_RANKINGS;
  assert.equal(data.communityItems?.length, 719, 'All collected items must be published');
  const index = Ranking.createIndex(data);
  for (const achievementId of [108,54,452,198]) {
    assert.equal(index.get(achievementId), null, 'These targets remain outside the 65 editorial reviews');
    assert.ok(index.communityFor(achievementId).length, `Screenshot achievement #${achievementId} must have a community rank`);
  }
});

test('combined categories, hiding completed targets and searches preserve original rank numbers', () => {
  assert.ok(Ranking);
  const index = Ranking.createIndex(fixture);
  const entries = [1,2,3,4,99].map((achievementId, order) => ({ achievementId, order, categories: [order % 2 ? 'challenge' : 'character'] }));
  const result = context.window.IsaacGuide.selectEntries(entries, {
    categories: ['challenge','character'], sort: 'rank',
    compareFor: (a,b,mode) => index.compare(a.achievementId,b.achievementId,mode),
    save: { isAchievementUnlocked: id => id === 2 }, showUnlocked: false
  });
  assert.deepEqual(Array.from(result, x => x.achievementId), [3,4,1,99]);
  assert.equal(index.get(result[2].achievementId).unlockRank, 2);
});

test('shipped rankings cover reviewed targets and record original priority corrections', () => {
  const source = path.join(__dirname, '../data/research_rankings.js');
  assert.ok(fs.existsSync(source), 'Compiled research data must exist');
  vm.runInNewContext(fs.readFileSync(source, 'utf8'), context);
  const data = context.window.ISAAC_RESEARCH_RANKINGS;
  assert.equal(data.entries.length, 65);
  const ids = new Set(data.entries.map(x => x.achievementId));
  assert.equal(ids.size, 65);
  assert.equal(data.entries.filter(x => x.parallelOrder).length, 10);
  assert.deepEqual(Array.from(data.entries.filter(x => x.unlockRank).map(x => x.unlockRank)).sort((a,b) => a-b), Array.from({length:55}, (_,i) => i+1));
  assert.equal(data.entries.find(x => x.achievementId === 231).priority, 'normal');
  assert.equal(data.entries.find(x => x.achievementId === 433).priority, 'recommended');
  const modem = data.entries.find(x => x.achievementId === 354);
  assert.equal(modem.communityReference.rank, 192);
  assert.equal(data.entries.find(x => x.achievementId === 156).strength, 'S');
});
