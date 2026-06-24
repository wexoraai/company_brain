# System Runbook: The Company Brain

This runbook outlines operational procedures for deploying, backing up, restoring, rotating credentials, and adding new integrations to **The Company Brain**.

---

## 1. Deployment Procedures

### Production Deploy (Dockerized VPS / Railway / Render)
1. **Provision a PostgreSQL instances** with `pgvector` enabled (e.g., Supabase, Neon, or self-hosted).
2. **Setup environment variables** in the hosting platform's dashboard:
   - `DATABASE_URL`: Connection string pointing to the production database.
   - `GEMINI_API_KEY`: Production Google AI Studio API key.
   - `SECRET_KEY`: A cryptographically secure random string.
3. **Deploy the container**:
   - The included `Dockerfile` can be used to build and deploy.
   - Ensure the server exposes port `8000` (or the configured `PORT`).

---

## 2. Backup & Restoration

### Backup Database
To back up the PostgreSQL database manually:
```bash
docker exec -t company_brain_db pg_dump -U postgres -d company_brain > backup.sql
```

### Restore Database
To restore the database from a backup SQL dump:
1. Ensure the target database exists.
2. Run the restore command:
   ```bash
   cat backup.sql | docker exec -i company_brain_db psql -U postgres -d company_brain
   ```

### Document Uploads Backup
All uploaded documents are stored in the folder configured by `UPLOAD_DIR` (default `./uploads`). Ensure this directory is backed up regularly to secure cloud storage (e.g., AWS S3 or Cloudflare R2).

## 3. 2FA Setup & Security Enforcement
For security and privacy policies, see [SECURITY.md](file:///c:/Users/darshan/Downloads/company_brain/SECURITY.md).

### Setting Up MFA for Admins/Engineers
1. When creating a new corporate account, immediately configure **2-Factor Authentication (MFA)**.
2. Store the **MFA Recovery Codes** directly in the shared Bitwarden vault under a secure note named `[Service Name] MFA Recovery Codes`.
3. If sharing an account login, generate the Authenticator TOTP token inside the Bitwarden item itself so all authorized team members can generate the 2FA code during login.

---

## 4. Off-boarding & Secret Rotation Checklist

When an engineer leaves the company or a security breach is suspected, rotate credentials in this order:
1. **GitHub Organization**: Remove the user from the organization members list. This automatically revokes their access to all repositories.
2. **Bitwarden Vault**:
   - Change the vault master password.
   - De-authorize the leaver's personal access to the vault.
3. **MFA & 2FA Reset**:
   - Regenerate recovery codes for shared accounts.
   - De-authorize active sessions on Google Workspace, Supabase, and GitHub.
4. **API Keys**:
   - Deactivate the old Google Gemini / Anthropic API keys. Generate new keys and update the configurations.
   - Rotate Zoho CRM, Zoho Books, and Retell Voice agent keys.
5. **Database Credentials**:
   - Change the PostgreSQL / Supabase user passwords.
   - Update the `DATABASE_URL` config variable.
   - Restart the server process to apply changes.
6. **Secret Key**:
   - Rotate the `SECRET_KEY` in environment configurations. Note: This will invalidate all active user session cookies.
