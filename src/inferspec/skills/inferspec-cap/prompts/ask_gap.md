You are asking the user ONE focused question about a `[GAP]` (or `[TBD]`)
marker in the cap's spec.

INPUT:
- `marker` — `{file, line, text, surrounding_requirement, surrounding_scenario}`
- `cap.external_context` — Jira/Confluence/URL content gathered earlier

ASK RULES (mandatory):

1. **Smallest possible question.** Don't say "Tell me about the rate limiter."
   Say "Is the rate limit 5 failures / 60 seconds (as inferred from
   `auth.py:9-15`) or different?"

2. **Offer candidate answers when possible.** Prefer multiple choice for
   binary or small-cardinality decisions:
   > "Unknown-user returns 401 same as wrong-password. Pick:
   > (a) intentional — anti-user-enumeration
   > (b) accidental — should be 404
   > (c) other — explain"

3. **Cite file:line for the source of the ambiguity.** Always.

4. **One question per iteration.** Don't ask compound questions like "Is the
   limit X AND should the counter reset on success?". Split.

5. **Re-state the marker text verbatim in a quote block** before asking — so
   the user knows exactly which marker is being addressed.

ACCEPT RESPONSES:

- A concrete answer → pass to `rewrite_requirement.md`.
- "TBD" / "I don't know" / "skip" → downgrade marker from `[GAP]` to `[TBD]`
  in-place; do not rewrite the Requirement; move to next marker.
- "stop" / "enough" / "done" → exit the loop with whatever's still unresolved.
- Anything else → ask for clarification once; if still ambiguous, treat as TBD.

OUTPUT for downstream rewrite step:
```json
{
  "marker_id": "...",
  "user_answer": "...",
  "decision": "answered" | "tbd" | "stop"
}
```
