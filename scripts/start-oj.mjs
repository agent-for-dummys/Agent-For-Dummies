import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
const python=path.resolve('.venv-oj',process.platform==='win32'?'Scripts/python.exe':'bin/python');
if(!existsSync(python)){console.error('请先在项目根目录运行 npm run setup 安装判题环境。');process.exit(1);}
const child=spawn(python,['-m','uvicorn','app:app','--app-dir','oj','--host','127.0.0.1','--port','8765'],{stdio:'inherit'});
for(const event of ['SIGINT','SIGTERM'])process.on(event,()=>child.kill());
child.on('exit',code=>process.exit(code||0));
