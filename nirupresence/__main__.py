"""Command line entry point."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from . import __version__
from . import legacy
from .core import preferences, set_preference, sync_cycle, sync_music

def show(data):
    print(json.dumps(data,ensure_ascii=False,indent=2))

def service_status():
    if shutil.which('systemctl') and Path('/run/systemd/system').exists():
        return {'systemd':subprocess.run(['systemctl','--user','is-active','nirupresence.service'],capture_output=True,text=True).stdout.strip()}
    path=Path.home()/'.local/state/nirupresence/daemon.lock'
    try:
        pid=int(path.read_text().strip()); os.kill(pid,0)
        return {'daemon':'running','pid':pid}
    except (OSError,ValueError):return {'daemon':'not running'}

def main():
    args=sys.argv[1:]
    cmd=args.pop(0) if args else 'tui'
    if cmd in ('tui','ui'):
        from .tui import run
        return run()
    if cmd=='daemon':
        from .daemon import run
        return run()
    if cmd=='import-token':show(legacy.cmd_import_token(args));return
    if cmd in ('--help','-h','help'):
        print('NIRUPRESENCE '+__version__+'\nCommands: tui, doctor, status, sync, sync-music, service-status, import-token FILE, temp-status STATUS MINUTES [DETAIL], cancel-temp, preferences, version\nUse the TUI to choose valid statuses and manage settings.')
        return
    if cmd=='version': print(__version__);return
    if cmd=='service-status':show(service_status());return
    if cmd=='sync':show(sync_cycle());return
    if cmd=='sync-music':show(sync_music(force=True));return
    if cmd=='preferences':
        if not args:show(preferences());return
        if len(args)!=2:raise ValueError('Usage: preferences heartbeat|music|night_policy|interval value')
        key,value=args
        if key=='interval':value=int(value)
        else:value=value.lower() in ('true','yes','on','1')
        show(set_preference(key,value));return
    if cmd=='doctor':
        r=legacy.cmd_doctor()
        r['version']=__version__
        r['preferences']=preferences()
        r['service']=service_status()
        show(r);return
    if cmd=='status':
        show(legacy.cmd_dashboard());return
    # Preserve the verified 0.4.1 commands, including microlog and Navidrome.
    sys.argv=[sys.argv[0],cmd,*args]
    legacy.main()

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print(f'NIRUPRESENCE: {exc}',file=sys.stderr)
        sys.exit(1)
