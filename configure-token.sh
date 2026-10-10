#!/usr/bin/env bash
set -euo pipefail
read -rsp 'NIRUPRESENCE API token: ' token
printf '\n'
if [[ -z "$token" ]]; then echo 'No token entered.' >&2; exit 1; fi
"$HOME/.local/bin/nirupresence" configure "$token"
unset token
