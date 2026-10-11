#!/usr/bin/env bash
set -Eeuo pipefail
BASE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.local/share/nirupresence/app"
BIN="$HOME/.local/bin/nirupresence"
STATE="$HOME/.local/state/nirupresence"

fail(){ printf '\n[FAIL] %s\n' "$*" >&2; exit 1; }
info(){ printf '[INFO] %s\n' "$*"; }
[[ $EUID -ne 0 ]] || fail 'Run as your normal user, not root. sudo is used only for dependencies.'
[[ -r /etc/os-release ]] || fail 'Cannot detect distribution: /etc/os-release missing.'
. /etc/os-release
case "${ID:-}" in
 debian|ubuntu) PM=apt; packages=(python3 playerctl util-linux) ;;
 void) PM=xbps; packages=(python3 playerctl util-linux) ;;
 *) fail "Unsupported distro ${ID:-unknown}. Supported: Debian, Ubuntu, Void." ;;
esac
missing=()
command -v python3 >/dev/null || missing+=(python3)
command -v playerctl >/dev/null || missing+=(playerctl)
command -v flock >/dev/null || missing+=(util-linux)
if ((${#missing[@]})); then
 info "Missing dependencies: ${missing[*]}"
 info "Requesting permission to install via $PM (sudo may prompt)."
 if [[ "$PM" == apt ]]; then
   sudo apt-get update && sudo apt-get install -y --no-install-recommends "${missing[@]}" || {
     printf 'Manual command: sudo apt-get update && sudo apt-get install %s\n' "${missing[*]}" >&2
     fail 'Dependency installation failed; existing installation was not changed.'
   }
 else
   sudo xbps-install -S -y "${missing[@]}" || {
     printf 'Manual command: sudo xbps-install -S %s\n' "${missing[*]}" >&2
     fail 'Dependency installation failed; existing installation was not changed.'
   }
 fi
fi
for tool in python3 playerctl flock; do command -v "$tool" >/dev/null || fail "Missing dependency: $tool"; done
python3 - <<'PY' || fail 'Python lacks curses, ssl or tkinter-independent standard library components.'
import curses, ssl, urllib.request
PY
[[ -f "$BASE/nirupresence/__main__.py" ]] || fail 'Incomplete release archive.'
python3 -m compileall -q "$BASE/nirupresence" || fail 'Python syntax check failed.'
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/nirupresence" "$HOME/.config/nirupresence" "$STATE"
chmod 700 "$HOME/.config/nirupresence" "$STATE"
STAGING="$HOME/.local/share/nirupresence/.app-staging-$$"
mkdir -p "$STAGING"
cp -a "$BASE/nirupresence" "$STAGING/"
cat > "$STAGING/launch" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$HOME/.local/share/nirupresence/app${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m nirupresence "$@"
SH
chmod 755 "$STAGING/launch"
if [[ -d "$DEST" ]]; then
  BACKUP="$HOME/.local/share/nirupresence/app-backup-$(date +%Y%m%d-%H%M%S)"
  mv "$DEST" "$BACKUP"
  info "Previous application backed up: $BACKUP"
fi
mv "$STAGING" "$DEST"
ln -sfn "$DEST/launch" "$BIN"
# Service never writes to global state until explicitly configured.
if command -v systemctl >/dev/null && [[ -d /run/systemd/system ]]; then
  mkdir -p "$HOME/.config/systemd/user"
  cat > "$HOME/.config/systemd/user/nirupresence.service" <<'SERVICE'
[Unit]
Description=NIRUPRESENCE background synchronization
After=network.target
[Service]
Type=simple
ExecStart=%h/.local/bin/nirupresence daemon
Restart=on-failure
RestartSec=10
[Install]
WantedBy=default.target
SERVICE
  if systemctl --user daemon-reload && systemctl --user enable --now nirupresence.service; then
    systemctl --user try-restart nirupresence.service || true
    info 'systemd user service enabled and started.'
  else
    info 'User systemd unavailable: run nirupresence daemon manually or enable it after login.'
  fi
else
  mkdir -p "$HOME/.config/autostart"
  # XDG Desktop Entry Exec is NOT a shell. Single quotes and $HOME are not expanded.
  # Use the real absolute path; escape characters significant to the Exec grammar.
  desktop_exec="${BIN//\\/\\\\}"
  desktop_exec="${desktop_exec// /\\ }"
  cat > "$HOME/.config/autostart/nirupresence.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=NIRUPRESENCE
Exec=$desktop_exec daemon
Terminal=false
X-GNOME-Autostart-enabled=true
DESKTOP
  # Detach fully from the installer terminal. flock in daemon prevents duplicates.
  nohup "$BIN" daemon </dev/null >>"$STATE/startup.log" 2>&1 &
  info 'Void: daemon started now; XDG autostart installed.'
  info 'For plain dwm/startx without XDG autostart, add this to ~/.xinitrc before exec dwm:'
  info '  ~/.local/bin/nirupresence daemon &'
fi
info 'Installed NIRUPRESENCE 0.5.8'
info 'Open TUI: nirupresence'
info 'Configure token in TUI → Settings → t, or import from JSON with Settings → f.'
info 'Default: music sync and heartbeat enabled; server controls AUTO/night mode.'
