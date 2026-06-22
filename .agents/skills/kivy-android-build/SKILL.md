# Kivy Android APK Build

Build a Kivy app into an Android APK using Buildozer + python-for-android in WSL.

## When to use

- User wants to package a Kivy project as `.apk` for Android
- Building from Windows via WSL (Ubuntu-24.04)
- User's network has proxy issues (needs Chinese mirrors)

## Prerequisites

- WSL Ubuntu-24.04 (or Linux) with:
  - `buildozer` ≥ 1.6.0
  - `python3` ≥ 3.10
  - Java (OpenJDK 17+, for gradle)
  - `pip install buildozer cython`
- Android SDK and NDK (auto-downloaded by buildozer)

## Quick start

```bash
cd /mnt/f/mywork/CurserProject/pytest
export PIP_BREAK_SYSTEM_PACKAGES=1
buildozer android debug
```

APK output: `bin/fitnessapp-*-debug.apk`

## Recipe source cache

Pre-download all recipe tarballs (avoid proxy corruption during build):

| File | URL |
|------|-----|
| Python 3.10.10 | `https://www.python.org/ftp/python/3.10.10/Python-3.10.10.tgz` |
| OpenSSL 1.1.1m | `https://www.openssl.org/source/openssl-1.1.1m.tar.gz` |
| libffi 3.4.2 | `https://github.com/libffi/libffi/archive/v3.4.2.tar.gz` |
| SDL2 2.26.1 | `https://github.com/libsdl-org/SDL/releases/download/release-2.26.1/SDL2-2.26.1.tar.gz` |
| SDL2_image 2.6.2 | `https://github.com/libsdl-org/SDL_image/releases/download/release-2.6.2/SDL2_image-2.6.2.tar.gz` |
| SDL2_mixer 2.6.2 | `https://github.com/libsdl-org/SDL_mixer/releases/download/release-2.6.2/SDL2_mixer-2.6.2.tar.gz` |
| SDL2_ttf 2.20.1 | `https://github.com/libsdl-org/SDL_ttf/releases/download/release-2.20.1/SDL2_ttf-2.20.1.tar.gz` |
| setuptools 51.3.3 | `https://files.pythonhosted.org/packages/source/s/setuptools/setuptools-51.3.3.tar.gz` |
| six 1.15.0 | `https://files.pythonhosted.org/packages/source/s/six/six-1.15.0.tar.gz` |
| sqlite 3.35.0 | `https://www.sqlite.org/2021/sqlite-amalgamation-3350500.zip` |
| pyjnius 1.5.0 | `https://github.com/kivy/pyjnius/archive/1.5.0.zip` |
| Kivy 2.1.0 | `https://github.com/kivy/kivy/archive/2.1.0.zip` |

Cache directory: `.buildozer/android/platform/build-arm64-v8a/packages/`
Each package needs a `.mark-FILENAME` file alongside it for p4a to skip download.

## p4a setup

python-for-android (p4a) must be set up with git for buildozer to accept it:

```bash
P4A=.buildozer/android/platform/python-for-android
rm -rf "$P4A"
mkdir -p "$(dirname "$P4A")"
unzip -q /path/to/p4a.zip -d "$(dirname "$P4A")"
mv "$(dirname "$P4A")/python-for-android-2023.09.16" "$P4A"
cd "$P4A"
git init -q
git config user.email "b@local"
git config user.name "build"
git add .
git commit -q -m "init"
git remote add origin https://github.com/kivy/python-for-android.git
git config branch.master.remote origin
git config branch.master.merge refs/heads/master
```

## Required patches

### 1. Python3 CFLAGS (NDK 25b errno fix)

File: `pythonforandroid/recipes/python3/__init__.py`

```python
# Change this:
env['CFLAGS'] = ' '.join(['-fPIC', '-DANDROID'])
# To this:
env['CFLAGS'] = ' '.join([
    '-fPIC', '-DANDROID', '-D__USE_GNU', '-D__USE_BSD',
    '-include errno.h', '-include sys/uio.h', '-include sys/time.h'
])
```

