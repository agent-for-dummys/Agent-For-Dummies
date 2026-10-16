import sys
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent_display import capture_call,attach,value_text


class ResultSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.module=types.ModuleType('practice.snapshot_fixture')
        exec('def change(items):\n    items.append("new")\n    return list(items)\n',self.module.__dict__)

    def test_inputs_are_frozen_before_student_mutation(self):
        original=['old']
        with capture_call(self.module.__name__,'change') as snapshot:
            self.module.change(original)
        self.assertEqual(snapshot['inputs'][0]['text'],"['old']")
        self.assertEqual(snapshot['actual'],"['old', 'new']")

    def test_expected_value_cannot_replace_actual_return(self):
        with capture_call(self.module.__name__,'change') as snapshot:
            self.module.change([])
        data=attach(snapshot,{},expected=['different'])
        self.assertEqual(data['expected'],"['different']")
        self.assertEqual(data['actual'],"['new']")

    def test_graph_thread_calls_are_captured(self):
        with capture_call(self.module.__name__,'change') as snapshot:
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(self.module.change,['thread']).result()
        self.assertEqual(snapshot['inputs'][0]['text'],"['thread']")
        self.assertEqual(snapshot['actual'],"['thread', 'new']")

    def test_credential_fields_are_redacted_recursively(self):
        text=value_text({'api_key':'fixture-sensitive','nested':{'X-APISpace-Token':'fixture-sensitive'},'value':3})
        self.assertNotIn('fixture-sensitive',text)
        self.assertIn("'value': 3",text)

    def test_profiling_is_restored_after_failure(self):
        before=sys.getprofile()
        with self.assertRaises(RuntimeError):
            with capture_call(self.module.__name__,'change'):
                raise RuntimeError('example')
        self.assertIs(sys.getprofile(),before)


if __name__=='__main__':unittest.main()
