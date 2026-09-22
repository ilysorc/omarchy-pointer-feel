#!/usr/bin/env bash
# The only bootstrap dependency is Bash (part of Omarchy).
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
if (( EUID == 0 )); then
  echo 'Run Mouse Style setup as your desktop user, without sudo.' >&2
  exit 1
fi
if ! command -v python3 >/dev/null; then
  for argument in "$@"; do
  case "$argument" in
    --status|--plan)
      printf '%s\n' '{"ready":false,"running":false,"message":"Python is missing. Install Mouse Style to install the required packages."}'
      exit 0 ;;
    --help|-h)
      echo 'Usage: ./install.sh [--yes] [--plan|--status|--uninstall] [--no-restart]'
      exit 0 ;;
  esac
  done
  command -v omarchy >/dev/null && command -v pacman >/dev/null || {
    echo 'Mouse Style requires an Omarchy desktop on Arch Linux.' >&2; exit 1;
  }
  echo 'Mouse Style needs Python. It will be installed from your configured Arch repositories.'
  if [[ " $* " != *' --yes '* ]]; then
    read -r -p 'Install the required packages and Mouse Style? [y/N] ' answer
    [[ "$answer" == y || "$answer" == Y ]] || exit 1
  fi
  if [[ -t 0 && -t 1 ]]; then
    sudo /usr/bin/pacman -S --needed --noconfirm -- python
  else
    /usr/bin/pkexec --disable-internal-agent /usr/bin/pacman -S --needed --noconfirm -- python
  fi
fi
exec python3 "$ROOT/setup.py" "$@"
