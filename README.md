# NIRUPRESENCE

Personal Linux companion for n.rudolfsson.net. **0.5.9** · MIT license.

Supports Debian/Ubuntu (systemd user service) and Void Linux (XDG autostart or dwm/xinit session autostart). Music sharing and heartbeat run independently of the terminal UI. Presence AUTO, night hours and manual offline are controlled by the server.

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

On Void with an existing `~/.xinitrc` sourcing `~/.config/xinitrc.d/*.sh`, the installer adds `80-nirupresence.sh` to start inside the graphical D-Bus session. Other Void desktops use XDG autostart. Installation does not start a daemon from a potentially incorrect installer environment. The daemon's file lock prevents duplicates. On Debian use `systemctl --user status nirupresence.service`.

The last background result is in `~/.local/state/nirupresence/last-sync.json`; errors in `daemon.log` or `startup.log`. Do not share tokens or private config files.

## 0.5.9

Void dwm/xinit autostart now inherits the graphical D-Bus session. An inaccessible MPRIS bus no longer clears Now Playing. Debian systemd startup remains unchanged. Existing config and state are preserved.

## 0.5.8

Fixes the Void XDG desktop entry: `Exec` now contains an absolute executable path instead of unsupported shell quoting and `$HOME` expansion. Corrects misleading installer heartbeat messaging. No server API or presence policy changes.
