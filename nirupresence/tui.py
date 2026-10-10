"""NIRUPRESENCE terminal UI. Keyboard-first, dependency-free curses."""
import curses
import json
import os
import locale
import time
from pathlib import Path
from . import __version__
from .core import legacy, preferences, set_preference, sync_music

MENU = [('Overview','overview'),('Presence','presence'),('Now playing','music'),('Night & privacy','night'),('Microlog','microlog'),('Settings','settings'),('Diagnostics','doctor')]

class UI:
    def __init__(self, screen):
        self.s=screen; self.page='overview'; self.selected=0; self.note=''; self.cache={}; self.last=0
        self.s.keypad(True); self.s.timeout(400)
        try:curses.curs_set(0)
        except curses.error:pass
        if curses.has_colors():
            curses.start_color()
            try:curses.use_default_colors(); bg=-1
            except curses.error:bg=curses.COLOR_BLACK
            curses.init_pair(1,curses.COLOR_CYAN,bg)
            curses.init_pair(2,curses.COLOR_GREEN,bg)
            curses.init_pair(3,curses.COLOR_YELLOW,bg)
    def put(self,y,x,text,attr=0):
        h,w=self.s.getmaxyx()
        if y<0 or y>=h or x<0 or x>=w-1:return
        try:self.s.addnstr(y,x,str(text).replace('\n',' '),w-x-1,attr)
        except curses.error:pass
    def prompt(self,label,default='',secret=False):
        h,w=self.s.getmaxyx()
        if h<12 or w<48:self.note='Terminal too small for input';return None
        self.s.timeout(-1)
        self.put(h-4,2,' '*max(0,w-4));self.put(h-4,2,label[:w-5],curses.A_BOLD)
        self.put(h-3,2,' '*max(0,w-4))
        buf=list('' if secret else str(default))
        try:curses.curs_set(1)
        except curses.error:pass
        try:
            while True:
                shown='•'*len(buf) if secret else ''.join(buf)
                self.put(h-3,2,' '*max(0,w-4))
                self.put(h-3,2,shown[-(w-6):])
                self.put(h-2,2,'Enter save   Esc cancel   Backspace delete')
                try:self.s.move(h-3, min(w-3,2+len(shown[-(w-6):])))
                except curses.error:pass
                ch=self.s.get_wch()
                if ch in ('\n','\r',10,13,curses.KEY_ENTER):return ''.join(buf)
                if ch in ('\x1b',27):return None
                if ch in ('\b','\x7f',8,127,curses.KEY_BACKSPACE):
                    if buf:buf.pop()
                elif ch in ('\x15',21):buf.clear()  # Ctrl+U
                elif isinstance(ch,str) and ch.isprintable() and len(buf)<1000:buf.append(ch)
        finally:
            try:curses.curs_set(0)
            except curses.error:pass
            self.s.timeout(400)
    def action(self,fn,description='Saved'):
        try:
            result=fn()
            if isinstance(result,dict) and (result.get('ok') is False or result.get('error')):
                self.note='ERROR · '+str(result.get('error') or result.get('reason') or result)[:90]
            else:self.note='OK · '+description
        except Exception as exc:
            # Never echo API tokens in TUI errors.
            message=str(exc)
            token=legacy.config().get('token','')
            if token:message=message.replace(token,'[REDACTED]')
            self.note='ERROR · '+message[:100]
        self.last=0
    def refresh(self):
        if time.monotonic()-self.last<5:return
        self.last=time.monotonic()
        for key,fn in [('player',legacy.playerctl_metadata),('public',lambda:legacy.api('',public=True))]:
            try:self.cache[key]=fn()
            except Exception as exc:self.cache[key]={'error':str(exc)}
    def draw(self):
        self.s.erase();h,w=self.s.getmaxyx()
        if h<18 or w<62:
            self.put(1,2,'NIRUPRESENCE · Enlarge terminal (62×18 minimum)');self.s.refresh();return
        accent=curses.color_pair(1) if curses.has_colors() else curses.A_BOLD
        good=curses.color_pair(2) if curses.has_colors() else curses.A_BOLD
        self.put(1,3,'NIRUPRESENCE',curses.A_BOLD|accent)
        self.put(1,w-10,'v'+__version__)
        self.put(2,2,'─'*(w-4))
        self.put(4,3,'WORKSPACE',curses.A_DIM)
        sidebar=23
        for i,(label,page) in enumerate(MENU):
            selected=i==self.selected
            mark='▸' if self.page==page else ' '
            self.put(6+i*2,3,(mark+' '+label).ljust(sidebar-4),curses.A_REVERSE if selected else 0)
        x=sidebar+3; maxval=w-x-3
        self.put(4,sidebar,'│')
        for y in range(5,h-4):self.put(y,sidebar,'│',curses.A_DIM)
        self.put(4,x,dict(MENU)[next(label for label,p in MENU if p==self.page)].upper(),accent|curses.A_BOLD)
        pub=self.cache.get('public',{});player=self.cache.get('player',{});p=preferences();s=legacy.state()
        sync={}
        try:sync=json.loads((Path.home()/'.local/state/nirupresence/last-sync.json').read_text())
        except (OSError,ValueError):pass
        last=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(sync['at'])) if sync.get('at') else 'Not yet'
        playing=player.get('playing',False)
        song=(' · '.join(filter(None,[str(player.get('artist') or ''),str(player.get('title') or '')]))) if playing else 'Nothing playing'
        rows=[];actions=[]
        if self.page=='overview':
            rows=[('PUBLIC PRESENCE',pub.get('status') or ('Online' if pub.get('online') else 'Offline')),
                  ('NIGHT MODE','Active' if pub.get('night_mode') else 'Inactive'),
                  ('NOW PLAYING',song),('SOURCE',player.get('source') or '—'),
                  ('LAST SYNC',last),('HEARTBEAT','Enabled' if p['heartbeat'] else 'Disabled · secondary device'),
                  ('MUSIC SHARING','Enabled' if p['music'] and s['share_music'] else 'Disabled')]
        elif self.page=='presence':
            temporary=pub.get('temporary') if isinstance(pub.get('temporary'),dict) else {}
            expiry=int(temporary.get('until') or 0)
            remaining=max(0,(expiry-int(time.time())+59)//60) if expiry else 0
            rows=[('PUBLIC STATUS',pub.get('status') or '—'),('TEMPORARY',f'Active · {remaining} min remaining' if expiry>time.time() else 'Inactive'),('EXPIRES',time.strftime('%Y-%m-%d %H:%M',time.localtime(expiry)) if expiry else '—'),('ONLINE','Yes' if pub.get('online') else 'No'),
                  ('DETAIL',pub.get('detail') or '—'),('MODE',str(pub.get('presence_mode') or 'auto').upper())]
            actions=['[a] Auto  [o] Online  [f] Offline','[s] Set status  [t] Temporary  [c] Cancel temporary']
        elif self.page=='music':
            rows=[('PLAYER',player.get('source') or '—'),('TYPE',player.get('media_type') or '—'),
                  ('ARTIST / CHANNEL',player.get('artist') or '—'),('TITLE',player.get('title') or '—'),
                  ('ALBUM',player.get('album') or '—'),('PLAYBACK','Playing' if playing else 'Stopped'),
                  ('SHARING','Enabled' if p['music'] and s['share_music'] else 'Disabled')]
            actions=['[m] Toggle sharing  [r] Send now']
        elif self.page=='night':
            rows=[('LOCAL NIGHT POLICY','Legacy · not used by background sync'),
                  ('SERVER NIGHT WINDOW','23:30–04:00 Stockholm'),('SERVER NIGHT', 'Active' if pub.get('night_mode') else 'Inactive'),
                  ('HEARTBEAT','Enabled' if p['heartbeat'] else 'Disabled'),
                  ('MUSIC','Independent of night and presence')]
            actions=['[n] Toggle night policy  [h] Toggle heartbeat']
        elif self.page=='microlog':
            rows=[('DRAFT',s['micro_draft'] or '(empty)'),('LENGTH',str(len(s['micro_draft']))+' / 1000 characters')]
            actions=['[e] Edit draft  [p] Publish  [x] Clear']
        elif self.page=='settings':
            rows=[('SERVER',legacy.config()['base_url']),('API TOKEN','Configured' if legacy.config()['token'] else 'Missing'),
                  ('TOKEN SOURCE','Local configuration (path not stored)'),('INTERVAL',str(p['interval'])+' seconds'),('HEARTBEAT','Enabled' if p['heartbeat'] else 'Disabled'),
                  ('NIGHT POLICY','Enabled' if p['night_policy'] else 'Disabled')]
            actions=['[a] Authentication setup  [f] Import file  [t] Paste token  [i] Interval','[h] Heartbeat  [n] Night policy']
        else:
            result=sync.get('result') or {}
            rows=[('TOKEN','Configured' if legacy.config()['token'] else 'Missing'),
                  ('PLAYERCTL','Available' if player.get('available') else 'Unavailable'),
                  ('LAST SYNC',last),('SYNC RESULT',str(result.get('music') or result.get('reason') or '—')),
                  ('SYNC ERROR',str(sync.get('error') or pub.get('error') or '—'))]
            actions=['[d] Run diagnostics  [r] Sync music']
        # Single-line key/value rows keep all actions visible on 24-line terminals.
        y=6
        value_x=min(x+19,w-16)
        for label,value in rows:
            if y>=h-9:break
            self.put(y,x,label[:max(4,value_x-x-1)],accent|curses.A_BOLD)
            self.put(y,value_x,str(value)[:max(1,w-value_x-3)],good if label in ('PLAYBACK','SHARING') and value in ('Playing','Enabled') else 0)
            y+=2
        if actions:
            ay=h-7
            for a in actions[:2]:
                self.put(ay,x,a[:maxval],curses.A_BOLD);ay+=1
        self.put(h-4,2,'─'*(w-4))
        self.put(h-3,3,'↑↓ / j k  Navigate     Enter  Open     Esc  Overview     q  Quit',curses.A_DIM)
        self.put(h-2,3,self.note[:w-6]);self.s.refresh()
    def choose_status(self):
        try:
            options=legacy.api('presence/statuses').get('statuses',[])
        except Exception as exc:
            self.note='ERROR · '+str(exc)[:90]
            return None
        if not options:
            self.note='ERROR · No statuses configured'
            return None
        # Numeric selection avoids typing errors and supports Unicode labels.
        choice=self.prompt('Status: '+ '  '.join(f'{i+1}:{x}' for i,x in enumerate(options))+'  0:Clear')
        if choice is None:return None
        if choice=='0':return ''
        if choice.isdigit() and 1<=int(choice)<=len(options):return options[int(choice)-1]
        self.note='ERROR · Select a listed number'
        return None
    def handle(self,key):
        if key in (ord('q'),ord('Q')):return False
        if key in (curses.KEY_UP,ord('k')):self.selected=(self.selected-1)%len(MENU);return True
        if key in (curses.KEY_DOWN,ord('j')):self.selected=(self.selected+1)%len(MENU);return True
        if key in (10,13,curses.KEY_ENTER):self.page=MENU[self.selected][1];self.note='';return True
        if key==27:self.page='overview';self.selected=0;self.note='';return True
        if self.page=='presence':
            if key==ord('a'):self.action(lambda:legacy.cmd_presence_mode('auto'),'Automatic presence')
            elif key==ord('o'):self.action(lambda:legacy.cmd_presence_mode('online'),'Manual online')
            elif key==ord('f'):self.action(lambda:legacy.cmd_presence_mode('offline'),'Manual offline')
            elif key==ord('s'):
                status=self.choose_status()
                if status is not None:
                    detail=self.prompt('Detail (optional):')
                    if detail is not None:self.action(lambda:legacy.cmd_status([status,detail]),'Status updated')
            elif key==ord('t'):
                status=self.choose_status()
                if status is not None:
                    detail=self.prompt('Temporary detail (optional):',str(self.cache.get('public',{}).get('detail') or ''))
                    if detail is not None:
                        minutes=self.prompt('Duration (30, 60, 120):','60')
                        if minutes:self.action(lambda:legacy.cmd_temp_status([status,minutes,detail]),'Temporary status set')
            elif key==ord('c'):self.action(legacy.cmd_cancel_temp,'Temporary status cleared')
        elif self.page=='music':
            if key==ord('m'):
                enabled=not legacy.state()['share_music'];self.action(lambda:legacy.cmd_share_music(str(enabled)),'Music sharing changed')
            elif key==ord('r'):self.action(lambda:sync_music(force=True),'Music sync completed')
        elif self.page in ('night','settings'):
            if key==ord('h'):self.action(lambda:set_preference('heartbeat',not preferences()['heartbeat']),'Heartbeat changed')
            elif key==ord('n'):self.action(lambda:set_preference('night_policy',not preferences()['night_policy']),'Night policy changed')
            elif self.page=='settings' and key==ord('i'):
                val=self.prompt('Sync interval (10–300 seconds):',str(preferences()['interval']))
                if val is not None:
                    try:
                        n=int(val)
                        if not 10<=n<=300:raise ValueError('Use 10–300 seconds')
                        self.action(lambda:set_preference('interval',n),'Interval saved')
                    except ValueError as exc:self.note='ERROR · '+str(exc)
            elif self.page=='settings' and key==ord('a'):
                choice=self.prompt('Authentication: 1 Import JSON / 2 Paste token:','1')
                if choice=='1':self.import_token()
                elif choice=='2':self.manual_token()
                elif choice is not None:self.note='Choose 1 or 2'
            elif self.page=='settings' and key==ord('f'):
                self.import_token()
            elif self.page=='settings' and key==ord('t'):
                self.manual_token()
        elif self.page=='microlog':
            if key==ord('e'):
                value=self.prompt('Edit draft (Ctrl+U clears):',legacy.state()['micro_draft'])
                if value is not None:self.action(lambda:legacy.cmd_draft([value]),'Draft saved')
            elif key==ord('p'):
                draft=legacy.state()['micro_draft']
                if draft and self.prompt('Publish draft? Type YES:')=='YES':self.action(lambda:legacy.cmd_microlog([draft]),'Published')
            elif key==ord('x'):
                if self.prompt('Clear draft? Type YES:')=='YES':self.action(lambda:legacy.cmd_draft([]),'Draft cleared')
        elif self.page=='doctor':
            if key==ord('d'):
                def doctor():
                    result=legacy.cmd_doctor();return {'ok':result.get('ok',False),'error':str(result.get('checks',{})) if not result.get('ok') else ''}
                self.action(doctor,'Diagnostics passed')
            elif key==ord('r'):self.action(lambda:sync_music(force=True),'Music sync completed')
        return True
    def import_token(self):
        path=self.prompt('JSON file path (type or paste; ~ supported):')
        if path:
            self.action(lambda:legacy.cmd_import_token([path]),'Token imported and connection verified')

    def manual_token(self):
        token=self.prompt('Paste API token (hidden):',secret=True)
        if token:
            base=self.prompt('HTTPS server:',legacy.config()['base_url'])
            if base is not None:
                self.action(lambda:legacy.cmd_configure([token,base]),'Token saved and connection verified')

    def run(self):
        while True:
            self.refresh();self.draw();key=self.s.getch()
            if key>=0 and not self.handle(key):break

def run():
    if not os.isatty(0) or not os.isatty(1):raise RuntimeError('TUI requires an interactive terminal')
    locale.setlocale(locale.LC_ALL, '')
    curses.wrapper(lambda screen:UI(screen).run())
