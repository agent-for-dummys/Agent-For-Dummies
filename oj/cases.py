"""Deterministic public/boundary cases. Kept on the judge, not shipped as test inputs."""
import torch
from extended_cases import extended_case

def make_case(problem_id, index):
    torch.manual_seed(7301 + index)
    dtype = torch.float64 if index == 3 else torch.float32
    rand = lambda *shape: torch.randn(*shape, dtype=dtype)
    tensor = lambda data: torch.tensor(data, dtype=dtype)
    grad = lambda x: x.requires_grad_(True)
    i = index
    if problem_id == 'P01': return [(2,3),(1,1),(3,4),(4,2),(1,7),(5,1)][i]
    if problem_id == 'P02': return (tensor([[1,3],[5,7]]) if i == 0 else torch.ones(3,2,dtype=dtype) if i == 1 else rand(1+i,2+i%3),)
    if problem_id == 'P03': return ([tensor([1,2]),tensor([3,4])] if i == 0 else [tensor([5,6,7])] if i == 1 else [rand(2+i) for _ in range(1+i%4)],)
    if problem_id == 'P04':
        b,t,h,d = [(1,3,2,2),(1,1,1,3),(2,4,3,2),(3,2,2,3),(2,3,2,2),(2,1,4,1)][i]
        x = torch.arange(b*t*h*d,dtype=dtype).reshape(b,t,h*d)
        if i == 4: x = x.transpose(1,2).contiguous().transpose(1,2)
        return x,h
    if problem_id == 'P05':
        if i == 0: return torch.arange(12,dtype=dtype).reshape(2,2,3),torch.tensor([[0,2],[1,0]])
        if i == 1: return tensor([[[10,20,30],[40,50,60]]]),torch.tensor([[2,0]])
        b,t,c = 1+i%3,1+i%4,2+i
        return rand(b,t,c),torch.randint(c,(b,t))
    if problem_id == 'P06':
        return [(torch.tensor([3,1,0]),4),(torch.tensor([0,2]),2),(torch.tensor([0,0]),0),(torch.tensor([5,3,1]),5),(torch.tensor([1]),1),(torch.tensor([0,4,2,4]),4)][i]
    if problem_id == 'P07':
        if i == 0: return tensor([[[1,2],[3,4],[99,99]]]),torch.tensor([[True,True,False]])
        if i == 1: return tensor([[[1,2],[3,4]]]),torch.tensor([[False,False]])
        b,t,d = 1+i%3,0 if i == 4 else 1+i,2+i%3
        return rand(b,t,d),torch.zeros(b,t,dtype=torch.bool) if i == 1 else torch.rand(b,t)>.4
    if problem_id == 'P08':
        groups = [[[2,4,6],[8]],[[0,2],[0]],[[1,2,3,4],[5,6],[7]],[[3],[4,5,6]], [[],[1,0,2]],[[],[]]]
        return ([torch.tensor(seq,dtype=torch.long) for seq in groups[i]],)
    if problem_id == 'P09':
        if i == 0: return tensor([[1,0],[0,1]]),tensor([[1,1],[1,0]])
        if i == 1: return tensor([[0,0],[1,0]]),tensor([[0,0],[1,0],[0,1]])
        q,d = rand(1+i%3,2+i),rand(2+i%4,2+i)
        if i in (1,4): q[0]=0;d[0]=0
        return q,d
    if problem_id == 'P10': return (tensor([2,-3]) if i == 0 else tensor([[-1,0,1],[2,-2,3]]) if i == 1 else rand(1+i%3,2+i%2),)
    if problem_id == 'P11':
        if i == 0: return tensor([[1],[2]]),tensor([3,5]),tensor([1]),tensor(0),.1
        if i == 1: return tensor([[1,0],[0,1]]),tensor([1,2]),tensor([0,0]),tensor(0),.1
        n,d = 1+i,2+i%2
        return rand(n,d),rand(n),rand(d),tensor(.5),[.1,.01,.05,.2,.03,.001][i]
    if problem_id == 'P12':
        if i == 0: return grad(tensor([[[2,0],[0,2],[10,-10]]])),torch.tensor([[0,1,-100]])
        if i == 1: return grad(tensor([[[1,2],[3,4]]])),torch.tensor([[-100,-100]])
        b,t,v=1+i%2,1+i%3,2+i
        labels=torch.randint(v,(b,t))
        if i==1:labels.fill_(-100)
        elif i==4:labels[:,0]=-100
        return grad(rand(b,t,v)),labels
    if problem_id == 'P13':
        if i in (0,1):
            q=torch.eye(3,dtype=dtype).reshape(1,1,3,3)
            v=tensor([[[[1,0],[0,1],[1,1] if i==0 else [99,99]]]])
            return grad(q.clone()),grad(q.clone()),grad(v),torch.tensor([[True,True,i==0]])
        b,h,t,d,dv=[(1,1,3,3,2),(1,1,3,2,2),(2,2,4,3,5),(2,1,2,2,3),(1,2,1,4,2),(2,3,3,2,4)][i]
        q,k=rand(b,h,t,d),rand(b,h,t,d)
        if i==0:q=k=torch.eye(3,dtype=dtype).reshape(1,1,3,3)
        valid=torch.ones(b,t,dtype=torch.bool)
        if i==1:valid[:,-1]=False
        elif i==2:valid[0]=False;valid[1,0]=False
        elif i==5:valid[:,1]=False
        if i==3:q=q*100;k=k*100
        return grad(q.clone()),grad(k.clone()),grad(rand(b,h,t,dv)),valid
    if problem_id == 'P14':
        if i in (0,1):return grad(tensor([[1,2]])),grad(torch.eye(2,dtype=dtype)),grad(tensor([[1,0]])),grad(tensor([[1],[2]]) if i==0 else tensor([[0],[0]])),2.
        din,dout,r=3+i%2,4+i%3,1+i%3
        x=rand(2,din) if i!=4 else rand(2,3,din)
        w,a,b=rand(dout,din),rand(r,din),rand(dout,r)
        if i==1:b.zero_()
        return grad(x),grad(w),grad(a),grad(b),0. if i==5 else 2.+i
    if problem_id == 'P15':
        if i==0:return grad(torch.eye(2,dtype=dtype)),grad(torch.eye(2,dtype=dtype)),1.
        if i==1:return grad(tensor([[1,0]])),grad(tensor([[0,1]])),.5
        b,d=1 if i==1 else 2+i%3,3+i%2
        q,doc=rand(b,d),rand(b,d)
        if i==4:q[0]=0;doc[0]=0
        return grad(q),grad(doc),[.5,.1,.07,.3,1.,.8][i]
    if problem_id == 'P16':
        if i==0:return grad(tensor([[[0,3,0],[0,0,3],[3,0,0]]])),torch.tensor([[0,1,2]]),torch.ones(1,3,dtype=torch.bool)
        if i==1:return grad(tensor([[[1,2]]])),torch.tensor([[1]]),torch.tensor([[True]])
        b,t,v=1+i%2,1 if i==1 else 4,3+i
        labels=torch.randint(v,(b,t));valid=torch.ones(b,t,dtype=torch.bool)
        if i==2:valid.zero_()
        elif i==3:labels[:,1]=-100
        elif i==4:valid[:,0]=False;valid[:,-1]=False
        return grad(rand(b,t,v)),labels,valid
    if problem_id == 'P17':
        if i==0:return tensor([.1,.6,.3]).log(),.7,1.
        if i==1:return tensor([1.,2.,3.]),.01,1.
        if i==2:return rand(7),1.,.5
        if i==3:return tensor([1.,1.,1.,1.]),.6,1.
        if i==4:return tensor([10000.,0.,-10000.]),.9,1.
        return rand(9),.85,1.7
    if problem_id == 'P18':
        if i==0:return grad(tensor([[[[1,0]]]])),grad(tensor([[[[0,1]]]])),grad(tensor([[[[0,1]]]])),grad(tensor([[[[1,0]]]])),grad(tensor([[[[1,0]]]]))
        if i==1:return grad(tensor([[[[0,1]]]])),grad(tensor([[[[1,0]]]])),grad(tensor([[[[2,3]]]])),None,None
        b,h,d,dv=1+i%2,1+i%3,2+i%2,3+i%2
        q,k,v=grad(rand(b,h,1,d)),grad(rand(b,h,1,d)),grad(rand(b,h,1,dv))
        past=[2,None,0,4,1,5][i]
        return q,k,v,None if past is None else grad(rand(b,h,past,d)),None if past is None else grad(rand(b,h,past,dv))
    return extended_case(problem_id,index,make_case)

def case_name(index):
    return ['公开用例 1','公开用例 2','批次与维度','双精度计算','边界输入','梯度与重复调用'][index]
