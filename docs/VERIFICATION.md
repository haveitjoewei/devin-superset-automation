# How the example fixes were checked

These notes record local checks performed for the demo. They are not new test results from this documentation update. Superset's fork checks require maintainer approval, and simulated check events are not test evidence. A person still needs to review each fix before merging.

## paramiko 4.x — [PR #37](https://github.com/haveitjoewei/superset/pull/37)

**Problem:** paramiko 4 removed `DSSKey`, but Superset's SSH-tunnel library still expects it. Creating a tunnel could raise `AttributeError`.

**Fix:** Devin allowed paramiko versions below 5 and added a compatibility workaround in `superset/extensions/ssh.py`. The replacement `DSSKey` lets the older library load but raises `SSHException` if a DSA key is used. It does not restore DSA support.

The recorded local checks found:

- Without the workaround, paramiko 4 has no `DSSKey` and the tunnel library fails.
- With it, the tunnel code imports.
- Trying to use the replacement key raises `SSHException`.

Test command, run in the Superset checkout on the fix branch:

```bash
pytest tests/unit_tests/extensions/ssh_test.py
```

**Still needs review:** check import order in the web app, background workers, and command-line tools. Document that DSA keys are rejected, and consider replacing or updating the older tunnel library rather than keeping the workaround indefinitely.

## apispec 6.10 — [PR #29](https://github.com/haveitjoewei/superset/pull/29)

**Problem:** the newer apispec version adds `additionalProperties` to generated API schemas, so an existing test expected the wrong output.

**Fix:** Devin removed the version restriction, regenerated `docs/static/resources/openapi.json`, and added `"additionalProperties": False` to the expected test result. Application source code did not change.

The recorded local checks confirmed that the old assertion failed on the new output and the updated assertion passed. The generated API file changed along with the library version.

Test command, run in the Superset checkout on the fix branch:

```bash
pytest tests/unit_tests/databases/api_test.py
```

**Still needs review:** explain the generated API-file changes in the PR and confirm that the new schema matches the intended API behavior.
