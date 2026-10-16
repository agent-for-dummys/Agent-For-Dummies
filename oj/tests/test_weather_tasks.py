import contextlib
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'oj'))
import agent_checks
import agent_workspace
from agent_executor import execute_project


@contextlib.contextmanager
def weather_project(env='WEATHER_API_KEY=fixture-weather\n'):
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        for name in ['practice/weather_support.py','practice/weather_cities.csv']:
            path=root/name
            path.parent.mkdir(exist_ok=True)
            path.write_text(agent_workspace.COURSE['files'][name],encoding='utf-8')
        lesson=next(ch for ch in agent_workspace.COURSE['chapters'] if ch['id']=='weather_tool')
        (root/lesson['file']).write_text(lesson['example'],encoding='utf-8')
        (root/'.env').write_text(env,encoding='utf-8')
        package=types.ModuleType('practice')
        package.__path__=[str(root/'practice')]
        previous=Path.cwd()
        with patch.dict(sys.modules,{'practice':package}):
            saved={name:sys.modules.pop(name,None) for name in ['practice.weather_support','practice.weather_tool']}
            try:
                os.chdir(root)
                import importlib
                support=importlib.import_module('practice.weather_support')
                tool=importlib.import_module('practice.weather_tool')
                yield support,tool
            finally:
                os.chdir(previous)
                for name,module in saved.items():
                    sys.modules.pop(name,None)
                    if module is not None:sys.modules[name]=module


class WeatherTaskTests(unittest.TestCase):
    def test_city_table_handles_real_city_names_without_defaulting(self):
        with weather_project() as (support,_):
            self.assertEqual(support.get_city_code('杭州'),'101210101')
            self.assertEqual(support.get_city_code('北京市'),'101010100')
            self.assertEqual(support.get_city_code('丰台区'),'101010900')
            with self.assertRaises(ValueError):support.get_city_code('不存在的城市xyz')
            with self.assertRaises(ValueError):support.get_city_code('鼓楼')

    def test_live_weather_needs_no_model_credentials(self):
        with weather_project():
            requests=[]
            def respond(request):
                requests.append(request)
                return httpx.Response(200,json={'result':{'realtime':{'temp':18.2,'text':'晴'}}})
            def get(url,**kwargs):
                with httpx.Client(transport=httpx.MockTransport(respond),trust_env=False) as client:
                    return client.get(url,**kwargs)
            events=[]
            with patch.object(httpx,'get',side_effect=get),patch('langchain_openai.ChatOpenAI',side_effect=AssertionError('不应创建模型')):
                result=agent_checks.live_run({'chapterId':'weather_tool','question':'杭州'},events.append,Path('.runtime'))
            self.assertEqual(result['verdict'],'OK')
            self.assertEqual(events[-1]['text'],'杭州：晴，18.2℃')
            self.assertEqual(requests[0].headers['X-APISpace-Token'],'fixture-weather')

    def test_weather_config_requires_own_key(self):
        with weather_project(env='MODEL_API_KEY=fixture-model\n') as (support,_):
            with self.assertRaisesRegex(ValueError,'WEATHER_API_KEY'):support.load_weather_config()

    def test_new_fields_preserve_existing_reader_env(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(agent_workspace,'WORKSPACES',Path(folder)):
            owner='weather-migration-fixture'
            root=agent_workspace.directory(owner)
            root.mkdir(parents=True)
            original='MODEL_API_KEY=fixture-model\nWEATHER_API_KEY=fixture-own-weather\nWEATHER_API_URL=https://example.invalid/custom\n'
            (root/'.env').write_text(original,encoding='utf-8')
            agent_workspace.initialize(owner)
            self.assertEqual((root/'.env').read_text(encoding='utf-8'),original)
            (root/'.env').write_text('MODEL_API_KEY=fixture-model',encoding='utf-8')
            agent_workspace.initialize(owner)
            migrated=(root/'.env').read_text(encoding='utf-8')
            self.assertTrue(migrated.startswith('MODEL_API_KEY=fixture-model\n'))
            self.assertIn('WEATHER_API_KEY=\n',migrated)
            agent_workspace.initialize(owner)
            self.assertEqual((root/'.env').read_text(encoding='utf-8'),migrated)

    def test_reference_weather_and_agent_use_mocked_http_in_worker(self):
        files=dict(agent_workspace.COURSE['files'])
        for lesson in agent_workspace.COURSE['chapters']:
            if lesson['id'] in {'weather_tool','weather_agent'}:files[lesson['file']]=lesson['example']
        for chapter in ['weather_tool','weather_agent']:
            with self.subTest(chapter=chapter):
                result=execute_project({'files':files,'chapterId':chapter,'mode':'check'})
                self.assertEqual(result['verdict'],'AC',result)


if __name__=='__main__':unittest.main()
