# NIRUPRESENCE

Personal Linux companion for n.rudolfsson.net. **0.5.10** · MIT license.

Supports Debian/Ubuntu and Arch (systemd user service) plus Void Linux (nirupi, dwm/xinit or XDG session autostart). Music sharing and heartbeat run independently of the terminal UI. Presence AUTO, night hours and manual offline are controlled by the server.

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

On Debian and Arch the installer uses the systemd user service. On Void it installs every applicable graphical-session hook: nirupi autostart when present, `~/.config/xinitrc.d/80-nirupresence.sh` when `~/.xinitrc` sources that directory, and the XDG autostart entry. The daemon's file lock prevents duplicates, and Void hooks start at the next graphical login rather than from the installer environment.

The last background result is in `~/.local/state/nirupresence/last-sync.json`; errors in `daemon.log` or `startup.log`. Do not share tokens or private config files. Use `systemctl --user status nirupresence.service` on Debian and Arch.

## 0.5.10

Void autostart now covers SDDM/nirupi sessions as well as dwm/xinit and XDG desktops; applicable hooks are installed together and the existing daemon lock prevents duplicates. Adds Arch and Arch derivatives to the installer with pacman package handling. Debian/Ubuntu and systemd startup are unchanged. Existing config and state are preserved.

## 0.5.9

Void dwm/xinit autostart now inherits the graphical D-Bus session. An inaccessible MPRIS bus no longer clears Now Playing. Debian systemd startup remains unchanged. Existing config and state are preserved.

## 0.5.8

Fixes the Void XDG desktop entry: `Exec` now contains an absolute executable path instead of unsupported shell quoting and `$HOME` expansion. Corrects misleading installer heartbeat messaging. No server API or presence policy changes.
