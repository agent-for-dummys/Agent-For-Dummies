"""Import dependencies first, then execute student files in a bounded process."""
import io
import json
import os
import sys
import traceback
import ast
import contextlib
import subprocess
import time
from pathlib import Path
for stream in (sys.stdin, sys.stdout, sys.stderr):
    stream.reconfigure(encoding='utf-8', errors='replace')
print(json.dumps({'workerPid': os.getpid()}), flush=True)
sys.path.insert(0, str(Path(__file__).parent.resolve()))
import agent_checks
import beginner_checks
import langchain_openai
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import dotenv_values
import httpx
import sqlite3
import ssl
ssl.create_default_context()
original_connect=sqlite3.connect
class RestrictedConnection(sqlite3.Connection):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.set_authorizer(lambda action,a,b,c,d:sqlite3.SQLITE_DENY if action in {sqlite3.SQLITE_ATTACH,sqlite3.SQLITE_DETACH} else sqlite3.SQLITE_OK)
    def set_authorizer(self,callback):
        if hasattr(self,'_policy_ready'):
            raise PermissionError('不能替换数据库文件访问限制')
        super().set_authorizer(callback)
        self._policy_ready=True
    def enable_load_extension(self,*args):raise PermissionError('不允许数据库扩展')
    def load_extension(self,*args):raise PermissionError('不允许数据库扩展')
def restricted_connect(database,*args,**kwargs):
    kwargs['factory']=RestrictedConnection
    return original_connect(database,*args,**kwargs)
sqlite3.connect=restricted_connect
payload = json.loads(sys.stdin.read(20000))
scratch = Path.cwd().resolve()
live = payload['mode'] == 'live'
data_root = Path(payload.get('dataRoot', scratch / '.runtime')).resolve()
if live:
    data_root.mkdir(parents=True, exist_ok=True)
allowed_read = [scratch, Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(), Path(httpx.__file__).resolve().parent,
                Path(__file__).parent.resolve() / 'agent_course.json']
if live:
    allowed_read.append(data_root)
command_context=False
text_suffixes={'.py','.md','.txt','.json','.yaml','.yml','.toml','.csv','.html','.css','.js','.ts','.sh'}
workspace_initial={path.relative_to(scratch).as_posix():path.read_text(encoding='utf-8') for path in (scratch/'workspace').rglob('*') if path.is_file() and path.suffix.lower() in text_suffixes and path.stat().st_size<=100000}


def bounded_python(args, cwd=None, timeout=5, **kwargs):
    """Native exports use subprocess; web exercises inherit this worker's limits."""
    global command_context
    if len(args)!=3 or args[0]!=sys.executable or args[1]!='-I':
        raise PermissionError('网页命令工具只接受当前项目的 Python 文件')
    target=Path(args[2]).resolve()
    work=(scratch/'workspace').resolve()
    if not target.is_relative_to(work) or target.suffix!='.py':
        raise PermissionError('运行文件必须位于代码工作目录中')
    source=target.read_text(encoding='utf-8')
    tree=ast.parse(source,filename=str(target))
    imports={'math','re','statistics','json','dataclasses','typing','collections'}
    for node in ast.walk(tree):
        if isinstance(node,ast.Import) and any(alias.name.split('.')[0] not in imports for alias in node.names):raise PermissionError('网页运行的 Python 文件包含不支持的导入')
        if isinstance(node,ast.ImportFrom) and (node.module or '').split('.')[0] not in imports:raise PermissionError('网页运行的 Python 文件包含不支持的导入')
        if isinstance(node,ast.Attribute) and node.attr.startswith('_'):raise PermissionError('网页运行不允许访问内部属性')
        if isinstance(node,ast.Name) and node.id in {'eval','exec','compile','__import__','globals','locals','getattr','setattr','breakpoint'}:raise PermissionError('网页运行不允许动态执行')
    deadline=time.monotonic()+min(max(timeout,.01),10)
    def trace(frame,event,arg):
        if time.monotonic()>deadline:raise subprocess.TimeoutExpired(args,timeout)
        return trace
    out,err=io.StringIO(),io.StringIO();code=0
    previous_trace=sys.gettrace();command_context=True
    try:
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            sys.settrace(trace)
            try:exec(compile(tree,str(target),'exec'),{'__name__':'__main__','__file__':str(target)})
            except subprocess.TimeoutExpired:raise
            except SystemExit as error:code=int(error.code or 0)
            except Exception:code=1;traceback.print_exc()
    finally:
        sys.settrace(previous_trace);command_context=False
    return subprocess.CompletedProcess(args,code,out.getvalue(),err.getvalue())


