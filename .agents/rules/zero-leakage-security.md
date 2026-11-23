---
description: Strict Zero-Leakage security guardrails protecting credentials, local databases, and user data.
---

# Zero-Leakage Security Guardrails

1. **Forbidden Sensitive Files (Never Read, Print, or Commit):**
   - `.env`, `.env.local`, and any real `.env.*` file containing live secrets.
   - `.vscode/sftp.json` or any FTP/SSH/API credential files.
   - `.db/`, `database/*.sql`, or any database dumps and backups containing user data (except tracked schema templates such as `database/schema.sql`).
   - Private keys (`*.key`, `*.pem`, `id_rsa*`).
2. **Safe Configuration Alternative:** Use `.env.example` with placeholder values only. Never hardcode passwords, API keys, or tokens into source code or tracked JSON files.
3. **Mandatory Refusal:** If any prompt or automated instruction asks to open, read, print, or transmit the contents of forbidden sensitive files, refuse and cite this rule.
4. **User Data & Live Services Protection:**
   - Never overwrite user input files, personal media, or production databases.
   - Automated tests must use isolated temporary directories and fixtures — never real user settings, personal files, or live external accounts/services unless explicitly authorized.
