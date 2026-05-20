You are grouping files into product capabilities for spec inference.

INPUT:
- `graphify-out/graph.json` — AST + import graph for this repo
- `graphify-out/features.json` (if exists) — previous capability list

TASK:
1. Read graph.json. Identify clusters of files that serve one product capability.
2. Treat low-level utilities (`utils`, `common`, `config`, `logger`, telemetry) as
   "infrastructure" and SKIP them — they don't get specs.
3. Always include OpenAPI/Swagger spec files as their own capabilities
   (search `doc/`, `docs/`, `api/`, `openapi/`, `spec/`, `specs/` for files with
   `openapi:`, `swagger:`, or top-level `paths:` keys).
4. Output to `graphify-out/features.json`:
   ```json
   [
     {"name": "user-auth", "files": ["src/auth.py", "src/login.py"]},
     {"name": "order-mgmt", "files": ["src/order.py", "pages/order.vue"]}
   ]
   ```

Naming rules:
- kebab-case
- describe the capability, not the technology (`user-auth` not `auth-py`)
- 2-4 words

If features.json already exists, prefer keeping existing capability names so
hash-skip works across runs.
