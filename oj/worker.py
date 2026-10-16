import contextlib
import io
import json
import sys
import time
import math
import os
import signal
from pathlib import Path
import torch
from cases import make_case, case_name
from policy import validate, namespace, PolicyError

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
COURSE=json.loads(Path(__file__).with_name('course.json').read_text(encoding='utf-8'))
PROBLEMS={p['id']:p for p in COURSE['problems']}

class LimitedOutput(io.StringIO):
    def write(self,text):
        remaining=8000-self.tell()
        if remaining>0:super().write(str(text)[:remaining])
        return len(text)

def clone(value):
    if isinstance(value,torch.Tensor):return value.detach().clone().requires_grad_(value.requires_grad)
    if isinstance(value,list):return [clone(v) for v in value]
    if isinstance(value,tuple):return tuple(clone(v) for v in value)
    return value

def describe(value):
    if isinstance(value,torch.Tensor):
        flat=value.detach().flatten()
        data=value.detach().tolist() if flat.numel()<=40 else flat[:20].tolist()
        def finite(item):
            if isinstance(item,list):return [finite(v) for v in item]
            if isinstance(item,float) and not math.isfinite(item):return str(item)
            return item
        data=finite(data)
        return {'shape':list(value.shape),'dtype':str(value.dtype).replace('torch.',''),'data':data,**({'truncated':True} if flat.numel()>40 else {})}
    if isinstance(value,(list,tuple)):return [describe(v) for v in value]
    return value

def same(got,expected,check_flags=False):
    if isinstance(expected,torch.Tensor):
        if not isinstance(got,torch.Tensor):return False,'应返回 torch.Tensor。'
        if got.shape!=expected.shape:return False,f'输出形状不符，期望 {list(expected.shape)}。'
        if got.dtype!=expected.dtype:return False,f'dtype 不符，期望 {expected.dtype}。'
        if check_flags and got.requires_grad!=expected.requires_grad:return False,'请勿改变输入的 requires_grad 状态。'
        if not torch.allclose(got.detach(),expected.detach(),rtol=2e-4,atol=2e-5,equal_nan=False):return False,'输出数值不匹配。'
        return True,''
    if isinstance(expected,(list,tuple)):
        if not isinstance(got,(list,tuple)) or len(got)!=len(expected):return False,'返回结构或元素数量不符。'
        for g,e in zip(got,expected):
            ok,why=same(g,e,check_flags=check_flags)
            if not ok:return ok,why
        return True,''
    return got==expected,'返回值不匹配。'

def tensors(value):
    if isinstance(value,torch.Tensor):return [value]
    if isinstance(value,(list,tuple)):return [t for v in value for t in tensors(v)]
    return []

def exact_output(got,expected):
    if isinstance(expected,torch.Tensor):
        return isinstance(got,torch.Tensor) and got.dtype==expected.dtype and got.shape==expected.shape and torch.equal(got.detach(),expected.detach())
    if isinstance(expected,(list,tuple)):
        return isinstance(got,(list,tuple)) and len(got)==len(expected) and all(exact_output(g,e) for g,e in zip(got,expected))
    return got==expected

def gradients(value,inputs):
    leaves=[v for v in tensors(inputs) if v.requires_grad]
    outputs=[v for v in tensors(value) if v.requires_grad]
    if not leaves:return []
    if not outputs:return [None for _ in leaves]
    # Different output positions need different probes: softmax / LayerNorm sums can be constant.
    loss=sum((v*torch.arange(1,v.numel()+1,dtype=v.dtype,device=v.device).reshape(v.shape)).sum() for v in outputs)
    return torch.autograd.grad(loss,leaves,allow_unused=True)

