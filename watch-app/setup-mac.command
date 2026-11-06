#!/bin/bash
# Apple Silicon macOS: install Gradle 8.9, generate official wrapper, and build debug APK.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
if [ ! -d "$ANDROID_HOME/platforms/android-35" ]; then
  echo "ERROR: Android SDK Platform 35 is missing in $ANDROID_HOME" >&2; exit 1
fi
if [ -z "${JAVA_HOME:-}" ]; then
  for studio in "/Applications/Android Studio.app/Contents/jbr/Contents/Home" "$HOME/Applications/Android Studio.app/Contents/jbr/Contents/Home"; do
    if [ -x "$studio/bin/java" ]; then export JAVA_HOME="$studio"; break; fi
  done
fi
if ! command -v java >/dev/null 2>&1 && [ -z "${JAVA_HOME:-}" ]; then
  echo "ERROR: Java/JDK 17+ not found. Install Android Studio first." >&2; exit 1
fi
if [ -n "${JAVA_HOME:-}" ]; then export PATH="$JAVA_HOME/bin:$PATH"; fi
echo "Java:"; java -version
GRADLE_VERSION=8.9
GRADLE_DIR="$HOME/.gradle/bootstrap/gradle-$GRADLE_VERSION"
if [ ! -x "$GRADLE_DIR/bin/gradle" ]; then
  TMPDIR_WORK="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR_WORK"' EXIT
  echo "Downloading official Gradle $GRADLE_VERSION (may be ~130 MB)..."
  curl --fail --location --retry 3 --connect-timeout 20 --output "$TMPDIR_WORK/gradle.zip" "https://services.gradle.org/distributions/gradle-$GRADLE_VERSION-bin.zip"
  unzip -q "$TMPDIR_WORK/gradle.zip" -d "$TMPDIR_WORK"
  mkdir -p "$(dirname "$GRADLE_DIR")"
  mv "$TMPDIR_WORK/gradle-$GRADLE_VERSION" "$GRADLE_DIR"
fi
echo "Generating official Gradle Wrapper..."
"$GRADLE_DIR/bin/gradle" wrapper --gradle-version "$GRADLE_VERSION" --distribution-type bin
chmod +x ./gradlew
echo "Building Wear OS debug APK..."
./gradlew --no-daemon :app:assembleDebug
APK="$ROOT/app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK" ]; then
 echo; echo "SUCCESS: $APK"; echo 'In Android Studio, open this watch-app folder and connect the watch to install.'
else
 echo 'Gradle exited but APK is missing.' >&2; exit 1
fi
