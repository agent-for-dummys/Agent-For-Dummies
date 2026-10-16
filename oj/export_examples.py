"""Refresh the two public examples from the same test factories used by the judge."""
import json
from pathlib import Path
from worker import COURSE, namespace, describe, grade
from cases import make_case
for problem in COURSE['problems']:
    ns=namespace();exec(problem['solution'],ns)
    previous=problem.get('examples',[])
    problem['examples']=[{'input':describe(make_case(problem['id'],i)),'output':describe(ns[problem['entry']](*make_case(problem['id'],i))),**({'explanation':previous[i]['explanation']} if i<len(previous) and previous[i].get('explanation') else {})} for i in range(2)]
for module in COURSE['modules']:
    for lesson in module['lessons']:
        result=grade({'kind':'example','code':lesson['code']})
        if result['verdict']!='OK':raise RuntimeError(f"{lesson['name']}: {result.get('message')}")
        lesson['output']=result['stdout'].strip()
Path(__file__).with_name('course.json').write_text(json.dumps(COURSE,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Exported public examples for',len(COURSE['problems']),'problems.')