subprocess.run=bounded_python


def audit(event, args):
    if event.startswith(('subprocess.', 'os.system', 'os.spawn', 'os.fork', 'os.exec', '_winapi.CreateProcess', 'ctypes.dlopen')):
        raise PermissionError('网页中的代码不允许启动外部进程')
    if event.startswith('socket.') and (not live or command_context):
        raise PermissionError('离线检查不允许联网')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        target = Path(os.fsdecode(args[0])).resolve()
        if command_context and '.env' in target.parts:raise PermissionError('命令工具不能访问模型配置')
        mode = args[1]
        flags = args[2] if len(args) > 2 else 0
        write = bool(isinstance(mode, str) and any(x in mode for x in 'wax+')) or bool(isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        roots = [scratch, data_root] if write and live else [scratch] if write else allowed_read
        if not any(target == root or target.is_relative_to(root) for root in roots):
            raise PermissionError('只能访问当前项目文件')
    if event.startswith(('os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.listdir', 'os.scandir', 'sqlite3.connect')):
        for value in args[:2] if event == 'os.rename' else args[:1]:
            if isinstance(value, (str, bytes, os.PathLike)) and value != ':memory:':
                if str(value).startswith('file:'):
                    raise PermissionError('不允许 SQLite URI')
                target = Path(os.fsdecode(value)).resolve()
                roots = [scratch, data_root] if live else [scratch]
                if not any(target == root or target.is_relative_to(root) for root in roots):
                    # Dependency discovery may list installed package directories.
                    if event in {'os.listdir', 'os.scandir'} and any(target.is_relative_to(root) for root in allowed_read):
                        continue
                    raise PermissionError('只能访问当前项目目录')
    if event in {'os.symlink', 'os.link', 'sqlite3.load_extension', 'sqlite3.enable_load_extension'}:
        raise PermissionError('不允许链接文件或数据库扩展')


sys.addaudithook(audit)
sys.path.insert(0, str(scratch))
output = io.StringIO()
original_stdout = sys.stdout
def emit(event):
    if event.get('type')=='tool_end':
        updates={}
        for path in (scratch/'workspace').rglob('*'):
            if not path.is_file() or path.suffix.lower() not in text_suffixes:continue
            name=path.relative_to(scratch).as_posix();initial=workspace_initial.get(name)
            if path.exists() and path.stat().st_size<=100000:
                current=path.read_text(encoding='utf-8')
                if current!=initial:
                    updates[name]=current
                    workspace_initial[name]=current
        if updates:
            original_stdout.write(json.dumps({'updates':updates},ensure_ascii=False)+'\n')
    original_stdout.write(json.dumps({'event': event}, ensure_ascii=False) + '\n')
    original_stdout.flush()
sys.stdout = output
try:
    if live:
        result = agent_checks.live_run(payload, emit, data_root)
        chapter=agent_checks.LESSONS.get(payload['chapterId'],{})
        editable=chapter.get('inputLabel','question')
        result['inputs']=[{**field,'text':payload.get('question',chapter.get('question','')) if field['name']==editable else field['text']}
                          for field in chapter.get('panelInputs',[])]
        result['expected']=chapter.get('runtimeOutput','')
        result['expectedLabel']='输出要求'
    else:
        result = agent_checks.check(payload['chapterId'], example_only=payload['mode']=='run')
    result['stdout'] = output.getvalue()[-20000:]
except Exception as error:
    result = {'verdict': 'CE' if isinstance(error, SyntaxError) else 'RE', 'message': ''.join(traceback.format_exception(error))[-8000:], 'cases': [], 'stdout': output.getvalue()[-20000:]}
finally:
    sys.stdout = original_stdout
print(json.dumps({'result': result}, ensure_ascii=False), flush=True)
