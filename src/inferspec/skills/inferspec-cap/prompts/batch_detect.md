You are deciding whether several `[GAP]` markers can be resolved by ONE user
answer ("batch resolve").

INPUT:
- `markers` — list of unresolved markers in the current cap's spec

JUDGEMENT RULES:

1. **Group only by SEMANTIC THEME, not by location.** Two markers in the same
   file aren't necessarily a batch; two markers asking about "auth" across
   different Requirements MAY be.

2. **Conservative bias.** When in doubt, do NOT batch. The cost of a wrongly
   bundled batch (user answers once, wrong scope of changes) is higher than
   the cost of asking a few extra questions.

3. **Minimum group size: 2.** Don't propose a "batch" of one marker.

4. **Maximum group size: 5.** Above 5, the user is overwhelmed; split.

5. **Each candidate group must pass this test**: "If the user answered the
   single question that captures this group's theme, would all members of the
   group be resolved by the same rewrite logic?" If the answer is anything
   other than a clear yes — don't batch.

OUTPUT: zero or more candidate groups, each:
```json
{
  "theme": "auth requirement on order endpoints",
  "markers": ["marker_id_1", "marker_id_3", "marker_id_5"],
  "proposed_question": "Are /orders endpoints meant to require auth? (y/n)"
}
```

The orchestrator presents each group to the user as a single prompt:

> "I see 3 markers all about whether /orders requires auth (in
>  user-auth/spec.md:67, order-management/spec.md:14, order-management/spec.md:78).
>  Answer once for all three? (y/n)"

If user says yes → answer-once flow.
If user says no → fall back to per-marker iteration.
