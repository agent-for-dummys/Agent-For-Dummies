"""Bounded, credential-free snapshots of student function inputs and returns."""
import re
import sys
import json
import threading
from functools import lru_cache
from contextlib import contextmanager
from pathlib import Path


def value_text(value,depth=0):
    if depth>4:return '...'
    if isinstance(value,str):return repr(value[:4000]+('…' if len(value)>4000 else ''))
    if value is None or isinstance(value,(bool,int,float)):return repr(value)
    if isinstance(value,Path):
        try:return repr(value.resolve().relative_to(Path.cwd()).as_posix())
        except ValueError:return repr(value.name)
    if isinstance(value,(list,tuple)):
        items=[value_text(item,depth+1) for item in value[:20]]
        if len(value)>20:items.append('...')
        return '['+', '.join(items)+']'
    if isinstance(value,dict):
        items=[]
        for key,item in list(value.items())[:20]:
            hidden=isinstance(item,str) and re.search(r'key|secret|password|token',str(key),re.I)
            items.append(repr(key)+': '+("'••••'" if hidden else value_text(item,depth+1)))
        if len(value)>20:items.append('...')
        return '{'+', '.join(items)+'}'
    if type(value).__module__.startswith('langchain_core.messages'):
        fields=['content='+value_text(value.content,depth+1)]
        if getattr(value,'tool_calls',None):fields.append('tool_calls='+value_text(value.tool_calls,depth+1))
        if hasattr(value,'tool_call_id'):fields.append('tool_call_id='+repr(value.tool_call_id))
        return type(value).__name__+'('+', '.join(fields)+')'
    if type(value).__module__.startswith('langchain_core.documents'):
        return 'Document(page_content='+value_text(value.page_content,depth+1)+')'
    if type(value).__module__.startswith('pydantic') or hasattr(type(value),'model_fields'):
        # Avoid serializing model clients, callback managers, or their credentials.
        if type(value).__module__.startswith(('practice.','mini_pi.')):
            return value_text(value.model_dump(),depth+1)
    if callable(value):return '<'+getattr(value,'__name__',type(value).__name__)+'>'
    return '<'+type(value).__name__+'>'


def field(name,value):
    return {'name':name,'type':type(value).__name__,'text':value_text(value)}


@contextmanager
def capture_call(module_name,function):
    snapshot={}
    previous=sys.getprofile()
    previous_threads=threading.getprofile()
    def profile(frame,event,arg):
        if previous:previous(frame,event,arg)
        if frame.f_globals.get('__name__')!=module_name or frame.f_code.co_name!=function:return
        if event=='call':
            names=frame.f_code.co_varnames[:frame.f_code.co_argcount+frame.f_code.co_kwonlyargcount]
            inputs=[]
            for name in names:
                if name=='self':
                    obj=frame.f_locals.get(name)
                    for attr in ['entries','pending','calls','tokens','max_calls','max_tokens']:
                        if hasattr(obj,attr):inputs.append(field('self.'+attr,getattr(obj,attr)))
                elif name in frame.f_locals:inputs.append(field(name,frame.f_locals[name]))
            snapshot['inputs']=inputs
        elif event=='return':
            snapshot['actual']=value_text(arg)
    threading.setprofile_all_threads(profile)
    try:yield snapshot
    finally:
        threading.setprofile_all_threads(previous_threads)
        sys.setprofile(previous)


def target_name(chapter):
    chapter=chapter or {}
    signature=chapter.get('interface',{}).get('function','').split('(')[0].split()
    name=chapter.get('focus') or (signature[-1] if signature else '')
    return {'edges':'build_graph','assembly':'build_project'}.get(name,name.split('.')[-1])


def attach(snapshot,chapter,expected=None):
    result={}
    if snapshot.get('inputs') is not None:result['inputs']=snapshot['inputs']
    if 'actual' in snapshot:result['actual']=snapshot['actual']
    if expected is not None:
        result['expected']=value_text(expected)
        result['expectedLabel']='预期输出'
    else:
        result['expected']=chapter.get('interface',{}).get('returns','').replace('`','')
        result['expectedLabel']='输出要求'
    return result


@lru_cache(maxsize=1)
def chapters():
    data=json.loads(Path(__file__).with_name('agent_course.json').read_text(encoding='utf-8'))
    return {chapter['id']:chapter for chapter in data['chapters']}
