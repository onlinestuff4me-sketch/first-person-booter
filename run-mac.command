#!/bin/bash
# First-Person Booter — macOS launcher.
# Double-click me in Finder (or run: bash run-mac.command).
# Finds (or offers to install) GZDoom, fetches the free Freedoom game data on
# first run, then boots the mod. Nothing here touches your system without asking.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; read -rp "Press Return to close... "; exit 1; }

# ---------------------------------------------------------------- the mod --
PK3=""
for c in "$HERE/dist/FirstPersonBooter.pk3" "$HERE/FirstPersonBooter.pk3"; do
	[ -f "$c" ] && PK3="$c" && break
done
[ -n "$PK3" ] || die "FirstPersonBooter.pk3 not found (looked in ./ and ./dist/).
Keep this script inside the repo folder, or put the pk3 next to it."

# ----------------------------------------------------------------- gzdoom --
find_gzdoom() {
	GZ=""
	for c in "/Applications/GZDoom.app/Contents/MacOS/gzdoom" \
	         "$HOME/Applications/GZDoom.app/Contents/MacOS/gzdoom"; do
		[ -x "$c" ] && GZ="$c" && return 0
	done
	if command -v gzdoom >/dev/null 2>&1; then
		GZ="$(command -v gzdoom)"
	fi
}

BREW=""
for c in "$(command -v brew 2>/dev/null || true)" /opt/homebrew/bin/brew /usr/local/bin/brew; do
	[ -n "$c" ] && [ -x "$c" ] && BREW="$c" && break
done

find_gzdoom
if [ -z "$GZ" ] && [ -n "$BREW" ]; then
	say "GZDoom isn't installed. Install it now with Homebrew (brew install --cask gzdoom)? [y/n]"
	read -r ans
	if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
		"$BREW" install --cask gzdoom
		find_gzdoom
	fi
fi
[ -n "$GZ" ] || die "GZDoom not found. Get the macOS build from https://zdoom.org/downloads,
drag GZDoom.app into /Applications, then run me again."

# Browser/brew downloads get quarantined and macOS refuses to launch them.
APP_ROOT="${GZ%/Contents/MacOS/gzdoom}"
if [ "$APP_ROOT" != "$GZ" ] && xattr -p com.apple.quarantine "$APP_ROOT" >/dev/null 2>&1; then
	say "macOS has quarantined GZDoom.app (normal for downloaded apps)."
	say "Remove the quarantine flag so it can run? [y/n]"
	read -r ans
	if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
		xattr -dr com.apple.quarantine "$APP_ROOT" || true
	fi
fi

# --------------------------------------------------------- game data (IWAD) --
SUPPORT="$HOME/Library/Application Support/gzdoom"
WAD=""
for c in "$HERE/freedoom2.wad" "$HERE/wads/freedoom2.wad" "$SUPPORT/freedoom2.wad" \
         "$HOME/Downloads/freedoom2.wad" "$HERE/doom2.wad" "$SUPPORT/doom2.wad" \
         "$HOME/Downloads/DOOM2.WAD"; do
	[ -f "$c" ] && WAD="$c" && break
done
if [ -z "$WAD" ]; then
	FD_VER="0.13.0"
	say "No game data found — downloading Freedoom $FD_VER (free, ~30 MB)..."
	TMP="$(mktemp -d)"
	trap 'rm -rf "$TMP"' EXIT
	curl -fL --progress-bar \
		"https://github.com/freedoom/freedoom/releases/download/v${FD_VER}/freedoom-${FD_VER}.zip" \
		-o "$TMP/freedoom.zip" \
		|| die "Download failed. Grab freedoom2.wad from https://freedoom.github.io/download.html
and put it next to this script, then run me again."
	unzip -j -o "$TMP/freedoom.zip" "*/freedoom2.wad" -d "$HERE" >/dev/null
	WAD="$HERE/freedoom2.wad"
fi

say "Booting: $(basename "$WAD") + $(basename "$PK3")"
exec "$GZ" -iwad "$WAD" -file "$PK3"
