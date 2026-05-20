You are resolving the user's `/inferspec-cap` argument to a concrete capability.

INPUT:
- `argv` — the raw argument(s) passed to /inferspec-cap. May be:
  - empty (no arg)
  - a slug like `user-auth`
  - a fuzzy phrase like "user auth", "rate limiting", "the login thing"
  - a slug followed by `--new` (force-bootstrap)
- `graphify-out/features.json` — list of known capabilities (may not exist)
- `openspec/specs/` directory (may not exist)

RESOLUTION RULES (apply in order, stop at first match):

1. **No features.json**: tell the user `/inferspec-scan` should run first.
   Offer to run it inline; if user agrees, run scan THEN restart cap resolution.

2. **Empty argv**: list every cap in features.json with its file count, plus a
   "(new)" option. Let user pick one. Resolved → cap.

3. **`--new` flag present**: bootstrap mode. Treat the slug before `--new` as
   the new cap's name; ask user for the relevant file paths (relative to repo
   root). Add the new cap to features.json. Resolved → new cap.

4. **Exact slug match in features.json**: resolved.

5. **Fuzzy phrase**: compute simple similarity (split phrase on whitespace,
   look for any token appearing in a slug or its file paths). Rank top 3.
   Show the user with file counts and ask them to pick. Resolved → chosen cap.

6. **No match at all**: tell the user and offer the empty-argv flow.

OUTPUT: a single resolved cap object `{name, files}`. Pass it to the next step
(source solicitation).

If the cap already has an `openspec/specs/<name>/spec.md`, also record:
- `existing_spec: true`
- `existing_markers: [<list of (file, line, marker text)>]`

These flow into the Q&A loop's initial queue.
