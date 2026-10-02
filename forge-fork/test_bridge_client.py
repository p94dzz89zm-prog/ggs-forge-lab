import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('bridge_client', Path(__file__).with_name('bridge_client.py'))
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)

class ClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        (self.directory / 'request.json').write_text(json.dumps({'request_id': 'current:1'}))

    def test_response_is_bound_to_inspected_request(self):
        client.respond(self.directory, 'current:1', {'index': -1})
        result = json.loads((self.directory / 'response.json').read_text())
        self.assertEqual(result, {'request_id': 'current:1', 'index': -1})
        with self.assertRaises(ValueError):
            client.respond(self.directory, 'current:1', {'index': 0})

    def test_stale_decision_is_not_written(self):
        with self.assertRaises(ValueError):
            client.respond(self.directory, 'old:1', {'index': 0})
        self.assertFalse((self.directory / 'response.json').exists())

if __name__ == '__main__':
    unittest.main()
