# Edit-learner eval (8 synthetic pairs, 5 planted habits, 2 distractors)

| Version | Rules | Planted habits found | False rules | Notes |
|---|---|---|---|---|
| v0 | 12 | 5/5 | 1 (turned a `[CHECK]` fill-in into a "rule") | 5 rules rest on one pair; one rule bundled two habits |
| v1 | 4 | 4/5 (contractions folded into "direct phrasing") | 0 | Two habits merged into one rule; scopes broadened to global |

Distractors: the date correction (e06) never reaches the model (edit ratio 0.045, under the 0.05 cutoff in code). The `[CHECK]` fill-in (e05) was learned by v0 and ignored by v1.

**Decision:** ship v1. A wrong Style Guide rule changes every future draft, so precision matters more than recall here; a missed habit will come back with more evidence. Code-side activation (2+ sightings) is a second filter.

**Next (v2):** tell the model to merge only rules that say the same thing, not related habits, and re-check recall on contractions.
