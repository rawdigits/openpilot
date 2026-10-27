# Task: Rivian bridge poll thread inherits SCHED_FIFO on the openpilot control core

Repo: rawdigits/opendbc (GitHub fork). You are on branch `fix/bridge-poll-thread-scheduling`,
based on `fix/follow-distance-sync-indent` (commit ccfd6b02) — that is the exact commit that
`rawdigits/openpilot` branch `yeetfollow` pins as its `opendbc_repo` submodule. Base the PR on
`fix/follow-distance-sync-indent`, NOT master.

## Context: the real-world symptom

Ryan drives a Rivian R1S running openpilot (branch `yeetfollow`). He reports that after he made
the network connection between the comma 3 and the TCM (which hosts the `rivian-bridge` HTTP
API) faster, openpilot became noticeably MORE RESPONSIVE to the lead car — without changing any
control tuning, personality, or car settings. We want to explain that and fix the underlying
defect.

## The hypothesis to verify (do NOT assume it is correct — check it)

File: `opendbc/car/rivian/rivian_bridge.py`

`RivianBridge.__init__` spawns a `threading.Thread(target=self._poll_loop, daemon=True)`.
That constructor is reached from `CarState.__init__` in `opendbc/car/rivian/carstate.py`, which
is reached from `Car()` in openpilot `selfdrive/car/card.py`.

In openpilot `selfdrive/car/card.py`:

    def main():
      config_realtime_process(4, Priority.CTRL_HIGH)   # SCHED_FIFO 53, affinity core 4, gc.disable()
      car = Car()                                      # -> CarState.__init__ -> RivianBridge() spawns thread
      car.card_thread()

`config_realtime_process` in openpilot `common/realtime.py` calls `os.sched_setscheduler(0,
os.SCHED_FIFO, ...)` and `os.sched_setaffinity(0, [4])` on the MAIN thread, BEFORE `Car()` is
constructed. On Linux, pthread_create inherits scheduling policy, priority and CPU affinity
from the creating thread by default. So the claim is: our HTTP poll thread runs as SCHED_FIFO
priority 53 pinned to core 4 — the same core and same priority as the 100Hz `card` loop and as
`controlsd`, which also does `config_realtime_process(4, Priority.CTRL_HIGH)`.

Under SCHED_FIFO at equal priority there is no timeslicing: a runnable thread runs until it
blocks. The poll loop does `urllib.request.urlopen(...)`, then `json.loads(...)`, then a dict
swap under a lock, and on personality change a `Params.put_nonblocking`. Those hold the CPython
GIL. The proposed causal chain: slow TCM link means each poll spends much longer in the
urllib/socket path, so there are more wakeups and more GIL-holding on the RT core, so `card`
and `controlsd` pick up scheduling jitter, so longitudinal actuation lands late, so it feels
less responsive to the lead car. Speeding up the link reduces that contention, which matches
Ryan's observation with zero tuning changes.

Secondary suspicion: `Params::putNonBlocking` in openpilot `common/params.cc` (~line 221)
pushes to a queue and launches `std::async` — that worker thread would ALSO inherit FIFO 53 and
core 4, and it does a filesystem write. It is now guarded to fire only when the personality
value actually changes, but it still lands on the RT core.

## Step 1 — VERIFY before you fix

- Read openpilot `common/realtime.py` (`config_realtime_process`, `set_core_affinity`,
  `Ratekeeper`) and `selfdrive/car/card.py` to confirm the ordering, and confirm that the main
  loop is NOT artificially sleeping. It is driven by `drain_sock_raw(wait_for_one=True)` and
  only calls `rk.monitor_time()`, which measures rather than throttles — verify that.
- Clone openpilot read-only for reference:
  `git clone --depth 40 -b yeetfollow https://github.com/rawdigits/openpilot.git /tmp/op-ref`
