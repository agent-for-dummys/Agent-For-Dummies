import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const root = fileURLToPath(new URL('../', import.meta.url));
export const pythonPath = path.join(root, '.venv-oj', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
export function checkNode() {
  if (Number(process.versions.node.split('.')[0]) < 22) throw Error('请先安装 Node.js 22 或更新版本。');
}
export function findPython() {
  const candidates = process.env.OJ_PYTHON ? [[process.env.OJ_PYTHON, []]] : process.platform === 'win32'
    ? [['py', ['-3.12']], ['py', ['-3.13']], ['py', ['-3.14']], ['python', []]]
    : [['python3.12', []], ['python3.13', []], ['python3.14', []], ['python3', []], ['python', []]];
  for (const [command, args] of candidates) {
    const result = spawnSync(command, [...args, '-c', 'import sys; print(sys.version.split()[0]); sys.exit(0 if (3,12)<=sys.version_info[:2]<(3,15) else 1)'], { encoding: 'utf8', windowsHide: true });
    if (!result.error && result.status === 0) return { command, args, version: result.stdout.trim() };
  }
  throw Error('未找到 Python 3.12～3.14。请先安装 Python，或用 OJ_PYTHON 指定解释器路径。');
}
export function checkEnvironment() {
  checkNode();
  if (!existsSync(pythonPath)) throw Error('本地环境尚未安装，请先运行 npm run setup。');
  if (!existsSync(path.join(root, 'node_modules/vitepress/bin/vitepress.js'))) throw Error('网页依赖尚未安装，请先运行 npm run setup。');
  const result = spawnSync(pythonPath, ['-X', 'utf8', '-c', 'import torch, fastapi, uvicorn, langchain, langchain_openai, langgraph, openai, dotenv; from langgraph.checkpoint.sqlite import SqliteSaver; print(torch.__version__)'], { cwd: root, encoding: 'utf8', windowsHide: true });
  if (result.error || result.status !== 0) throw Error('本地学习环境不完整，请重新运行 npm run setup。');
  return result.stdout.trim();
}
