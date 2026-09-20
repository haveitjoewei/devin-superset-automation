# Loom script — Devin Auto-Fix (≤5 min)

Audience: VP Eng + senior ICs evaluating Devin. Goal: problem → live demo →
why Devin → next steps. Keep it tight; let the demo carry it.

Setup before recording: services up (`docker compose up` or the local run),
Superset dashboard open, Slack channel visible, a seeded issue ready. Have the
[apache/superset](https://github.com/apache/superset) `requirements/base.in`
pinned-deps open in a tab.

---

## 0:00–0:45 — What: the problem (with real numbers)

> "Scanners find vulnerable dependencies and Dependabot proposes upgrades — but
> both stop when the upgrade *breaks the build*. Someone still has to fix the code
> and tests. I measured this on Apache Superset: 2,658 Dependabot PRs last year,
> about 17% needed human code work — roughly 450 upgrades a year, ~1,350 developer
> hours, that fall out of the fast lane. A CRITICAL CVE sat unpatched 634 days."

Show `requirements/base.in` — the pinned deps with "breaks a test, needs
attention" comments. "This is the dead lane. That's what I'm automating."

## 0:45–2:45 — How: the demo (the core)

1. **Trigger.** Label a GitHub issue `devin-remediate` (or run
   `scripts/simulate_issue.py <n>`). "An event starts it — no human in the loop."
2. **Devin working.** Open the Devin session: it's reading the code, running the
   failing test, fixing it. "This is the engineering the bot can't do."
3. **Output.** Show the PR Devin opened, and the **Slack thread** updating in real
   time (fixing → PR opened → checks running), ending in an **on-call @mention**.
4. **Dashboard.** Switch to Superset: success rate, dev-hours saved, MTTR, tasks by
   state. "This is how a leader knows it's working — and every number here started
   as an estimate in my ROI model; now it's measured live."

Architecture aside (15 sec, show the code tree): "One engine, pluggable trigger
adapters — `triggers/github.py` today; Linear or a scanner is one more adapter.
The Devin logic is shared." Mention the human-merge boundary: "It never
auto-merges — checks passing is evidence, not proof; a person merges."

## 2:45–3:45 — Why Devin uniquely

> "A script can bump a version. It can't read the codebase, figure out what the new
> version broke, fix it, and iterate until tests pass — in parallel, across every
> upgrade the scanner produces. That's the difference between a bot and an agent.
> The value scales with sessions, not headcount, and it clears work that otherwise
> never gets done."

## 3:45–4:45 — When: next steps in a real engagement

- Wire the real triggers (Dependabot failing PRs, a CVE scanner, Linear tickets).
- Turn the estimated inputs into the customer's own measured baseline.
- Hand off the production items their team owns (auth, idempotency, retries, secrets).
- Expand from dependencies to the other dead-lane streams (flaky tests, triaged bugs).

> "Same engine, more triggers. That's the deployment path."

## Honesty notes (say these — they build trust)
- The CI-success step in the demo is simulated locally (disclaimed in every PR
  comment) because Superset's fork-PR CI needs maintainer approval. Production uses
  the real `check_suite` webhook.
- "Checks passed" ≠ "verified correct." Merges stay human-gated.
