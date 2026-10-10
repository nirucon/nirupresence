"""Compatibility layer for the verified 0.4.1 API client."""
from . import legacy
from . import __version__
legacy.VERSION = __version__
legacy.UA = f"NIRUPRESENCE-Linux/{__version__}"

import json
import os
import time
from pathlib import Path

PREFS = Path.home() / '.config/nirupresence/linux.json'

def preferences():
    defaults = {'heartbeat': False, 'music': True, 'interval': 20, 'night_policy': False}
    defaults.update({k:v for k,v in legacy.read_json(PREFS, {}).items() if k in defaults})
    return defaults

def set_preference(key, value):
    if key not in preferences():
        raise ValueError('Unknown preference')
    p = preferences()
    p[key] = value
    legacy.atomic_write(PREFS, p)
    return p

def sync_cycle():
    p = preferences()
    if not legacy.config()['token']:
        return {'ok': False, 'reason': 'not configured'}
    # Presence offline does not disable explicitly opted-in music sharing.
    result = {}
    # Multi-device safety: a secondary computer never sends global offline or
    # wake events unless the user explicitly enables heartbeat/night policy.
    if p['heartbeat'] and not legacy.state()['manual_offline']:
        if p['night_policy']:
            result['heartbeat'] = legacy.cmd_heartbeat()
        else:
            s = legacy.state()
            if not s['session_started']:
                legacy.save_state({'session_started': int(time.time())})
                s = legacy.state()
            result['heartbeat'] = legacy.api('presence/heartbeat', 'PUT', {'session_started': s['session_started']})
        # Temporary presence is server-owned and expires without a client heartbeat.
    if p['music'] and legacy.state()['share_music']:
        # Original sync-music invokes global night policy. For secondary hosts,
        # bypass that side effect while preserving the verified MPRIS selection.
        m = legacy.playerctl_metadata()
        payload = {'sharing': True, 'playing': bool(m.get('playing'))}
        if m.get('playing'):
            payload.update({k:m.get(k,'') for k in ('artist','title','album','source')})
            payload['media_type'] = m.get('media_type', 'music')
        if not m.get('available'):
            return {'ok': True, **result, 'music': {'skipped': 'playerctl unavailable'}}
        key = '|'.join(str(payload.get(k,'')) for k in ('playing','source','artist','title','album','media_type'))
        s = legacy.state()
        now = int(time.time())
        if key != s['last_track_key'] or now - s['last_music_sent'] >= 180:
            result['music'] = legacy.api('presence/nowplaying','PUT',payload)
            legacy.save_state({'last_track_key': key, 'last_music_sent': now})
        else:
            result['music'] = {'unchanged': True}
    return {'ok': True, **result}


def sync_music(force=False):
    """Manual music sync uses the same rules as the background daemon."""
    p = preferences()
    if not p['music'] or not legacy.state()['share_music']:
        return {'ok': True, 'skipped': 'sharing disabled'}
    # Force refresh by clearing only the cached track signature, not user settings.
    if force:
        legacy.save_state({'last_track_key': '', 'last_music_sent': 0})
    result = sync_cycle()
    return {'ok': result.get('ok', False), **result.get('music', {})}
