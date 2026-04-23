#!/usr/bin/env bash
# One-line installer: curl -fsSL https://raw.githubusercontent.com/franzenzenhofer/tinyscreenshot/main/scripts/install.sh | bash
#
# Prefers `pipx` for an isolated install. Falls back to `pip install --user`.
# Works on macOS and Linux with Python 3.9+.
set -euo pipefail

PKG="tinyscreenshot"
VERSION="${TINYSCREENSHOT_VERSION:-}"
SPEC="$PKG"
[ -n "$VERSION" ] && SPEC="${PKG}==${VERSION}"

log() { printf '>> %s\n' "$*" >&2; }
err() { printf '!! %s\n' "$*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

log "detecting Python..."
if have python3; then PY=python3
elif have python; then PY=python
else err "need Python 3.9+; install from https://www.python.org/downloads/ or your package manager"
fi

PY_OK=$("$PY" -c 'import sys; print("1" if sys.version_info >= (3,9) else "0")')
[ "$PY_OK" = "1" ] || err "Python 3.9+ required (found $($PY --version))"
log "using $PY ($($PY --version 2>&1))"

install_with_pipx() {
  log "installing $SPEC via pipx..."
  pipx install --force "$SPEC"
}

install_with_pip() {
  log "pipx not found — falling back to 'pip install --user'"
  "$PY" -m pip install --user --upgrade "$SPEC"
  log "make sure \$(python3 -m site --user-base)/bin is on your PATH"
}

if have pipx; then
  install_with_pipx
else
  log "tip: installing via pipx is cleaner — see https://pipx.pypa.io/"
  install_with_pip
fi

if have tinyscreenshot; then
  tinyscreenshot --version
  log "✓ installed. try:   tinyscreenshot list"
  log "✓ wire up Claude Code skill: tinyscreenshot install-skill"
else
  log "installed, but 'tinyscreenshot' not on PATH yet. Check your shell PATH (pipx ensurepath / ~/.local/bin)."
fi