### 2. Local gradle (avoid gradlew download failure)

File: `pythonforandroid/toolchain.py`

```python
# Change:
gradlew = sh.Command('./gradlew')
# To:
gradlew = sh.Command('/home/skaven/gradle-7.4.1/bin/gradle')
```

### 3. Gradle Aliyun mirrors (proxy bypass)

File: `pythonforandroid/bootstraps/common/build/templates/build.tmpl.gradle`

Remove `google()` and `jcenter()` lines. Add before them:
```
maven { url 'https://maven.aliyun.com/repository/google' }
maven { url 'https://maven.aliyun.com/repository/public' }
```

### 4. Buildozer git branch check

File: `/usr/local/lib/python3.12/dist-packages/buildozer/targets/android.py`

```python
# Wrap git branch -vv call in try/except:
try:
    cur_branch = buildops.cmd(
        ["git", "branch", "-vv"],
        get_stdout=True, cwd=p4a_dir, env=self.buildozer.environ
    ).stdout.split()[1]
except:
    cur_branch = "unknown"
```

> Buildozer is system-installed: use PYTHONPATH override if no sudo.

### 5. pip mirror (optional, for speed)

```bash
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
```

## SDL2 external dependencies

SDL2_image uses `external/download.sh` (git submodules). SDL2_mixer has a similar script.

Pre-cloned repos needed: jpeg, png, tiff, webp (for image), flac, ogg, vorbis, lame, modplug (for mixer).

Place these in:
- `.buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2_image/external/`
- `.buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2_mixer/external/`

Modify `download.sh` to skip existing dirs:
```bash
sed -i 's|git clone|test -d "$2" \&\& echo "skip" || git clone|' download.sh
```

## Gradle setup

```bash
# Install gradle 7.4.1 locally:
unzip -q gradle-7.4.1-all.zip -d /home/skaven/
# Pre-place in wrapper cache:
DIST=/home/skaven/.gradle/wrapper/dists/gradle-7.4.1-all/1746691698
mkdir -p "$DIST"
cp gradle-7.4.1-all.zip "$DIST/"
```

## Build command

```bash
cd /project/root
export PIP_BREAK_SYSTEM_PACKAGES=1
# If using local buildozer patch:
export PYTHONPATH=/home/skaven/local_buildozer:$PYTHONPATH
# Disable proxy (Chinese mirrors):
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
buildozer android debug
```

## Troubleshooting

### "RPC failed" / git clone fails
- Network/proxy issue. Pre-download packages manually.
- Use `--depth 1` git clones where possible.

### "errno.h not found" / errno compilation errors
- Apply patch #1 (add `-include errno.h` to CFLAGS).
- NDK 25b needs explicit header includes.

### "gradlew failed" / gradle connection reset
- Use local gradle (patch #2) + Aliyun mirrors (patch #3).
- Gradle wrapper tries to download from Google/JCenter which is blocked.

### "Label.padding value length is immutable"
- Kivy 2.1.0 on Android only supports 2-value padding `[h, v]`, not 4-value `[l, t, r, b]` for Labels.

### No crash log written
- Exception is at C level (not Python), or log path not writable.
- Add error screen in `build()`:
  ```python
  try:
      ... normal init ...
  except Exception:
      from kivy.uix.label import Label
      import traceback, io
      buf = io.StringIO()
      traceback.print_exc(file=buf)
      return Label(text=buf.getvalue(), ...)
  ```

## Android-specific code issues

- **Font paths**: Use `LabelBase.register()` at startup, not file paths in `font_name`.
- **Database path**: On Android use `App.get_running_app().user_data_dir`, not `os.path.dirname(__file__)`.
- **File access**: Assets are inside APK, not on filesystem. Use Kivy's resource system.
