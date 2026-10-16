import importlib
import io
import json
import os
import sys
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'oj'))
from agent_executor import execute_project
import agent_workspace as workspace


def reference_files():
    files=dict(workspace.COURSE['files'])
    for chapter in workspace.COURSE['chapters']:
        files[chapter['file']]=chapter['example']
    return files


class AgentComponents(unittest.TestCase):
    def test_reference_components_in_isolated_workers(self):
        for chapter in workspace.COURSE['chapters']:
            with self.subTest(chapter=chapter['id']):
                result=execute_project({'files':reference_files(),'chapterId':chapter['id'],'mode':'check'})
                self.assertEqual(result['verdict'],'OK' if chapter['id']=='intro' else 'AC',result)

    def test_starter_is_not_silently_completed(self):
        result=execute_project({'files':dict(workspace.COURSE['files']),'chapterId':'first_reply','mode':'check'})
        self.assertEqual(result['verdict'],'WA')

    def test_export_own_files_and_blank_env(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(workspace,'WORKSPACES',Path(folder)):
            session=uuid.uuid4().hex;other=uuid.uuid4().hex
            workspace.write_file(session,'.env','OPENAI_API_KEY=fixture-secret\n')
            workspace.write_file(session,'mini_pi/messages.py','# my implementation\n')
            workspace.write_file(session,'workspace/src/new.py','print("new")\n')
            self.assertNotIn('fixture-secret',workspace.read_files(other)['.env'])
            with zipfile.ZipFile(io.BytesIO(workspace.export_project(session))) as archive:
                self.assertNotIn('fixture-secret',archive.read('.env').decode())
                self.assertEqual(archive.read('mini_pi/messages.py').decode(),'# my implementation\n')
                self.assertIn('NotImplementedError',archive.read('mini_pi/project.py').decode())
                self.assertEqual(archive.read('workspace/src/new.py').decode(),'print("new")\n')
            with self.assertRaises(ValueError):workspace.write_file(session,'../.env','bad')

    def test_offline_network_and_host_files_are_blocked(self):
        files=reference_files()
        for code in ['import socket\nsocket.create_connection(("127.0.0.1",8765))',
                     'from pathlib import Path\nPath("'+str(ROOT/'README.md').replace('\\','/')+'").read_text()',
                     'import sqlite3\nc=sqlite3.connect(":memory:")\nc.execute("ATTACH DATABASE \'file:///host\' AS host")']:
            with self.subTest(code=code.splitlines()[0]):
                files['mini_pi/messages.py']=code
                result=execute_project({'files':files,'chapterId':'messages','mode':'check'})
                self.assertNotEqual(result['verdict'],'AC',result)

    def test_streams_are_observed_before_job_completes(self):
        # Exercise NDJSON callbacks without contacting a provider.
        files=reference_files()
        files['mini_pi/config.py']='from langchain_core.messages import AIMessageChunk\nclass Model:\n    def stream(self,messages):\n        yield AIMessageChunk(content="first")\n        yield AIMessageChunk(content="second")\ndef load_config(path): return {}\ndef create_model(config): return Model()\n'
        events=[]
        result=execute_project({'files':files,'chapterId':'streaming','mode':'live','question':'hello'},events.append)
        self.assertEqual(result['verdict'],'OK',result)
        self.assertTrue(events)
        self.assertTrue(all('text' in event for event in events))

    def test_live_complete_answer_requires_a_model_call(self):
        files=reference_files()
        files['mini_pi/config.py']='from langchain_core.messages import AIMessage\nclass Model:\n    def invoke(self,messages): return AIMessage(content="variable")\ndef load_config(path): return {}\ndef create_model(config): return Model()\n'
        files['mini_pi/messages.py']='from langchain_core.messages import AIMessage\ndef ask(model,question,history=()): return AIMessage(content="fabricated")\n'
        result=execute_project({'files':files,'chapterId':'messages','mode':'live','question':'x'})
        self.assertEqual(result['verdict'],'RE',result)
        self.assertIn('没有调用',result['message'])

    def test_live_graph_can_pause_and_resume_across_processes(self):
        files=reference_files()
        files['mini_pi/config.py']='''from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
class Model:
    def bind_tools(self,tools): return self
    def stream(self,messages):
        if isinstance(messages[-1],ToolMessage):
            yield AIMessageChunk(content='arbitrary answer')
        else:
            yield AIMessageChunk(content='',tool_calls=[{'name':'edit','args':{'path':'hello.py','old':'reader','new':'learner'},'id':'edit-one','type':'tool_call'}])
def load_config(path): return {}
def create_model(config): return Model()
'''
        with tempfile.TemporaryDirectory() as folder:
            payload={'files':files,'chapterId':'app','mode':'live','question':'edit','threadId':'demo','dataRoot':folder}
            first=execute_project(payload)
            self.assertEqual(first['verdict'],'WAITING',first)
            second=execute_project({**payload,'approval':True})
            self.assertEqual(second['verdict'],'OK',second)
            self.assertIn('learner',second['changedFiles']['workspace/hello.py'])

    def test_actual_sdk_complete_and_stream_with_mock_transport(self):
        import httpx
        from openai import OpenAI
        from agent_project.config import create_model
        from agent_project.streaming import collect_stream
        from langchain_core.messages import HumanMessage
        for provider,base in [('openai','https://api.openai.com/v1'),('zhipu','https://open.bigmodel.cn/api/paas/v4/')]:
            requests=[]
            def respond(request):
                value=json.loads(request.content);requests.append(value)
                if value.get('stream'):
                    rows=[]
                    for text in ['任意','回答']:
                        rows.append('data: '+json.dumps({'id':'fixture','object':'chat.completion.chunk','created':0,'model':'fixture','choices':[{'index':0,'delta':{'role':'assistant','content':text},'finish_reason':None}]},ensure_ascii=False)+'\n\n')
                    return httpx.Response(200,headers={'Content-Type':'text/event-stream'},content=''.join(rows)+'data: [DONE]\n\n')
                return httpx.Response(200,json={'id':'fixture','object':'chat.completion','created':0,'model':'fixture','choices':[{'index':0,'message':{'role':'assistant','content':'另一种回答'},'finish_reason':'stop'}]})
            model=create_model({'provider':provider,'model':'fixture','api_key':'fixture-key','base_url':base})
            with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
                sdk=OpenAI(api_key='fixture-key',base_url=base,http_client=transport)
                model.client=sdk.chat.completions
                full=model.invoke([HumanMessage(content='question')]);shown=[]
                streamed=collect_stream(model.stream([HumanMessage(content='question')]),shown.append)
                self.assertEqual(full.content,'另一种回答')
                self.assertEqual(streamed.content,'任意回答')
                self.assertEqual(shown,['任意','回答'])
                self.assertEqual(len(requests),2)

    def test_native_mcp_adapter_with_in_memory_server(self):
        import asyncio
        from fastmcp import FastMCP
        from agent_project.mcp import load_mcp_tools
        server=FastMCP('fixture')
        @server.tool
        def multiply(a:int,b:int)->int:
            """Multiply two integers."""
            return a*b
        async def run():
            tools=await load_mcp_tools(server)
            self.assertEqual([tool.name for tool in tools],['multiply'])
            value=await tools[0].ainvoke({'a':3,'b':4})
            self.assertIn('12',str(value))
        asyncio.run(run())

if __name__=='__main__':unittest.main()
