#!/usr/bin/env bash
# Deploy debug APK to running emulator/device on code change.
# Usage:
#   ./scripts/deploy.sh          # build + install + restart once
#   ./scripts/deploy.sh --watch  # auto-rebuild on file change (requires fswatch)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGE="com.kidscheck.app"
MAIN_ACTIVITY="com.kidscheck.app.MainActivity"

# Locate Android SDK
if [ -z "${ANDROID_HOME:-}" ]; then
  if [ -d "$HOME/Library/Android/sdk" ]; then
    export ANDROID_HOME="$HOME/Library/Android/sdk"
  elif [ -f "$PROJECT_DIR/local.properties" ]; then
    export ANDROID_HOME=$(grep '^sdk.dir' "$PROJECT_DIR/local.properties" | cut -d'=' -f2 | sed 's/\\//g')
  else
    echo "❌ ANDROID_HOME not set and SDK not found. Complete Android Studio setup first." >&2
    exit 1
  fi
fi

ADB="$ANDROID_HOME/platform-tools/adb"
if [ ! -x "$ADB" ]; then
  echo "❌ adb not found at $ADB. Complete Android Studio SDK setup first." >&2
  exit 1
fi

build_and_deploy() {
  echo "🔨 Building debug APK..."
  "$PROJECT_DIR/gradlew" -p "$PROJECT_DIR" assembleDebug -q

  APK=$(find "$PROJECT_DIR/app/build/outputs/apk/debug" -name "*.apk" | head -1)
  if [ -z "$APK" ]; then
    echo "❌ APK not found after build." >&2
    return 1
  fi

  echo "📲 Installing to device..."
  "$ADB" install -r "$APK"

  echo "🔄 Restarting app..."
  "$ADB" shell am force-stop "$PACKAGE"
  "$ADB" shell am start -n "$PACKAGE/$MAIN_ACTIVITY"

  echo "✅ Done! App restarted on device."
}

build_and_deploy

if [ "${1:-}" = "--watch" ]; then
  if ! command -v fswatch &>/dev/null; then
    echo "⚠️  fswatch not found. Install with: brew install fswatch" >&2
    exit 1
  fi
  echo ""
  echo "👀 Watching for changes in app/src/..."
  echo "   Press Ctrl+C to stop."
  echo ""
  fswatch -o "$PROJECT_DIR/app/src" | while read -r _; do
    echo ""
    echo "--- Change detected $(date +%H:%M:%S) ---"
    build_and_deploy || true
  done
fi
