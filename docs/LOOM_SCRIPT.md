# Loom script — Devin Auto-Fix (target 5 min)

Audience: VP Eng + senior ICs, Cognition Deployed Engineer role. One continuous
investigation of a concrete customer problem. **The live run is the proof** —
spend the time there, cut presentation overhead.

> **[CORE]** = say on camera. **[DEPTH]** = README / longer cut. Say the CORE lines
> and you land ~5:00. No roadmap slide, no per-section mini-maps — keep it flowing.

---

## The 5-minute spine (trimmed running order)

Every beat below hits one hiring signal; cut anything not here. Detail follows.

| Time | Beat | On screen | Signal it proves |
|---|---|---|---|
| 0:00–0:30 | Problem + what I built + what I'll show | Slide 1 | customer judgment |
| 0:30–1:00 | Cost (evidence-captioned) + capacity≠cash + the 3 metrics | Slide 1 | economic framing, honesty |
| 1:00–1:35 | Before/after architecture; "never auto-merges"; one trade-off | Slide 2 | engineering ownership |
| 1:35–3:25 | **LIVE:** label #31 → Slack/GitHub live → **real failing test → Devin diff → test passing** → simulated `check_suite` drives bounded repair → PR (backup PR #29) | live screen | *the system works* |
| 3:25–3:55 | One decision that withstands scrutiny: two-strike CI repair + never-auto-merge | live code | senior-IC credibility |
| 3:55–4:30 | Dashboard (3 metrics, live tile moves) + why-Devin responsibility line | dashboard + Slide 3 | measures value, product judgment |
| 4:30–5:00 | Ladder + baseline→run POC, thresholds agreed up front | Slide 5 | drives adoption |

Half the time is the live demo. If you overrun, cut the architecture trade-off and
the second engineering decision first — never cut the real failing→passing test.

---

## Open (0:00–0:30)

**[CORE]** Straight in — no metaphor yet.
> "Apache Superset had 2,600+ Dependabot PRs in the period I analyzed. Dependency
> updates are easy to find, but when they break code or tests, someone still has to
> investigate and fix them. I built an event-driven system that turns those blocked
> upgrades into review-ready PRs using Devin — it detects eligible work, lets an
> engineer approve it, and manages the fix through to validation. I'll show you a real
> fix, how it handles failure, and how we'd evaluate it in a customer deployment."

## 1 · The problem & its cost (0:30–1:05) — WHAT

**[CORE]** Stat graphic + a real Superset issues screenshot. **Label every number with
its evidence** (a small caption per figure — this is what makes it defensible):

| Number | Evidence to show |
|---|---|
| 2,600+ Dependabot PRs | exact `gh` query + date range + repo |
| ~17% need code work | how you classified (non-bot commits / abandoned) + sample size |
| ~3 h/fix | **assumption**, labeled as such |
| ~$135k–200k/yr | engineering **capacity** cost — not cash saved |
| 634-day exposure | the exact CVE + dependency + the two dated events |

> "That's ~450 upgrades a year and ~1,350 engineer-hours of *capacity* on one repo —
> not a cash refund, but time you'd redeploy. And a blocked upgrade is an exposure
> window: one CRITICAL dependency CVE here went 634 days between advisory and fix."

**[CORE] The metric — stated as three, because merge isn't ours:**
- **Primary (what the system controls):** time to a **validated, review-ready PR**.
- **Business:** time to **merged** (includes human review).
- **Reliability:** **validated-PR yield** — % of eligible issues that reach a PR meeting
  the criteria with **zero human code edits**.

## 2 · Architecture (1:05–1:45) — HOW

**[CORE]** Show a **before/after** diagram (colored boxes → where MTTR compresses):
- Before: Dependabot PR → breaks CI → human investigates → fixes → re-runs CI → reviews
  → merges.
- After: detector flags → human labels → **Devin fixes + iterates on CI** → status to
  **Slack + GitHub** → human reviews & merges. The funnel:
  `DETECT → APPROVE → FIX → CHECK → MERGE`.
> "Devin is the coding worker; my service is orchestration and it never auto-merges."

**[DEPTH] One or two trade-offs (why simple on purpose):** Postgres job/event store now
(swap Kafka/Kinesis at scale); a custom API handler over Devin's native integration for
control, metrics, concurrency and audit/governance; observability pluggable (Superset
here, OTel→Grafana elsewhere). *"I deliberately didn't build Kafka or a multi-agent
framework — the value is the loop, not the infrastructure."*

## 3 · Live demo — the proof (1:45–3:30)

**[CORE]** This is the centerpiece. Make the evidence explicit — these are *different
claims*, don't blur them:

| What you show | What it proves |
|---|---|
| Signed webhook accepted → Devin session created | orchestration handles the event |
| **Real failing test → Devin's change → same test passing** | Devin produced a working fix |
| (Simulated `check_suite` event) | the CI-failure branch of your loop runs |

