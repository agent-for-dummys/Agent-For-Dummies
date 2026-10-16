import { spawn } from 'node:child_process';
import path from 'node:path';
const python=path.resolve('.venv-oj',process.platform==='win32'?'Scripts/python.exe':'bin/python');
const child=spawn(python,['-X','utf8','-m','unittest','discover','-s','oj/tests','-v'],{stdio:'inherit',env:process.env});
child.on('error',()=>{console.error('请先安装 .venv-oj 环境。');process.exit(1);});
child.on('exit',code=>process.exit(code||0));
