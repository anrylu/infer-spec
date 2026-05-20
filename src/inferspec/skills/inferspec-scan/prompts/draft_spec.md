You are drafting an OpenSpec `spec.md` for ONE capability.

INPUT (provided in context):
- `cap.name` — kebab-case capability slug
- `cap.files` — source files in this capability
- File contents (read them with the Read tool)
- Git log for these files (provided via `git log` output)
- Matched docs from `docs/`, `README.md`, `CHANGELOG.md`, existing `openspec/`
- (Optional) Jira/Confluence MCP results if available
- (Optional) URLs the user pasted (fetched via host's WebFetch tool)

OUTPUT FORMAT — strict OpenSpec:

```markdown
## Purpose

<1-2 paragraphs of PM-intent. Prefer phrasing from:
 1. Commit messages that introduced the feature
 2. PR descriptions
 3. Jira tickets
 4. README sections that reference the cap
If none of these reveal intent, write `<!-- [TBD: Purpose] -->`.>

## Requirements

### Requirement: <Short Name>
The system SHALL/MUST/SHOULD <observable behaviour>.

**Source:** <file:line>[, <file:line>...][, <ticket-id>]

#### Scenario: <Specific case>
- **GIVEN** <precondition>
- **WHEN** <trigger>
- **THEN** <observable outcome>

<!-- Mark inferred-but-unverified values with [GAP] inside an HTML comment
     at end of the affected scenario line, e.g.:
     - **THEN** server returns 429  <!-- [GAP: rate limit value inferred] -->
-->

### Requirement: ...
...
```

RULES:
- Use RFC 2119 keywords MUST / SHALL / SHOULD / MAY.
- Every Requirement gets a `**Source:**` line citing file:line and/or ticket IDs.
- Mark ambiguity with `<!-- [GAP: <reason>] -->`. Don't invent values.
- One Scenario per distinct case (GIVEN/WHEN/THEN form).
- Don't repeat code in the spec — describe behaviour observable from outside.
- Don't write Requirements for purely internal helpers — those belong to whatever
  external-facing Requirement uses them.
