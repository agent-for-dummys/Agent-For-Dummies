import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'oj'))
from agent_workspace import COURSE
from agent_executor import execute_project
from beginner_checks import live, check
from langchain_core.messages import AIMessage


class LearningProgressionTests(unittest.TestCase):
    def test_example_run_uses_one_case_while_submission_checks_all(self):
        lesson = next(ch for ch in COURSE['chapters'] if ch['id'] == 'weather_tool')
        files = dict(COURSE['files'])
        source = lesson['example'].replace('code = get_city_code(city)',
                                          'if city == "北京市":\n        return "错误的固定结果"\n    code = get_city_code(city)')
        files[lesson['file']] = source
        preview = execute_project({'files':files,'chapterId':'weather_tool','mode':'run'})
        submitted = execute_project({'files':files,'chapterId':'weather_tool','mode':'check'})
        self.assertEqual(preview['verdict'], 'AC', preview)
        self.assertEqual(preview['total'], 1)
        self.assertEqual(submitted['verdict'], 'WA', submitted)
        self.assertEqual(submitted['total'], 7)

    def test_offline_worker_runs_only_the_example_case(self):
        files=dict(COURSE['files'])
        lesson=next(ch for ch in COURSE['chapters'] if ch['id']=='weather_tool')
        files[lesson['file']]=lesson['example']
        result=execute_project({'files':files,'chapterId':'weather_tool','mode':'run'})
        self.assertEqual(result['verdict'],'AC',result)
        self.assertEqual(result['total'],1)

    def test_new_model_runs_use_student_functions_and_pass_history(self):
        config = {'model': 'fixture', 'api_key': 'fixture', 'base_url': 'https://fixture.invalid'}
        for identifier in ['conversation', 'workflow', 'checkpoint', 'async_reply']:
            with self.subTest(chapter=identifier):
                lesson = next(ch for ch in COURSE['chapters'] if ch['id'] == identifier)
                self.assertTrue(lesson['live'])
                module = types.ModuleType('practice.' + identifier)
                exec(lesson['example'], module.__dict__)
                class Model:
                    def __init__(self):self.requests=[]
                    def invoke(self, messages):
                        self.requests.append(messages)
                        return AIMessage(content='不同措辞的真实回答')
                    async def ainvoke(self, messages):
                        self.requests.append(messages)
                        return AIMessage(content='不同措辞的真实回答')
                model=Model()
                events=[]
                with patch.dict(sys.modules, {'practice':types.ModuleType('practice'), 'practice.'+identifier:module}):
                    result=live(identifier,{'question':'我叫什么？'},events.append,lambda values:model,config)
                self.assertEqual(result['verdict'],'OK')
                self.assertEqual(events[-1]['text'],'不同措辞的真实回答')
                self.assertTrue(model.requests)
                if identifier=='conversation':
                    self.assertEqual([m.content for m in model.requests[0]],['我叫小林','你好，小林。','我叫什么？'])
                if identifier=='checkpoint':
                    self.assertEqual(len(model.requests),2)
                    self.assertEqual(len(model.requests[1]),3)

    def check_reply_source(self, source):
        module = types.ModuleType('practice.first_reply')
        exec(source, module.__dict__)
        with patch.dict(sys.modules, {'practice': types.ModuleType('practice'), 'practice.first_reply': module}):
            return check('first_reply', None)

    def test_overwritten_question_has_specific_feedback(self):
        lesson = next(ch for ch in COURSE['chapters'] if ch['id'] == 'first_reply')
        source = lesson['example'].replace('answer = model.invoke(question)',
                                          'question = "你好，请介绍一下自己。"\n    answer = model.invoke(question)')
        result = self.check_reply_source(source)
        self.assertEqual(result['verdict'], 'WA')
        self.assertTrue(all('不要在函数内把 question 改成固定文字' in case['message'] for case in result['cases']))

    def test_wrong_return_is_distinguished_from_wrong_input(self):
        lesson = next(ch for ch in COURSE['chapters'] if ch['id'] == 'first_reply')
        result = self.check_reply_source(lesson['example'].replace('return answer.content', 'return answer'))
        self.assertEqual(result['verdict'], 'WA')
        self.assertTrue(all('问题已正确发送' in case['message'] for case in result['cases']))

    def test_reference_reply_handles_changing_questions(self):
        lesson = next(ch for ch in COURSE['chapters'] if ch['id'] == 'first_reply')
        result = self.check_reply_source(lesson['example'])
        self.assertEqual(result['verdict'], 'AC')
        self.assertEqual(len(result['cases']), 2)

    def test_first_reply_does_not_require_later_pi_functions(self):
        files = dict(COURSE['files'])
        lesson = next(ch for ch in COURSE['chapters'] if ch['id'] == 'first_reply')
        files[lesson['file']] = lesson['example']
        result = execute_project({'files': files, 'chapterId': 'first_reply', 'mode': 'check'})
        self.assertEqual(result['verdict'], 'AC', result)

    def test_live_answers_can_use_different_words(self):
        lesson = next(ch for ch in COURSE['chapters'] if ch['id'] == 'first_reply')
        module = types.ModuleType('practice.first_reply')
        exec(lesson['example'], module.__dict__)
        config = {'model': 'fixture', 'api_key': 'fixture', 'base_url': 'https://fixture.invalid'}
        for answer in ['这是第一种回答。', '换一种说法也可以完成调用。']:
            events = []
            class Model:
                def invoke(self, question):
                    return AIMessage(content=answer)
            with patch.dict(sys.modules, {'practice': types.ModuleType('practice'), 'practice.first_reply': module}):
                result = live('first_reply', {'question': '任意问题'}, events.append, lambda values: Model(), config)
            self.assertEqual(result['verdict'], 'OK')
            self.assertEqual(events[-1]['text'], answer)

    def test_live_reply_must_really_call_the_model(self):
        module = types.ModuleType('practice.first_reply')
        exec('from langchain_openai import ChatOpenAI\ndef reply(config, question):\n    return "写死的文字"\n', module.__dict__)
        with patch.dict(sys.modules, {'practice': types.ModuleType('practice'), 'practice.first_reply': module}):
            with self.assertRaisesRegex(AssertionError, '没有调用模型'):
                live('first_reply', {'question': '问题'}, lambda event: None, lambda values: None, {})

    def test_project_reports_an_unfinished_key_function(self):
        files = dict(COURSE['files'])
        for lesson in COURSE['chapters']:
            files[lesson['file']] = lesson['example']
        files['mini_pi/loop.py'] = COURSE['files']['mini_pi/loop.py']
        result = execute_project({'files': files, 'chapterId': 'project', 'mode': 'check'})
        self.assertEqual(result['verdict'], 'RE', result)
        self.assertIn('亲手写出 Pi 的 Agent 循环', result['message'])


if __name__ == '__main__':
    unittest.main()
