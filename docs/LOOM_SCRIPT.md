# Loom script — Devin Auto-Fix (target 5 min)

Audience: VP Eng + senior ICs, for the Cognition Deployed Engineer role. A
customer-facing technical demo. The **live run is the source of truth**.

> Holds MORE than 5 minutes. Lines are **[CORE]** (say on camera) or **[DEPTH]**
> (README / longer cut). Say every CORE line → ~5:00.
> **Signposting:** open with the whole-talk map, then a one-line mini-map at the
> start of each section ("In this section: X, Y, Z").

---

## Open: the ladder + the roadmap (0:00–0:20)

**[CORE]** Lead with the **ladder of confidence** (the strategy). Hold the funnel for
the architecture section.
```
        architectural redesigns        ← hard, low confidence (later rungs)
        multi-file features
        bug fixes
        UI tweaks
   ↑    dependency upgrades / lint      ← Devin starts here, high confidence
```
> "Engineering work is a ladder. Bottom rungs — lint, dependency upgrades — an agent
> can act on with high confidence. Top — hairy architecture. The play is to earn trust
> at the bottom and climb. Today: one of the highest-value bottom rungs."

**[CORE] Roadmap slide:** "In 5 minutes: the problem and its cost, the architecture,
a live fix, the engineering calls, how a leader measures it, and how we'd roll it out."

## Timeline

| # | Section | Time |
|---|---|---|
| 1 | Problem, cost & the metric | 0:20–1:00 |
| 2 | Architecture (before/after) | 1:00–1:45 |
| 3 | Live demo (centerpiece) | 1:45–3:30 |
| 4 | Engineering decisions | 3:30–4:05 |
| 5 | Results & why Devin | 4:05–4:40 |
| 6 | Rollout & the close | 4:40–5:00 |

---

## 1 · Problem, cost & the metric (0:20–1:00) — WHAT

Mini-map: *"the problem, what it costs in dollars and risk, and the one metric we track."*

**[CORE]** Stat graphic + a real Superset issues screenshot.
> "I ran a static analysis of Superset's open issues and PRs to find the highest-value,
> most-remediable work — dependency upgrades. 2,658 Dependabot PRs last year, ~17% need
> human code work: ~450 upgrades/year, **~1,350 developer-hours** in a dead lane."

**[CORE] Put it in dollars and risk:**
> "At a loaded ~$100–150/hr, that's **~$135k–200k a year** of senior-engineer time on
> one repo. And the hours aren't the only cost — an upgrade that sits blocked is an
> exposure window. In this repo a CRITICAL dependency CVE sat **634 days** before the
> fix landed. Dev-hours plus risk-exposure is the real bill."

**[DEPTH]** Optionally show one real breach headline to anchor "exposure = money." Use a
genuine article only — don't fabricate.

**[CORE] Name the metric:** *"The number I optimize is **MTTR — label to merged PR**.
Every design choice compresses it, and it's the KPI on the dashboard."*

## 2 · Architecture, before/after (1:00–1:45) — HOW

Mini-map: *"the flow, who owns what, and the trade-offs behind two or three decisions."*

**[CORE] Draw it as boxes — a before/after** (build this as a real diagram, colored):
- **Before (grey/slow):** Dependabot files a PR/alert → it breaks CI → a human
  investigates → fixes code → re-runs CI → reviews → merges. Long MTTR.
- **After (Devin, green/fast):** nightly detector flags the blocked upgrade → human
  labels → **Devin** fixes + iterates on CI → status streams to **Slack + GitHub** →
  human reviews & merges. Color the boxes Devin/automation now owns to show **where the
  MTTR gets compressed.**
- Boxes to include: detector, issue, Devin session, **CI + bounded repair**, review,
  **Slack/GitHub events**, merge.

Here's the workflow that diagram animates (the funnel):
```
DETECT (nightly) → APPROVE (human labels) → FIX (Devin) → CHECK → MERGE (human)
```
> "Devin is the coding worker. My service is orchestration and it never auto-merges."

**[DEPTH] Trade-offs (pick 1–2 on camera):** Postgres event/job store now vs
Kafka/Kinesis at scale; a custom API handler over Devin's native integration for
control, metrics, concurrency and audit/governance; two flows on purpose (labeled
issues + `check_suite` failures); observability pluggable — Superset here, OTel→Grafana
elsewhere.

## 3 · Live demo (1:45–3:30) — the centerpiece

Mini-map: *"trigger it, watch Devin work, see it report and self-heal CI, read the diff."*

Tabs ready. **Issue #31 (apispec)** — auto-filed by the detector.
1. **[CORE] Trigger.** Show auto-created issues #30–33. Label **#31 `devin-fix`** — the
   human approval gate on an automatically-filed issue.
2. **[CORE] Report where they work.** Slack thread filling live (webhook) + mirror
   GitHub comments; on-call tagged when ready.
3. **[CORE] Devin working.** Session reading code, running the failing test, fixing it.
4. **[CORE] CI feedback loop.** *"If checks fail, the failure feeds back to the same
   session for a bounded repair — Devin fixes its own CI; past the threshold it
   escalates to a human."* (Built: `handle_ci_failure`.)
5. **[CORE] The PR + the metric hook.** Open the **diff** (apispec unpinned, test
   fixed). Note *"every transition also writes to the metrics store — which is what the
   leadership dashboard reads, coming up."*

