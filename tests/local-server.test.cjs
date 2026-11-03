const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { once } = require('node:events');
const http = require('node:http');

let createLocalServer;
try { ({ createLocalServer } = require('../tools/local-server.cjs')); }
catch (error) { if (error.code !== 'MODULE_NOT_FOUND') throw error; }

function makeSave(unlockedId) {
  const data = Buffer.alloc(40);
  data.write('ISAACNGSAVE09R  ', 'ascii');
  data.writeUInt32LE(1, 20);
  data.writeUInt32LE(8, 24);
  data.writeUInt32LE(8, 28);
  data[32 + unlockedId] = 1;
  return data;
}

async function fixture(t) {
  assert.equal(typeof createLocalServer, 'function', 'The local read-only server must be available');
  const parent = path.resolve(__dirname, '../.local/test-runs');
  await fs.mkdir(parent, { recursive: true });
  const root = await fs.mkdtemp(path.join(parent, 'server-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  await fs.mkdir(path.join(root, '.local'));
  await fs.writeFile(path.join(root, 'index.html'), '<h1>Planner</h1>');
  await fs.writeFile(path.join(root, '.local/config.json'), '{"private":true}');
  const savePath = path.join(root, '.local/rep+persistentgamedata1.dat');
  await fs.writeFile(savePath, makeSave(1));
  const server = createLocalServer({ root, savePath });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  t.after(() => new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }));
  return { root, savePath, base: `http://127.0.0.1:${server.address().port}` };
}

test('the local API reads the bound save and detects subsequent game writes', async t => {
  const { base, savePath } = await fixture(t);
  const first = await (await fetch(`${base}/api/local-save`)).json();
  assert.equal(first.name, 'rep+persistentgamedata1.dat');
  assert.deepEqual(Buffer.from(first.data, 'base64'), makeSave(1));
  assert.equal((await fetch(`${base}/api/local-save?revision=${first.revision}`)).status, 204);
  await fs.writeFile(savePath, makeSave(2));
  const next = await (await fetch(`${base}/api/local-save?revision=${first.revision}`)).json();
  assert.notEqual(next.revision, first.revision);
  assert.deepEqual(Buffer.from(next.data, 'base64'), makeSave(2));
});

test('configuration, saves and repository metadata are never served as static files', async t => {
  const { base } = await fixture(t);
  assert.equal(await (await fetch(base)).text(), '<h1>Planner</h1>');
  for (const file of ['.local/config.json', '.local/rep+persistentgamedata1.dat', '.git/config', 'tools/local-server.cjs', 'data/../.local/config.json', 'assets/%2e%2e/%2e%2e/config.json']) {
    assert.equal((await fetch(`${base}/${file}`)).status, 404, file);
  }
});

test('other websites and unknown host names cannot read a bound save', async t => {
  const { base } = await fixture(t);
  assert.equal((await fetch(`${base}/api/local-save`, { headers: { Origin: 'https://example.com' } })).status, 403);
  const unknownHostStatus = await new Promise((resolve, reject) => {
    http.get(`${base}/api/local-save`, { headers: { Host: 'example.com' } }, response => {
      response.resume();
      resolve(response.statusCode);
    }).on('error', reject);
  });
  assert.equal(unknownHostStatus, 403);
  assert.equal((await fetch(`${base}/api/local-save`, { method: 'POST' })).status, 405);
});

test('a missing or partially written save reports an error without changing the file', async t => {
  const { base, savePath } = await fixture(t);
  await fs.writeFile(savePath, 'partial game write');
  assert.equal((await fetch(`${base}/api/local-save`)).status, 503);
  assert.equal(await fs.readFile(savePath, 'utf8'), 'partial game write');
  await fs.unlink(savePath);
  assert.equal((await fetch(`${base}/api/local-save`)).status, 503);
});
