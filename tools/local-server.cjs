/* Optional, dependency-free local server. Static hosting still works without it. */
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { parsePersistentGameData } = require('../js/save-parser.js');

const ROOT = path.resolve(__dirname, '..');
const MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.ico': 'image/x-icon' };

function createLocalServer({ root = ROOT, savePath = null } = {}) {
  const publicRoot = path.resolve(root);
  return http.createServer(async (request, response) => {
    response.setHeader('Cache-Control', 'no-store');
    response.setHeader('X-Content-Type-Options', 'nosniff');
    response.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
    const send = (status, body, type = 'application/json; charset=utf-8') => {
      response.writeHead(status, { 'Content-Type': type });
      response.end(request.method === 'HEAD' ? undefined : (typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body)));
    };
    try {
      const host = request.headers.host || '';
      const hostUrl = new URL(`http://${host}`);
      if (!['127.0.0.1', 'localhost'].includes(hostUrl.hostname) ||
          (request.headers.origin && request.headers.origin !== hostUrl.origin) ||
          request.headers['sec-fetch-site'] === 'cross-site') {
        send(403, { error: '仅允许从本机攻略页面访问。' });
        return;
      }
      if (!['GET', 'HEAD'].includes(request.method)) {
        response.setHeader('Allow', 'GET, HEAD');
        send(405, { error: '此服务只读取文件。' });
        return;
      }
      const url = new URL(request.url, hostUrl);
      if (url.pathname === '/api/health') {
        send(200, { app: 'isaac-unlock-planner', version: 1, saveBound: Boolean(savePath) });
        return;
      }
      if (url.pathname === '/api/local-save') {
        if (!savePath) { send(404, { error: '尚未绑定本机存档。' }); return; }
        try {
          const stats = await fs.stat(savePath);
          if (stats.size > 4 * 1024 * 1024) throw new Error('存档文件过大。');
          const data = await fs.readFile(savePath);
          parsePersistentGameData(data);
          const revision = createHash('sha256').update(data).digest('hex');
          if (url.searchParams.get('revision') === revision) { response.writeHead(204); response.end(); return; }
          send(200, { name: path.basename(savePath), lastModified: stats.mtimeMs, revision, data: data.toString('base64') });
        } catch (_) {
          send(503, { error: '绑定存档暂时无法读取；请等待游戏保存完毕，或检查本机绑定路径。' });
        }
        return;
      }

      const pathname = decodeURIComponent(url.pathname);
      const relative = pathname === '/' ? 'index.html' : pathname.slice(1);
      if (!/^(?:index\.html|styles\.css|isaac-unlock-planner-offline\.html|(?:assets|data|js)\/.+)$/u.test(relative)) {
        send(404, { error: '文件不存在。' }); return;
      }
      const candidate = path.resolve(publicRoot, relative);
      const relativePath = path.relative(publicRoot, candidate);
      if (relativePath.startsWith('..') || path.isAbsolute(relativePath) || relativePath.split(path.sep).some(part => part.startsWith('.'))) {
        send(404, { error: '文件不存在。' }); return;
      }
      try {
        const real = await fs.realpath(candidate);
        const realRelative = path.relative(publicRoot, real);
        if (realRelative.startsWith('..') || path.isAbsolute(realRelative)) { send(404, { error: '文件不存在。' }); return; }
        send(200, await fs.readFile(real), MIME[path.extname(real).toLowerCase()] || 'application/octet-stream');
      } catch (_) { send(404, { error: '文件不存在。' }); }
    } catch (_) { send(400, { error: '请求地址无效。' }); }
  });
}

async function main() {
  let config = {};
  try { config = JSON.parse((await fs.readFile(path.join(ROOT, '.local/config.json'), 'utf8')).replace(/^\uFEFF/u, '')); }
  catch (error) { if (error.code !== 'ENOENT') throw new Error('无法读取 .local/config.json，请检查 JSON 格式。'); }
  const port = Number(config.port || 18789);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('端口必须在 1–65535 之间。');
  const server = createLocalServer({ savePath: config.savePath ? path.resolve(ROOT, config.savePath) : null });
  server.on('error', error => { console.error(error.message); process.exitCode = 1; });
  server.listen(port, '127.0.0.1', () => console.log(`Isaac unlock planner: http://127.0.0.1:${port}`));
}

module.exports = { createLocalServer };
if (require.main === module) main().catch(error => { console.error(error.message); process.exitCode = 1; });
