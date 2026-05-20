You are gathering external context for the resolved capability BEFORE drafting.

This step is what distinguishes /inferspec-cap from /inferspec-scan. Scan is
passive; cap actively asks the user.

INPUT:
- `cap` — resolved `{name, files}` from Step 1
- Available host tools — check whether `mcp__*__jira_*`, `mcp__*__confluence_*`,
  and a WebFetch-like tool are present.

ASK SEQUENCE (one prompt at a time; user may answer "skip" to any):

1. **Jira tickets** (only if Jira MCP available):
   "Any Jira ticket(s) for `<cap.name>`? Paste IDs (e.g. `AUTH-456, AUTH-789`) or 'skip'."
   - Parse IDs from reply; fetch each via the Jira MCP. Collect title + description + recent comments.

2. **Confluence pages** (only if Confluence MCP available):
   "Any Confluence page(s) for `<cap.name>`? Paste URLs or page IDs, or 'skip'."
   - Fetch each via the Confluence MCP. Collect page body.

3. **External context** — either MERGED or SPLIT depending on host:

   **If at least one of Jira/Confluence MCP is present** (split form):
   - 3a. URLs: "Any other docs to consult (PR threads, design pages, RFCs)? Paste URL(s) or 'skip'."
   - 3b. Hand-pasted: "Anything else I should know about `<cap.name>`? Paste text or 'skip'."

   **If NEITHER Jira nor Confluence MCP is present** (merged form — recommended in this case):
   - 3. "Any external context to add for `<cap.name>`? Paste URL(s), notes, or 'skip'."
   - Parse the reply: any `https?://...` matches are URLs (fetch each via the host's WebFetch); the remaining text is treated as freeform notes. If the reply is exactly `skip` (case-insensitive), treat both as empty.

   Rationale: when there are no ticketing/wiki tools to interrogate, the
   common case is "nothing to add". A single prompt collapses 2 turns of
   "skip" into 1 without losing any capability.

Collect everything into a `cap.external_context` dict:
```json
{
  "jira": [{"id": "AUTH-456", "title": "...", "body": "..."}],
  "confluence": [{"url": "...", "title": "...", "body": "..."}],
  "urls": [{"url": "...", "body": "..."}],
  "freeform": "...user-pasted text..."
}
```

Token budget: cap entire `external_context` at ~8K tokens. Summarise lengthy
Jira/Confluence bodies; keep titles, acceptance criteria, and any explicit
numbers (limits, timeouts, etc.) verbatim.

Pass `cap.external_context` to drafting and to the Q&A loop.
