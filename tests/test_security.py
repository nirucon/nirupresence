import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nirupresence import legacy

class SecurityTests(unittest.TestCase):
    def test_https_required(self):
        for url in ('http://example.com','https://user:pass@example.com','https://example.com?token=x'):
            with self.assertRaises(ValueError): legacy.secure_base_url(url)
    def test_import_validates_without_printing_token(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'token.json'
            token='nru_'+'x'*48
            f.write_text(json.dumps({'token':token,'base_url':'https://example.com'}))
            with patch.object(legacy,'cmd_configure',return_value={'ok':True}) as cmd:
                self.assertEqual(legacy.cmd_import_token([str(f)]),{'ok':True})
                cmd.assert_called_once_with([token,'https://example.com'])
    def test_import_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/'original.json';original.write_text('{}')
            link=Path(d)/'link.json';link.symlink_to(original)
            with self.assertRaises(ValueError):legacy.cmd_import_token([str(link)])
    def test_navidrome_requires_explicit_url(self):
        with patch.object(legacy,'config',return_value={'navidrome':{'username':'a','password':'b'}}):
            self.assertIsNone(legacy._navidrome_song('123','https://evil.example/stream?id=123'))
if __name__=='__main__':unittest.main()
