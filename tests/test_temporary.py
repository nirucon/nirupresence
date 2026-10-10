import unittest
from unittest.mock import patch
from nirupresence import legacy

class TemporaryTests(unittest.TestCase):
    @patch.object(legacy,'api')
    def test_temporary_uses_server_endpoint(self,api):
        legacy.cmd_temp_status(['Ute','60','Helg med ungarna åäö'])
        api.assert_called_once_with('presence/temporary','PUT',{'status':'Ute','minutes':60,'detail':'Helg med ungarna åäö'})
    @patch.object(legacy,'api')
    def test_cancel_is_server_owned(self,api):
        legacy.cmd_cancel_temp()
        api.assert_called_once_with('presence/temporary','DELETE')
    def test_reject_invalid_duration(self):
        with self.assertRaises(RuntimeError):legacy.cmd_temp_status(['Ute','5'])
