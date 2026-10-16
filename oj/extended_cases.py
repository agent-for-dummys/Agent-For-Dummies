"""Case families for function exercises and transfer problems; inputs stay on the judge."""
import json
from pathlib import Path
import torch

PROBLEMS={p['id']:p for p in json.loads(Path(__file__).with_name('course.json').read_text(encoding='utf-8'))['problems']}

def extended_case(problem_id,index,base_case):
    spec=PROBLEMS[problem_id].get('caseSpec')
    if not spec:raise KeyError(problem_id)
    i=index;dtype=torch.float64 if i==3 else torch.float32
    t=lambda v:torch.tensor(v,dtype=dtype)
    rand=lambda *shape:torch.randn(*shape,dtype=dtype)
    family=spec.get('family')
    if family=='standardize':
        samples=[
            [[1,3],[5,7]],
            [[.1,3],[.1,3],[.1,3]],
            [[0,1e-30,5],[2e-30,3e-30,5],[4e-30,5e-30,5]],
            [[0.,1e-300,999.9999999999],[2e-300,3e-300,1000.],[4e-300,5e-300,999.9999999998]],
            [[7.,-.1,0.]],
            [[1000.,-1000.,0.],[-1000.,1000.,0.],[0.,0.,0.]],
        ]
        args=(t(samples[i]),)
    elif family=='positive_weights':
        samples=[
            [[1,3],[5,7]],
            [[2,-2,0],[0,0,0],[-1,-4,-2]],
            [[1e-30,3e-30,-1],[2e-30,2e-30,0]],
            [[1e-300,3e-300,0],[2e-300,2e-300,-1]],
            [[2e38,2e38,0],[1e38,2e38,-1]],
            [[7],[0],[-3]],
        ]
        x=t(samples[i])
        args=(x.T.contiguous() if spec.get('columns') else x,)
    elif spec.get('source'):
        args=base_case(spec['source'],index)
        if spec.get('asymmetric') and i==0:
            args=(args[0],t([[1,0],[1,1]]).requires_grad_(True),args[2])
        if spec.get('uneven') and i==0:
            args=(t([[[0,3,0],[0,0,3],[3,0,0]],[[0,0,0],[0,0,0],[0,0,0]]]).requires_grad_(True),torch.tensor([[0,1,2],[0,1,2]]),torch.tensor([[True,True,True],[True,True,False]]))
        if spec.get('longHistory') and i==0:
            args=(*args[:3],t([[[[0,1],[1,0],[1,1]]]]).requires_grad_(True),t([[[[1,0],[0,1],[2,2]]]]).requires_grad_(True))
    elif family in ('matrix','numbers'):
        x=t([[1,3],[5,7]]) if i==0 else t([[2,-2,0]]) if i==1 else torch.zeros(2,3,dtype=dtype) if i==4 else rand(1+i%3,2+i%3)
        args=(x.tolist() if family=='numbers' else x,)
    elif family=='boolean':
        args=(torch.tensor([[True,False],[False,True]]) if i==0 else torch.tensor([[False,False]]) if i==1 else torch.rand(1+i%3,2+i%3)>.5,)
    elif family=='rows':
        x=t([[1,2],[3,4],[5,6]]) if i==0 else t([[7,8]]) if i==1 else rand(2+i,2+i%3)
        indices=torch.tensor([2,0]) if i==0 else torch.tensor([0,0]) if i==1 else torch.tensor([],dtype=torch.long) if i==4 else torch.randint(x.size(0),(1+i,))
        args=x,indices
    elif family=='pair':
        x=t([[1,0],[0,1]]) if i==0 else t([[1,2]]) if i==1 else rand(1+i%3,2+i%3)
        y=t([[1,2],[3,4]]) if i==0 else t([[3,4],[5,6]]) if i==1 else rand(2+i%3,2+i%2)
        args=x,y
    elif family in ('batched','batched_equal'):
        b,n,k,m=[(1,2,2,2),(2,1,2,1),(3,2,4,3),(2,3,2,4),(1,1,1,1),(2,4,3,2)][i]
        a=torch.arange(b*n*k,dtype=dtype).reshape(b,n,k)
        args=a,torch.ones_like(a) if family=='batched_equal' else torch.arange(b*k*m,dtype=dtype).reshape(b,k,m)
    elif family in ('categories','embedding'):
        labels,classes=[([0,2,1],3),([],4),([1,1,0],2),([0,3,2],4),([0],1),([2,0,2,1],3)][i]
        d=2 if i<2 else 1+i%4
        args=torch.tensor(labels,dtype=torch.long),classes if family=='categories' else torch.arange(classes*d,dtype=dtype).reshape(classes,d)
    elif family=='square_scores':
        args=(t([[2,0],[0,2]]) if i==0 else t([[3]]) if i==1 else rand(1+i%3,1+i%3),)
    elif family=='segments':
        if i==0:args=t([[1,2],[3,4],[5,6]]),torch.tensor([0,1,0]),3
        elif i==1:args=torch.empty(0,2,dtype=dtype),torch.tensor([],dtype=torch.long),2
        else:
            n,d,k=2+i,1+i%3,2+i%2
            args=rand(n,d),torch.randint(k,(n,)),k
    elif family=='linear':
        if i==0:args=t([[1,2]]),torch.eye(2,dtype=dtype),t([.5,-.5])
        elif i==1:args=t([[0,0],[1,1]]),t([[1,-1]]),t([2])
        else:
            n,d,o=1+i%3,2+i%2,1+i%3
            args=rand(n,d),rand(o,d),rand(o)
    elif family=='scores':
        x=t([[1,3,2],[-2,0,4]]) if i==0 else t([[2,2,1]]) if i==1 else t([[1000,0,-1000]]) if i==4 else rand(1+i%3,3+i%3)
        args=(x,)
    elif family=='softmask':
        x=t([[1,2,3],[3,2,1]]) if i==0 else t([[1,2,3]]) if i==1 else rand(1+i%3,2+i%3)
        mask=torch.tensor([[True,True,False],[False,False,False]]) if i==0 else torch.ones_like(x,dtype=torch.bool) if i==1 else torch.rand_like(x)>.5
        if i==4:mask.zero_()
        args=x,mask
    elif family=='binary':
        x=t([[0,2],[-2,0]]) if i==0 else t([[0,0]]) if i==1 else t([[1000,-1000]]) if i==4 else rand(1+i%3,2+i%2)
        targets=t([[0,1],[1,0]]) if i==0 else torch.zeros_like(x) if i==1 else torch.randint(2,x.shape).to(dtype)
        args=x,targets
        if spec.get('masked'):
            mask=torch.tensor([[True,True],[False,True]]) if i==0 else torch.zeros_like(x,dtype=torch.bool) if i in (1,4) else torch.rand_like(x)>.4
            args=(*args,mask)
        if spec.get('weighted'):args=(*args,torch.arange(1,x.size(-1)+1,dtype=dtype))
    elif family=='image':
        size=3 if i==0 else 2 if i==1 else 3+i%3
        b=1 if i<2 else 1+i%3
        x=torch.arange(b*size*size,dtype=dtype).reshape(b,1,size,size)
        if i>=2:x=x-x.mean()
        args=(x,)
        if spec.get('kernel'):args=(*args,torch.ones(1,1,spec.get('kernel',2),spec.get('kernel',2),dtype=dtype))
    elif family=='batchdata':
        x=t([[1,2],[3,4],[5,6]]) if i==0 else t([[7,8]]) if i==1 else rand(2+i,2+i%3)
        args=x,[2,4,1,3,2,4][i]
    elif family=='ffn':
        d,h=2+i%2,3+i%3
        if i==0:args=t([[1,2]]),t([[1,0],[0,1],[1,1]]),t([0,0,0]),t([[1,0,0],[0,1,0]]),t([0,0])
        elif i==1:args=torch.ones(2,d,dtype=dtype),torch.zeros(h,d,dtype=dtype),torch.zeros(h,dtype=dtype),torch.ones(d,h,dtype=dtype),torch.zeros(d,dtype=dtype)
        else:args=rand(1+i%3,d),rand(h,d),rand(h),rand(d,h),rand(d)
    else:raise ValueError(f'Unknown case family: {family}')
    args=tuple(args)
    if 'select' in spec:args=tuple(args[j] for j in spec['select'])
    if spec.get('gradInputs'):
        for j in spec['gradInputs']:
            if isinstance(args[j],torch.Tensor) and args[j].is_floating_point():args[j].requires_grad_(True)
    extras=[]
    for item in spec.get('extras',[]):
        if item=='bias':extras.append(torch.arange(args[1].size(0),dtype=dtype).requires_grad_(True))
        elif item=='labels':extras.append(torch.arange(args[0].size(0),dtype=torch.long)%args[1].size(0))
        elif item=='sample_weights':extras.append(torch.zeros(args[0].size(0),dtype=dtype) if i==4 else torch.arange(1,args[0].size(0)+1,dtype=dtype)*(1e-13 if i==3 else 1.))
        else:extras.append(item['values'][i] if isinstance(item,dict) and 'values' in item else item)
    return (*args,*extras)
