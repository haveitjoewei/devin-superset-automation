# Verifying the fixes

The point of this system is *verified* remediation — a green check from Devin is not a
merge signal. Below is how each remediated PR was independently verified (the failure
reproduced, the fix run, the result scrutinised), and what I'd still push back on.
All verification is **local**: Apache Superset's fork CI needs maintainer approval, so
the repository's CI is not the proof here — a local run is. PRs stay open until a human
reviews and merges.

## paramiko 4.x — PR #37 (`superset/extensions/ssh.py`)

**What Devin changed.** paramiko 4.0 removed `DSSKey`, which `sshtunnel` (Superset's
SSH-tunnel dependency) still references, so every tunnel raised `AttributeError`. Devin
raised the cap to `<5.0` and added a **conditional compatibility shim**: if paramiko
lacks `DSSKey`, inject a `_RemovedDSSKey` stand-in that **raises `SSHException` on any
DSA-key use** — it restores the attribute `sshtunnel` needs without restoring DSA
support. No application logic changed; it added a unit test.

**Is shimming a third-party's removed API acceptable, or a hack?** That's the question a
reviewer should ask, so I checked:

- **Is a real fix available?** `sshtunnel`'s latest is **0.4.0, from January 2021** —
  unmaintained, no upper paramiko bound, no paramiko-4 release. The shim is the only
  path, not laziness.
- **Reproduce the failure** (paramiko 4, no shim): `hasattr(paramiko, "DSSKey")` is
  `False`; `sshtunnel` then raises `AttributeError`.
- **Confirm the fix**: on the branch, `paramiko.DSSKey` resolves to `_RemovedDSSKey` and
  the tunnel machinery imports.
- **No security regression**: `paramiko.DSSKey()` **raises `SSHException`** — DSA keys
  are rejected, not silently accepted.
- **Tests**: `pytest tests/unit_tests/extensions/ssh_test.py`.

**What I'd still push back on:** verify the shim module is imported *before* `sshtunnel`
builds its key table in every entry point (web, celery, CLI); note the DSA-rejection as
a behavior change in the release notes; and flag in the PR that `sshtunnel` is abandoned,
with a plan to fork or replace it so the shim isn't permanent.

## apispec 6.10 — PR #29 (`tests/unit_tests/databases/api_test.py`)

**What Devin changed.** No application source — it unpinned apispec, regenerated
`docs/static/resources/openapi.json`, and updated a **test expectation**: apispec 6.10
now emits `additionalProperties` in the serialized JSON schema, so the expected dict
gained `"additionalProperties": False`.

**The question: did Devin just change the test to make it green?** Verified it didn't:

- On apispec 6.10 with the **old** assertion the test fails (actual output now includes
  `additionalProperties`); with Devin's updated assertion it passes.
- The new expected value is **genuine apispec-6.10 output** (the app generates it; the
  test tracks it) — not a value picked to go green. The 498-line `openapi.json` diff is
  the mechanical consequence of the bump, confirmed, not unrelated churn.
- `pytest tests/unit_tests/databases/api_test.py`.

**What I'd push back on:** the PR should call out the `openapi.json` regeneration
explicitly, and add a one-line comment on *why* the expected schema changed so the next
reviewer doesn't re-litigate it.