**[CORE] Choreography/honesty:** runs take minutes — if #31 is still going, *"here's a
completed run"* → **PR #29**. **Verification:** *"CI is simulated locally for the demo
(Superset fork CI needs maintainer approval), disclaimed in every PR comment. Checks =
evidence, a human merges."*

## 4 · Engineering decisions (3:30–4:05) — HOW

Mini-map: *"the calls that make this deployable, not a one-off."* Say 2, each with its
snippet on screen (keep the snippet to ~5 lines — enough to read, not scroll).

**Pluggable triggers/ + reporters/** — the whole webhook surface is one adapter; a new
source or output is one file.
```python
# triggers/github.py
async def route(event_type, event_data, background_tasks):
    if event_type == "issues":         await handle_issue_event(...)
    elif event_type == "check_suite":  await handle_check_suite_event(...)
    elif event_type == "pull_request": await handle_pull_request_event(...)
# Linear/Sentry = a sibling triggers/<source>.py; reporters/ is symmetric.
```
**[DEPTH]** Direction: route by trigger to different models/workers (don't burn a top
model on a lint bug); a strategy pattern in `route()` → per-type Devin config.

**Completion ≠ success — never auto-merge** (the removable human gate):
```python
# CI success -> checks_passed, NOT merged. A human merges.
job.state = "checks_passed"
# GitHub comment: "checks passed — ready for human review (not auto-merged)"
```
Plus the self-healing CI loop:
```python
# check_suite failure -> one bounded repair, then escalate to on-call
await devin_client.send_message(job.devin_session_id, failing_check_details)
job.attempts += 1
if job.attempts >= 1: job.state = "checks_failed"   # pings the human
```

**Idempotency** (a re-delivered webhook won't spawn a second session):
```python
existing = session.execute(
    select(Job).where(Job.issue_number == issue["number"])).scalar_one_or_none()
if existing: return
```
**[DEPTH] Cost guard + concurrency** — the customer's bill is real money:
```python
def _daily_spend_exceeded(session):
    spent = session.execute(select(func.coalesce(func.sum(Job.cost), 0.0))
              .where(Job.created_at >= day_start)).scalar()
    return spent >= settings.DAILY_COST_CAP     # checked before each new session
```

## 5 · Results & why Devin (4:05–4:40) — WHY

Mini-map: *"how a leader measures it, and why an autonomous agent — not a script."*

**[CORE] Dashboard** (auto-refresh; the live #31 bumps a tile): *"Verified outcomes, not
AI activity. Baseline is representative history; the tile that moved is real. MTTR is
the headline."*

**[CORE] Why Devin — as a matrix:**

| | Deterministic bot | Cursor / Claude Code / Codex | **Devin** |
|---|---|---|---|
| Bumps a version, opens PR | ✅ | ✅ | ✅ |
| Fixes code when the upgrade breaks | ❌ | ~ (human-driven) | ✅ autonomous |
| Iterates on failing CI | ❌ | ❌ | ✅ bounded loop |
| Validates own work (tests, screenshots) | ❌ | partial | ✅ |
| Runs unattended, reports in Slack/GitHub | ❌ | ❌ | ✅ |
| Managed infra / session API | — | varies | ✅ |

> "You could stitch your own software factory from those agents. Devin closes the loop
> *as an engineer* — investigate, adapt, iterate, validate, on your team's turf."

## 6 · Rollout & the close (4:40–5:00) — WHEN

Mini-map: *"a black-and-white 2-week POC with a purchase signal."*

**[CORE] Make it a bet with a number, not a vibe:**
> "Concrete offer: a **2-week POC** on one of your repos, the dependency dead-lane.
> We agree the success bar *now*, black and white:
> **≥70% of eligible blocked upgrades produce a validated PR with zero human code
> edits, MTTR from label→merge under 4 hours, and ≥40 engineer-hours reclaimed** in the
> window. Hit the bar → we expand to more repos and climb the ladder, and that's your
> purchase signal. Miss it → you've spent two weeks and one repo to find out."

Then: a named **decision date** (end of the two weeks), a **weekly check-in**, and I
(deployed engineer) **embed** to wire triggers, tune prompts, and hit the bar with them.

Close: *"Today it's a working fix loop in Superset. The engagement is a measured bet:
clear the dead lane on one repo in two weeks, then climb the ladder — one verified rung
at a time."*

---

## Assets to prepare (visuals matter here)
- [ ] Ladder graphic (open) · roadmap slide
- [ ] Stat graphic with the **$135k–200k + 634-day exposure** numbers
- [ ] **Before/after architecture diagram** (colored boxes showing MTTR compression)
- [ ] **Why-Devin matrix** as a clean slide
- [ ] Rollout slide with the POC success bar + decision date
- [ ] Tabs: issues #30–33 · Devin session · PR #29 (backup) · dashboard (auto-refresh) · Slack thread

## Honesty guardrails
- Dependency **auto-fix**, not active-CVE remediation. The 634-day figure is a real
  measured exposure from this repo — use it as risk context, not a claim you patch CVEs.
- CI validation is **simulated locally**, disclaimed in every PR comment.
- Dashboard baseline is **representative demo data**; the live run is real.
- Model-tiering + strategy pattern are **design directions** — say "would," not "does."
- Only claim native-Devin-integration if it's actually in the submitted repo.
