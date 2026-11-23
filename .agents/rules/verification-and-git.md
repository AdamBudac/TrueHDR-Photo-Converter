---
description: Engineering verification discipline, API version checking, no-silent-failures rule, and Git/publishing boundaries.
---

# Verification, API Discipline & Git Boundaries

1. **Evidence Over Assumptions:**
   - After any non-trivial code change, verify affected functionality (syntax/lint, typecheck, unit/UI tests, or smoke test appropriate to the scope).
   - Never report an unverified assumption, a planned check, or a passing build alone as runtime verification. Clearly separate *actually verified* checks from *planned* or *skipped* checks.
   - Do not fabricate testing when only documentation changed.
2. **Verify Exact API Versions:**
   - Before designing or implementing against an external library or framework API, check official documentation (or `context7` / `microsoft-learn` / `deepwiki` MCP if connected) for the **pinned version** used in this project.
   - Do not confuse `latest` documentation with an older pinned version, and do not bypass dependency conflicts with `--force` or `--legacy-peer-deps`.
   - Ask before introducing a new external dependency; prefer existing dependencies and standard libraries.
3. **Minimal Diffs & No Silent Failures:**
   - Touch only code directly related to the current task; preserve existing unrelated code and user work-in-progress.
   - Detect invalid inputs, corrupted state, and failed writes explicitly and report them clearly; never swallow errors or silently fall back to degraded behavior.
4. **Git & GitHub Desktop Boundaries:**
   - Do not assume a `.git` repository exists during local development; the user maintains local folder backups while working and performs final commits, pushes, and releases manually via **GitHub Desktop**.
   - Never execute `git init`, `git add`, `git commit`, `git push`, `git rebase`, `git checkout`, `git reset`, tag releases, or publish/deploy without explicit user instruction.
5. **Communication Language:**
   - Communicate with the user and write plans in **Slovak**; keep code, identifiers, comments, logs, agent files, technical docs (`README-DEVELOPER.md`, `SPEC.md`, `README-AI-AGENT.md`), and primary public docs (`README.md`, `README-USER.md`) in **English**.
