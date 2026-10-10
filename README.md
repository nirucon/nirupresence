# NIRUPRESENCE

A lightweight Linux terminal application for managing presence, status updates, music activity and related features on my personal website.

**Version 0.5.7 · Personal project · Open source · MIT License**  
Created by **Ing Leif Nicklas Rudolfsson**.

## About this project

NIRUPRESENCE was developed primarily for my own website, systems and workflow. It reflects my personal requirements and is not intended to be a general-purpose product. Compatibility with other websites, APIs or environments is not guaranteed.

I publish the source code openly in case others find it useful or want to adapt it to their own projects. You are free to use, study, modify and redistribute the software, including commercially, under the terms of the [MIT License](LICENSE).

The software is provided **as is**, without warranty, guaranteed support, or any commitment to ongoing maintenance. Feel free to make it your own.

## Installation

Debian 13 / Ubuntu and Void Linux (glibc or musl):

```bash
bash install.sh
nirupresence
```

The installer checks and installs `python3`, `playerctl` and `util-linux` using APT or XBPS, reports failures and prints the manual command. The TUI uses Python's built-in `curses` library; no pip installation is required.

The background daemon runs without the TUI. Debian uses a systemd user service. Void installs an XDG autostart entry and starts the daemon for the current session. **For minimal dwm sessions that do not implement XDG autostart**, add `~/.local/bin/nirupresence daemon &` to `~/.xinitrc` before `exec dwm`. The daemon uses a process lock, so a second invocation exits safely. No dwm statusbar integration is included.

## TUI

Run `nirupresence` to open the terminal interface. Arrow keys/j/k navigate; Enter selects; Esc returns; q exits. The UI has Presence, Now Playing, Night & Privacy, Microlog, Settings and Diagnostics. Status editing, temporary status, offline/online, sharing, API token (`t`, not `k`) and draft publishing are available through the corresponding hotkeys displayed on each page. Microlog editor is a single-line editor (up to the terminal width); longer texts can be published through the CLI.

## Commands

```bash
nirupresence doctor
nirupresence status
nirupresence service-status
nirupresence now-playing
nirupresence sync
nirupresence preferences
nirupresence preferences heartbeat true
nirupresence preferences night_policy true
nirupresence offline true
nirupresence offline false
nirupresence microlog 'Text to publish'
```

## Multi-computer safety

**Heartbeat is OFF by default on new Debian/Void installations.** Music sharing is ON. This avoids an idle secondary computer continuously claiming global presence or triggering night/offline actions. Enable heartbeat on the computer you want to report Daily Driver first signal. The original 0.4.1 night policy uses 23:00–04:00 and is OFF by default on Linux. The server has shared global music state: **this release does not solve cross-device ownership or music arbitration**. Two simultaneously playing computers can still overwrite each other's Now Playing. Do not enable night policy on multiple machines. Historical Daily Driver rows are server-side and are not cleared by this client.

## Upgrading and rollback

`install.sh` preserves `~/.config/nirupresence/config.json`, `~/.config/nirupresence/linux.json` and `~/.local/state/nirupresence/`. Existing application code is moved to a timestamped `app-backup-*` directory. The Omarchy QuickShell plugin remains untouched.

Systemd logs: `journalctl --user -u nirupresence -n 50`.
Void log: `~/.local/state/nirupresence/daemon.log`.

This package is tested with syntax checks and local mocks, **not on a live Debian or Void desktop**. Verify service autostart after logout/login.

## Features and compatibility

Music sync is independent of night mode and manual offline. `sync-music` uses the daemon path and forces an immediate update. `k` navigates up consistently; Settings token shortcut is `t`. Updated compact two-column TUI and improved masked input. Temporary presence requires website API 0.7.19 or newer.

## Token import (multiple machines)

Import from your existing JSON configuration without copying the file into the repository:

```bash
nirupresence import-token ~/path/to/nirupresence-config.json
```

No default path is embedded in the source. In the TUI, open Settings and press `f`, then enter the path yourself. Supported JSON keys: `token` (or `api_token`) and optional `base_url`; alternatively these keys may be inside `config`. The token is validated against the server before the previous configuration is retained or replaced. Never commit the token JSON.

For security, both API and Navidrome require HTTPS. Navidrome metadata lookup requires an explicitly configured server URL; automatic discovery from media stream URLs is disabled. Existing local config is preserved during upgrade.

## Server dependency

Temporary status now requires n.rudolfsson.net **0.7.19** or newer. In the TUI select a predefined status by number, enter optional Unicode detail, then choose 30, 60 or 120 minutes. Server-side expiry avoids multi-device restore races. Install the server patch first. `nirupresence --help` lists commands.

## Authentication

In TUI → Settings press `a` to choose **Import JSON** or **Paste token**.
Press `f` to import directly or `t` to paste a token directly.
Import asks for the JSON path each time; no personal path is stored or shipped.
Manual entry prompts for the HTTPS server address. The token is masked and the
connection is verified before the previous working configuration is replaced.
The import file is read-only. Its path is neither stored nor sent to the API.

This release does not add a graphical filesystem picker, token visibility toggle,
or new server endpoints. Those require separate UX/security review.

## Privacy

Removed hard-coded personal token file path from application source and documentation. Import requires an explicit file path. No import source path is persisted. Existing saved token and settings remain intact on upgrade. The token can still be pasted manually in Settings (`t`).

## Release checks

Run `python3 -m unittest discover -s tests -v` before publishing. No credentials, private configuration or machine-specific token paths belong in the repository.
