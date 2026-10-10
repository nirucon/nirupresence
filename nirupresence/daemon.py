"""Headless background sync, independent of the terminal UI."""
import fcntl
import json
import logging
import os
import signal
import time
from pathlib import Path
from .core import preferences, sync_cycle

STATE = Path.home()/'.local/state/nirupresence'
STOP = False

def stop(*_):
    global STOP
    STOP = True

def run():
    STATE.mkdir(parents=True, exist_ok=True)
    os.chmod(STATE, 0o700)
    logging.basicConfig(filename=STATE/'daemon.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    with (STATE/'daemon.lock').open('w') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return 0
        lock.write(str(os.getpid()))
        lock.flush()
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        while not STOP:
            try:
                result = sync_cycle()
                (STATE/'last-sync.json').write_text(json.dumps({'at':int(time.time()),'result':result}, ensure_ascii=False))
            except Exception as exc:
                logging.warning('Sync failed: %s', str(exc)[:300])
                (STATE/'last-sync.json').write_text(json.dumps({'at':int(time.time()),'error':str(exc)[:300]}))
            for _ in range(max(10,min(300,int(preferences()['interval'])))):
                if STOP: break
                time.sleep(1)
    return 0
