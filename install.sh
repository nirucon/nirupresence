#!/usr/bin/env bash
set -Eeuo pipefail
BASE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.local/share/nirupresence/app"
BIN="$HOME/.local/bin/nirupresence"
STATE="$HOME/.local/state/nirupresence"
OS_RELEASE="${NIRUPRESENCE_OS_RELEASE:-/etc/os-release}"
SYSTEMD_RUNTIME="${NIRUPRESENCE_SYSTEMD_RUNTIME:-/run/systemd/system}"

fail(){ printf '\n[FAIL] %s\n' "$*" >&2; exit 1; }
info(){ printf '[INFO] %s\n' "$*"; }
[[ $EUID -ne 0 ]] || fail 'Run as your normal user, not root. sudo is used only for dependencies.'
[[ -r "$OS_RELEASE" ]] || fail "Cannot detect distribution: $OS_RELEASE missing."
. "$OS_RELEASE"
ids=" ${ID:-} ${ID_LIKE:-} "
case "$ids" in
 *' debian '*|*' ubuntu '*) PM=apt; PYTHON_PACKAGE=python3 ;;
 *' void '*) PM=xbps; PYTHON_PACKAGE=python3 ;;
 *' arch '*) PM=pacman; PYTHON_PACKAGE=python ;;
 *) fail "Unsupported distro ${ID:-unknown}. Supported: Debian/Ubuntu, Void, Arch." ;;
esac
missing=()
command -v python3 >/dev/null || missing+=("$PYTHON_PACKAGE")
command -v playerctl >/dev/null || missing+=(playerctl)
command -v flock >/dev/null || missing+=(util-linux)
install_dependencies(){
 case "$PM" in
  apt) sudo apt-get update && sudo apt-get install -y --no-install-recommends "${missing[@]}" ;;
  xbps) sudo xbps-install -S -y "${missing[@]}" ;;
  pacman) sudo pacman -S --needed --noconfirm "${missing[@]}" ;;
 esac
}
manual_command(){
 case "$PM" in
  apt) printf 'sudo apt-get update && sudo apt-get install %s\n' "${missing[*]}" ;;
  xbps) printf 'sudo xbps-install -S %s\n' "${missing[*]}" ;;
  pacman) printf 'sudo pacman -S --needed %s\n' "${missing[*]}" ;;
 esac
}
if ((${#missing[@]})); then
 info "Missing dependencies: ${missing[*]}"
 info "Requesting permission to install via $PM (sudo may prompt)."
 if ! install_dependencies; then
   printf 'Manual command: %s\n' "$(manual_command)" >&2
   fail 'Dependency installation failed; existing installation was not changed.'
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
has_systemd(){ command -v systemctl >/dev/null 2>&1 && [[ -d "$SYSTEMD_RUNTIME" ]]; }
has_nirupi(){ command -v nirupi-autostart.sh >/dev/null 2>&1 || [[ -x "$HOME/.local/bin/nirupi-autostart.sh" ]]; }
has_xinit_hook(){ [[ -f "$HOME/.xinitrc" && -d "$HOME/.config/xinitrc.d" ]] && grep -q 'xinitrc.d/' "$HOME/.xinitrc"; }
install_systemd(){
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
 systemctl --user daemon-reload && systemctl --user enable --now nirupresence.service || return 1
 systemctl --user try-restart nirupresence.service || true
 info 'systemd user service enabled and started.'
}
install_nirupi_autostart(){
 local entry="$HOME/.config/nirupi/autostart/50-nirupresence.sh"
 mkdir -p "${entry%/*}"
 cat > "$entry" <<'NIRUPI'
#!/usr/bin/env bash
# name: NIRUPRESENCE
if command -v nirupresence >/dev/null 2>&1; then
  exec nirupresence daemon </dev/null >>"$HOME/.local/state/nirupresence/startup.log" 2>&1
fi
NIRUPI
 chmod 755 "$entry"
}
install_xinit_autostart(){
 local entry="$HOME/.config/xinitrc.d/80-nirupresence.sh"
 mkdir -p "${entry%/*}"
 cat > "$entry" <<'XINIT'
#!/usr/bin/env bash
# Loaded by ~/.xinitrc inside the graphical D-Bus session.
if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]] && command -v nirupresence >/dev/null 2>&1; then
  nirupresence daemon </dev/null >>"$HOME/.local/state/nirupresence/startup.log" 2>&1 &
fi
XINIT
 chmod 755 "$entry"
}
install_xdg_autostart(){
 mkdir -p "$HOME/.config/autostart"
 local desktop="$HOME/.config/autostart/nirupresence.desktop"
 local disabled="$desktop.disabled"
 local desktop_exec="${BIN//\\/\\\\}"
 desktop_exec="${desktop_exec// /\\ }"
 cat > "$desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=NIRUPRESENCE
Exec=$desktop_exec daemon
Terminal=false
X-GNOME-Autostart-enabled=true
DESKTOP
 if [[ -f "$disabled" ]] && grep -qx 'Name=NIRUPRESENCE' "$disabled"; then
   rm -f "$disabled"
 fi
}
SYSTEMD_OK=0
if has_systemd && install_systemd; then
 SYSTEMD_OK=1
fi
if ((!SYSTEMD_OK)); then
 got=()
 if has_nirupi; then
   install_nirupi_autostart
   got+=(nirupi)
 fi
 if has_xinit_hook; then
   install_xinit_autostart
   got+=(xinitrc)
 fi
 install_xdg_autostart
 got+=(XDG)
 info "Graphical-session autostart installed (${got[*]}); starts at next login."
fi
info 'Installed NIRUPRESENCE 0.5.10'
info 'Open TUI: nirupresence'
info 'Configure token in TUI → Settings → t, or import from JSON with Settings → f.'
info 'Default: music sync and heartbeat enabled; server controls AUTO/night mode.'
