import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nirupresence import legacy

class TokenPrivacyTests(unittest.TestCase):
    def test_import_requires_explicit_path(self):
        with self.assertRaisesRegex(ValueError, 'path'):
            legacy.cmd_import_token([])
    def test_path_not_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            config = Path(d) / 'config.json'
            source = Path(d) / 'token.json'
            source.write_text(json.dumps({'token':'nru_'+'x'*48}))
            with patch.object(legacy,'CONFIG',config), patch.object(legacy,'cmd_configure',return_value={'ok':True}):
                legacy.cmd_import_token([str(source)])
                self.assertNotIn('token_import_path',json.loads(config.read_text()))
