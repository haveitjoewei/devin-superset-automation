# How the example fixes were checked

Public evidence checked on 23 September 2026. The local checks below are historical demo notes; they were not rerun against Superset during this maintenance update. Simulated events are not test evidence.

| Fix | Public outcome at inspection |
|---|---|
| Paramiko #37 | Merged; 54 successful checks and 11 skipped on `31c3136c788b27b2d79babbad6178a692ac3f8b2` |
| Apispec #29 | Open; 53 successful checks, 11 skipped, one failed docs build on `99546583c23a9013004deaa3c74abd0d30d09e00` |

The [apispec docs failure](https://github.com/haveitjoewei/superset/actions/runs/35539813116/job/106155326942) reports broken internal links in files outside that PR’s diff. It appears unrelated to the upgrade, but a base-branch comparison is needed to establish that.

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

**Still needs review:** check import order in the web app, background workers, and command-line tools. The PR includes a release note about DSA rejection. Consider replacing or updating the older tunnel library rather than keeping the workaround indefinitely.

## apispec 6.10 — [PR #29](https://github.com/haveitjoewei/superset/pull/29)

**Problem:** the newer apispec version adds `additionalProperties` to generated API schemas, so an existing test expected the wrong output.

**Fix:** Devin raised the upper version bound from `<6.7` to `<7`, regenerated `docs/static/resources/openapi.json`, and added `"additionalProperties": False` to the expected test result. Application source code did not change.

The recorded local checks confirmed that the old assertion failed on the new output and the updated assertion passed. The generated API file changed along with the library version.

Test command, run in the Superset checkout on the fix branch:

```bash
pytest tests/unit_tests/databases/api_test.py
```

**Still needs review:** explain the generated API-file changes in the PR and confirm that the new schema matches the intended API behavior.