def grade(payload):
    started=time.perf_counter();out=LimitedOutput()
    problem=PROBLEMS.get(payload.get('problemId'))
    if payload['kind']!='example' and not problem:return {'verdict':'CE','message':'题目不存在。','cases':[]}
    code=payload['code']
    try:
        tree=validate(code,problem if payload['kind']!='example' else None)
        ns=namespace()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):exec(compile(tree,'<submission>','exec'),ns)
        if payload['kind']=='example':return {'verdict':'OK','stdout':out.getvalue(),'cases':[],'elapsedMs':round((time.perf_counter()-started)*1000)}
        student=ns[problem['entry']]
        reference_ns=namespace();exec(problem['solution'],reference_ns);reference=reference_ns[problem['entry']]
        results=[]
        for index in range(2 if payload['kind']=='run' else 6):
            args=make_case(problem['id'],index);user_args=clone(args);expected_args=clone(args);before=clone(user_args)
            case={'name':case_name(index),'public':index<2}
            torch.manual_seed(101+index)
            expected=reference(*expected_args)
            try:
                torch.manual_seed(101+index)
                with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):got=student(*user_args)
                ok,why=same(got,expected)
                exact=exact_output(got,expected)
                if payload['kind']=='run' and ok and not exact:ok=False;why='输出与预期结果不完全一致。'
                unchanged,mutation=same(user_args,before,check_flags=True)
                if not unchanged:ok=False;why=mutation if 'requires_grad' in mutation else '请勿原地修改输入。'
                if ok and problem.get('detachedOutput') and any(t.requires_grad for t in tensors(got)):ok=False;why='本题的返回值需要 detach。'
                if ok and tensors(expected_args) and any(t.requires_grad for t in tensors(expected_args)):
                    g_grad=gradients(got,user_args);e_grad=gradients(expected,expected_args)
                    for g,e in zip(g_grad,e_grad):
                        if e is None:
                            if g is not None:ok=False;why='应冻结的参数仍收到梯度。';break
                        elif g is None:ok=False;why='梯度通路被切断。';break
                        elif not torch.allclose(g,e,rtol=4e-4,atol=5e-5):ok=False;why='梯度结果不匹配。';break
                case.update(status='passed' if ok else 'failed',message=why if not ok else '',matchesExpected=ok and exact)
                if index<2 or not ok:case.update(input=describe(args),expected=describe(expected),actual=describe(got))
            except Exception as error:
                case.update(status='error',message=f'{type(error).__name__}: {str(error)[:300]}',input=describe(args),expected=describe(expected))
                trace=error.__traceback__
                while trace:
                    if trace.tb_frame.f_code.co_filename=='<submission>':case['line']=trace.tb_lineno
                    trace=trace.tb_next
            results.append(case)
        passed=sum(c['status']=='passed' for c in results)
        verdict='AC' if passed==len(results) else 'RE' if any(c['status']=='error' for c in results) else 'WA'
        return {'verdict':verdict,'passed':passed,'total':len(results),'cases':results,'stdout':out.getvalue(),'elapsedMs':round((time.perf_counter()-started)*1000)}
    except (SyntaxError,PolicyError) as error:return {'verdict':'CE','message':str(error),'line':getattr(error,'lineno',None),'cases':[],'stdout':out.getvalue()}
    except Exception as error:return {'verdict':'RE','message':f'{type(error).__name__}: {str(error)[:300]}','cases':[],'stdout':out.getvalue()}

def audit(event,args):
    if event.startswith(('socket.','subprocess.','os.exec','os.spawn','ctypes.')) or event in {'os.system','os.remove','os.rename','os.mkdir','os.rmdir'}:raise PermissionError('练习进程不允许网络、文件修改或系统调用。')
    if event=='open':
        path,mode,flags=args
        if isinstance(path,(str,bytes)):
            resolved=Path(path).resolve()
            allowed=Path(torch.__file__).resolve().parents[1]
            if not resolved.is_relative_to(allowed) or any(c in str(mode) for c in 'wa+') or flags& (1|2|64|512):raise PermissionError('练习进程不允许读取项目文件或写文件。')

if __name__=='__main__':
    # Warm the optimizer's lazy Python imports before applying the audit boundary.
    p=torch.nn.Parameter(torch.tensor([1.]));optimizer=torch.optim.SGD([p],lr=.1);optimizer.zero_grad();(p*p).sum().backward();optimizer.step()
    print(json.dumps({'workerReady':True}),flush=True)
    payload=json.loads(sys.stdin.read(24000))
    if hasattr(signal,'SIGALRM'):
        signal.signal(signal.SIGALRM,signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL,float(os.environ.get('OJ_TIMEOUT_SECONDS','20')))
    sys.addaudithook(audit)
    result=grade(payload)
    sys.stdout.write(json.dumps(result,ensure_ascii=False,allow_nan=False))