- Confirm from pthread_attr_setinheritsched semantics that Python `threading.Thread` does NOT
  reset policy, priority or affinity (CPython does not pass a custom sched attr).
- Write your findings into the PR body. If the hypothesis turns out to be WRONG, say so plainly
  and do NOT fabricate a fix. Open the PR as a documented negative result, or report back via
  `openclaw-notify` instead of pushing a bogus change.

## Step 2 — the fix (MINIMAL and SAFE)

Inside `_poll_loop`, as the very first thing the thread does, drop itself off the realtime
scheduling class and off the isolated control cores. Sketch — adapt as you see fit, but keep it
defensive, this runs in a car:

    def _poll_loop(self):
        try:
            os.sched_setscheduler(0, os.SCHED_OTHER, os.sched_param(0))
        except Exception:
            pass
        try:
            # cores 4 and 5 are openpilot isolated RT cores (card/controlsd on 4,
            # radard/plannerd on 5). Keep this thread off them.
            allowed = set(range(os.cpu_count() or 1)) - {4, 5}
            if allowed:
                os.sched_setaffinity(0, allowed)
        except Exception:
            pass
        while True:
            ...

Requirements:

- MUST be wrapped so it can never raise and kill the poll thread. This is a car; a dead poll
  thread means a frozen set speed.
- MUST be a no-op / harmless on a dev PC where the process is not SCHED_FIFO. openpilot guards
  RT setup behind a `PC` check — mirror that tolerance.
- Do NOT change the poll rate, the 0.3s sleep, the warmup behaviour, the staleness semantics,
  or anything in `carstate.py`. Scope creep is not wanted.
- Add a comment explaining WHY (thread inherits FIFO and affinity from the card main thread),
  because this is exactly the kind of line someone deletes later as "unnecessary".

## Step 3 — note but do NOT fix a separate latent bug

`_poll_loop` swallows every exception with a bare `except: pass` and never clears `self.state`.
If the bridge becomes unreachable mid-drive, the last payload sticks around forever with
`stale: false` frozen in it, so openpilot keeps using a stale set speed instead of falling back.
The bridge server computes its own 5s staleness (rivian-tcm-bridge `main.go` ~line 386) but that
value can never reach us if the request itself fails. Mention this in the PR body as follow-up
work. Do NOT implement it here.

## Constraints

- Do NOT commit to `master`. Work only on `fix/bridge-poll-thread-scheduling`.
- This is safety-relevant vehicle code. Small diff, heavy comments, no refactors.
- No on-device testing is possible right now — the truck is being driven. Note in the PR that
  on-device verification is pending, and include the exact verification command:
  `ps -L -o tid,cls,rtprio,psr,pcpu,comm -p $(pgrep -f selfdrive.car.card)`
  Expected BEFORE fix: the extra poll thread shows `cls=FF rtprio=53 psr=4`.
  Expected AFTER fix: `cls=TS rtprio=0` and `psr` not in {4,5}.

## Step 4 — open the PR

GitHub repo `rawdigits/opendbc`. Base branch `fix/follow-distance-sync-indent`, head branch
`fix/bridge-poll-thread-scheduling`.

Auth: a GitHub token is already embedded in this box git config, so `git push` just works.
For the API call, pull the token out of git config rather than retyping it:

    GHT=$(git config --global --get-regexp "url.*github" | grep -oE "ghp_[A-Za-z0-9]+" | head -1)
    curl -sX POST -H "Authorization: token $GHT" https://api.github.com/repos/rawdigits/opendbc/pulls -d '...'

The `gh` CLI is also fine if present.

PR title: `fix(rivian): keep bridge poll thread off the SCHED_FIFO control core`

PR body must contain: the symptom Ryan reported, the verified mechanism, the diff rationale, the
on-device verification command with expected before/after, and the follow-up note from Step 3.

## When Done

Run: `openclaw-notify "rawdigits/opendbc — <PR url> — <one line: hypothesis confirmed or not>"`
