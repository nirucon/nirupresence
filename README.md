# NIRUPRESENCE

Personal Linux companion for n.rudolfsson.net. **0.5.8** · MIT license.

Supports Debian/Ubuntu (systemd user service) and Void Linux (XDG autostart). Music sharing and heartbeat run independently of the terminal UI. Presence AUTO, night hours and manual offline are controlled by the server.

## Install / update

```bash
git clone https://github.com/nirucon/nirupresence.git
cd nirupresence
bash install.sh
```

On an existing checkout: `git pull --ff-only && bash install.sh`.

The installer keeps personal configuration and state, and backs up the previous application code. Configure the API token in `nirupresence` → Settings.

## Check

```bash
nirupresence version
nirupresence service-status
nirupresence doctor
nirupresence sync
```

On Void, check `~/.config/autostart/nirupresence.desktop`. The desktop session must support XDG autostart. Minimal dwm/startx setups without it need `~/.local/bin/nirupresence daemon &` before `exec dwm` in `~/.xinitrc`. The daemon's file lock prevents duplicates. On Debian use `systemctl --user status nirupresence.service`.

The last background result is in `~/.local/state/nirupresence/last-sync.json`; errors in `daemon.log` or `startup.log`. Do not share tokens or private config files.

## 0.5.8

Fixes the Void XDG desktop entry: `Exec` now contains an absolute executable path instead of unsupported shell quoting and `$HOME` expansion. Corrects misleading installer heartbeat messaging. No server API or presence policy changes.
