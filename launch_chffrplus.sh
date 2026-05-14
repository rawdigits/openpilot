#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

source "$DIR/launch_env.sh"

function agnos_init {
  # TODO: move this to agnos
  sudo rm -f /data/etc/NetworkManager/system-connections/*.nmmeta

  # set success flag for current boot slot
  sudo abctl --set_success

  # TODO: do this without udev in AGNOS
  # udev does this, but sometimes we startup faster
  sudo chgrp gpu /dev/adsprpc-smd /dev/ion /dev/kgsl-3d0
  sudo chmod 660 /dev/adsprpc-smd /dev/ion /dev/kgsl-3d0

  # Check if AGNOS update is required
  if [ $(< /VERSION) != "$AGNOS_VERSION" ]; then
    AGNOS_PY="$DIR/system/hardware/tici/agnos.py"
    MANIFEST="$DIR/system/hardware/tici/agnos.json"
    if $AGNOS_PY --verify $MANIFEST; then
      sudo reboot
    fi
    $DIR/system/hardware/tici/updater $AGNOS_PY $MANIFEST
  fi
}

function launch {
  # Remove orphaned git lock if it exists on boot
  [ -f "$DIR/.git/index.lock" ] && rm -f $DIR/.git/index.lock

  # Recover from build state corrupted by an unclean shutdown mid-build
  # (e.g. truck powered off while build.py was running). Three failure modes,
  # all of which persist across reboots on /data (eMMC) and wedge the
  # "openpilot failed to build" splash until manually cleaned:
  #
  # 1. Orphaned SCons CacheDir lockfile (/data/scons_cache/config.lock):
  #    SCons' FileLock has no crash-recovery. On next boot build.py hits
  #    SConsLockFailure: Timeout waiting for lock on '/data/scons_cache/config'
  #    after 5s.
  #
  # 2. Zero-byte .o / .os files in the source tree AND in the SCons cache:
  #    SCons' CacheDir.push() copies completed objects to the cache. If a
  #    child cc/clang++ is SIGKILL'd mid-push (power loss), the cache entry
  #    is left at 0 bytes. Next build retrieves the 0-byte cache, ar packs
  #    it into the static lib, the SharedLibrary link fails with
  #    "undefined reference to ..." on whatever symbols that .o defined.
  #    Hit on tizi 2026-05-14: 0-byte swaglog.o in libcommon.a → libdbc.so
  #    link failed on cloudlog_e references from parser.cc.
  #
  # 3. Orphaned *.o.tmp / *.os.tmp staging files from interrupted
  #    CacheDir.push() writes. Always safe to remove — they're regenerated
  #    on the next build.
  # `! -path "$DIR/third_party/*"` is required: `third_party/**/*.so` and
  # `third_party/**/*.a` are Git LFS-tracked prebuilt binaries. If an LFS smudge
  # ever ends up at 0 bytes, the SCons rebuild can't regenerate them — we'd
  # break the build worse than we'd recover it. (`-prune` cannot be combined
  # with `-delete` because `-delete` forces depth-first traversal.)
  rm -f /data/scons_cache/*.lock 2>/dev/null
  find /data/scons_cache -type f -size 0 -delete 2>/dev/null
  find "$DIR" -type f ! -path "$DIR/third_party/*" \( -name '*.o' -o -name '*.os' -o -name '*.so' -o -name '*.a' \) -size 0 -delete 2>/dev/null
  find "$DIR" -type f ! -path "$DIR/third_party/*" \( -name '*.o.tmp' -o -name '*.os.tmp' \) -delete 2>/dev/null

  # Check to see if there's a valid overlay-based update available. Conditions
  # are as follows:
  #
  # 1. The DIR init file has to exist, with a newer modtime than anything in
  #    the DIR Git repo. This checks for local development work or the user
  #    switching branches/forks, which should not be overwritten.
  # 2. The FINALIZED consistent file has to exist, indicating there's an update
  #    that completed successfully and synced to disk.

  if [ -f "${DIR}/.overlay_init" ]; then
    find ${DIR}/.git -newer ${DIR}/.overlay_init | grep -q '.' 2> /dev/null
    if [ $? -eq 0 ]; then
      echo "${DIR} has been modified, skipping overlay update installation"
    else
      if [ -f "${STAGING_ROOT}/finalized/.overlay_consistent" ]; then
        if [ ! -d /data/safe_staging/old_openpilot ]; then
          echo "Valid overlay update found, installing"
          LAUNCHER_LOCATION="${BASH_SOURCE[0]}"

          mv $DIR /data/safe_staging/old_openpilot
          mv "${STAGING_ROOT}/finalized" $DIR
          cd $DIR

          echo "Restarting launch script ${LAUNCHER_LOCATION}"
          unset AGNOS_VERSION
          exec "${LAUNCHER_LOCATION}"
        else
          echo "openpilot backup found, not updating"
          # TODO: restore backup? This means the updater didn't start after swapping
        fi
      fi
    fi
  fi

  # handle pythonpath
  ln -sfn $(pwd) /data/pythonpath
  export PYTHONPATH="$PWD"

  # hardware specific init
  if [ -f /AGNOS ]; then
    agnos_init
  fi

  # write tmux scrollback to a file
  tmux capture-pane -pq -S-1000 > /tmp/launch_log

  # start manager
  cd system/manager
  if [ ! -f $DIR/prebuilt ]; then
    ./build.py
  fi
  ./manager.py

  # if broken, keep on screen error
  while true; do sleep 1; done
}

launch
