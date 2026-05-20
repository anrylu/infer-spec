You are rewriting ONE Requirement block in `openspec/specs/<cap>/spec.md`
based on the user's answer to a `[GAP]` question.

INPUT:
- `requirement_block` — the existing `### Requirement: ...` block, verbatim
- `marker` — the `[GAP]` text being resolved
- `user_answer` — the answer text from the user
- `spec_full_text` — the entire current spec (for cross-reference, do not
  rewrite anything else)

REWRITE RULES:

1. **Touch only this Requirement block.** Don't edit Purpose, sibling
   Requirements, or the meta footer.

2. **Remove the resolved marker.** Replace `<!-- [GAP: ...] -->` with nothing
   (delete the HTML comment) once the Scenario/THEN line reflects the answer.

3. **Preserve `**Source:**` citations.** Add new citations if the user
   referenced new file:line ranges or ticket IDs.

4. **If the answer reveals a new edge case**, add a new `#### Scenario:` for
   it — but only inside this Requirement. New cross-Requirement scenarios
   should surface as a new `[GAP]` instead (will be added to the queue).

5. **If the answer changes the RFC 2119 keyword** (e.g., user says "actually
   that's optional, not required"), update SHALL → MAY or vice versa.

6. **Follow draft_spec.md conventions** for Scenarios — same AND/BUT rules,
   same one-claim-per-scenario rule.

OUTPUT: the rewritten Requirement block as a full string, ready to splice
back into spec.md replacing the original block.

After splicing, the orchestrator (SKILL.md) will:
- Re-scan the modified spec for `[GAP]` markers.
- Append any NEW markers introduced by the rewrite to the question queue.
- Show the user a 2-line diff summary of what changed.
- Move to the next marker.
