# Independent verification — the paramiko upgrade (demo runbook)

Goal: demonstrate **technical depth** — verify Devin's fix works by running it and
scrutinizing it yourself, and show you can **critique** the approach. Don't trust the
agent's "checks passed."

## The fix (PR #37) — what Devin actually did

Issue: `pyproject.toml` capped `paramiko<4.0` because **paramiko 4.0 removed `DSSKey`**,
which `sshtunnel` (Superset's SSH-tunnel dep) still references → `AttributeError` on any
tunnel. Devin:
- raised the cap to `<5.0`,
- added a **conditional compatibility shim** in `superset/extensions/ssh.py`: if paramiko
  lacks `DSSKey` (i.e. 4.0+), inject a `_RemovedDSSKey` stand-in that **raises
  `SSHException` on any DSA-key use** (it restores the *attribute* sshtunnel needs, but
  not DSA support — no security downgrade),
- added a unit test (`tests/unit_tests/extensions/ssh_test.py`),
- updated lockfiles + the pyproject comment.

The critical question: **is shimming a third-party's removed API acceptable, or a hack?**

## Independent verification (run it yourself)

Setup once (before recording), in the fork with paramiko 4:
```bash
cd ~/Projects/superset
source .venv/bin/activate        # your Superset dev env
pip install 'paramiko>=4,<5'     # the upgrade under test
```

1. **Confirm the break is real** (paramiko 4, no shim):
```bash
python -c "import paramiko; print('DSSKey present:', hasattr(paramiko,'DSSKey'))"   # False
python -c "from sshtunnel import SSHTunnelForwarder; SSHTunnelForwarder._get_transport"  # AttributeError path via DSSKey
```
2. **Confirm the shim fixes it** (checkout Devin's branch):
```bash
git checkout devin/1789996327-paramiko-4
python -c "import superset.extensions.ssh; import paramiko; print(paramiko.DSSKey)"  # _RemovedDSSKey
```
3. **Confirm NO security regression** — a DSA key must be *rejected*, not silently accepted:
```bash
python -c "import superset.extensions.ssh, paramiko; paramiko.DSSKey()"   # raises SSHException
```
4. **Run the tests you can run locally:**
```bash
pytest tests/unit_tests/extensions/ssh_test.py -q
```

## What to say — the critique (this is the depth)

- **"Devin shimmed a third-party's removed API — that's the thing I scrutinize hardest.
  So I checked whether a real fix exists."** `sshtunnel` latest is **0.4.0 (Jan 2021),
  unmaintained, no paramiko-4 release** — so the shim is the *only* path, not laziness.
  Good judgment.
- **"And it's a careful shim, not a hack."** It's conditional (only paramiko 4+), it
  **raises on DSA use** (doesn't fake insecure-key support), it's documented, and it ships
  a test. I verified all four.
- **Push back (show judgment):**
  - **Import-order risk:** the shim lives in `superset/extensions/ssh.py` — it only works
    if that module is imported *before* sshtunnel builds its key table. I'd verify it's
    loaded early in *every* entry point (web, celery, CLI), or move it to a guaranteed-early
    init, and add a test that imports sshtunnel cold.
  - **Behavior change:** DSA (`ssh-dss`) tunnels now fail with a clear error. That's fine
    (DSA is deprecated/insecure), but it belongs in the **release notes**.
  - **Tech-debt note:** the PR should flag that `sshtunnel` is abandoned and propose a
    plan (fork it, or replace with a maintained lib) so the shim isn't permanent.

## Honesty framing
- This is **real code validation** run locally — distinct from any **simulated
  `check_suite` event**, which only exercises the orchestration loop.
- Superset's fork CI needs maintainer approval, so the repo's CI isn't the proof here —
  **your local run is.** Keep PR #37 **open**; the human gate is the point.

---
### Bottom-rung example (apispec, PR #29) — shorter
Devin changed **no app source** — it unpinned apispec, regenerated `openapi.json`, and
updated a **test expectation** (apispec 6.10 now emits `additionalProperties`). Verify the
new expected value is genuine library output (run the test on 6.10 with the old vs new
assertion), not a value picked to go green. Good "did-the-agent-hack-the-test?" example;
paramiko is the meatier one.
