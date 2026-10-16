import asyncio
import sys
import unittest
from collections import defaultdict, deque
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as api
from fastapi import HTTPException
from starlette.responses import JSONResponse

class LocalQueueTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        api.jobs = {}
        api.rates = defaultdict(deque)
        api.queue = asyncio.Queue(maxsize=2)
        self.request = SimpleNamespace(client=SimpleNamespace(host='127.0.0.1'))
        self.owner = 'local-browser-session-123'

    async def submit(self, request_id, code='print(1)'):
        return await api.submit(api.Submission(kind='example', code=code, requestId=request_id), self.request, self.owner)

    async def test_busy_executor_accepts_waiting_tasks(self):
        first = await self.submit('request-first-123')
        second = await self.submit('request-second-123')
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(api.queue.qsize(), 2)
        self.assertEqual(first['status'], 'queued')

    async def test_capacity_retry_waits_for_available_position(self):
        await self.submit('request-first-123')
        await self.submit('request-second-123')
        with self.assertRaises(HTTPException) as caught:
            await self.submit('request-third-123')
        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(len(api.jobs), 2)
        api.queue.get_nowait()
        third = await self.submit('request-third-123')
        self.assertEqual(third['status'], 'queued')

    async def test_retry_deduplicates_and_preserves_clicked_code(self):
        body = api.Submission(kind='example', code='print("original")', requestId='request-original-123')
        first = await api.submit(body, self.request, self.owner)
        body.code = 'print("edited")'
        self.assertEqual(api.jobs[first['id']]['payload']['code'], 'print("original")')
        retry = await self.submit('request-original-123', 'print("original")')
        self.assertEqual(first['id'], retry['id'])
        self.assertEqual(api.queue.qsize(), 1)
        with self.assertRaises(HTTPException) as caught:
            await self.submit('request-original-123', 'print("replacement")')
        self.assertEqual(caught.exception.status_code, 409)

    async def test_another_browser_cannot_read_private_job(self):
        job = await self.submit('request-private-123')
        with self.assertRaises(HTTPException) as caught:
            await api.job_status(job['id'], 'another-browser-session')
        self.assertEqual(caught.exception.status_code, 404)

    async def test_public_clients_and_rebound_hosts_are_rejected(self):
        async def next_response(request):
            return JSONResponse({'ok': True})
        for ip, host, origin, expected in [
            ('127.0.0.1', '127.0.0.1:8765', None, 200),
            ('::1', '[::1]:8765', None, 200),
            ('192.0.2.1', '127.0.0.1:8765', None, 403),
            ('127.0.0.1', 'attacker.example:8765', None, 403),
            ('127.0.0.1', 'localhost:8765', 'https://attacker.example', 403),
        ]:
            with self.subTest(ip=ip, host=host):
                headers = {'host': host}
                if origin: headers['origin'] = origin
                request = SimpleNamespace(client=SimpleNamespace(host=ip), headers=headers, method='GET',url=SimpleNamespace(path='/api/health'))
                response = await api.boundary(request, next_response)
                self.assertEqual(response.status_code, expected)

    async def test_course_validation_and_agent_queue_payload(self):
        body=api.ComponentRun(chapterId='first_reply',mode='check',requestId='agent-request-12345')
        job=await api.component_run(body,self.owner)
        self.assertEqual(api.jobs[job['id']]['payload']['track'],'agent')
        self.assertIn('mini_pi/messages.py',api.jobs[job['id']]['payload']['files'])
        self.assertNotIn('fixture-secret',api.jobs[job['id']]['payload']['files']['.env'])
        with self.assertRaises(HTTPException) as caught:
            await api.submit(api.Submission(kind='submit',track='pytorch',problemId='A01',code='pass'),self.request,self.owner)
        self.assertEqual(caught.exception.status_code,404)

    async def test_export_response_is_zip_and_no_current_env(self):
        response=await api.project_export(self.owner)
        import io,zipfile
        with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
            self.assertIn('MODEL_API_KEY=\n',archive.read('.env').decode())
            self.assertIn('mini_pi/app.py',archive.namelist())

    async def test_offline_example_run_uses_no_model_credentials(self):
        from agent_workspace import COURSE
        job=await api.component_run(api.ComponentRun(chapterId='weather_tool',mode='run',requestId='offline-example-123'),self.owner)
        payload=api.jobs[job['id']]['payload']
        self.assertEqual(payload['mode'],'run')
        self.assertEqual(payload['files']['.env'],COURSE['files']['.env'])

if __name__ == '__main__':
    unittest.main()
