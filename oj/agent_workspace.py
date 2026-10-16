"""Local, per-browser project files. API never shares an existing root .env."""
import hashlib
import io
import json
import os
import threading
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSE = json.loads(Path(__file__).with_name('agent_course.json').read_text(encoding='utf-8'))
WORKSPACES = ROOT / '.agent-workspaces' / 'course-v3'
LOCK = threading.RLock()
TEXT_SUFFIXES={'.py','.md','.txt','.json','.yaml','.yml','.toml','.csv','.html','.css','.js','.ts','.sh'}


def valid_name(name):
    if name in COURSE['files']:return True
    if not isinstance(name,str) or '\\' in name or len(name)>240:return False
    if any(ord(char)<32 or char in '<>:"|?*' for char in name):return False
    if any(part.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for part in name.split('/')):return False
    path=Path(name)
    return name.startswith('workspace/') and path.as_posix()==name and path.suffix.lower() in TEXT_SUFFIXES and not any(part in {'..','.'} or part.startswith('.') for part in path.parts)


def directory(owner):
    target = WORKSPACES / hashlib.sha256(owner.encode()).hexdigest()
    if not target.resolve().is_relative_to(WORKSPACES.resolve()):
        raise ValueError('工作目录不正确')
    return target


def path_for(owner, name):
    if not valid_name(name):
        raise ValueError('文件不属于当前项目')
    root = directory(owner)
    target = root / name
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('文件路径不正确')
    return target


def initialize(owner):
    with LOCK:
        for name, content in COURSE['files'].items():
            path = path_for(owner, name)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding='utf-8')
            elif name=='.env':
                saved=path.read_text(encoding='utf-8')
                fields={line.split('=',1)[0].strip() for line in saved.splitlines() if '=' in line}
                additions=[line for line in COURSE['files']['.env'].splitlines()
                           if line.startswith(('WEATHER_API_KEY=','WEATHER_API_URL=')) and line.split('=',1)[0] not in fields]
                if additions:
                    path.write_text(saved+('' if saved.endswith('\n') else '\n')+'\n'.join(additions)+'\n',encoding='utf-8')


def read_files(owner):
    initialize(owner)
    with LOCK:
        names=list(COURSE['files'])
        root=directory(owner)
        for path in (root/'workspace').rglob('*'):
            if path.is_file():
                name=path.relative_to(root).as_posix()
                if valid_name(name) and name not in names:names.append(name)
        return {name: path_for(owner, name).read_text(encoding='utf-8') for name in names}


def write_file(owner, name, content):
    if len(content.encode('utf-8')) > 100_000:
        raise ValueError('单个文件不能超过 100 KB')
    initialize(owner)
    with LOCK:
        path = path_for(owner, name)
        all_files=read_files(owner)
        if name not in all_files and len(all_files)>=200:raise ValueError('项目文件数量达到上限')
        if sum(len(value.encode('utf-8')) for key,value in all_files.items() if key!=name)+len(content.encode('utf-8'))>1_200_000:raise ValueError('项目文件总大小超过 1.2 MB')
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary = path.with_name(path.name + '.saving')
        temporary.write_text(content, encoding='utf-8')
        os.replace(temporary, path)


def export_project(owner):
    files = read_files(owner)
    files['.env'] = COURSE['files']['.env']
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()