Sequence:
1. **[CORE] Trigger.** Auto-filed issues #30–33; label **#31 `devin-fix`** — the human
   approval gate on an automatically-detected issue.
2. **[CORE] Report where they work.** Slack thread filling live via webhook + mirror
   GitHub comments; on-call tagged when ready.
3. **[CORE] The real fix (lead with this).** Show the failing apispec test *before*,
   Devin's diff (unpin + code change), and the **same test passing after**. *"This is
   the actual validation — a real test that failed, now passes."*
4. **[CORE] Orchestration under failure.** Show the simulated `check_suite` failure
   driving the **bounded repair** — Devin gets the failure, fixes, and only a *second*
   failure escalates to a human. *"The GitHub CI event here is simulated — Superset's
   fork CI needs maintainer approval — so I'm proving the loop, not the repo's CI."*
5. **[CORE] The PR + metric hook.** Open the diff and note every transition writes the
   metrics store the dashboard reads.

**[CORE] Backup:** if #31 is still running, switch to the completed **PR #29**. Never
fake instant.

## 4 · Engineering decisions (3:30–4:05) — HOW

**[CORE]** Two, each with a ~5-line snippet on screen.

**Pluggable triggers/ + reporters/** — the webhook surface is one adapter:
```python
async def route(event_type, event_data, background_tasks):   # triggers/github.py
    if event_type == "issues":         await handle_issue_event(...)
    elif event_type == "check_suite":  await handle_check_suite_event(...)
    elif event_type == "pull_request": await handle_pull_request_event(...)
# a new source (Linear/Sentry) is a sibling file; reporters/ is symmetric.
```

**Bounded CI repair — two strikes, then a human** (corrected logic):
```python
if job.attempts < 1:                      # first CI failure: ask Devin, stay & wait
    await devin_client.send_message(job.devin_session_id, failing_details)
    job.attempts += 1
else:                                      # still failing after repair -> escalate
    job.state = "checks_failed"           # pings on-call; never auto-merges
```

**[DEPTH]** Idempotency is a `unique(issue_number)` constraint + caught `IntegrityError`
(atomic, not check-then-insert); a daily `DAILY_COST_CAP` + concurrency cap.

## 5 · Results & why Devin (4:05–4:35) — WHY

**[CORE] Dashboard** (auto-refresh; live #31 moves a tile): *"Verified outcomes, not AI
activity. Baseline is representative history for shape; the tile that moved is real.
The three metrics — review-ready time, yield, and merged time — separate what we
control from the org's review bottleneck."*

**[CORE] Why Devin — responsibility, not a feature checklist:**

| Approach | Who owns the engineering |
|---|---|
| Deterministic automation | known transforms + predefined recovery only |
| Roll your own agent runtime | you build/operate the runtime, exec env, session lifecycle, integrations |
| **This Devin integration** | Devin does autonomous coding; my service owns events, policy, reporting, state |

> "I lean on Devin's session API — create, poll status, send follow-up messages, read
> PR metadata — and keep the customer-specific orchestration mine. That's the split
> that makes it deployable."

## 6 · Rollout & the ladder (4:35–5:00) — WHEN

**[CORE]** Now the **ladder of confidence** (earned here, so it lands):
> "Engineering work is a ladder — dependency upgrades and lint at the bottom, high
> confidence; architecture at the top. We start at the bottom, prove it, and climb —
> removing the human gate a rung at a time as trust builds."

**[CORE] The POC as a measured partnership, not a guarantee:**
> "Two weeks, one repo. **Week 1 we establish the baseline** on a representative set of
> blocked upgrades. **Week 2 we run the automation** on the same class of work and
> measure: validated-PR yield, time to review-ready PR, human intervention, and cost
> per successful fix. **We agree the decision thresholds before we start.** If my
> Superset results hold, ~70% yield is a fair opening target — but we set it against
> *your* baseline, not a promise. Hitting it is the signal to expand and climb."

Close: *"Today it's a working fix loop in Superset. The engagement is a measured bet:
clear one rung on one repo in two weeks, with the evidence to decide the next."*

---

## Assets to prepare
- [ ] Stat graphic with **evidence captions** per number
- [ ] Before/after architecture diagram (colored, MTTR compression)
- [ ] The **real failing→passing apispec test** captured (before/after) — the proof
- [ ] Devin responsibility table + the API calls you use
- [ ] Rollout slide: baseline→run, the four measures, "thresholds agreed up front"
- [ ] Tabs: issues #30–33 · Devin session · PR #29 (backup) · dashboard (auto-refresh) · Slack

## Honesty guardrails
- Numbers carry evidence captions; **capacity reclaimed ≠ cash saved**; 634 days is a
  measured exposure, not a claim you patch CVEs.
- Distinguish the **simulated GitHub CI event** (orchestration) from the **real
  failing→passing test** (validation). Lead with the real test.
- Dashboard baseline is **representative demo data**; the live run is real.
- Model-tiering / strategy-pattern are **design directions** — say "would," not "does."
- Claim native-Devin-integration only if it's actually in the submitted repo.
