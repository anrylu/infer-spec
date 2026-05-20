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

3. **Arbitrary URLs** (always — relies on host's WebFetch):
   "Any other docs to consult (PR threads, design pages, RFCs)? Paste URL(s) or 'skip'."
   - For each URL, use the host's WebFetch tool. Collect rendered body text.

4. **Hand-pasted text** (always):
   "Anything else I should know about `<cap.name>`? Paste text or 'skip'."

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
