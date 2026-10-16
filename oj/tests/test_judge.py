import json
import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from worker import COURSE,PROBLEMS,grade,namespace
from cases import make_case
from executor import execute
from policy import validate,PolicyError

def reference(problem_id,*args):
    problem=PROBLEMS[problem_id];scope=namespace();exec(problem['solution'],scope)
    return scope[problem['entry']](*args)

class CurriculumTests(unittest.TestCase):
    def test_all_reference_answers_and_cases(self):
        self.assertEqual(len(COURSE['modules']),6)
        self.assertEqual(sum(p.get('kind','problem')=='problem' for p in COURSE['problems']),30)
        self.assertEqual(sum(p.get('kind')=='practice' for p in COURSE['problems']),80)
        self.assertEqual(sum(p.get('kind')=='variation' for p in COURSE['problems']),30)
        for problem in COURSE['problems']:
            with self.subTest(problem=problem['id']):
                result=grade({'kind':'submit','problemId':problem['id'],'code':problem['solution']})
                self.assertEqual(result['verdict'],'AC',result)
                self.assertEqual(result['passed'],6)
                self.assertEqual(len(problem['examples']),2)
                self.assertTrue(problem['parameters'] and problem['ranges'] and problem['analysis'])
                self.assertTrue(all('input' not in case for case in result['cases'][2:]))

    def test_all_function_examples_execute(self):
        for module in COURSE['modules']:
            for lesson in module['lessons']:
                with self.subTest(function=lesson['name']):
                    result=grade({'kind':'example','code':lesson['code']})
                    self.assertEqual(result['verdict'],'OK',result)
                    self.assertTrue(result['stdout'])
                    self.assertEqual(lesson['output'],result['stdout'].strip())
                    self.assertEqual(len(lesson['practices']),2)
                    for pid in lesson['practices']:self.assertEqual(PROBLEMS[pid]['kind'],'practice')

    def test_known_sgd_step(self):
        w,b,loss=reference('P11',*make_case('P11',0))
        torch.testing.assert_close(w,torch.tensor([1.8]))
        torch.testing.assert_close(b,torch.tensor(.5))
        torch.testing.assert_close(loss,torch.tensor(6.5))

    def test_transfer_conditions_reject_original_solution(self):
        for pid in ['P01','P02','P11','P15','P16','P18','P27','P29']:
            variant=PROBLEMS['V'+pid[1:]]
            code=PROBLEMS[pid]['solution'].replace(PROBLEMS[pid]['entry'],variant['entry'])
            with self.subTest(parent=pid):
                result=grade({'kind':'submit','problemId':variant['id'],'code':code})
                self.assertEqual(result['verdict'],'WA',result)

    def test_padding_embedding_checks_gradient(self):
        problem=PROBLEMS['F11B']
        code=problem['solution'].replace(',padding_idx=0','').replace(', padding_idx=0','')
        result=grade({'kind':'submit','problemId':'F11B','code':code})
        self.assertEqual(result['verdict'],'WA',result)
        self.assertTrue(any('梯度' in case.get('message','') for case in result['cases']))

    def test_layer_norm_probe_is_not_constant_sum(self):
        from worker import gradients
        x=torch.zeros(2,3,requires_grad=True)
        expected=torch.nn.functional.layer_norm(x,(3,))
        fake=torch.nn.functional.layer_norm(x.detach(),(3,))+x*0
        correct=gradients(expected,[x])[0];wrong=gradients(fake,[x])[0]
        self.assertFalse(torch.allclose(correct,wrong))

    def test_group_mean_keeps_small_positive_weight(self):
        out=reference('V22',torch.tensor([[2.],[4.]],dtype=torch.float64),torch.tensor([0,0]),2,torch.tensor([1e-13,1e-13],dtype=torch.float64))
        torch.testing.assert_close(out,torch.tensor([[3.],[0.]],dtype=torch.float64))

    def test_attention_against_torch_sdpa(self):
        for index in range(6):
            q,k,v,valid=make_case('P13',index)
            allowed=torch.ones(q.size(-2),q.size(-2),dtype=torch.bool).tril() & valid[:,None,None,:]
            expected=torch.nn.functional.scaled_dot_product_attention(q,k,v,attn_mask=allowed,dropout_p=0)*valid[:,None,:,None]
            torch.testing.assert_close(reference('P13',q,k,v,valid),expected,rtol=2e-4,atol=2e-5)

    def test_nucleus_crossing_and_stable_ties(self):
        torch.testing.assert_close(reference('P17',torch.tensor([.1,.6,.3]).log(),.7,1.),torch.tensor([0.,2/3,1/3]))
        torch.testing.assert_close(reference('P17',torch.zeros(4),.6,1.),torch.tensor([1/3,1/3,1/3,0.]))

    def test_shifted_loss_is_aligned(self):
        logits,labels,mask=make_case('P16',0)
        self.assertLess(reference('P16',logits,labels,mask).item(),.1)
        self.assertGreater(torch.nn.functional.cross_entropy(logits.reshape(-1,3),labels.reshape(-1)).item(),3.)

    def test_common_wrong_answers_rejected(self):
        mutations={
            'P01':'import torch\ndef make_grid(rows, cols):\n    return torch.zeros(rows, cols)\n',
            'P08':PROBLEMS['P08']['solution'].replace('return padded, valid','return padded, padded != 0'),
            'P14':PROBLEMS['P14']['solution'].replace('weight.detach()','weight'),
            'P12':PROBLEMS['P12']['solution'].replace('logits.sum() * 0','torch.tensor(0., dtype=logits.dtype)'),
            'P11':PROBLEMS['P11']['solution'].replace('return w.detach(), b.detach(), loss.detach()','return w, b, loss'),
            'P17':PROBLEMS['P17']['solution'].replace('values.cumsum(-1) - values < top_p','values.cumsum(-1) <= top_p'),
        }
        for pid,code in mutations.items():
            with self.subTest(problem=pid):self.assertNotEqual(grade({'kind':'submit','problemId':pid,'code':code})['verdict'],'AC')
        self.assertEqual(grade({'kind':'run','problemId':'P01','code':'def make_grid('})['verdict'],'CE')
        self.assertEqual(grade({'kind':'run','problemId':'P01','code':'def make_grid(rows, cols):\n    raise ValueError("错误")'})['verdict'],'RE')
        code=PROBLEMS['P12']['solution'].replace('valid = labels != -100','logits.requires_grad_(False)\n    valid = labels != -100')
        self.assertNotEqual(grade({'kind':'submit','problemId':'P12','code':code})['verdict'],'AC')

    def test_policy_blocks_system_access(self):
        for code in ['import os','from torch import save','import torch\ntorch.save(1,"out")','print(torch.__dict__)','from math import __dict__']:
            with self.subTest(code=code),self.assertRaises(PolicyError):validate(code)

    def test_common_tensor_apis_execute_in_real_environment(self):
        code='''import torch
import torch.linalg as LA
import torch.special as S
x = torch.tensor([[1., 3.], [5., 7.]])
print(x.amin(dim=0), torch.aminmax(x), torch.std_mean(x, dim=0, correction=0))
print(torch.isclose(x, x), torch.nan_to_num(x), x.prod(dim=1))
print(torch.broadcast_tensors(x, torch.ones(2)), x.movedim(0, 1))
print(torch.take_along_dim(x, torch.tensor([[1], [0]]), dim=1))
print(LA.vector_norm(x, dim=1), S.expit(x))
print(sorted([3, 1]), all([True, True]), any([False, True]))
'''
        # expit is a common torch.special function as well.
        result=grade({'kind':'example','code':code})
        self.assertEqual(result['verdict'],'OK',result)

    def test_normalization_boundaries_against_independent_decimal_arithmetic(self):
        from decimal import Decimal, localcontext
        for pid in ['V02','P29','V29']:
            for i in range(6):
                x,=make_case(pid,i)
                with self.subTest(problem=pid,case=i),localcontext() as context:
                    context.prec=90
                    data=[[Decimal.from_float(float(v)) for v in row] for row in x.tolist()]
                    expected=[[Decimal(0) for _ in row] for row in data]
                    if pid=='V02':
                        for j in range(x.size(1)):
                            column=[row[j] for row in data]
                            mean=sum(column)/len(column)
                            std=(sum((v-mean)**2 for v in column)/len(column)).sqrt()
                            for r,v in enumerate(column):expected[r][j]=(v-mean)/std if std else Decimal(0)
                    else:
                        for r in range(x.size(0)):data[r]=[max(v,Decimal(0)) for v in data[r]]
                        for r in range(x.size(0)):
                            for j in range(x.size(1)):
                                total=sum(data[r]) if pid=='P29' else sum(row[j] for row in data)
                                expected[r][j]=data[r][j]/total if total else Decimal(0)
                    expected=torch.tensor([[float(v) for v in row] for row in expected],dtype=x.dtype)
                    actual=reference(pid,x)
                    self.assertTrue(torch.isfinite(actual).all())
                    torch.testing.assert_close(actual,expected,rtol=2e-5,atol=2e-6)

    def test_fixed_epsilon_normalization_answers_are_rejected(self):
        old_answers={
            'V02':'def standardize_columns(x):\n    return (x-x.mean(0,keepdim=True))/x.std(0,keepdim=True,correction=0).clamp_min(1e-12)',
            'P29':'def clamp_and_normalize(x):\n    y=x.clamp_min(0)\n    return y/y.sum(1,keepdim=True).clamp_min(1e-12)',
            'V29':'def normalize_columns(x):\n    y=x.clamp_min(0)\n    return y/y.sum(0,keepdim=True).clamp_min(1e-12)',
        }
        for pid,code in old_answers.items():
            with self.subTest(problem=pid):self.assertEqual(grade({'kind':'submit','problemId':pid,'code':code})['verdict'],'WA')

    def test_failed_cases_include_actionable_details(self):
        code=PROBLEMS['P01']['solution'].replace('return torch.arange', 'return 1 + torch.arange')
        result=grade({'kind':'submit','problemId':'P01','code':code})
        self.assertEqual(result['verdict'],'WA')
        for case in result['cases']:
            self.assertEqual(case['status'],'failed')
            self.assertTrue(case['message'])
            self.assertIn('input',case)
            self.assertIn('expected',case)
            self.assertIn('actual',case)
        result=grade({'kind':'submit','problemId':'P01','code':'def make_grid(rows, cols):\n    raise ValueError("测试错误")'})
        self.assertEqual(result['verdict'],'RE')
        self.assertEqual(result['cases'][0]['line'],2)
        self.assertIn('expected',result['cases'][0])
        self.assertIn('input',result['cases'][0])

    def test_run_compares_full_outputs_exactly(self):
        correct=grade({'kind':'run','problemId':'P02','code':PROBLEMS['P02']['solution']})
        self.assertTrue(all(case['matchesExpected'] for case in correct['cases']))
        code=PROBLEMS['P02']['solution'].replace('return x - x.mean(dim=0, keepdim=True)','return x - x.mean(dim=0, keepdim=True) + 1e-6')
        result=grade({'kind':'run','problemId':'P02','code':code})
        self.assertEqual(result['verdict'],'WA')
        self.assertFalse(result['cases'][0]['matchesExpected'])
        self.assertIn('不完全一致',result['cases'][0]['message'])
        # Submission judging still permits the numerical tolerance needed by equivalent algorithms.
        self.assertEqual(grade({'kind':'submit','problemId':'P02','code':code})['verdict'],'AC')

@unittest.skipUnless(os.environ.get('OJ_TEST_EXECUTOR')=='1','Set OJ_TEST_EXECUTOR=1 for isolated-process integration tests.')
class ProcessTests(unittest.TestCase):
    def test_utf8_and_real_pytorch(self):
        result=execute({'kind':'example','code':'import torch\nprint("中文输出", torch.arange(3))'})
        self.assertEqual(result['verdict'],'OK',result)
        self.assertIn('中文输出 tensor([0, 1, 2])',result['stdout'])

    def test_real_submission_and_optimizer(self):
        for pid in ['P01','P10','P11','P13','P18']:
            with self.subTest(problem=pid):
                result=execute({'kind':'submit','problemId':pid,'code':PROBLEMS[pid]['solution']})
                self.assertEqual(result['verdict'],'AC',result)
                self.assertEqual(result['cases'][0]['name'],'公开用例 1')

    def test_loop_timeout_is_bounded(self):
        start=time.monotonic()
        result=execute({'kind':'example','code':'while True:\n    pass'},timeout=15)
        self.assertEqual(result['verdict'],'TLE',result)
        self.assertLess(result['elapsedMs'],18000)
        self.assertLess(time.monotonic()-start,78)

if __name__=='__main__':unittest.main()
