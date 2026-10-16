import { spawn } from 'node:child_process';
import net from 'node:net';
import path from 'node:path';
import { root, pythonPath, checkEnvironment } from './local-runtime.mjs';

const children = new Set(); let stopping = false;
function launch(command, args) {
  const child = spawn(command, args, { cwd: root, stdio: 'inherit', windowsHide: true, env: { ...process.env, SITE_BASE: '/' } });
  children.add(child);
  child.on('error', error => { console.error(error.message); stop(1); });
  child.on('exit', code => { children.delete(child); if (!stopping) stop(code || 0); });
  return child;
}
function stop(code = 0) {
  if (stopping) return;
  stopping = true; process.exitCode = code;
  for (const child of children) child.kill('SIGTERM');
}
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => stop());
async function portFree(port) {
  return new Promise(resolve => {
    const server = net.createServer(); server.once('error', () => resolve(false));
    server.listen(port, '127.0.0.1', () => server.close(() => resolve(true)));
  });
}
async function probe(url) {
  try { return await fetch(url, { signal: AbortSignal.timeout(1000) }); } catch { return null; }
}
async function waitFor(url, predicate) {
  for (let attempt = 0; attempt < 90 && !stopping; attempt++) {
    const response = await probe(url); if (response?.ok && await predicate(response)) return;
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw Error('启动未完成，请检查终端中的错误信息。');
}
function openBrowser(url) {
  if (process.argv.includes('--no-open')) return;
  const command = process.platform === 'win32' ? 'cmd.exe' : process.platform === 'darwin' ? 'open' : 'xdg-open';
  const args = process.platform === 'win32' ? ['/d', '/s', '/c', 'start', '""', url] : [url];
  const child = spawn(command, args, { detached: true, stdio: 'ignore', windowsHide: true });
  child.on('error', () => console.log(`请在浏览器打开 ${url}`)); child.unref();
}
try {
  console.log(`PyTorch ${checkEnvironment()} · CPU`);
  const apiUrl = 'http://127.0.0.1:8765/api/health', siteUrl = 'http://127.0.0.1:4173/practice';
  const api = await probe(apiUrl);
  const apiReady = api?.ok && (await api.json()).service === 'agent-for-dummies-oj';
  if (!apiReady && !await portFree(8765)) throw Error('端口 8765 已被其他服务占用，请先释放该端口。');
  const site = await probe('http://127.0.0.1:4173/__local-learning');
  let siteReady = false;
  if(site?.ok){try{siteReady=(await site.json()).service==='agent-for-dummies-site';}catch{}}
  if (!siteReady && !await portFree(4173)) throw Error('端口 4173 已被其他服务占用，请先释放该端口。');
  if (!apiReady) launch(pythonPath, ['-m', 'uvicorn', 'app:app', '--app-dir', 'oj', '--host', '127.0.0.1', '--port', '8765']);
  const synced = spawn(process.execPath, ['scripts/sync-content.mjs'], { cwd: root, stdio: 'inherit', windowsHide: true });
  await new Promise((resolve, reject) => { synced.on('error', reject); synced.on('exit', code => code === 0 ? resolve() : reject(Error('网页内容同步失败。'))); });
  if (!siteReady) launch(process.execPath, ['node_modules/vitepress/bin/vitepress.js', 'dev', 'site', '--host', '127.0.0.1', '--port', '4173', '--strictPort']);
  await Promise.all([waitFor(apiUrl, async response => (await response.json()).ready === true), waitFor(siteUrl, async () => true)]);
  console.log(`练习页面：${siteUrl}\n按 Ctrl+C 结束本次启动的服务。`); openBrowser(siteUrl);
  if (!children.size) console.log('网页和判题服务已经在其他终端运行，本次直接复用。');
} catch (error) { console.error(error.message); stop(1); }
