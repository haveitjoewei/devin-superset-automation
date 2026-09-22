# Evidence and estimates

These figures describe the project's Superset analysis. They estimate the opportunity for automation, not savings already achieved. The raw sample and exact analysis dates are not stored here, so the reported counts cannot be fully reproduced from this repo alone.

| Figure | Value | Basis |
|---|---|---|
| Dependabot PRs in a 12-month period | 2,658 | Reported GitHub search count |
| PRs that may need manual work | 17 of 100 | Recent PR sample; see limits below |
| Upgrades that could need help per year | About 450 | 2,658 × 17%, rounded |
| Manual effort per fix | 3 hours | Assumption |
| Potential annual work | About 1,350 hours | 450 × 3 hours |
| Engineering cost per hour | $90–150 | Assumption; currency not specified in the analysis |
| Value of that time | About $122,000–203,000 | 1,350 × hourly cost; not cash savings |
| Time to merge an update | Median 6.4 hours | Reported sample of 200 merged Dependabot PRs |
| Advisory publication to fix | Median 34 days; maximum 634 | Reported sample of seven vulnerabilities |

## How the analysis was done

**PR volume.** This query counts Dependabot PRs after a chosen date. Replace `<one-year-ago>` with the start date of the period being measured:

```bash
gh api graphql -f query='{ search(query:"repo:apache/superset author:app/dependabot is:pr created:>=<one-year-ago>", type:ISSUE, first:1){ issueCount } }'
```

**Manual work.** The analysis counted PRs with a non-bot commit or that closed without merging. That is only a rough indicator: a maintainer rebase is not necessarily a code fix, and an unmerged PR may have been replaced. The original estimate was 10–17%; the annual calculation uses the upper end.

**Merge time.** The analysis compared creation and merge times for 200 merged PRs; 92.5% merged within 24 hours. This excludes unmerged PRs and does not establish why other upgrades stalled.

**Vulnerability timing.** The analysis compared NVD advisory dates with the last change to the relevant dependency line in `requirements/base.in`. For seven vulnerabilities, it reported a median of 34 days and a maximum of 634 days for CVE-2024-52338. A line's last-change date may differ from the actual fix date. This is an estimate of delay, not proof the application was exploitable throughout that period.

## Dashboard figures

Job counts and timestamps come from the app. Seeded demo jobs and simulated events can also appear in that data.

- The app assigns **two estimated hours saved** when a job's checks pass. It does not measure avoided developer work. This differs from the three-hour business-case assumption above.
- `mttr_hours` measures time from labeling to reported check success, not time to merge.
- The success rate counts passed or merged jobs against passed, merged, and failed jobs. It excludes `needs_human` jobs.
- `net_saved` values time at $90/hour and subtracts recorded Devin usage. That usage may be in ACUs rather than dollars, so this is not a reliable dollar-saving figure without conversion.

Use actual manual effort, billing rates, and verified outcomes before making a financial claim.
