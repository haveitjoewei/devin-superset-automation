# Evidence behind the numbers

Every figure in the pitch is either **measured** (with the exact query) or **assumed**
(labeled as such). Capacity reclaimed is *engineer-hours*, not cash saved.

| Figure | Value | Source | Kind |
|---|---|---|---|
| Dependabot PRs / 12mo | 2,658 | GraphQL search | measured |
| Human-code-work rate | ~17% | 100-PR sample | measured |
| Eligible upgrades / yr | ~450 | 2,658 × 17% | derived |
| Effort per fix | 3 h | — | **assumption** |
| Engineer-hours / yr | ~1,350 | 450 × 3 | derived |
| Loaded rate | $90–150/h | industry | **assumption** |
| Annual capacity cost | ~$135–200k | hours × rate | derived (capacity, not cash) |
| Clean-bump merge latency | median 6.4 h | 200 PRs | measured |
| CVE exposure (advisory→fix) | median 34 d, max 634 d | NVD + git blame | measured |

## How each was measured

**2,658 Dependabot PRs / 12 months.**
```
gh api graphql -f query='{ search(query:"repo:apache/superset author:app/dependabot is:pr created:>=<one-year-ago>", type:ISSUE, first:1){ issueCount } }'
```

**~17% need human code work.** Sampled the 100 most recent Dependabot PRs; counted those
with commits by a non-Dependabot author (a human had to intervene) or closed unmerged
(the bot couldn't produce a compatible update). 17/100. *Caveat:* "non-bot commit"
slightly over-counts (maintainer rebases), so the genuine code-fix rate is ~10–17% — I
quote the band, not a false-precise point.

**Clean-bump merge latency — median 6.4 h** across 200 merged Dependabot PRs
(`createdAt`→`mergedAt`), 92.5% under 24 h. This is the contrast: clean bumps fly; the
ones needing code are what stall — so the exposure below is a code-work problem, not a
review-speed problem.

**CVE exposure — median 34 days, max 634 days.** For the seven CVEs referenced in
`requirements/base.in`, the exposure window = NVD `published` date → the date the fix
landed (git blame on the pin line). Median 34 d; the max is a CRITICAL pyarrow
deserialization CVE (CVE-2024-52338) at 634 days. *Caveat:* the fix date is a git-blame
proxy (a moved line could overstate it); the magnitudes are far too large to be noise.

## Honesty notes
- **Effort/fix (3 h) and the loaded rate are assumptions**, not measured — the softest
  inputs. In a real engagement they'd be calibrated from the customer's own history.
- **"$135–200k" is reclaimed capacity**, not cash that appears in a budget.
- The dashboard's live numbers replace the *effort* estimate with measured Devin
  throughput as real jobs accrue.
