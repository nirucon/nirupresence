import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nirupresence import legacy

class AuthSetupTests(unittest.TestCase):
    def test_import_does_not_remember_path(self):
        with tempfile.TemporaryDirectory() as directory:
            conf=Path(directory)/'config.json'
            source=Path(directory)/'token.json'
            source.write_text(json.dumps({'token':'nru_'+'x'*48}))
            with patch.object(legacy,'CONFIG',conf), patch.object(legacy,'cmd_configure',return_value={'ok':True}):
                legacy.cmd_import_token([str(source)])
                self.assertNotIn('token_import_path',json.loads(conf.read_text()))
    def test_failed_import_does_not_store_path(self):
        with tempfile.TemporaryDirectory() as directory:
            conf=Path(directory)/'config.json'
            source=Path(directory)/'token.json'
            source.write_text(json.dumps({'token':'nru_'+'x'*48}))
            with patch.object(legacy,'CONFIG',conf), patch.object(legacy,'cmd_configure',side_effect=RuntimeError('Rejected')):
                with self.assertRaises(RuntimeError):legacy.cmd_import_token([str(source)])
                self.assertFalse(conf.exists())
