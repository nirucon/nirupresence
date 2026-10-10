"""Regression checks for server-owned automatic presence (0.5.7)."""
import unittest
from unittest.mock import patch
from nirupresence import core, legacy


class AutoPresenceTests(unittest.TestCase):
    def test_new_install_heartbeat_default(self):
        with patch.object(core.legacy, 'read_json', return_value={}):
            self.assertTrue(core.preferences()['heartbeat'])

    def test_existing_heartbeat_preference_preserved(self):
        with patch.object(core.legacy, 'read_json', return_value={'heartbeat': False}):
            self.assertFalse(core.preferences()['heartbeat'])

    def test_auto_online_offline_modes(self):
        for mode in ('auto', 'online', 'offline'):
            with self.subTest(mode=mode), patch.object(legacy, 'api', return_value={'ok': True}) as api, patch.object(legacy, 'save_state') as save:
                self.assertTrue(legacy.cmd_presence_mode(mode)['ok'])
                api.assert_called_once_with('presence/offline', 'PUT', {'mode': mode})
                save.assert_called_once_with({'manual_offline': mode == 'offline'})

    def test_failed_mode_does_not_change_local_state(self):
        with patch.object(legacy, 'api', return_value={'ok': False}), patch.object(legacy, 'save_state') as save:
            self.assertFalse(legacy.cmd_presence_mode('offline')['ok'])
            save.assert_not_called()

    def test_reject_invalid_mode(self):
        with self.assertRaises(ValueError):
            legacy.cmd_presence_mode('unknown')


if __name__ == '__main__':
    unittest.main()
