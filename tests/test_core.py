import unittest
from unittest.mock import patch
from nirupresence import core

class CoreTests(unittest.TestCase):
    def test_secondary_host_does_not_send_heartbeat(self):
        with patch.object(core,'preferences',return_value={'heartbeat':False,'music':True,'interval':20,'night_policy':False}), patch.object(core.legacy,'config',return_value={'token':'fake'}), patch.object(core.legacy,'state',return_value={'manual_offline':False,'share_music':True,'last_track_key':'','last_music_sent':0}), patch.object(core.legacy,'playerctl_metadata',return_value={'available':True,'playing':True,'source':'nplay','artist':'P1','title':'Studio Ett','album':'Sveriges Radio · LIVE','media_type':'radio'}), patch.object(core.legacy,'api',return_value={'ok':True}) as api, patch.object(core.legacy,'save_state'):
            self.assertTrue(core.sync_cycle()['ok'])
            self.assertEqual(api.call_count,1)
            self.assertEqual(api.call_args.args[:2],('presence/nowplaying','PUT'))
            self.assertEqual(api.call_args.args[2]['media_type'],'radio')
    def test_manual_offline_still_shares_music_without_heartbeat(self):
        prefs={'heartbeat':False,'music':True,'interval':20,'night_policy':False}
        state={'manual_offline':True,'share_music':True,'last_track_key':'','last_music_sent':0}
        with patch.object(core,'preferences',return_value=prefs), patch.object(core.legacy,'config',return_value={'token':'fake'}), patch.object(core.legacy,'state',return_value=state), patch.object(core.legacy,'playerctl_metadata',return_value={'available':True,'playing':True,'source':'nplay','artist':'Slayer','title':'Killing Fields','album':'Divine Intervention','media_type':'music'}), patch.object(core.legacy,'api',return_value={'ok':True}) as api, patch.object(core.legacy,'save_state'):
            self.assertTrue(core.sync_cycle()['ok'])
            self.assertEqual(api.call_count,1)
            self.assertEqual(api.call_args.args[0],'presence/nowplaying')
    def test_force_music_does_not_run_night_policy(self):
        with patch.object(core,'preferences',return_value={'heartbeat':False,'music':True,'interval':20,'night_policy':True}), patch.object(core.legacy,'config',return_value={'token':'fake'}), patch.object(core.legacy,'state',return_value={'manual_offline':False,'share_music':True,'last_track_key':'','last_music_sent':0}), patch.object(core.legacy,'clock_policy',side_effect=AssertionError('night policy must not run')), patch.object(core.legacy,'playerctl_metadata',return_value={'available':True,'playing':True,'source':'nplay','artist':'P1','title':'Studio Ett','album':'Sveriges Radio · LIVE','media_type':'radio'}), patch.object(core.legacy,'api',return_value={'ok':True}), patch.object(core.legacy,'save_state'):
            self.assertTrue(core.sync_music(force=True)['ok'])

if __name__=='__main__':unittest.main()
